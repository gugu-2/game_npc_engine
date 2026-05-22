// Unreal Engine 5 NPC Engine Plugin
// File: NPCEnginePlugin.h
// Drop into your UE5 project: Source/YourGame/NPCEngine/NPCEnginePlugin.h

#pragma once

#include "CoreMinimal.h"
#include "HttpModule.h"
#include "Interfaces/IHttpRequest.h"
#include "Interfaces/IHttpResponse.h"
#include "Json.h"
#include "JsonUtilities.h"
#include "Sound/SoundWave.h"
#include "GameFramework/Actor.h"
#include "NPCEnginePlugin.generated.h"

// ─────────────────────────────────────────────────────────────
// Response struct (matches the Python API response JSON)
// ─────────────────────────────────────────────────────────────
USTRUCT(BlueprintType)
struct FNPCResponse
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly) FString Character;
    UPROPERTY(BlueprintReadOnly) FString Dialogue;
    UPROPERTY(BlueprintReadOnly) FString Emotion;
    UPROPERTY(BlueprintReadOnly) FString Trigger;
    UPROPERTY(BlueprintReadOnly) FString AudioFile;
};

// ─────────────────────────────────────────────────────────────
// Delegate types — fire these on your Blueprints/Components
// ─────────────────────────────────────────────────────────────
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnNPCDialogueReceived, const FNPCResponse&, Response);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnNPCError, const FString&, ErrorMessage);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnQuestTriggered, const FString&, TriggerName);

// ─────────────────────────────────────────────────────────────
// Main NPC Engine Component
// ─────────────────────────────────────────────────────────────
UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class YOURGAME_API UNPCEngineComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UNPCEngineComponent();

    // ── Inspector-editable properties ────────────────────────
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="NPC Engine|Server")
    FString ServerURL = "http://localhost:8000";

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="NPC Engine|Character")
    FString SessionID;  // Auto-generated on BeginPlay if empty

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="NPC Engine|Character")
    FString CharacterName = "NPC";

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="NPC Engine|Character",
              meta=(MultiLine=true))
    FString CharacterPersona = "A helpful village guard.";

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="NPC Engine|Voice")
    FString VoiceReferenceWav;  // Leave empty to use emotion-auto-select

    // ── Events (bind in Blueprints) ───────────────────────────
    UPROPERTY(BlueprintAssignable, Category="NPC Engine|Events")
    FOnNPCDialogueReceived OnDialogueReceived;

    UPROPERTY(BlueprintAssignable, Category="NPC Engine|Events")
    FOnNPCError OnError;

    UPROPERTY(BlueprintAssignable, Category="NPC Engine|Events")
    FOnQuestTriggered OnQuestTriggered;

    // ── Blueprint-callable functions ───────────────────────────
    UFUNCTION(BlueprintCallable, Category="NPC Engine")
    void SpeakToNPC(const FString& PlayerMessage);

    UFUNCTION(BlueprintCallable, Category="NPC Engine")
    void ClearMemory();

    UFUNCTION(BlueprintCallable, Category="NPC Engine")
    void ReportGossipEvent(const FString& EventDescription, float GossipSpeed = 0.7f);

    UFUNCTION(BlueprintCallable, Category="NPC Engine")
    void UpdateWorldState(const FString& WorldStateJson);

protected:
    virtual void BeginPlay() override;

private:
    bool bIsWaiting = false;

    void OnTalkResponseReceived(FHttpRequestPtr Request,
                                 FHttpResponsePtr Response,
                                 bool bConnectedSuccessfully);

    void DownloadAndPlayAudio(const FString& AudioFilename);
    void OnAudioResponseReceived(FHttpRequestPtr Request,
                                  FHttpResponsePtr Response,
                                  bool bConnectedSuccessfully,
                                  FString AudioFilename);
};
