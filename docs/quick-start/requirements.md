---
icon: material/format-list-checks
---

# Requirements

Before a machine can join Agora, it must meet a set of minimum requirements. The sections below cover hardware, OS, networking, and the HuggingFace token the client needs at startup.

!!! info "No machine that meets the requirements?"
    A GPU instance can be rented from AWS, GCP, RunPod, Vast.ai, Tensordock, or Lambda Labs. The [Cloud Options guide](setup-guides/cloud.md) covers selecting and provisioning one for each provider, including cheapest-option recommendations.

---

## Hardware

| Resource | Minimum | Notes |
|----------|---------|-------|
| **GPU** | 24 GB VRAM | RTX 4090 or equivalent. Consumer cards work. |
| **RAM** | 80 GB per GPU | A 2-GPU machine needs 160 GB total. |
| **Disk** | 80 GB free | For model weights, checkpoints, logs. |
| **Network** | 200 Mbps stable | See shared-bandwidth note below. |
| **Latency** | < 80 ms | RTT to our NA-based peers. |

!!! warning "Cloud bandwidth is often shared"
    Some cloud providers advertise bandwidth shared across tenants. Your effective throughput may be significantly lower than the advertised value. Run a speed test on the actual instance before committing to a long run.

!!! info "Spot instances are supported"
    Spot / pre-emptible instances work for Agora. Pre-emption pauses your accrual rather than erasing it, and presence points credit for every active hour, so an interrupted run still earns a baseline.

!!! info "Maximum 2 peers per account"
    Scores sum across all peers running under the same HuggingFace identity, up to **2 active peers per account**. We may relax this cap during the live run.

!!! warning "GPU model must be on the validated allowlist"
    Meeting the 24 GB VRAM minimum is necessary but not sufficient: the authorization service maintains an allowlist of validated GPU models. If your GPU is rejected with `GPU device not in allowlist: '<model>'`, [open an issue](https://github.com/PluralisResearch/agora/issues) with the GPU model (from `nvidia-smi --query-gpu=name --format=csv,noheader`), VRAM, host RAM, OS, and cloud instance type if applicable.

Check your GPU is visible:

```bash
nvidia-smi
```

The output should list the GPU and VRAM. If this command is not found, install [NVIDIA drivers](setup-guides/useful-links.md#gpu-nvidia-drivers) first.

---

## Operating system

Agora runs on:

- **Linux**: any modern distro with recent NVIDIA drivers
- **Windows 10/11 + WSL2**: [enable CUDA support in WSL](https://docs.nvidia.com/cuda/wsl-user-guide/index.html)

macOS is not supported (no CUDA).

---

## Network

Other peers need to reach your node on a TCP port. The default is **49200**. This port must be **open for inbound connections**.

Where to configure it depends on the setup:

- **Cloud VM**: open the port in your provider's security group / firewall rule. See the [cloud provider walkthroughs](setup-guides/cloud.md) (each AWS, GCP, RunPod, Vast.ai, Tensordock, and Lambda Labs section includes the per-provider steps inline).
- **Laptop / home machine**: see [Personal / home machine](#personal-home-machine) below.
- **WSL2**: see [Windows + WSL2](#windows-wsl2) below.

!!! info "Multiple GPUs need multiple ports"
    Each GPU on the same machine needs its own port: 49200 for GPU 0, 49201 for GPU 1, and so on. Open each one.

!!! warning "RunPod, Vast.ai, and Tensordock remap ports externally"
    These providers assign a random external port that differs from the internal one. Pass both `--host_port 49200` and `--announce_port <external>`. The matching [cloud-provider walkthrough](setup-guides/cloud.md) explains how to read the external port.

!!! info "Network latency"
    The current run measures round-trip latency from your node to our NA-based peers and admits joiners below ~80 ms. North-American nodes have the highest join success today; we aim to relax this in future runs.

### Personal / home machine

If the node lives on a laptop or desktop on your home network, two things need to allow `49200/tcp`:

1. **Local firewall**: open inbound `49200/tcp`:
    - Linux: `ufw allow 49200/tcp`
    - macOS: System Settings → Network → Firewall
    - Windows: Defender Firewall inbound rule
2. **Router**: set up port forwarding for `49200/tcp` from the WAN to your machine's LAN IP. The exact location varies by router brand; look for *Port Forwarding*, *Virtual Server*, or *NAT*.

### Windows + WSL2

Windows + WSL2 adds an extra hop: traffic arrives at Windows and needs a port-proxy into the WSL2 VM.

1. **Enable localhost forwarding**: create `C:\Users\<YourUsername>\.wslconfig` with:

    ```text
    [wsl2]
    localhostforwarding=true
    ```

2. **Configure the port proxy** (PowerShell **as Administrator**). First find the WSL container's IP:

    ```powershell
    ((wsl hostname -I) -split " ")[0]
    ```

    Add the proxy, replacing `<wsl_ip>` with the IP from above:

    ```powershell
    netsh interface portproxy add v4tov4 listenport=49200 listenaddress=0.0.0.0 connectport=49200 connectaddress=<wsl_ip>
    ```

    Open the Windows firewall for the port:

    ```powershell
    netsh advfirewall firewall add rule name="agora" dir=in action=allow protocol=TCP localport=49200
    ```

3. **Router**: set up port forwarding from the WAN to your Windows machine on `49200/tcp`.
4. **Restart** to apply changes.

---

## Authentication: HuggingFace token

Agora requires a free HuggingFace access token. The token is used for identity only: no read/write scopes required.

1. Create an account at [huggingface.co](https://huggingface.co) if one does not already exist
2. [Generate an access token](https://huggingface.co/docs/hub/en/security-tokens)
3. Save it where it can be retrieved; the CLI will prompt for it on first run

---

## Pre-flight checklist

Before moving on, confirm:

- [ ] GPU has ≥ 24 GB VRAM (verified with `nvidia-smi`)
- [ ] 80 GB RAM per GPU, 80 GB free disk
- [ ] Stable 200 Mbps+ connection
- [ ] Round-trip latency under ~80 ms to our NA-based peers
- [ ] Port 49200 open for inbound TCP (per GPU)
- [ ] HuggingFace token generated and saved in a location you can copy from

Once all of these are satisfied, [continue to running Agora](run.md).
