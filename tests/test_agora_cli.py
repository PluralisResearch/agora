# Copyright 2026 Pluralis Research
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import contextlib
import io
import shlex
import unittest
from unittest.mock import Mock, patch

import agora_cli


class DockerCommandTests(unittest.TestCase):
    def docker_server_args(self, cli_args, run_config="run.yml"):
        run = {
            "run_config": run_config,
            "auth_server": "https://auth.example.invalid",
            "prom_gateway": "https://metrics.example.invalid",
            "initial_peers": ["/ip4/127.0.0.1/tcp/49200"],
        }
        args = agora_cli.build_parser().parse_args(
            ["start", "--use_docker", "--skip_input", "--token", "test-token", *cli_args]
        )
        with patch.multiple(
            agora_cli,
            print_banner=Mock(),
            load_user_config=Mock(return_value={}),
            load_run_json=Mock(return_value=run),
            save_user_config=Mock(),
            ensure_installed=Mock(),
            load_gpu_config=Mock(return_value={}),
            save_gpu_config=Mock(),
            get_public_ip=Mock(return_value="127.0.0.1"),
            find_agora_containers=Mock(return_value=[]),
        ), patch.object(agora_cli, "run_cmd") as run_cmd, contextlib.redirect_stdout(io.StringIO()):
            agora_cli.cmd_start(args)

        run_cmd.assert_called_once()
        command = run_cmd.call_args.args[0]
        self.assertEqual(command[:2], ["docker", "run"])
        self.assertEqual(command[-3:-1], ["bash", "-c"])
        shell_args = shlex.split(command[-1])
        self.assertEqual(shell_args[:3], ["CUDA_VISIBLE_DEVICES=0", "python3.11", agora_cli.DOCKER_SERVER_PATH])
        self.assertEqual(shell_args[-3:], [">", "agora_output_gpu0.log", "2>&1"])
        return shell_args[3:-3]

    def test_default_paths(self):
        args = self.docker_server_args([])
        self.assertEqual(args[args.index("--log_file") + 1], "logs/server_gpu0.log")
        self.assertEqual(args[args.index("--identity_path") + 1], "private_gpu0.key")

    def test_custom_paths_with_spaces(self):
        args = self.docker_server_args(
            ["--log_file", "logs/my node.log", "--identity_path", "keys/my node.key"]
        )
        self.assertEqual(args[args.index("--log_file") + 1], "logs/my node.log")
        self.assertEqual(args[args.index("--identity_path") + 1], "keys/my node.key")

    def test_run_config_path_with_spaces(self):
        args = self.docker_server_args([], run_config="configs/my run.yml")
        self.assertEqual(args[args.index("--config") + 1], "configs/my run.yml")


if __name__ == "__main__":
    unittest.main()
