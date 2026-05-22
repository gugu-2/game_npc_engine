// Unreal Engine 5 NPC Engine Plugin
// File: NPCEnginePlugin.cpp

#include "NPCEnginePlugin.h"
#include "HttpModule.h"
#include "Misc/Guid.h"

UNPCEngineComponent::UNPCEngineComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
}

void UNPCEngineComponent::BeginPlay()
{
    Super::BeginPlay();
    // Auto-generate unique session ID from the actor's GUID + character name
    if (SessionID.IsEmpty())
    {
        SessionID = CharacterName + "_" + FGuid::NewGuid().ToString().Left(8);
    }
    UE_LOG(LogTemp, Log, TEXT("[NPCEngine] %s ready. Session: %s"), *CharacterName, *SessionID);
}

void UNPCEngineComponent::SpeakToNPC(const FString& PlayerMessage)
{
    if (bIsWaiting)
    {
        UE_LOG(LogTemp, Warning, TEXT("[NPCEngine] %s is still processing. Please wait."), *CharacterName);
        return;
    }
    if (PlayerMessage.TrimStartAndEnd().IsEmpty()) return;

    bIsWaiting = true;

    // Build JSON payload
    TSharedPtr<FJsonObject> JsonObj = MakeShareable(new FJsonObject());
    JsonObj->SetStringField("session_id",          SessionID);
    JsonObj->SetStringField("character_name",      CharacterName);
    JsonObj->SetStringField("character_persona",   CharacterPersona);
    JsonObj->SetStringField("player_message",      PlayerMessage);
    if (!VoiceReferenceWav.IsEmpty())
        JsonObj->SetStringField("voice_reference_wav", VoiceReferenceWav);

    FString JsonString;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&JsonString);
    FJsonSerializer::Serialize(JsonObj.ToSharedRef(), Writer);

    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> HttpReq = FHttpModule::Get().CreateRequest();
    HttpReq->SetURL(ServerURL + "/talk");
    HttpReq->SetVerb("POST");
    HttpReq->SetHeader("Content-Type", "application/json");
    HttpReq->SetContentAsString(JsonString);
    HttpReq->SetTimeout(60.0f);
    HttpReq->OnProcessRequestComplete().BindUObject(this, &UNPCEngineComponent::OnTalkResponseReceived);
    HttpReq->ProcessRequest();
}

void UNPCEngineComponent::OnTalkResponseReceived(FHttpRequestPtr Request,
                                                   FHttpResponsePtr Response,
                                                   bool bConnectedSuccessfully)
{
    bIsWaiting = false;

    if (!bConnectedSuccessfully || !Response.IsValid())
    {
        OnError.Broadcast("Could not connect to NPC Engine server.");
        return;
    }

    if (Response->GetResponseCode() != 200)
    {
        OnError.Broadcast(FString::Printf(TEXT("Server error %d"), Response->GetResponseCode()));
        return;
    }

    // Parse response
    TSharedPtr<FJsonObject> JsonObj;
    TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Response->GetContentAsString());
    if (!FJsonSerializer::Deserialize(Reader, JsonObj)) { return; }

    FNPCResponse NPCResp;
    NPCResp.Character = JsonObj->GetStringField("character");
    NPCResp.Dialogue  = JsonObj->GetStringField("dialogue");
    NPCResp.Emotion   = JsonObj->GetStringField("emotion");
    NPCResp.Trigger   = JsonObj->GetStringField("trigger");
    NPCResp.AudioFile = JsonObj->GetStringField("audio_file");

    UE_LOG(LogTemp, Log, TEXT("[%s][%s]: %s"), *NPCResp.Character, *NPCResp.Emotion.ToUpper(), *NPCResp.Dialogue);

    // Fire dialogue event
    OnDialogueReceived.Broadcast(NPCResp);

    // Fire quest trigger event
    if (!NPCResp.Trigger.IsEmpty() && NPCResp.Trigger != "none")
    {
        UE_LOG(LogTemp, Log, TEXT("[NPCEngine] Quest trigger: %s"), *NPCResp.Trigger);
        OnQuestTriggered.Broadcast(NPCResp.Trigger);
    }

    // Download and play audio
    if (!NPCResp.AudioFile.IsEmpty())
    {
        DownloadAndPlayAudio(FPaths::GetCleanFilename(NPCResp.AudioFile));
    }
}

void UNPCEngineComponent::DownloadAndPlayAudio(const FString& AudioFilename)
{
    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> HttpReq = FHttpModule::Get().CreateRequest();
    HttpReq->SetURL(ServerURL + "/audio/" + AudioFilename);
    HttpReq->SetVerb("GET");
    HttpReq->OnProcessRequestComplete().BindUObject(
        this, &UNPCEngineComponent::OnAudioResponseReceived, AudioFilename);
    HttpReq->ProcessRequest();
}

void UNPCEngineComponent::OnAudioResponseReceived(FHttpRequestPtr Request,
                                                    FHttpResponsePtr Response,
                                                    bool bConnectedSuccessfully,
                                                    FString AudioFilename)
{
    if (!bConnectedSuccessfully || !Response.IsValid() || Response->GetResponseCode() != 200)
    {
        UE_LOG(LogTemp, Warning, TEXT("[NPCEngine] Audio fetch failed for %s"), *AudioFilename);
        return;
    }

    // Save to temp location and play via AudioComponent
    FString TempPath = FPaths::ProjectSavedDir() + "NPCAudio_" + AudioFilename;
    TArray<uint8> Content = Response->GetContent();
    FFileHelper::SaveArrayToFile(Content, *TempPath);
    UE_LOG(LogTemp, Log, TEXT("[NPCEngine] Audio saved to %s. Wire to UAudioComponent to play."), *TempPath);
    // NOTE: To auto-play, use GetOwner()->FindComponentByClass<UAudioComponent>() and load from TempPath.
}

void UNPCEngineComponent::ClearMemory()
{
    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> HttpReq = FHttpModule::Get().CreateRequest();
    HttpReq->SetURL(ServerURL + "/session/" + SessionID + "/" + CharacterName);
    HttpReq->SetVerb("DELETE");
    HttpReq->ProcessRequest();
    UE_LOG(LogTemp, Log, TEXT("[NPCEngine] Memory cleared for session %s"), *SessionID);
}

void UNPCEngineComponent::ReportGossipEvent(const FString& EventDescription, float GossipSpeed)
{
    TSharedPtr<FJsonObject> JsonObj = MakeShareable(new FJsonObject());
    JsonObj->SetStringField("source_npc",          CharacterName);
    JsonObj->SetStringField("player_session_id",   SessionID);
    JsonObj->SetStringField("event_description",   EventDescription);
    JsonObj->SetNumberField("gossip_speed",         GossipSpeed);

    FString JsonString;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&JsonString);
    FJsonSerializer::Serialize(JsonObj.ToSharedRef(), Writer);

    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> HttpReq = FHttpModule::Get().CreateRequest();
    HttpReq->SetURL(ServerURL + "/gossip");
    HttpReq->SetVerb("POST");
    HttpReq->SetHeader("Content-Type", "application/json");
    HttpReq->SetContentAsString(JsonString);
    HttpReq->ProcessRequest();
}

void UNPCEngineComponent::UpdateWorldState(const FString& WorldStateJson)
{
    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> HttpReq = FHttpModule::Get().CreateRequest();
    HttpReq->SetURL(ServerURL + "/world");
    HttpReq->SetVerb("PUT");
    HttpReq->SetHeader("Content-Type", "application/json");
    HttpReq->SetContentAsString(WorldStateJson);
    HttpReq->ProcessRequest();
}
