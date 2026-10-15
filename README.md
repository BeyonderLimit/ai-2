<p align="center"><img src="branding/ai2-logo.svg" width="420" alt="> AI-2"></p>

# AI-2

**Give your computer an AI brain.**

AI-2 turns an ordinary or old PC into a local AI machine that fits what that hardware can actually do. It detects
the machine, tunes it, measures what it can really manage, and recommends models that fit, locally where possible
and remotely only by explicit choice. Reference platform is Artix Linux with runit.

# AI-2 on Debian/Ubuntu

This is a port of the Post-Install AI-2 for Debian/Ubuntu original Repo [AI-2] (https://github.com/ProWoos-Devs/ai-2)

AI-2 turns Debian/Ubuntu into a local AI machine. This guide covers installation, configuration, and usage.

## Quick Start

There is no `ai2` package in Debian or Ubuntu — `sudo apt install ai2` fails with
`E: Unable to locate package ai2`. Setup has three parts:

1. **Install AI-2** into a virtual environment (see [Installation](#installation)).
2. **Provide the AI engine** — Debian ships no `ai2-llama-cpp` package, so build
   llama.cpp and put it in `/opt/ai2/llama` (see [Installation](#installation)).
3. **Run** `sudo ai-2 wizard` — it tunes the system and offers a model.

Knowledge Pack and document search use the same engine to embed text, so they
work only after step 2.

## What AI-2 Does for You

- **Hardware detection**: Identifies CPU features (AVX2, SSE4.1, etc.) and picks the matching llama.cpp runtime
- **Tier assignment**: Recommends a configuration tier based on your RAM and cores
- **System tuning**: Installs zram/zswap for memory efficiency, earlyoom to prevent OOM kills, and disables unnecessary services
- **Model management**: Downloads and serves local LLMs (Qwen, Gemma, Smollm3, etc.)
- **Knowledge packs**: Indexes documents for AI-powered search and answers
- **Accessibility**: Screen reader and speech support for users with disabilities

## Installation

### 1. Install AI-2

AI-2 is **not** in the Debian or Ubuntu repositories and this project ships no
`.deb`. Stock Debian also has no `pip` for the system Python (`python3 -m pip`
prints `No module named pip`), and Debian 12 marks that Python as externally
managed (PEP 668), so even with `python3-pip` installed an install into it is
refused. Install into a virtual environment instead; Python 3.11+ is required.
Run these from the repository root — the directory holding `pyproject.toml`,
not the inner `ai2/` package directory:

```bash
sudo apt install git python3-venv              # git to clone, venv for the isolated pip
git clone https://github.com/ProWoos-Devs/ai-2.git
cd ai-2                                        # the repo root (has pyproject.toml)
python3 -m venv ~/.local/venvs/ai2
~/.local/venvs/ai2/bin/pip install -e .        # fetches PyYAML + setuptools (network)

# the wizard tunes the system, so root must find the command too:
sudo ln -sf ~/.local/venvs/ai2/bin/ai-2 /usr/local/bin/ai-2
sudo ln -sf ~/.local/venvs/ai2/bin/AI-2 /usr/local/bin/AI-2
```

The editable install leaves an `ai2.egg-info/` directory in the checkout; git
ignores it.

### 2. Provide the AI engine

The **inference engine is not packaged for Debian**: `ai2-llama-cpp` is an
Artix package and does not exist here, so `sudo ai-2 runtime install` will say
so. Build llama.cpp and place the two binaries AI-2 runs — `llama-bench` (for
the AI Score) and `llama-server` (for chat and for embedding documents) — in
`/opt/ai2/llama`, the directory AI-2 searches first:

```bash

sudo mkdir -pv /opt/ai2/llama

sudo apt install build-essential cmake
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
cmake -B build                                   # CPU build; no CUDA needed
cmake --build build --config Release -j"$(nproc)"
ln -s build/bin/llama-server
ln -s build/bin/llama-bench

sudo cp llama-* /opt/ai2/llama/

sudo ai-2 wizard
```

Then `sudo ai-2 doctor` should report `ok  AI engine  <variant> build at
/opt/ai2/llama`. AI-2 also looks in `/usr/lib/ai2/runtimes/llama.cpp`,
`/usr/lib/ai2/runtimes/llama.cpp-<variant>`, and `~/llama`. Instead of copying
the binaries, you can point `AI2_RUNTIME_DIR` at your build's `build/bin`; that
variable must reach the root process too, so use
`sudo AI2_RUNTIME_DIR=/path/to/build/bin ai-2 ...`, or just use
`/opt/ai2/llama`, which needs no variable.

Once a `llama-bench` answers for your CPU, `sudo ai-2 init --apply` skips the
engine-package step instead of failing on a package Debian does not have.

## First-Time Setup

Run the wizard:

```bash
sudo ai-2 wizard
```

The wizard will:
1. Detect your hardware (CPU, RAM, GPU)
2. Assign a tier (Tiny, Light, Standard, Creator, Studio, or Workstation)
3. Look for the llama.cpp runtime for your CPU variant. With step 2 of
   Installation done it finds `/opt/ai2/llama`; without it, it says what is
   missing and how to provide it, and the tuning still applies
4. Tune your system (zram/swap, earlyoom, disable idle-suspend, sysctl)
5. Offer to download a chat model

You can run the wizard at any time to reconfigure or update. The same tuning
runs non-interactively as:

```bash
sudo ai-2 init --apply
```

With the engine in place this finishes with no failing step; if you have not
built llama.cpp yet, the tuning still applies and the engine step reports what
is missing.

## Using AI-2

### Chat with the AI

```bash
ai-2 chat
```

This starts the local AI server and opens a browser window. Use `ai-2 chat --terminal` for headless or accessibility use.

### Ask the AI a Question

```bash
ai-2 chat --terminal
```

Type the question and press Enter; `ai-2 chat` (without `--terminal`) opens the
same AI as a browser page. To ask about your own documents instead, index them
and use `ai-2 doc ask "..."` (see below).

### Search Your Documents

Knowledge Packs ship ready to search; install one, then search it (no AI model
is used — the passages are shown with their source):

```bash
ai-2 knowledge install ai2-help
ai-2 doc search "Linux security best practices"
```

Index your own files and have the AI answer from them with `ai-2 doc index FILE`
and `ai-2 doc ask "..."`. Both need the engine from Installation: the query is
embedded with it.

### Benchmark Your System

The AI Score is measured on one fixed model (Qwen2.5 0.5B Instruct, ~380 MB) so
scores compare across machines. Pull it once, then benchmark:

```bash
ai-2 model pull qwen2.5-0.5b
ai-2 benchmark
```

This prints your AI Score (0–100) from token generation speed, plus a
recommended local model. Use it to compare machines or track improvements.

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

Use the scheme the server actually serves: a `llama-server` on this machine
speaks plain `http://127.0.0.1:8080`, not `https://`. Asking for
`https://127.0.0.1:8080` fails with an SSL handshake timeout.

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

`sudo ai-2 runtime install` cannot fetch `ai2-llama-cpp` here: Debian and Ubuntu
have no such package. Build llama.cpp and point AI-2 at it (this is step 2 of
Installation):

- copy `llama-bench`/`llama-server` into `/opt/ai2/llama`, or
- set `AI2_RUNTIME_DIR` to the directory that holds them, or
- point at a server on another machine with `ai-2 remote set <url>` (no local runtime needed)

Once a `llama-bench` answers for your CPU, `sudo ai-2 init --apply` skips the
package step instead of failing on it. Note the directory must contain
`llama-bench`: that is how AI-2 recognizes an engine.

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

MIT, see `LICENSE`. Two small pieces derived from Artix Linux keep their own terms, see `LICENSES.md`.

## About

AI-2 is made by Rafael Minuesa (ProWoos, https://prowoos.com), built with Claude Code. MIT licensed; Artix Linux, llama.cpp and the models keep their own licenses (see `LICENSES.md`). Project page: https://prowoos.com/software-development/linux/ai-2/
