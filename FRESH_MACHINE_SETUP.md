# Fresh Machine Training Setup Guide
# Ultimate Game NPC Engine — Complete From-Scratch Installation

This document covers **everything** you must install on a brand new computer
before you can train the NPC AI model. Follow every step in order.
Do not skip any section.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 0 — MINIMUM HARDWARE REQUIREMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| Component     | Minimum                     | Recommended               |
|---------------|-----------------------------|---------------------------|
| GPU           | NVIDIA RTX 3060 (12 GB VRAM)| RTX 4090 / RTX 5090       |
| CPU           | 8-core CPU                  | 16-core CPU               |
| RAM           | 16 GB                       | 32 GB                     |
| Storage       | 60 GB free                  | 100 GB free (SSD)         |
| OS            | Windows 10/11 (64-bit)      | Windows 11 (64-bit)       |
| Internet      | Required for downloads      | Fast connection (>50 Mbps)|

WHY 60 GB?
  - CUDA Toolkit installer:      ~3 GB
  - cuDNN:                       ~1 GB
  - Python + venv packages:      ~8 GB
  - Gemma-2 2B base model:       ~5 GB (downloaded once by Unsloth)
  - Training outputs:            ~3 GB
  - Dataset (Airoboros):         ~2 GB
  - TOTAL SAFE ESTIMATE:         ~22 GB  (60 GB gives you breathing room)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 1 — NVIDIA GPU DRIVER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This is the foundation. Everything else requires the GPU driver first.

STEP 1.1 — Download NVIDIA Driver
  URL: https://www.nvidia.com/en-us/drivers/
  - Click "Game Ready Driver" or "Studio Driver"
  - Select your GPU model (e.g., RTX 4070, RTX 5050)
  - Download the .exe file (~600 MB)

STEP 1.2 — Install Driver
  - Run the downloaded .exe
  - Choose "Custom Installation"
  - Check "Clean Installation" checkbox (important for fresh machines)
  - Click Next → Restart the computer

STEP 1.3 — Verify Driver Installed
  Open PowerShell and run:
    nvidia-smi

  You should see output like:
    +-----------------------------------------------------------------------------+
    | NVIDIA-SMI 546.33     Driver Version: 546.33    CUDA Version: 12.3         |
    +-----------------------------------------------------------------------------+

  If nvidia-smi does not work, the driver is not installed correctly. Reinstall.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 2 — INSTALL WSL 2 (WINDOWS SUBSYSTEM FOR LINUX)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHY IS THIS REQUIRED?
  Unsloth (the training speed library we use) compiles Triton CUDA kernels.
  Triton only runs on Linux. Without WSL, training will either fail or run
  at 10x slower speed. WSL IS NOT OPTIONAL.

STEP 2.1 — Enable WSL
  Open PowerShell AS ADMINISTRATOR and run:
    wsl --install

  This command automatically:
    - Enables the WSL feature
    - Enables Virtual Machine Platform
    - Installs Ubuntu (the default Linux distribution)
    - Downloads the Linux kernel

  If WSL was already partially installed, run this instead:
    wsl --install -d Ubuntu-22.04

STEP 2.2 — Restart the Computer
  WSL requires a full reboot to complete installation.

STEP 2.3 — Set Up Ubuntu User
  After reboot, the Ubuntu terminal will open automatically.
  Create your Linux username and password when prompted.
  Remember this password — you will need it for sudo commands.

STEP 2.4 — Set WSL 2 as Default (Important)
  In PowerShell (as Admin):
    wsl --set-default-version 2

STEP 2.5 — Verify WSL 2 Is Running
  In PowerShell:
    wsl --list --verbose

  You should see:
    NAME            STATE    VERSION
    Ubuntu-22.04    Running  2

  VERSION must be 2. If it says 1, run:
    wsl --set-version Ubuntu-22.04 2

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 3 — CUDA TOOLKIT (INSIDE WSL)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

NOTE: The GPU driver you installed in Section 1 provides the CUDA runtime
for Windows. But WSL needs its own CUDA toolkit for compiling Triton kernels.

Open WSL Ubuntu terminal and run ALL of the following commands:

STEP 3.1 — Update Ubuntu First
  sudo apt-get update
  sudo apt-get upgrade -y

STEP 3.2 — Install CUDA 12.1 Toolkit in WSL
  (Copy and paste each line exactly as shown)

  wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-wsl-ubuntu.pin
  sudo mv cuda-wsl-ubuntu.pin /etc/apt/preferences.d/cuda-repository-pin-600

  wget https://developer.download.nvidia.com/compute/cuda/12.1.0/local_installers/cuda-repo-wsl-ubuntu-12-1-local_12.1.0-1_amd64.deb
  sudo dpkg -i cuda-repo-wsl-ubuntu-12-1-local_12.1.0-1_amd64.deb

  sudo cp /var/cuda-repo-wsl-ubuntu-12-1-local/cuda-*-keyring.gpg /usr/share/keyrings/
  sudo apt-get update
  sudo apt-get -y install cuda

STEP 3.3 — Add CUDA to PATH
  Open the bash profile file:
    nano ~/.bashrc

  Scroll to the very bottom and add these 2 lines:
    export PATH=/usr/local/cuda-12.1/bin:$PATH
    export LD_LIBRARY_PATH=/usr/local/cuda-12.1/lib64:$LD_LIBRARY_PATH

  Save the file: Press Ctrl+X, then Y, then Enter.

  Reload the profile:
    source ~/.bashrc

STEP 3.4 — Verify CUDA Is Working
  nvcc --version

  Expected output:
    nvcc: NVIDIA (R) Cuda compiler driver
    Cuda compilation tools, release 12.1, V12.1.66

  Also verify the GPU is visible from WSL:
    nvidia-smi

  You should see the same GPU info as on Windows.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 4 — GIT (INSIDE WSL)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Git is needed to download Unsloth from GitHub (it is not on PyPI).

  sudo apt-get install git -y

  Verify:
    git --version
  Expected: git version 2.x.x

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 5 — PYTHON 3.11 (INSIDE WSL)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHY PYTHON 3.11 SPECIFICALLY?
  Unsloth is tested and guaranteed on Python 3.11.
  Python 3.12 has breaking changes with some ML packages.
  Python 3.10 is too old for several dependencies.
  USE 3.11 ONLY.

STEP 5.1 — Add Python 3.11 Repository
  sudo apt-get install software-properties-common -y
  sudo add-apt-repository ppa:deadsnakes/ppa -y
  sudo apt-get update

STEP 5.2 — Install Python 3.11
  sudo apt-get install python3.11 python3.11-venv python3.11-dev -y

STEP 5.3 — Install pip for Python 3.11
  curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

STEP 5.4 — Verify Python
  python3.11 --version
  Expected: Python 3.11.x

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 6 — HUGGING FACE ACCOUNT + CLI TOKEN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHY IS THIS NEEDED?
  Gemma-2 is a gated model. Google requires you to accept a license agreement
  before you can download it. Without this, the download will fail with a 401
  Unauthorized error.

STEP 6.1 — Create a Hugging Face Account
  Go to: https://huggingface.co/
  Click "Sign Up" and create a free account.

STEP 6.2 — Accept the Gemma License
  Go to: https://huggingface.co/unsloth/gemma-2-2b-it
  Click "Agree and access repository" button.
  (You must be logged in for this to work.)

STEP 6.3 — Create a Hugging Face Token
  Go to: https://huggingface.co/settings/tokens
  Click "New token"
  Name it: "npc-training"
  Role: "Read"
  Click "Generate token"
  COPY THE TOKEN — you will only see it once.
  It looks like: hf_aBcDeFgHiJkLmNoPqRsTuVwXyZ

STEP 6.4 — Log In from WSL
  In WSL terminal:
    pip install huggingface_hub
    huggingface-cli login

  Paste your token when prompted.
  You should see: "Login successful"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 7 — CREATE PYTHON VIRTUAL ENVIRONMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHY A VIRTUAL ENVIRONMENT?
  A venv isolates all the packages for this project so they do not conflict
  with any other Python projects on the same machine.

STEP 7.1 — Navigate to the Project Folder
  In WSL, the Windows file system is mounted under /mnt/c/
  Your project is at:
    cd /mnt/c/Users/<your-username>/Downloads/xllm/game_npc_engine

  Replace <your-username> with your actual Windows username.

STEP 7.2 — Create the Virtual Environment
  python3.11 -m venv venv

STEP 7.3 — Activate the Virtual Environment
  source venv/bin/activate

  Your terminal prompt will change to show (venv) at the start:
    (venv) user@machine:~/...$ 

  IMPORTANT: Every time you open a new WSL terminal, you must
  run this activate command again before running any Python scripts.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 8 — INSTALL PYTORCH WITH CUDA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHY INSTALL PYTORCH SEPARATELY?
  If you just run pip install torch, you get the CPU-only version.
  You MUST install the CUDA version or training will run on CPU
  (which is 50-100x slower and will take days instead of hours).

STEP 8.1 — Install PyTorch with CUDA 12.1 Support
  (venv must be active — you should see (venv) in your prompt)

  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

STEP 8.2 — Verify PyTorch Sees the GPU
  python3.11 -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"

  Expected output (example):
    True
    NVIDIA GeForce RTX 4070

  If it prints False, PyTorch is using CPU mode. Do not proceed.
  Reinstall using the CUDA link above.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 9 — INSTALL UNSLOTH (MOST IMPORTANT PACKAGE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHY UNSLOTH?
  Unsloth makes Gemma-2 training 2x faster and uses 70% less VRAM.
  Without it, the 2B model would not fit in consumer GPU VRAM during training.
  Unsloth is NOT on PyPI (you cannot do pip install unsloth normally).
  It must be installed from GitHub.

STEP 9.1 — Install Unsloth from GitHub
  pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"

  This downloads and compiles Unsloth from source.
  It will take 3-10 minutes. This is normal.

STEP 9.2 — Install Unsloth's Companion Packages
  These must be installed with exact version constraints or they
  will conflict with Unsloth:

  pip install --no-deps "xformers<0.0.27" "trl<0.9.0" peft accelerate bitsandbytes

STEP 9.3 — Verify Unsloth Installed
  python3.11 -c "from unsloth import FastLanguageModel; print('Unsloth OK')"

  Expected: Unsloth OK

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 10 — INSTALL ALL OTHER PYTHON PACKAGES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Now install everything else from the requirements file:

  pip install -r requirements.txt

Below is a full list of what this installs and WHY each one is needed:

┌─────────────────────┬──────────────────────────────────────────────────────┐
│ Package             │ Purpose                                              │
├─────────────────────┼──────────────────────────────────────────────────────┤
│ datasets            │ Downloads the Airoboros roleplay training dataset     │
│                     │ from Hugging Face. Used by prepare_data.py           │
├─────────────────────┼──────────────────────────────────────────────────────┤
│ torch               │ PyTorch — the deep learning framework the model runs │
│                     │ on. Already installed in Section 8 (CUDA version)    │
├─────────────────────┼──────────────────────────────────────────────────────┤
│ transformers        │ Hugging Face Transformers library. Loads tokenizer,  │
│                     │ model config, and handles the Gemma-2 architecture   │
├─────────────────────┼──────────────────────────────────────────────────────┤
│ trl                 │ Transformer Reinforcement Learning library.          │
│                     │ Provides SFTTrainer which runs the fine-tuning loop  │
├─────────────────────┼──────────────────────────────────────────────────────┤
│ peft                │ Parameter-Efficient Fine-Tuning. Provides LoRA       │
│                     │ adapter layers — the core of QLoRA training          │
├─────────────────────┼──────────────────────────────────────────────────────┤
│ accelerate          │ Handles distributed training, mixed precision (fp16/ │
│                     │ bf16), and GPU memory management automatically       │
├─────────────────────┼──────────────────────────────────────────────────────┤
│ bitsandbytes        │ Enables 4-bit model quantization. Without this the  │
│                     │ model does not fit in VRAM and training will fail    │
├─────────────────────┼──────────────────────────────────────────────────────┤
│ fastapi             │ The web framework that runs npc_api.py server.       │
│                     │ Unity/Unreal/Godot connect to this API               │
├─────────────────────┼──────────────────────────────────────────────────────┤
│ uvicorn[standard]   │ ASGI server that runs FastAPI. The [standard] extra  │
│                     │ installs websocket and HTTP/2 support                │
├─────────────────────┼──────────────────────────────────────────────────────┤
│ pydantic            │ Request validation for FastAPI. Ensures bad data     │
│                     │ from game engines never reaches the AI model         │
├─────────────────────┼──────────────────────────────────────────────────────┤
│ python-multipart    │ Required for FastAPI to accept form data. Some game  │
│                     │ engine integrations send multipart requests          │
├─────────────────────┼──────────────────────────────────────────────────────┤
│ TTS                 │ Coqui TTS — the voice synthesis engine. Downloads    │
│                     │ XTTS-v2 model for NPC voice cloning                 │
├─────────────────────┼──────────────────────────────────────────────────────┤
│ soundfile           │ Reads and writes .wav audio files for voice output   │
├─────────────────────┼──────────────────────────────────────────────────────┤
│ pygame              │ Audio playback in the terminal test client           │
│                     │ (test_chat.py). Not needed for the API server itself │
├─────────────────────┼──────────────────────────────────────────────────────┤
│ requests            │ HTTP client used by test_chat.py and the stress test │
│                     │ tool to send requests to the running API             │
└─────────────────────┴──────────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 11 — MODEL DOWNLOAD (HAPPENS AUTOMATICALLY)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You do NOT need to manually download any model file.
When you run train_npc.py for the first time, Unsloth automatically:

  1. Downloads the base model: unsloth/gemma-2-2b-it (~5 GB)
     from: https://huggingface.co/unsloth/gemma-2-2b-it

  2. Caches it locally in: ~/.cache/huggingface/hub/

  3. You only download it ONCE. All future training runs use the cache.

  The Coqui TTS voice model (XTTS-v2, ~2 GB) is also downloaded
  automatically the first time npc_api.py starts, cached in:
    ~/.local/share/tts/

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 12 — SYSTEM-LEVEL LIBRARIES (WSL)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Some Python packages require system-level C libraries. Install them now:

  sudo apt-get install -y \
    build-essential \
    libsndfile1 \
    libportaudio2 \
    ffmpeg \
    curl \
    wget \
    unzip

What each one does:
  build-essential  → C/C++ compiler (gcc, g++) needed to compile Triton kernels
  libsndfile1      → C library for reading/writing audio files (soundfile needs it)
  libportaudio2    → Audio device library used by some TTS packages
  ffmpeg           → Audio/video conversion tool used by Coqui TTS internally
  curl / wget      → Download tools used in setup commands
  unzip            → Extracting downloaded archives

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 13 — FULL INSTALLATION CHECKLIST (QUICK REFERENCE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Use this as a checklist. Check each item as you complete it.

  [  ] NVIDIA GPU Driver installed (nvidia-smi works in PowerShell)
  [  ] WSL 2 installed (wsl --list --verbose shows VERSION = 2)
  [  ] Ubuntu 22.04 set up with username and password
  [  ] CUDA 12.1 installed inside WSL (nvcc --version works)
  [  ] CUDA PATH added to ~/.bashrc and sourced
  [  ] Git installed inside WSL (git --version works)
  [  ] Python 3.11 installed inside WSL (python3.11 --version works)
  [  ] pip installed for Python 3.11
  [  ] Hugging Face account created
  [  ] Gemma-2 license accepted on Hugging Face
  [  ] Hugging Face token created and saved
  [  ] huggingface-cli login done inside WSL
  [  ] System libraries installed (build-essential, libsndfile1, ffmpeg, etc.)
  [  ] Virtual environment created: python3.11 -m venv venv
  [  ] Virtual environment activated: source venv/bin/activate
  [  ] PyTorch (CUDA) installed and verified: torch.cuda.is_available() = True
  [  ] Unsloth installed from GitHub
  [  ] Unsloth companion packages installed (xformers, trl, peft, accelerate, bitsandbytes)
  [  ] All requirements installed: pip install -r requirements.txt
  [  ] Project files copied to this machine

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 14 — COPY PROJECT FILES TO THIS MACHINE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You need to get the project code onto the training machine.

OPTION A — USB Drive
  Copy the entire game_npc_engine folder to a USB drive.
  Plug the USB into the training machine.
  Copy to: C:\Users\<username>\Downloads\xllm\game_npc_engine

OPTION B — Git Repository (Recommended)
  On the training machine in WSL:
    git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
    cd game_npc_engine

OPTION C — Network Share
  Share the folder on your Windows network and map it on the training machine.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 15 — RUN TRAINING (AFTER ALL ABOVE IS DONE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Once everything above is installed, follow these steps in WSL:

  # Step 1: Navigate to the project
  cd /mnt/c/Users/<username>/Downloads/xllm/game_npc_engine

  # Step 2: Activate the virtual environment
  source venv/bin/activate

  # Step 3: Download and prepare the training dataset
  python3.11 prepare_data.py

  # Step 4: Run the training (takes 1-4 hours depending on GPU)
  python3.11 train_npc.py

  # Step 5: When training is complete, you will see:
  #   Training Complete!
  #   Your NPC Brain is saved in the 'npc_lora_model' folder.

  # Step 6: Copy the npc_lora_model folder back to your main machine
  #         (the one running the game engine / Unity / Unreal)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 16 — TROUBLESHOOTING COMMON ERRORS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ERROR: "CUDA out of memory"
  CAUSE:  The GPU does not have enough VRAM.
  FIX:    In train_npc.py, change:
            per_device_train_batch_size=2  →  per_device_train_batch_size=1
            gradient_accumulation_steps=4 →  gradient_accumulation_steps=8

ERROR: "nvidia-smi not found" inside WSL
  CAUSE:  The NVIDIA driver on Windows was not installed, or is too old.
  FIX:    Install / update the Windows GPU driver first (Section 1).
          nvidia-smi inside WSL reads from the Windows driver directly.
          Do NOT install a separate NVIDIA driver inside WSL.

ERROR: "401 Unauthorized" when downloading Gemma-2
  CAUSE:  You are not logged into Hugging Face, or you did not accept the
          Gemma-2 license agreement.
  FIX:    1. Go to https://huggingface.co/unsloth/gemma-2-2b-it
          2. Accept the license.
          3. Re-run: huggingface-cli login

ERROR: "ModuleNotFoundError: No module named 'unsloth'"
  CAUSE:  The virtual environment is not activated.
  FIX:    Run: source venv/bin/activate
          (You must do this every time you open a new terminal.)

ERROR: "torch.cuda.is_available() returns False"
  CAUSE:  PyTorch was installed without CUDA support.
  FIX:    Uninstall and reinstall PyTorch with the CUDA link:
    pip uninstall torch torchvision torchaudio -y
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

ERROR: "Triton compilation error" or "triton not found"
  CAUSE:  Unsloth requires triton which only works on Linux (WSL).
  FIX:    Make sure you are running inside WSL, not Windows PowerShell.

ERROR: "OSError: libsndfile.so not found"
  CAUSE:  libsndfile1 system library is missing.
  FIX:    sudo apt-get install libsndfile1 -y

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 17 — ESTIMATED TIME PER STEP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| Step                              | Estimated Time         |
|-----------------------------------|------------------------|
| NVIDIA Driver installation        | 5 minutes              |
| WSL 2 installation + Ubuntu setup | 10-15 minutes          |
| CUDA Toolkit download + install   | 20-40 minutes          |
| Python 3.11 installation          | 5 minutes              |
| Hugging Face account + token      | 5 minutes              |
| PyTorch (CUDA) installation       | 10-15 minutes          |
| Unsloth installation from GitHub  | 5-10 minutes           |
| All other pip packages            | 10-20 minutes          |
| Dataset download (Airoboros)      | 5-15 minutes           |
| Gemma-2 2B model download         | 10-30 minutes          |
| Training (3 epochs, RTX 4070)     | 1-2 hours              |
| Training (3 epochs, RTX 3060)     | 2-4 hours              |
| TOTAL SETUP + TRAINING            | ~4-6 hours first time  |

Second and future training runs:
  Models are cached. Dataset is already downloaded.
  Training only: ~1-2 hours.
