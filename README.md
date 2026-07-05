<!-- markdownlint-disable first-line-h1 -->
<!-- markdownlint-disable html -->
<!-- markdownlint-disable no-duplicate-header -->

<!-- docs-exclude-start -->
<div align="center">
    <a href="https://pluralis.ai/" target="_blank">
    <picture>
        <source media="(prefers-color-scheme: dark)" srcset="images/agora-logo-white.svg">
        <source media="(prefers-color-scheme: light)" srcset="images/agora-logo-black.svg">
        <img alt="PluralisResearch Agora Logo" src="images/agora-logo-black.svg" width="500px" style="max-width: 100%; margin-bottom: 30px">
    </picture>
    </a>
</div>
<div align="center">
    <a href="https://agora.pluralis.ai/"><img alt="Dashboard"
    src="https://img.shields.io/badge/Dashboard-Online-62BB47"/></a>
    <a href="https://pluralis.ai/"><img alt="Website"
    src="https://img.shields.io/badge/PluralisResearch-Website-6F02B5"/></a>
    <a href="https://pluralis.ai/docs/"><img alt="Docs"
    src="https://img.shields.io/badge/Docs-Website-C76e00"/></a>    
</div>

<div align="center">
    <img src="images/run-concluded-banner.svg" alt="The Pluralis-8B run has concluded. We're pleased to announce that the Pluralis-8B run has successfully completed after training 500B tokens over 7 weeks. We thank all the contributors!" width="760" style="max-width: 100%"/>
</div>
<!-- docs-exclude-end -->

## ✨ Description

Agora is a collaborative event powered by Protocol Learning, our decentralized approach to AI development.

Anyone with a 24 GB consumer GPU (e.g. an NVIDIA RTX 4090) can participate. Each participant hosts one pipeline stage of the model; participants can join and leave at any time, and adding more peers per stage increases data-parallel throughput within that stage.

By pooling compute from many sources, Agora makes it feasible to train larger models than any single participant's hardware could handle alone.

Full documentation: [pluralis.ai/docs](https://pluralis.ai/docs/).

<!-- docs-exclude-start -->
Each participant's progress is logged - check their contribution in the dashboard.

<div align="center">
  <a href="https://agora.pluralis.ai/">
    <img src="images/dashboard-button.svg" alt="Dashboard"/>
  </a>
</div>
      
## 📑 Table of Contents

- [Requirements](#-requirements)
- [Getting Started](#-getting-started)
- [Startup & Training](#-startup-training)
- [Important](#-important)
- [Troubleshooting](#-troubleshooting)
- [Citations](#-citations)
- [License](#-license)
- [Acknowledgements](#-acknowledgements)
<!-- docs-exclude-end -->
## 📋 Requirements

### Hardware Requirements

**PC/Server with Nvidia GPU:**

- Minimum 24GB GPU memory (RTX 4090 or equivalent)
- Minimum 80GB RAM per GPU (e.g. a 2-GPU machine needs 160GB total)
- Minimum 80GB disk space

### Supported GPUs

Meeting the minimum VRAM requirement above is necessary but not sufficient: the authorization service maintains an allowlist of validated GPU models, so a GPU with 24 GB+ VRAM may still be rejected if its model has not been validated yet. If your GPU is rejected with `GPU device not in allowlist: '<model>'`, please open an issue requesting it be added, and include:

- GPU model (e.g. the output of `nvidia-smi --query-gpu=name --format=csv,noheader`)
- VRAM size
- Host RAM
- OS, and instance type if running on a cloud provider

### Operating System Requirements

- Linux
- Windows + WSL2 ([enable CUDA support in WSL](https://docs.nvidia.com/cuda/wsl-user-guide/index.html))

### Network Requirements

- Stable internet connection with a minimum of 200 Mbps bandwidth. Note that some cloud providers advertise shared bandwidth split across multiple tenants — the effective throughput may be significantly lower than advertised.
- The port you are exposing (default is 49200) must be accessible to external connections.

### Cloud Services

Follow ([cloud services](https://pluralis.ai/docs/quick-start/setup-guides/cloud/)) for how to set up cloud instances that meet the requirements.

### Authentication

Create HuggingFace access token ([instruction](https://huggingface.co/docs/hub/en/security-tokens)). The token doesn't need any read/write permissions as it will only be used for authorization.

## 🚀 Getting Started

Before joining, check the live wait time on the [Dashboard](https://dashboard.pluralis.ai/). If joining is paused, check with the team for updates.

You will need a HuggingFace token — [create one here](https://huggingface.co/docs/hub/en/security-tokens) (no special permissions needed). Make sure port **49200** is open for inbound connections.

Then run:

```bash
git clone https://github.com/PluralisResearch/agora
cd agora
python3 agora_cli.py
```

The CLI will guide you through setup and start training. Your settings are saved automatically — next time, just run `python3 agora_cli.py` again.

Using an AI coding agent like Claude Code? Run it from inside the cloned repo and invoke `/agora-join` — the bundled skill ([`.claude/skills/agora-join/SKILL.md`](.claude/skills/agora-join/SKILL.md)) walks you through the same setup conversationally, launches the server, and watches the startup logs. Other agents (Cursor, Codex CLI) can read the same `SKILL.md` directly.

We recommend running with **Docker**. If Docker is not available, **Python 3.11** (exact version) is required, and we recommend running inside [tmux](https://github.com/tmux/tmux/wiki) or [screen](https://www.gnu.org/software/screen/) so the server keeps running when you disconnect.

To **stop**:

- **Native:** press `Ctrl + C`
- **Docker:** `docker stop <container> && docker rm <container>`

You can rejoin anytime — your contribution is saved.

### Multiple GPUs

To use more than one GPU on the same machine, run one instance per GPU:

```bash
python3 agora_cli.py --gpu_id 0
python3 agora_cli.py --gpu_id 1
```

When running natively, use a separate terminal for each GPU. When using Docker, each instance runs in its own container automatically.

Each GPU automatically gets its own port (49200, 49201, ...). Make sure each port is open.

### Advanced Options

The CLI prompts for everything interactively. You can also pass values directly:

| Flag | Description |
|------|-------------|
| `--gpu_id <ID>` | GPU to use (default: 0) |
| `--token <TOKEN>` | HuggingFace token |
| `--email <EMAIL>` | Email address (optional) |
| `--host_port <PORT>` | Listening port (default: 49200 + gpu_id) |
| `--announce_port <PORT>` | External port, if different from host_port (e.g. on RunPod) |
| `--use_docker` | Run inside Docker|
| `--log_file <PATH>` | Log file path (default: `logs/server_gpu<ID>.log`) — leave as default unless you have a specific reason |
| `--identity_path <PATH>` | Identity key path (default: `private_gpu<ID>.key`) — leave as default unless you have a specific reason |
| `--batch_size_override <N>` | Override the batch size defined in the config. Only set this if you hit CUDA out-of-memory errors with the default. |
| `--skip_input` | Non-interactive mode (all values must come from args or saved config) |
| `--reconfigure` | Re-prompt all settings from scratch |

### Manual Installation

> This section is optional. `agora_cli.py` is the recommended way to install and run — it handles everything automatically. The instructions below are for advanced users.

**Step 1 — Install dependencies**

*Docker:*

```bash
docker build . -t pluralis_agora --label image_version=1
```

*Native (no Docker):*

Requirements: Python 3.11, pip >= 25.3, NVIDIA GPU drivers with CUDA 12.8 support, conda.

```bash
# Create and activate a Python 3.11 environment
conda create -y -n agora python=3.11
conda activate agora

# Upgrade pip
pip install --upgrade "pip>=25.3"

# Install PyTorch with CUDA 12.8 support
pip install torch==2.7.0 --index-url https://download.pytorch.org/whl/cu128

# Install the two required packages from source
pip install --constraint constraints.txt --build-constraint constraints.txt -e ./agora_server
pip install --constraint constraints.txt --build-constraint constraints.txt -e ./agora
```

**Step 2 — Read runtime parameters**

`run.json` at the repo root contains values required by `run_server.py`:

| `run.json` field | `run_server.py` argument |
| --- | --- |
| `run_config` | `--config` |
| `auth_server` | `--auth_server` |
| `prom_gateway` | `--prom_gateway` |
| `seeds` (array) | `--initial_peers` |

```bash
RUN_CONFIG=$(jq -r '.run_config' run.json)
AUTH_SERVER=$(jq -r '.auth_server' run.json)
PROM_GATEWAY=$(jq -r '.prom_gateway' run.json)
SEEDS=$(jq -r '.seeds[]' run.json)
```

**Step 3 — Get your public IP**

```bash
PUBLIC_IP=$(curl -s https://api.ipify.org)
```

**Step 4 — Launch**

Default port convention: `49200 + gpu_id`. Each GPU on the same machine needs its own port.

*Native:*

```bash
CUDA_VISIBLE_DEVICES=<gpu_id> python3.11 agora/src/agora/run_server.py \
  --gpu_id <gpu_id> \
  --config "$RUN_CONFIG" \
  --token <hf_token> \
  --auth_server "$AUTH_SERVER" \
  --prom_gateway "$PROM_GATEWAY" \
  --host_maddrs /ip4/0.0.0.0/tcp/<port> \
  --announce_maddrs /ip4/$PUBLIC_IP/tcp/<port> \
  --initial_peers $SEEDS \
  --email <email> \
  --log_file logs/server_gpu<gpu_id>.log \
  --identity_path private_gpu<gpu_id>.key
```

*Docker:*

```bash
docker run -d --name agora_gpu<gpu_id> --ipc=host --network=host \
  --gpus device=<gpu_id> \
  -v $(pwd):/home -w /home \
  pluralis_agora \
  bash -c "CUDA_VISIBLE_DEVICES=0 python3.11 agora/src/agora/run_server.py \
    --gpu_id <gpu_id> \
    --config $RUN_CONFIG \
    --token <hf_token> \
    --auth_server $AUTH_SERVER \
    --prom_gateway $PROM_GATEWAY \
    --host_maddrs /ip4/0.0.0.0/tcp/<port> \
    --announce_maddrs /ip4/$PUBLIC_IP/tcp/<port> \
    --initial_peers $SEEDS \
    --email <email> \
    --log_file logs/server_gpu<gpu_id>.log \
    --identity_path private_gpu<gpu_id>.key"
```

## ✅ Startup & Training

When your node starts, it first runs network checks, downloads the model weights, and waits for authorization before training begins:

<pre>
[NETWORK]  Running internet speed test...
[DOWNLOAD] Downloading model weights...
[DOWNLOAD] Model weights downloaded. Waiting for authorization...
[AUTH]     Authorization queue: position <b>2</b>, estimated wait: <b>1m</b>
[AUTH]     Access granted for <b>your_user</b>
</pre>

Once authorized, training begins and you will see regular status updates:

<pre>
[SERVER]   Training started
[TRAINING] Training step <b>1</b>
[PROGRESS] Processed <b>51</b> batches in the last 60s
[PROGRESS]   Forward pass: 28 batches
[PROGRESS]   Backward pass: 23 batches
</pre>

If you see `Processed [N] batches` updates regularly, your node is working correctly.

When joining an active run, your node may first enter a **warmup period** to catch up with other nodes. During this time you will see:

<pre>
[WARMUP] Node warmup started, catching up with other nodes
</pre>

This is normal. Once the node has caught up, it will begin processing batches and you will see:

<pre>
[WARMUP] Node warmup complete
</pre>

Check `logs/server_gpu<ID>.log` for detailed logs.

## 🚨 Important

### private.key

The code generates a **private.key** file during initial setup. This file:

- Contains your node's cryptographic identity
- Is required for secure communication within the network
- Should be kept confidential and never shared publicly

### Docker files

All files created within the Docker container have a different level of ownership. To modify/delete them outside of the container, you need to reclaim ownership.

**Linux:**

```bash
sudo chown -R <linux_user> <path/to/project>
```

## 🔍 Troubleshooting

### Hardware & Environment

- **`Wrong pytorch version. Please install torch 2.7`**

    A PyTorch version other than 2.7.x is installed. If running via `python3 agora_cli.py`, the CLI installs the correct version automatically. For manual installs, run: `pip install torch==2.7.0 --index-url https://download.pytorch.org/whl/cu128`.

- **`CUDA is not available. Exiting run.`**

    No GPU was detected. Verify that NVIDIA drivers are installed (`nvidia-smi`), the CUDA toolkit is accessible, and (if using Docker) that the container was launched with `--gpus`.

- **`GPU is not eligible (GPU VRAM: X GB).`**

    The GPU does not meet the minimum VRAM requirement. A GPU with at least 24 GB VRAM is required.

- **`GPU device not in allowlist: '<model>'`**

    The GPU meets the minimum VRAM requirement but its model is not yet on the validated GPU allowlist. See [Supported GPUs](#supported-gpus) for how to request that your model be added.

### Authorization

- **`Verification failed.`**

    The verification process detected local modifications or a stale installation. Revert any local changes. Make sure you are using the latest version of the code.

- **`Port test failed. Make sure your port forwarding is correct`**

    The authorization server could not reach your node on the announced port. Verify that port **49200** (or your configured port) is open for inbound connections. Check firewall rules and cloud security groups.

- **`Authorization timeout after <N>s`**

    The node waited too long for authorization. This can happen during high demand. Restart the node to re-enter the authorization queue.

- **`Invalid HuggingFace token`**

    The token provided via `--token` is invalid or expired. [Create a new token](https://huggingface.co/docs/hub/en/security-tokens) (no special permissions required) and retry.

- **`This peer_id is already used by another user`**

    You are joining with a different HuggingFace account than the one that originally registered this node's `private.key`. Either use the original account, or delete `private.key` and restart to generate a new identity.

- **`This node is already in the authorization queue. Please remove private key from the node and try again.`**

    A node with this `private.key` is already queued. Delete `private.key` and restart.

- **`Download is too slow, please ensure sufficient bandwidth and try again.`**

    Your node took too long to download model weights, so it was dropped from the queue. Verify that your connection meets the 200 Mbps minimum and restart.

### Network & Connectivity

- **`An unknown connection error occurred. Exiting run.`**

    A fatal connection failure was detected. Verify your internet connection, check that no firewall is blocking outbound traffic, and restart the node.

### State Download & Training Runtime

- **`Too many failed all-reduce attempts. Exiting run.`**

    Multiple consecutive parameter averaging rounds timed out, indicating the node's internet connection is too slow or unstable. Check your connection speed and restart.

- **`Failed to connect to CUDA. Exiting run.`**

    A CUDA error was detected during training. Verify GPU driver health with `nvidia-smi`. If the GPU is shared with other workloads, free resources and restart.

- **`CUDA out of memory`**

    The batch size selected for your GPU's VRAM is too high (this can happen if other processes are using the same GPU, or on edge-case GPU models). Restart with a smaller batch size using `--batch_size_override <N>` (e.g. `python3 agora_cli.py --batch_size_override 1`). Lower the value until the error stops.

- **`RAM usage exceeded threshold. Exiting run.`**

    System RAM usage exceeded the allowed threshold. Close other processes consuming memory and restart. If running inside Docker, increase the container's memory limit.

- **`Server exited with -9`**

    The server process was killed by the OS, usually because the instance ran out of system resources. Common causes include exceeding available RAM or hitting a per-process limit on open threads/file descriptors. Check system resource usage (`free -h`, `ulimit -u`, `ulimit -n`), ensure the machine meets the RAM requirements (80GB per GPU), and raise thread/file-descriptor limits if your instance enforces low defaults.


## 📚 Citations

If you use this project in your research, please cite:

Gil Avraham, Violetta Shevchenko, Karol Pajak, James Snewin, Harry Xi, Hadi Mohaghegh Dolatabadi, Thalaiyasingam Ajanthan, Sameera Ramasinghe, Chamin Hewa Koneputugodage, Shamane Siriwardhana, Alexander Long. **Pluralis 8b: Asynchronous Large-Scale Distributed Training over the Internet**. 2026.

```bibtex
@misc{avraham2026agora,
    title={Pluralis 8b: Asynchronous Large-Scale Distributed Training over the Internet}, 
    author={Gil Avraham and Violetta Shevchenko and Karol Pajak and James Snewin and Harry Xi and Hadi Mohaghegh Dolatabadi and Thalaiyasingam Ajanthan and Sameera Ramasinghe and Chamin Hewa Koneputugodage and Shamane Siriwardhana and Alexander Long},
    year={2026},
    url={https://github.com/PluralisResearch/agora}, 
}
```

&nbsp;

Sameera Ramasinghe, Thalaiyasingam Ajanthan, Gil Avraham, Yan Zuo, and Alexander Long. [Protocol Models: Scaling Decentralized Training with Communication-Efficient Model Parallelism](https://arxiv.org/pdf/2506.01260). 2025.

```bibtex
@misc{ramasinghe2025protocolmodelsscalingdecentralized,
    title={Protocol Models: Scaling Decentralized Training with Communication-Efficient Model Parallelism}, 
    author={Sameera Ramasinghe and Thalaiyasingam Ajanthan and Gil Avraham and Yan Zuo and Alexander Long},
    year={2025},
    eprint={2506.01260},
    archivePrefix={arXiv},
    primaryClass={cs.LG},
    url={https://arxiv.org/abs/2506.01260}, 
}
```

 &nbsp;

Pluralis Research. [AsyncMesh: Fully Asynchronous Optimization for Data and Pipeline Parallelism](https://arxiv.org/pdf/2601.22442). 2026. *The SPARTA optimizer used in the live run.*

```bibtex
@misc{pluralis2026asyncmesh,
    title={AsyncMesh: Fully Asynchronous Optimization for Data and Pipeline Parallelism},
    author={Pluralis Research},
    year={2026},
    eprint={2601.22442},
    archivePrefix={arXiv},
    primaryClass={cs.LG},
    url={https://arxiv.org/abs/2601.22442},
}
```

 &nbsp;

Thalaiyasingam Ajanthan, Sameera Ramasinghe, Yan Zuo, Gil Avraham, and Alexander Long. [Nesterov Method for Asynchronous Pipeline Parallel Optimization](https://arxiv.org/pdf/2505.01099). ICML. 2025.
```bibtex
@article{ajanthan2025asyncpp,
    title={Nesterov Method for Asynchronous Pipeline Parallel Optimization},
    author={Ajanthan, Thalaiyasingam and Ramasinghe, Sameera and Zuo, Yan and Avraham, Gil and Long, Alexander},
    journal={ICML},
    year={2025}
}
```

## 📄 License

Distributed under the [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0) License. See [LICENSE](LICENSE) for more information.

Third-party dependencies and their licenses are listed in [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).

## 🙏 Acknowledgements

### Core Framework

This project is built upon the [Hivemind library](https://github.com/learning-at-home/hivemind) for decentralized deep learning, distributed under the [MIT License](https://opensource.org/license/mit).

### Datasets

This project uses the [FineWeb-Edu dataset](https://huggingface.co/datasets/HuggingFaceFW/fineweb-edu) by HuggingFace, made available under the [Open Data Commons Attribution License (ODC-BY) v1.0](https://opendatacommons.org/licenses/by/1-0/).
