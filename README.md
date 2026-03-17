# PermaScribe

Always-on audio transcription and daily AI summarization for Windows.

PermaScribe listens through your laptop microphone all day, transcribes speech to text locally using Whisper, and generates a structured end-of-day summary with action items using Ollama. The summary is delivered via email and a web dashboard accessible from any device on your network.

- **Transcription** runs locally on the laptop (no cloud, no API keys)
- **Summarization** uses Ollama (local or Ollama Pro cloud models)
- **Dashboard** is accessible from any device on the same network
- **Works on budget hardware** -- tested on $200-300 i5 laptops

---

## Requirements

- Windows 10 or 11
- Python 3.11+
- Ollama (with an Ollama Pro subscription for cloud models, or local models)
- A microphone (built-in or USB)
- Internet connection (only needed for Ollama Pro cloud models during summarization)

---

## Quick Start

```
1. Install Python    -->  https://www.python.org/downloads/  (check "Add to PATH")
2. Install Ollama    -->  https://ollama.com/download  (sign in to Pro)
3. Copy this folder to the laptop
4. Double-click install.bat
5. Double-click start.bat
6. Open http://localhost:5000
```

---

## Setup Guide

### Step 1: Install Python

1. Go to https://www.python.org/downloads/
2. Download Python 3.11 or newer
3. Run the installer
4. **Check the box "Add Python to PATH"** at the bottom of the first screen. This is the most common mistake.
5. Click "Install Now" and wait for it to finish

Verify: open a command prompt and run `python --version`. You should see `Python 3.x.x`.

### Step 2: Install Ollama

1. Go to https://ollama.com/download
2. Download and install Ollama for Windows
3. Ollama will appear in your system tray (bottom-right, near the clock)
4. Sign in to your Ollama Pro account via the system tray icon

Verify: open a command prompt and run `ollama --version`.

### Step 3: Copy PermaScribe to the Laptop

Copy the entire folder to the laptop using a USB drive, shared folder, or anything else. Put it somewhere like `C:\PermaScribe` or on the Desktop.

### Step 4: Run the Installer

1. Open the PermaScribe folder
2. Double-click `install.bat`
3. It checks for Python and Ollama, installs packages, pulls the AI model, and verifies everything
4. When it says "Setup Complete!", you're done

### Step 5: Disable Sleep

Since the laptop will be always-on and plugged in:

1. Right-click `disable_sleep.bat` and select "Run as administrator"
2. This prevents the laptop from sleeping or hibernating
3. The screen will still turn off after 5 minutes to save power -- recording continues fine with the screen off

### Step 6: Test It

1. Make sure a microphone is connected and Ollama is running (system tray icon)
2. Double-click `start.bat`
3. Talk for about a minute
4. Check that transcript files appear in `data/transcripts/`
5. Open http://localhost:5000 to see the dashboard
6. Click "Generate Summary Now" to test summarization
7. Press Ctrl+C to stop

### Step 7: Set Up Auto-Start

So it runs automatically when the laptop boots:

1. Right-click `setup_autostart.bat` and select "Run as administrator"
2. Restart the laptop to verify

To undo: `schtasks /delete /tn "PermaScribe" /f` (run as admin).

---

## Configuration

Edit `config.yaml` with Notepad. All settings have sensible defaults.

### Recording

```yaml
recording:
  chunk_duration: 30        # Seconds per audio chunk. 30 is a good default.
  silence_threshold: 50     # Audio quieter than this is skipped. Lower = more sensitive.
```

### Transcription

```yaml
transcription:
  model: "base"             # tiny = fastest, base = balanced (recommended), small = most accurate
  device: "cpu"             # cpu for budget laptops, cuda if you have an NVIDIA GPU
  language: "en"            # Language code, or null for auto-detect
```

### Summarization

```yaml
summarization:
  model: "deepseek-v3.1:671b-cloud"   # Any model available in Ollama
  trigger_time: "18:00"               # When to generate the daily summary (24h format)
  ollama_url: "http://localhost:11434"
```

### Email

```yaml
email:
  enabled: true
  smtp_host: "smtp.gmail.com"
  smtp_port: 587
  smtp_user: "you@gmail.com"
  smtp_password: "abcd efgh ijkl mnop"   # Gmail App Password, NOT your real password
  to: "you@gmail.com"
```

To get a Gmail App Password:
1. Enable 2-Factor Authentication at https://myaccount.google.com/security
2. Go to https://myaccount.google.com/apppasswords
3. Create a new password for "Mail" / "Other (PermaScribe)"
4. Copy the 16-character password into config.yaml

Other providers:
- Outlook: `smtp_host: "smtp-mail.outlook.com"`, port 587
- Yahoo: `smtp_host: "smtp.mail.yahoo.com"`, port 587 (needs app password)

### Web Dashboard

```yaml
web:
  host: "0.0.0.0"          # Accessible from other devices on the network
  port: 5000
```

The dashboard is at `http://<laptop-ip>:5000` from any device on the same network. To find the laptop's IP, run `ipconfig` in a command prompt and look for the IPv4 address.

---

## Daily Usage

Once set up, the laptop runs unattended:

- **All day:** Records and transcribes in the background
- **At the configured time:** Generates an AI summary and emails it to you
- **Dashboard:** Open `http://<laptop-ip>:5000` from any phone, tablet, or computer on the same network
- **Manual summary:** Click "Generate Summary Now" on the dashboard anytime
- **Raw transcripts:** Click "View Raw Transcripts" on the dashboard

The daily summary includes:
- Day overview
- Key conversations and topics
- Action items and to-dos
- Key decisions made
- Notable quotes

---

## Included Scripts

| Script | Purpose |
|---|---|
| `install.bat` | First-time setup: installs packages, pulls models, verifies everything |
| `start.bat` | Starts PermaScribe (with visible console window) |
| `check_setup.bat` | Diagnostic: checks Python, Ollama, mic, config |
| `setup_autostart.bat` | Registers PermaScribe to start on boot (run as admin) |
| `disable_sleep.bat` | Prevents sleep/hibernate for always-on operation (run as admin) |
| `run.pyw` | Silent launcher used by auto-start (no console window) |

---

## Architecture

PermaScribe runs as a single Python process with three background threads and a web server:

```
Microphone
    |
    v
[Recorder Thread]     Records 30-second WAV chunks, skips silence
    |
    v
[Transcriber Thread]  Converts audio to text using faster-whisper (local)
    |
    v
[Scheduler Thread]    At trigger time: groups transcripts into hourly blocks,
    |                 summarizes each block, then produces a final day summary
    v                 via Ollama. Sends email if configured.
[Flask Web Server]    Dashboard at http://0.0.0.0:5000
```

Summarization uses a **two-pass hierarchical approach** to handle full-day transcripts that exceed LLM context windows:
1. Transcripts are grouped into 1-hour blocks
2. Each block is summarized independently (~500 words each)
3. All hourly summaries are combined and fed into a final summary prompt

---

## File Structure

```
PermaScribe/
  permascribe/            Python source code
    main.py               Entry point
    recorder.py           Audio capture
    transcriber.py        Whisper transcription
    summarizer.py         Ollama summarization
    emailer.py            SMTP email delivery
    web.py                Flask dashboard
    config.py             Configuration loader
  templates/              HTML templates for the dashboard
  data/                   Created at runtime
    audio/                Raw WAV chunks (deleted after transcription)
    transcripts/          Text files organized by date
    summaries/            Markdown summaries organized by date
    permascribe.log       Application log
  config.yaml             User configuration
  requirements.txt        Python dependencies
```

---

## Troubleshooting

**"No module named 'yaml'" or other import errors**
Run `install.bat`, or manually: `pip install sounddevice numpy scipy faster-whisper flask pyyaml schedule markdown`

**No microphone detected**
Check Windows Settings > System > Sound > Input. If using USB, replug it.

**Transcripts appear but are empty or very short**
Lower `silence_threshold` in config.yaml (try 20 or 10). Speak closer to the mic.

**"Ollama unreachable" during summarization**
Make sure Ollama is running (system tray icon). Run `ollama list` to check. Make sure you have internet if using cloud models.

**"Python is not recognized as a command"**
Reinstall Python and check "Add to PATH", or manually add Python's install directory to your PATH environment variable.

**Dashboard won't load**
Make sure PermaScribe is running. Try http://127.0.0.1:5000. If port 5000 is taken, change `port` in config.yaml.

**Laptop runs slow**
Change Whisper model to "tiny" or increase `chunk_duration` to 60 in config.yaml.

**Recording stops when laptop is locked**
It shouldn't -- Windows keeps background processes running when locked. Make sure sleep is disabled (`disable_sleep.bat`). Check Settings > Privacy > Microphone to ensure mic access is enabled.

---

## Uninstalling

1. Remove auto-start: `schtasks /delete /tn "PermaScribe" /f` (run as admin)
2. Re-enable sleep: Settings > System > Power > set sleep back to your preference
3. Delete the PermaScribe folder
4. Optionally uninstall Python and Ollama from Settings > Apps

---

## License

MIT
