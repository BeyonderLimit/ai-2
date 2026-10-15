# AI-2 on Debian/Ubuntu

AI-2 turns Debian/Ubuntu into a local AI machine. This guide covers installation, configuration, and usage.

## Quick Start

There is no `ai2` package in Debian or Ubuntu — `sudo apt install ai2` fails with
`E: Unable to locate package ai2`. Install AI-2 into a virtual environment
(see Installation), then:

```bash
sudo ai-2 wizard
```

The setup tunes the system and walks you through choosing a model. It does not
install the AI engine here: `ai2-llama-cpp` is an Artix package, so provide a
llama.cpp build yourself (see Installation).

## What AI-2 Does for You

- **Hardware detection**: Identifies CPU features (AVX2, SSE4.1, etc.) and picks the matching llama.cpp runtime
- **Tier assignment**: Recommends a configuration tier based on your RAM and cores
- **System tuning**: Installs zram/zswap for memory efficiency, earlyoom to prevent OOM kills, and disables unnecessary services
- **Model management**: Downloads and serves local LLMs (Qwen, Gemma, Smollm3, etc.)
- **Knowledge packs**: Indexes documents for AI-powered search and answers
- **Accessibility**: Screen reader and speech support for users with disabilities

## Installation

AI-2 is **not** in the Debian or Ubuntu repositories and this project ships no
`.deb`. Stock Debian also has no `pip` for the system Python (`python3 -m pip`
prints `No module named pip`), and Debian 12 marks that Python as externally
managed (PEP 668), so even with `python3-pip` installed an install into it is
refused. Install into a virtual environment instead; Python 3.11+ is required.
Run these from the repository root — the directory holding `pyproject.toml`,
not the inner `ai2/` package directory:

```bash
git clone https://github.com/ProWoos-Devs/ai-2.git
cd ai-2                                       # the repo root (has pyproject.toml)
sudo apt install python3-venv                 # the venv module and its pip
python3 -m venv ~/.local/venvs/ai2
~/.local/venvs/ai2/bin/pip install -e .       # fetches PyYAML + setuptools (network)

# the wizard tunes the system, so root must find the command too:
sudo ln -sf ~/.local/venvs/ai2/bin/ai-2 /usr/local/bin/ai-2
sudo ln -sf ~/.local/venvs/ai2/bin/AI-2 /usr/local/bin/AI-2
```

Then run `sudo ai-2 wizard`. The editable install leaves an `ai2.egg-info/`
directory in the checkout; git ignores it.

System tuning goes through apt and systemd (zram-generator, earlyoom), which
this path supports. The **inference engine is not packaged for Debian**: the
`ai2-llama-cpp` package installed by the ISO and the Artix repository does not
exist here, so `sudo ai-2 runtime install` will tell you to build it yourself.
Install llama.cpp (`llama-bench`, `llama-server`) and put it where AI-2 looks —
`/opt/ai2/llama`, or set `AI2_RUNTIME_DIR` — or use `ai-2 remote` to point at a
server running elsewhere.

## First-Time Setup

Run the wizard:

```bash
sudo ai-2 wizard
```

The wizard will:
1. Detect your hardware (CPU, RAM, GPU)
2. Assign a tier (Tiny, Light, Standard, Creator, Studio, or Workstation)
3. Look for the llama.cpp runtime for your CPU variant (on Debian it will not be
   installed by a package — see Installation — and the wizard says so)
4. Tune your system (zram, earlyoom, disable unnecessary services)
5. Offer to download a chat model

You can run the wizard at any time to reconfigure or update.

## Using AI-2

### Chat with the AI

```bash
ai-2 chat
```

This starts the local AI server and opens a browser window. Use `ai-2 chat --terminal` for headless or accessibility use.

### Run Commands with AI

```bash
ai-2 doc "How do I install nginx on Debian?"
```

### Search Your Documents

```bash
ai-2 knowledge install ai2-help
ai-2 doc search "Linux security best practices"
```

### Benchmark Your System

```bash
sudo ai-2 benchmark
```

This measures your AI Score (0–100) based on token generation speed. Use it to compare machines or track improvements.

### Manage Models

```bash
ai-2 model list          # Show installed models
ai-2 model pull <id>     # Download a model
ai-2 model rm <id>       # Remove a model
ai-2 model verify        # Check model integrity
```

### Remote Inference

If your machine is too slow for larger models, use remote inference:

```bash
ai-2 remote set https://llama-server.example.com
ai-2 chat --remote
```

## Configuration

### Check Your Tier

```bash
ai-2 tier
```

### View System Profile

```bash
ai-2 profile
```

### Init System

AI-2 is configured for **systemd** (the default on Debian/Ubuntu). If you're using a different init system, file a bug.

### Reverting Changes

```bash
sudo ai-2 init --revert
```

This undoes all AI-2 tuning (zram, earlyoom, service changes) but leaves packages installed.

## Troubleshooting

### Runtime Not Installed

The `ai2-llama-cpp` package AI-2 installs on Artix does not exist in Debian or
Ubuntu, so `sudo ai-2 runtime install` cannot fetch it here and says so. Install
llama.cpp yourself and point AI-2 at it:

- Build llama.cpp and copy `llama-bench`/`llama-server` into `/opt/ai2/llama`, or
- set `AI2_RUNTIME_DIR` to the directory that holds them, or
- point at a server on another machine with `ai-2 remote set <url>` (no local runtime needed)

### OOM Kills

If your system is swapping heavily, run `ai-2 init --revert` to disable zram, or manually increase swap space.

### GPU Not Detected

AI-2 runs on the CPU by default. GPUs are detected but not used for inference. To enable GPU acceleration, you'll need to build a CUDA-enabled llama.cpp runtime.

### Accessibility Issues

For screen reader or speech support, run:

```bash
sudo ai-2 accessibility setup
```

## Reporting Issues

Before filing a bug, run:

```bash
sudo ai-2 doctor
sudo ai-2 report
```

Attach the generated report to your issue.

## License

AI-2 is MIT licensed. See the main README for details.

---

*AI-2 is built by the ProWoos-Devs community. For more information, see the main README.*
