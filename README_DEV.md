# Developer notes (local)

This repo lives on an external **exFAT** drive (`/media/jch903/fidelio1/...`). exFAT does **not** support the symlinks Python virtualenvs often use, so **do not** create `.venv/` inside the repo.

## Recommended setup

Use Python 3.13 (available on this machine) and keep the venv under your home directory:

```bash
python3.13 -m venv "$HOME/.venvs/PortalRecruit"
source "$HOME/.venvs/PortalRecruit/bin/activate"
python -m pip install -U pip
```

## Install dependencies (ML stack is core)

This project uses `sentence-transformers`, which depends on **PyTorch**.

### CPU (default)

If you install `torch` from PyPI on Linux it may pull CUDA wheels and can be **~1GB+**.
For most dev workflows here, **CPU torch** is sufficient.

Recommended:

```bash
pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision torchaudio
pip install -r requirements.txt
```

### GPU / CUDA

Install GPU torch following PyTorch’s official instructions for your CUDA version:

- https://pytorch.org/get-started/locally/

Then install project requirements:

```bash
pip install -r requirements.txt
```

## One-command bootstrap

CPU:

```bash
./scripts/bootstrap_local.sh
```

GPU (expects you already installed CUDA-enabled torch):

```bash
./scripts/bootstrap_gpu.sh
```

## Doctor (sanity checks)

```bash
python scripts/doctor.py
```

## Run

```bash
source "$HOME/.venvs/PortalRecruit/bin/activate"
python run_portalrecruit.py
# or
streamlit run src/dashboard/Home.py
```

## Data + secrets

- `*.env` is ignored. Keep real secrets in `.env` locally.
- `data/` is ignored and can be large (video clips, chroma db, sqlite, etc.).

