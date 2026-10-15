"""apt package backend (Debian/Ubuntu). The Debian path: install/remove/update
through apt, with the zram/OOM provider tables in tuning.py carrying a systemd
entry. The engine stays backend-agnostic; Artix keeps using pacman."""

from __future__ import annotations

import shutil
import subprocess


class AptBackend:
    name = "apt"

    def available(self) -> bool:
        return shutil.which("apt-get") is not None

    def is_installed(self, pkg: str) -> bool | None:
        if not self.available():
            return None
        try:
            return subprocess.run(
                ["dpkg", "-s", pkg], capture_output=True, text=True, timeout=10
            ).returncode == 0
        except subprocess.TimeoutExpired:
            return None      # a stalled local-db read is "unknown", not "missing"

    def install_cmd(self, pkgs: list[str]) -> list[str]:
        return ["apt-get", "install", "-y", *pkgs]

    def remove_cmd(self, pkgs: list[str]) -> list[str]:
        return ["apt-get", "remove", "-y", *pkgs]

    def update_cmd(self, extra: list[str]) -> list[list[str]]:
        # apt splits refreshing the indexes from upgrading, where pacman's -Syu
        # does both. full-upgrade matches -Syu's handling of changed
        # dependencies. `extra` is a package to install (Broadcom kernel
        # headers), never an argument to `update`, which takes none.
        cmds = [["apt-get", "update"], ["apt-get", "full-upgrade", "-y"]]
        if extra:
            cmds.append(["apt-get", "install", "-y", "--no-install-recommends", *extra])
        return cmds
