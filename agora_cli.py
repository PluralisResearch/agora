#!/usr/bin/env python3

# Copyright 2026 Pluralis Research

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Unified CLI for agora — handles installation, configuration, and server launch.

Usage:
    ./agora_cli.py                              # start (interactive, reuses saved config)
    ./agora_cli.py start [--token X] [flags]    # start with explicit args
    ./agora_cli.py start --reconfigure          # re-prompt all parameters
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import time

from pathlib import Path
from urllib import request


# ─── Constants ───────────────────────────────────────────────────────────────

ROOT_DIR = Path(__file__).resolve().parent
CONFIG_DIR = Path.home() / ".agora"
USER_CONFIG_PATH = CONFIG_DIR / "user_config.json"
RUN_JSON_PATH = ROOT_DIR / "run.json"
DOCKER_IMAGE = "ghcr.io/pluralisresearch/agora:latest" 
DOCKER_WORKDIR = "/home"
DEFAULT_PORT = 49200
RUN_SERVER_PATH = ROOT_DIR / "agora" / "src" / "agora" / "run_server.py"
DOCKER_SERVER_PATH = Path("agora", "src", "agora", "run_server.py").as_posix()
MIN_PIP_VERSION = (25, 3)
USER_CONFIG_KEYS = ["token", "email", "use_docker"]
GPU_CONFIG_KEYS = ["host_port", "announce_port"]

# fmt: off
LIBRARY_NAME = [32, 32, 10,
                    9617, 9608, 9608, 9608, 9608, 9608, 9559, 9617, 9617, 9608, 9608, 9608, 9608, 9608, 9608, 9559, 9617, 9617, 9608,
                    9608, 9608, 9608, 9608, 9608, 9559, 9617, 9608, 9608, 9608, 9608, 9608, 9608, 9559, 9617, 9617, 9608, 9608, 9608,
                    9608, 9608, 9559, 9617, 10,
                    9608, 9608, 9556, 9552, 9552, 9608, 9608, 9559, 9608, 9608, 9556, 9552, 9552, 9552, 9552, 9565, 9617, 9608, 9608,
                    9556, 9552, 9552, 9552, 9608, 9608, 9559, 9608, 9608, 9556, 9552, 9552, 9608, 9608, 9559, 9608, 9608, 9556, 9552,
                    9552, 9608, 9608, 9559, 10,
                    9608, 9608, 9608, 9608, 9608, 9608, 9608, 9553, 9608, 9608, 9553, 9617, 9617, 9608, 9608, 9608, 9559, 9608, 9608,
                    9553, 9617, 9617, 9617, 9608, 9608, 9553, 9608, 9608, 9608, 9608, 9608, 9608, 9556, 9565, 9608, 9608, 9608, 9608,
                    9608, 9608, 9608, 9553, 10,
                    9608, 9608, 9556, 9552, 9552, 9608, 9608, 9553, 9608, 9608, 9553, 9617, 9617, 9617, 9608, 9608, 9553, 9608, 9608,
                    9553, 9617, 9617, 9617, 9608, 9608, 9553, 9608, 9608, 9556, 9552, 9552, 9608, 9608, 9559, 9608, 9608, 9556, 9552,
                    9552, 9608, 9608, 9553, 10,
                    9608, 9608, 9553, 9617, 9617, 9608, 9608, 9553, 9562, 9608, 9608, 9608, 9608, 9608, 9608, 9556, 9565, 9562, 9608,
                    9608, 9608, 9608, 9608, 9608, 9556, 9565, 9608, 9608, 9553, 9617, 9617, 9608, 9608, 9553, 9608, 9608, 9553, 9617,
                    9617, 9608, 9608, 9553, 10,
                    9562, 9552, 9565, 9617, 9617, 9562, 9552, 9565, 9617, 9562, 9552, 9552, 9552, 9552, 9552, 9565, 9617, 9617, 9562,
                    9552, 9552, 9552, 9552, 9552, 9565, 9617, 9562, 9552, 9565, 9617, 9617, 9562, 9552, 9565, 9562, 9552, 9565, 9617,
                    9617, 9562, 9552, 9565]

COMPANY_NAME = [119927, 119949, 119958, 119955, 119938, 119949, 119946, 119956, 32, 119929, 119942, 119956, 119942, 119938, 119955, 119940, 119945]
# fmt: on


# ─── Output helpers ──────────────────────────────────────────────────────────

_BOLD = "\033[1m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_RED = "\033[91m"
_RESET = "\033[0m"


def info(msg: str):
    print(f"{_GREEN}{msg}{_RESET}")


def warn(msg: str):
    print(f"{_YELLOW}[WARN] {msg}{_RESET}")


def error(msg: str):
    print(f"{_RED}[ERROR] {msg}{_RESET}")


def print_banner():
    print("".join(chr(c) for c in LIBRARY_NAME))
    print("".join(chr(c) for c in COMPANY_NAME))
    print()


def print_quick_reference():
    lines = [
        "HuggingFace token: https://huggingface.co/docs/hub/en/security-tokens",
        "GPU ID:            Run 'nvidia-smi' to see your GPUs",
        "Host port:         The port the server listens on locally",
        "Announce port:     The port others use to reach you",
        "                   (differs from host port if using NAT)",
        "Native mode:       Runs directly on your machine, without Docker",
        "",
        "For full documentation, see README.md",
    ]
    w = max(len(line) for line in lines)
    print(f"┌─ Quick Reference {'─' * (w - 14)}┐")
    for line in lines:
        print(f"│  {line:<{w}}  │")
    print(f"└{'─' * (w + 4)}┘")
    print()


# ─── Shell / input helpers ───────────────────────────────────────────────────


def run_cmd(cmd: list[str], error_msg: str, **kwargs) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, **kwargs)
    if result.returncode != 0:
        error(error_msg)
        sys.exit(1)
    return result


def ask_yn(prompt: str, default: bool = True) -> bool:
    answer = input(prompt).lower().strip()
    while True:
        if not answer:
            return default
        if answer[0] in ("y", "n"):
            return answer[0] == "y"
        hint = "Y/n" if default else "y/N"
        answer = input(f"Invalid input. Please enter {hint}: ").lower().strip()


def prompt_with_default(msg: str, default, validator=None):
    raw = input(f"{msg} (default {default}, press Enter to accept): ").strip()
    if not raw:
        return default
    if validator:
        while True:
            result = validator(raw)
            if result is not None:
                return result
            raw = input(f"Invalid value. {msg}: ").strip()
    return raw


def validate_port(value: str) -> int | None:
    try:
        port = int(value)
        return port if 1 <= port <= 65535 else None
    except ValueError:
        return None


def validate_gpu_id(value: str) -> int | None:
    try:
        gpu = int(value)
        return gpu if gpu >= 0 else None
    except ValueError:
        return None


def validate_email(email: str) -> str | None:
    email = email.strip()
    if email == "":
        return ""
    if re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        return email
    return None


# ─── Environment detection ───────────────────────────────────────────────────


def detect_docker() -> bool:
    if not shutil.which("docker"):
        return False
    try:
        return subprocess.run(["docker", "info"], capture_output=True, timeout=10).returncode == 0
    except Exception:
        return False


def detect_docker_image() -> bool:
    try:
        result = subprocess.run(
            ["docker", "images", "-q", DOCKER_IMAGE],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return bool(result.stdout.strip())
    except Exception:
        return False


def detect_missing_packages() -> list[str]:
    """Return list of missing packages from {agora_server, agora}."""
    missing = []
    for pkg in ("agora_server", "agora"):
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", pkg],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode != 0:
                missing.append(pkg)
        except Exception:
            missing.append(pkg)
    return missing


def detect_conda() -> bool:
    return shutil.which("conda") is not None


def detect_conda_initialized() -> bool:
    """Check if conda shell integration is set up."""
    return os.environ.get("CONDA_SHLVL") is not None


def _conda_activate_instructions(env_name: str) -> list[str]:
    if detect_conda_initialized():
        return [f"conda activate {env_name}"]
    return [
        "conda init",
        "source ~/.bashrc (or your shell's equivalent init file)",
        f"conda activate {env_name}",
    ]


def has_correct_python() -> bool:
    return sys.version_info[:2] == (3, 11)


def ensure_pip_version():
    """Ensure pip >= 25.3 is installed, upgrading automatically if needed."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        match = re.match(r"pip (\d+)\.(\d+)", result.stdout)
        if match and (int(match.group(1)), int(match.group(2))) >= MIN_PIP_VERSION:
            return
    except Exception:
        pass
    info(f"Upgrading pip to >= {'.'.join(map(str, MIN_PIP_VERSION))}...")
    run_cmd(
        [sys.executable, "-m", "pip", "install", "--upgrade", f"pip>={'.'.join(map(str, MIN_PIP_VERSION))}"],
        "Failed to upgrade pip.",
        capture_output=True,
    )


def find_agora_containers(include_stopped: bool = False) -> list[str]:
    try:
        cmd = ["docker", "ps", "--format", "{{.Names}}"]
        if include_stopped:
            cmd.insert(2, "-a")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return [n for n in result.stdout.strip().split("\n") if n.startswith("agora_")]
    except Exception:
        return []


# ─── Installation ────────────────────────────────────────────────────────────


def pull_docker_image():
    if not detect_docker():
        error("Docker is not available. Please install Docker first.")
        sys.exit(1)
    info(f"Pulling Docker image {DOCKER_IMAGE}...")
    run_cmd(
        ["docker", "pull", DOCKER_IMAGE],
        f"Failed to pull Docker image. Re-run with 'docker pull {DOCKER_IMAGE}' to see full output.",
    )
    info("Docker image pulled successfully.")


def install_from_source(packages: list[str]):
    if not has_correct_python():
        error(f"Python 3.11 is required, but you are running {sys.version_info[0]}.{sys.version_info[1]}.")
        error("Please activate a Python 3.11 environment first.")
        sys.exit(1)
    ensure_pip_version()
    os.chdir(ROOT_DIR)
    info("Installing PyTorch with CUDA 12.8 support...")
    run_cmd(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "torch==2.7.0",
            "--index-url",
            "https://download.pytorch.org/whl/cu128",
        ],
        "Failed to install PyTorch. Re-run with 'pip install torch==2.7.0 --index-url https://download.pytorch.org/whl/cu128' to see full output.",
        capture_output=True,
    )
    constraints = str(ROOT_DIR / "constraints.txt")
    for pkg in packages:
        info(f"Installing {pkg}... (this may take a few minutes)")
        run_cmd(
            [sys.executable, "-m", "pip", "install", "--constraint", constraints, "--build-constraint", constraints, "-e", f"./{pkg}"],
            f"pip install {pkg} failed. Re-run with 'pip install --constraint constraints.txt --build-constraint constraints.txt -e ./{pkg}' to see full output.",
            capture_output=True,
        )
    info("Installation complete.")


def ensure_python_environment(skip_input: bool):
    """Ensure we're in a suitable Python 3.11 environment for native mode.

    If correct Python is available, do nothing.
    Otherwise, offer to create a conda env with Python 3.11.
    """
    if has_correct_python():
        return

    warn(f"Python 3.11 is required, but you are running {sys.version_info[0]}.{sys.version_info[1]}.")

    current_env = os.environ.get("CONDA_DEFAULT_ENV") or os.environ.get("VIRTUAL_ENV")
    if current_env:
        warn(f"Your current environment '{current_env}' does not have Python 3.11.")

    if skip_input:
        error("Wrong Python version. Create a conda/venv environment with Python 3.11.")
        sys.exit(1)

    conda_available = detect_conda()
    if conda_available:
        # Check if 'agora' conda env already exists
        try:
            result = subprocess.run(["conda", "env", "list"], capture_output=True, text=True, timeout=15)
            agora_env_exists = any(line.split()[0] == "agora" for line in result.stdout.splitlines() if line.strip())
        except Exception:
            agora_env_exists = False

        if agora_env_exists:
            info("A conda environment 'agora' already exists.")
            print()
            print(f"  {_BOLD}>>> To continue, activate it and re-run this script:{_RESET}")
            for step in _conda_activate_instructions("agora"):
                print(f"  {_BOLD}>>> {step}{_RESET}")
            print(f"  {_BOLD}>>> ./agora_cli.py{_RESET}")
            print()
            sys.exit(0)

        info("Conda is available. A conda environment with Python 3.11 can be created.")
        if ask_yn("Would you like to create a conda environment 'agora' with Python 3.11? [Y/n] "):
            run_cmd(
                ["conda", "create", "-y", "-n", "agora", "python=3.11"],
                "Failed to create conda environment.",
            )
            info("Conda environment 'agora' created successfully.")
            print()
            print(f"  {_BOLD}>>> To continue, activate the environment and re-run this script:{_RESET}")
            for step in _conda_activate_instructions("agora"):
                print(f"  {_BOLD}>>> {step}{_RESET}")
            print(f"  {_BOLD}>>> ./agora_cli.py{_RESET}")
            print()
            sys.exit(0)

    info("You can create a virtual environment manually:")
    if conda_available:
        activate_cmd = " && ".join(["conda create -n agora python=3.11"] + _conda_activate_instructions("agora"))
        print(f"  {activate_cmd}")
        error("Cannot continue without Python 3.11.")
        sys.exit(1)
    print("  python3.11 -m venv .venv && source .venv/bin/activate")
    error("Cannot continue without Python 3.11.")
    sys.exit(1)


def ensure_installed(use_docker: bool, skip_input: bool = False):
    """Check if agora is ready to run and offer to install/rebuild if needed."""
    if use_docker:
        if detect_docker_image():
            if not skip_input and ask_yn(f"Check for a newer version of {DOCKER_IMAGE}? [y/N] ", default=False):
                pull_docker_image()
        else:
            if skip_input:
                error(f"Docker image '{DOCKER_IMAGE}' not found. Run: docker pull {DOCKER_IMAGE}")
                sys.exit(1)
            warn(f"Docker image '{DOCKER_IMAGE}' not found.")
            if ask_yn("Would you like to pull it now? [Y/n] "):
                pull_docker_image()
            else:
                error(f"Cannot start without Docker image. Run: docker pull {DOCKER_IMAGE}")
                sys.exit(1)
    else:
        missing = detect_missing_packages()
        if missing:
            missing_str = ", ".join(missing)
            install_str = " && ".join(f"pip install --constraint constraints.txt --build-constraint constraints.txt -e ./{pkg}" for pkg in missing)
            if skip_input:
                error(f"{missing_str} not installed. Run: {install_str}")
                sys.exit(1)
            warn(f"{missing_str} not installed.")
            if ask_yn("Would you like to install now? [Y/n] "):
                install_from_source(missing)
            else:
                error(f"Cannot start without {missing_str}. Run: {install_str}")
                sys.exit(1)


# ─── Config persistence ─────────────────────────────────────────────────────


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


def _save_json(path: Path, config: dict, keys: list[str]):
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        to_save = {k: config[k] for k in keys if k in config and config[k] is not None}
        with open(path, "w") as f:
            json.dump(to_save, f, indent=2)
    except Exception:
        error(f"Failed to save config to {path}")


def load_user_config() -> dict:
    return _load_json(USER_CONFIG_PATH)


def save_user_config(config: dict):
    _save_json(USER_CONFIG_PATH, config, USER_CONFIG_KEYS)


def gpu_config_path(gpu_id: int = 0) -> Path:
    return CONFIG_DIR / f"config_gpu{gpu_id}.json"


def load_gpu_config(gpu_id: int = 0) -> dict:
    return _load_json(gpu_config_path(gpu_id))


def save_gpu_config(config: dict, gpu_id: int = 0):
    _save_json(gpu_config_path(gpu_id), config, GPU_CONFIG_KEYS)


def load_run_json() -> dict:
    if not RUN_JSON_PATH.exists():
        error(f"run.json not found at {RUN_JSON_PATH}")
        sys.exit(1)

    try:
        with open(RUN_JSON_PATH) as f:
            data = json.load(f)
    except Exception as e:
        error(f"Failed to parse run.json: {e}")
        sys.exit(1)

    required_keys = ["run_config", "auth_server", "seeds", "prom_gateway"]
    missing = [k for k in required_keys if not data.get(k) or data[k] == "none" or data[k] == []]
    if missing:
        error(f"run.json is missing required values: {', '.join(missing)}")
        sys.exit(1)

    result = {}
    for key in ("run_config", "auth_server", "prom_gateway"):
        result[key] = data[key]
    result["initial_peers"] = data["seeds"]
    return result


# ─── Public IP ───────────────────────────────────────────────────────────────


def get_public_ip() -> str:
    ip_services = [
        "https://api.ipify.org",
        "https://ifconfig.me",
        "https://icanhazip.com",
    ]
    info("Fetching public IP...")
    for url in ip_services:
        try:
            with request.urlopen(url, timeout=5) as resp:
                ip = resp.read().decode("utf-8").strip()
                if ip:
                    info(f"Public IP: {ip}")
                    return ip
        except Exception as e:
            warn(f"Failed to reach {url}: {e}")
    error("Cannot determine public IP address. Check your internet connection.")
    sys.exit(1)


# ─── Interactive parameter collection ────────────────────────────────────────


def collect_user_params(config: dict, skip_input: bool = False) -> dict:
    """Collect user-level parameters (token, email, docker)."""
    if skip_input:
        missing = []
        if not config.get("token"):
            missing.append("--token")
        if not config.get("auth_server"):
            missing.append("auth_server in run.json")
        if not config.get("run_config"):
            missing.append("run_config in run.json")
        if not config.get("initial_peers"):
            missing.append("seeds in run.json")
        if missing:
            error(f"Missing required parameters: {', '.join(missing)}")
            sys.exit(1)
        config.setdefault("use_docker", False)
        return config

    while True:
        if not config.get("token"):
            token = input("Please enter your HuggingFace token: ")
            while not (token := token.strip()):
                token = input("Token cannot be empty. Please enter your HuggingFace token: ")
            config["token"] = token

        if config.get("email") is None:
            email = input("Please enter your email [optional]: ")
            while (email := validate_email(email)) is None:
                email = input("Wrong email format. Please enter valid email or leave empty: ")
            config["email"] = email

        if config.get("use_docker") is None:
            if Path("/.dockerenv").exists():
                info("Already running inside a container, will run natively.")
                config["use_docker"] = False
            elif detect_docker():
                config["use_docker"] = ask_yn(
                    "Do you want to run inside a Docker container (recommended, unless already in a container)? [Y/n] "
                )
            else:
                warn("Docker not detected. We recommend using Docker, unless already in a container.")
                if not ask_yn("Do you want to proceed with native installation? [Y/n] "):
                    error("Please install Docker and try again.")
                    sys.exit(1)
                config["use_docker"] = False

        # Show summary and allow changes
        docker_label = "Docker" if config["use_docker"] else "native"
        print(f"\n{_BOLD}User preferences:{_RESET}")
        print(f"  token:      {config['token']}")
        print(f"  email:      {config.get('email', '')}")
        print(f"  runtime:    {docker_label}")

        if not ask_yn("\nDo you want to change anything? [y/N] ", default=False):
            return config

        editable = [
            ("token", "token"),
            ("email", "email"),
            ("use_docker", "runtime (Docker/native)"),
        ]
        print("\nPlease select the parameter you want to change:")
        for i, (_, label) in enumerate(editable, 1):
            print(f"  {i}. {label}")
        print("  0. Cancel")

        choice = input(f"Enter (0-{len(editable)}): ").strip()
        try:
            idx = int(choice)
            if 1 <= idx <= len(editable):
                config[editable[idx - 1][0]] = None
        except ValueError:
            pass
        print()


def collect_gpu_params(config: dict, skip_input: bool = False) -> dict:
    """Collect GPU-level parameters (ports). Shows full summary for confirmation."""
    if skip_input:
        return config

    gpu_id = config["gpu_id"]
    default_port = DEFAULT_PORT + gpu_id

    while True:
        if not config.get("host_port"):
            config["host_port"] = prompt_with_default("Please enter host port to use", default_port, validate_port)

        if not config.get("announce_port"):
            default_ap = config.get("host_port", default_port)
            config["announce_port"] = prompt_with_default(
                "Please enter announce port to use", default_ap, validate_port
            )

        # Show full summary
        print(f"\n{_BOLD}The server will run with the following parameters:{_RESET}")
        print(f"  token:         {config['token']}")
        print(f"  email:         {config.get('email', '')}")
        print(f"  gpu_id:        {gpu_id}")
        print(f"  host_port:     {config.get('host_port', default_port)}")
        print(f"  announce_port: {config.get('announce_port', default_port)}")

        if not ask_yn("\nDo you want to change anything? [y/N] ", default=False):
            port = config.get("announce_port", default_port)
            print(f"\n{_BOLD}Note:{_RESET} Port {port} needs to be:")
            print("  - Open in your firewall/router for incoming connections")
            print("  - Not already in use by another server")
            if not ask_yn("\nConfirm and continue? [Y/n] "):
                info("Aborted.")
                sys.exit(0)
            print()
            return config

        editable = ["host_port", "announce_port"]
        print("\nPlease select the parameter you want to change:")
        for i, key in enumerate(editable, 1):
            print(f"  {i}. {key}")
        print("  0. Cancel")

        choice = input(f"Enter (0-{len(editable)}): ").strip()
        try:
            idx = int(choice)
            if 1 <= idx <= len(editable):
                config[editable[idx - 1]] = None
        except ValueError:
            pass
        print()


# ─── Subcommands ─────────────────────────────────────────────────────────────


def cmd_start(args):
    print_banner()
    if not args.skip_input:
        print_quick_reference()

    # User preferences (token, email, docker) ──
    config = {}
    if not args.reconfigure:
        config.update(load_user_config())

    # CLI overrides for user-level keys
    for key in ("token", "email"):
        value = getattr(args, key, None)
        if value is not None:
            config[key] = value
    if args.use_docker:
        config["use_docker"] = True

    # Load run.json
    config.update(load_run_json())

    # Collect user params interactively
    config = collect_user_params(config, skip_input=args.skip_input)

    # Save user config so it persists for future runs
    save_user_config(config)

    # Installation
    if not config["use_docker"]:
        ensure_python_environment(args.skip_input)
    ensure_installed(config["use_docker"], skip_input=args.skip_input)

    # GPU selection and GPU-specific config
    cli_gpu_id = getattr(args, "gpu_id", None)
    if cli_gpu_id is not None:
        gpu_id = int(cli_gpu_id)
    elif not args.skip_input:
        gpu_id = int(prompt_with_default("Please enter GPU ID to use", 0, validate_gpu_id))
    else:
        gpu_id = 0
    config["gpu_id"] = gpu_id

    # Load saved GPU config
    if not args.reconfigure:
        config.update(load_gpu_config(gpu_id))

    # CLI overrides for GPU-level keys
    for key in ("host_port", "announce_port", "log_file", "identity_path", "batch_size_override"):
        value = getattr(args, key, None)
        if value is not None:
            config[key] = value

    # Collect GPU params interactively
    config = collect_gpu_params(config, skip_input=args.skip_input)

    # Derive defaults for computed values
    config.setdefault("host_port", DEFAULT_PORT + gpu_id)
    config.setdefault("announce_port", config["host_port"])
    config.setdefault("log_file", f"logs/server_gpu{gpu_id}.log")
    config.setdefault("identity_path", f"private_gpu{gpu_id}.key")
    config.setdefault("email", "")

    # Save GPU config
    save_gpu_config(config, gpu_id)
    info("Configuration saved")

    public_ip = get_public_ip()

    # Build run_server.py arguments
    server_args = [
        "--gpu_id",
        str(gpu_id),
        "--config",
        f"{config['run_config']}",
        "--token",
        config["token"],
        "--auth_server",
        config["auth_server"],
        "--prom_gateway",
        config["prom_gateway"],
        "--host_maddrs",
        f"/ip4/0.0.0.0/tcp/{config['host_port']}",
        "--announce_maddrs",
        f"/ip4/{public_ip}/tcp/{config['announce_port']}",
        "--initial_peers",
        *config["initial_peers"],
    ]
    if config.get("email"):
        server_args.extend(["--email", config["email"]])
    server_args.extend(["--log_file", config["log_file"]])
    server_args.extend(["--identity_path", config["identity_path"]])
    if config.get("batch_size_override") is not None:
        server_args.extend(["--batch_size_override", str(config["batch_size_override"])])

    print(f"\n{'=' * 60}")
    print(f"{_BOLD}  Starting agora server...{_RESET}")
    print(f"{'=' * 60}\n")

    if config["use_docker"]:
        _start_docker(config, server_args, skip_input=args.skip_input)
    else:
        _start_native(config, server_args)


def _start_docker(config: dict, server_args: list, skip_input: bool = False):
    gpu_id = config["gpu_id"]
    container_name = f"agora_gpu{gpu_id}"

    # Check for existing container on the same GPU
    existing = find_agora_containers(include_stopped=True)
    if container_name in existing:
        info(f"Container '{container_name}' already exists on GPU {gpu_id}.")
        print(
            "  Restarting is safe if this is a leftover from a previous run. Skip only if this container is still needed."
        )
        if not skip_input:
            if not ask_yn("Stop and restart? [Y/n] "):
                info("Aborted.")
                sys.exit(0)
        info(f"Stopping existing container {container_name}...")
        subprocess.run(["docker", "stop", container_name], capture_output=True, timeout=30)
        subprocess.run(["docker", "rm", container_name], capture_output=True, timeout=10)

    inner_cmd = f"CUDA_VISIBLE_DEVICES=0 python3.11 {DOCKER_SERVER_PATH} {shlex.join(server_args)} > agora_output_gpu{gpu_id}.log 2>&1"

    docker_cmd = [
        "docker",
        "run",
        "-d",
        "--init",
        "--name",
        container_name,
        "--ipc=host",
        "--network=host",
        "--gpus",
        f"device={config['gpu_id']}",
        "-v",
        f"{ROOT_DIR}:{DOCKER_WORKDIR}",
        "-w",
        DOCKER_WORKDIR,
        DOCKER_IMAGE,
        "bash",
        "-c",
        inner_cmd,
    ]

    info(f"Starting server (container: {container_name})...")
    run_cmd(docker_cmd, "Failed to start Docker container.", capture_output=True)
    info("Server started successfully!")
    print(f"\n{_BOLD}What's happening:{_RESET}")
    print(f"  Your agora server is now running in a Docker container named '{container_name}'.")
    print("  It runs in the background — you can close this terminal safely.")
    print(f"\n{_BOLD}Useful commands:{_RESET}")
    print(f"  View live logs:    tail -f agora_output_gpu{gpu_id}.log")
    print(f"  Check status:      docker ps --filter name={container_name}")
    print(f"  Stop the server:   docker stop {container_name} && docker rm {container_name}")


def _start_native(config: dict, server_args: list):
    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = str(config["gpu_id"])
    cmd = [sys.executable, str(RUN_SERVER_PATH)] + server_args
    info("Starting server...")
    info("Press Ctrl+C to stop.\n")

    process = subprocess.Popen(cmd, env=env, start_new_session=True)
    info(f"Started server with process group (pid={process.pid})")

    stop_signal: dict[str, int | None] = {"value": None}
    original_handlers = {}

    def _forward_stop_signal(signal_number: int, _frame) -> None:
        if stop_signal["value"] is None:
            stop_signal["value"] = signal_number

    def _stop_process_group(grace_seconds: int = 8) -> tuple[int, bool]:
        if process.poll() is not None:
            return process.returncode or 0, False

        try:
            pgid = os.getpgid(process.pid)
        except ProcessLookupError:
            return process.returncode or 0, False

        escalated = False
        try:
            info("Stopping node process group with SIGTERM...")
            os.killpg(pgid, signal.SIGTERM)
        except ProcessLookupError:
            return process.returncode or 0, False

        try:
            return process.wait(timeout=grace_seconds), False
        except subprocess.TimeoutExpired:
            escalated = True
            warn("Graceful shutdown timed out; sending SIGKILL to process group...")
            try:
                os.killpg(pgid, signal.SIGKILL)
            except ProcessLookupError:
                pass

            try:
                return process.wait(timeout=5), escalated
            except subprocess.TimeoutExpired:
                error("Process group did not exit after SIGKILL")
                return 1, escalated

    for signum in (signal.SIGINT, signal.SIGTERM):
        original_handlers[signum] = signal.getsignal(signum)
        signal.signal(signum, _forward_stop_signal)

    exit_code = 1
    try:
        while True:
            requested_signal = stop_signal["value"]
            if requested_signal is not None:
                info(f"Received {signal.Signals(requested_signal).name}, shutting down...")
                child_code, escalated = _stop_process_group()

                if escalated:
                    exit_code = 137
                elif requested_signal == signal.SIGINT:
                    exit_code = 130
                else:
                    exit_code = 143
                break

            try:
                exit_code = process.wait(timeout=1)
                break
            except subprocess.TimeoutExpired:
                continue

        # Clean up any remaining processes in the child's process group.
        pgid = process.pid
        try:
            os.killpg(pgid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError, OSError):
            pass  # group already gone
        else:
            time.sleep(2)
            try:
                os.killpg(pgid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError, OSError):
                pass
    finally:
        for signum, handler in original_handlers.items():
            signal.signal(signum, handler)

    if exit_code == 0:
        info("Server exited cleanly")
    else:
        warn(f"Server exited with code {exit_code}")

    sys.exit(exit_code)


# ─── Argument parser & main ─────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agora_cli",
        description="Unified CLI for agora — install, configure, and run the training server.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # Start
    sp = subparsers.add_parser("start", help="Configure and start the training server")
    sp.add_argument("--token", type=str, help="HuggingFace token")
    sp.add_argument("--email", type=str, help="Email address (optional)")
    sp.add_argument("--host_port", type=int, help=f"Host port (default: {DEFAULT_PORT} + gpu_id)")
    sp.add_argument("--announce_port", type=int, help=f"Announce port (default: {DEFAULT_PORT} + gpu_id)")
    sp.add_argument("--gpu_id", type=int, help="GPU ID to use (default: 0)")
    sp.add_argument("--log_file", type=str, help="Log file path (default: logs/server_gpu<ID>.log)")
    sp.add_argument("--identity_path", type=str, help="Identity key path (default: private_gpu<ID>.key)")
    sp.add_argument("--batch_size_override", type=int, help="Advanced: override the batch size")
    sp.add_argument("--use_docker", action="store_true", help="Run inside Docker container")
    sp.add_argument("--skip_input", action="store_true", help="Skip interactive prompts")
    sp.add_argument("--reconfigure", action="store_true", help="Ignore saved config and re-prompt all parameters")

    return parser


def main():
    parser = build_parser()

    known_commands = {"start"}
    argv = sys.argv[1:]
    if not argv or (argv[0] not in known_commands and argv[0] not in ("-h", "--help")):
        argv = ["start"] + argv

    args = parser.parse_args(argv)

    commands = {
        "start": cmd_start,
    }
    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
