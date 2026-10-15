"""Package backends: a stalled local-database query is "unknown", never a hang
and never "missing"."""
import subprocess

from ai2.backends.apt import AptBackend
from ai2.backends.pacman import PacmanBackend


def test_query_timeout_is_unknown(monkeypatch):
    def hang(cmd, **kw):
        assert kw.get("timeout"), "query must be time-boxed"
        raise subprocess.TimeoutExpired(cmd, kw["timeout"])
    for backend in (PacmanBackend(), AptBackend()):
        monkeypatch.setattr(backend, "available", lambda: True)
        monkeypatch.setattr(subprocess, "run", hang)
        assert backend.is_installed("anything") is None


def test_update_and_remove_commands():
    """pacman upgrades and adds packages in one -Syu; apt needs three commands,
    and its `update` takes no package arguments."""
    pac = PacmanBackend()
    assert pac.remove_cmd(["broadcom-wl"]) == ["pacman", "-Rns", "--noconfirm", "broadcom-wl"]
    assert pac.update_cmd([]) == [["pacman", "-Syu"]]
    assert pac.update_cmd(["linux-headers"]) == [["pacman", "-Syu", "linux-headers"]]

    apt = AptBackend()
    assert apt.remove_cmd(["broadcom-sta-dkms"]) == ["apt-get", "remove", "-y", "broadcom-sta-dkms"]
    assert apt.update_cmd([]) == [["apt-get", "update"], ["apt-get", "full-upgrade", "-y"]]
    assert apt.update_cmd(["linux-headers-6.1.0-amd64"]) == [
        ["apt-get", "update"],
        ["apt-get", "full-upgrade", "-y"],
        ["apt-get", "install", "-y", "--no-install-recommends", "linux-headers-6.1.0-amd64"],
    ]
