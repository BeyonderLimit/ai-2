"""The broadcom-wl -> broadcom-wl-dkms replacement trap: what the update
preflight and the doctor do on machines with and without Broadcom WiFi."""
from ai2 import broadcom, software
from ai2.backends.apt import AptBackend
from ai2.backends.pacman import PacmanBackend

LSPCI_ATHEROS = """01:00.0 Ethernet controller [0200]: Realtek Semiconductor Co., Ltd. RTL8111/8168 [10ec:8168] (rev 10)
02:00.0 Network controller [0280]: Qualcomm Atheros QCA9565 / AR9565 Wireless Network Adapter [168c:0036] (rev 01)
"""
LSPCI_BROADCOM = """02:00.0 Ethernet controller [0200]: Broadcom Inc. NetLink BCM57780 Gigabit Ethernet PCIe [14e4:1692] (rev 01)
03:00.0 Network controller [0280]: Broadcom Inc. and subsidiaries BCM4313 802.11bgn Wireless Network Adapter [14e4:4727] (rev 01)
"""


def test_only_broadcom_network_controllers_count():
    assert broadcom.broadcom_wifi_devices(LSPCI_ATHEROS) == []
    devs = broadcom.broadcom_wifi_devices(LSPCI_BROADCOM)
    assert len(devs) == 1 and devs[0].startswith("Broadcom Inc. and subsidiaries BCM4313")


def test_no_broadcom_machine_removes_wl_before_the_upgrade():
    p = broadcom.assess([], {"broadcom-wl": True, "broadcom-wl-dkms": False, "linux-headers": False},
                        "linux-headers", pkg_backend=PacmanBackend())
    assert p.state == "remove-wl" and p.pre_commands == [["pacman", "-Rns", "--noconfirm", "broadcom-wl"]]
    assert p.extra_packages == [] and "600 MB" in p.message
    p = broadcom.assess([], {"broadcom-wl": False, "broadcom-wl-dkms": True, "linux-headers": False},
                        "linux-headers", pkg_backend=PacmanBackend())
    assert p.state == "remove-dkms" and p.pre_commands[0][-1] == "broadcom-wl-dkms"
    assert broadcom.assess([], {"broadcom-wl": False, "broadcom-wl-dkms": False, "linux-headers": False},
                           "linux-headers", pkg_backend=PacmanBackend()).state == "clean"


def test_debian_uses_apt_and_the_debian_driver_name():
    """The trap is Artix's, but on Debian/Ubuntu the commands must be apt's and
    the driver is broadcom-sta-dkms, not broadcom-wl-dkms."""
    backend = AptBackend()
    p = broadcom.assess([], {"broadcom-wl": False, "broadcom-sta-dkms": True, "linux-headers-6.1.0-amd64": False},
                        "linux-headers-6.1.0-amd64", pkg_backend=backend)
    assert p.state == "remove-dkms"
    assert p.pre_commands == [["apt-get", "remove", "-y", "broadcom-sta-dkms"]]
    p = broadcom.assess(["BCM4313"], {"broadcom-wl": False, "broadcom-sta-dkms": False,
                                      "linux-headers-6.1.0-amd64": False},
                        "linux-headers-6.1.0-amd64", pkg_backend=backend)
    assert p.state == "wl-missing"
    assert "apt-get install" in p.fix and "broadcom-sta-dkms" in p.fix


def test_broadcom_machine_gets_headers_into_the_upgrade():
    dev = ["BCM4313"]
    p = broadcom.assess(dev, {"broadcom-wl": True, "broadcom-wl-dkms": False, "linux-lts-headers": False},
                        "linux-lts-headers", pkg_backend=PacmanBackend())
    assert p.state == "needs-headers" and p.extra_packages == ["linux-lts-headers"] and p.pre_commands == []
    p = broadcom.assess(dev, {"broadcom-wl": False, "broadcom-wl-dkms": True, "linux-headers": True},
                        "linux-headers", pkg_backend=PacmanBackend())
    assert p.state == "ok-broadcom"
    p = broadcom.assess(dev, {"broadcom-wl": False, "broadcom-wl-dkms": False, "linux-headers": False},
                        "linux-headers", pkg_backend=PacmanBackend())
    assert p.state == "wl-missing" and "broadcom-wl-dkms linux-headers" in p.fix


def test_headers_package_follows_the_installed_kernel(monkeypatch):
    class Pkg:
        name = "pacman"

        def is_installed(self, pkg):
            return pkg == "linux-lts"

        def available(self):
            return True

    assert broadcom.headers_package(pkg_backend=Pkg()) == "linux-lts-headers"


def test_headers_package_on_debian_names_the_running_kernel(monkeypatch):
    monkeypatch.setattr(broadcom.os, "uname", lambda: type("U", (), {"release": "6.1.0-13-amd64"})())
    assert broadcom.headers_package(pkg_backend=AptBackend()) == "linux-headers-6.1.0-13-amd64"


class _Proc:
    def __init__(self, rc):
        self.returncode = rc


def test_update_runs_the_removal_first_then_the_upgrade_with_extras(monkeypatch, capsys):
    monkeypatch.setattr(software.os, "geteuid", lambda: 1000)
    calls = []
    run = lambda cmd, *a, **kw: calls.append(cmd) or _Proc(0)
    plan = broadcom.Plan("remove-wl", pre_commands=[["pacman", "-Rns", "--noconfirm", "broadcom-wl"]], message="no Broadcom here")
    pre = lambda say, run_, sudo: broadcom.preflight(say, run_, sudo, plan=plan)
    assert software.update(run=run, preflight=pre, pkg_backend=PacmanBackend()) == 0
    assert calls == [["sudo", "pacman", "-Rns", "--noconfirm", "broadcom-wl"], ["sudo", "pacman", "-Syu"]]
    assert "no Broadcom here" in capsys.readouterr().out
    calls.clear()
    plan = broadcom.Plan("needs-headers", extra_packages=["linux-headers"], message="Broadcom found")
    pre = lambda say, run_, sudo: broadcom.preflight(say, run_, sudo, plan=plan)
    assert software.update(run=run, preflight=pre, pkg_backend=PacmanBackend()) == 0
    assert calls == [["sudo", "pacman", "-Syu", "linux-headers"]]


def test_failed_removal_stops_the_update(monkeypatch, capsys):
    monkeypatch.setattr(software.os, "geteuid", lambda: 0)
    calls = []
    run = lambda cmd, *a, **kw: calls.append(cmd) or _Proc(1)
    plan = broadcom.Plan("remove-wl", pre_commands=[["pacman", "-Rns", "--noconfirm", "broadcom-wl"]], message="m")
    assert software.update(run=run, pkg_backend=PacmanBackend(),
                           preflight=lambda s, r, su: broadcom.preflight(s, r, su, plan=plan)) == 1
    assert calls == [["pacman", "-Rns", "--noconfirm", "broadcom-wl"]]
    assert "not continuing" in capsys.readouterr().out


def test_doctor_reports_the_trap(monkeypatch):
    from ai2 import doctor
    monkeypatch.setattr(broadcom, "current_plan", lambda run=None: broadcom.Plan("remove-wl", message="m", fix="f"))
    c = doctor.check_broadcom()
    assert c.status == doctor.WARN and "Fix: f" in c.detail
    monkeypatch.setattr(broadcom, "current_plan", lambda run=None: broadcom.Plan("clean"))
    assert doctor.check_broadcom().status == doctor.OK


def test_sysfs_detection_matches_the_installer_rule(tmp_path):
    for name, cls, vendor, dev in (("0000:01:00.0", "0x020000", "0x10ec", "0x8168"),
                                   ("0000:02:00.0", "0x028000", "0x14e4", "0x4727"),
                                   ("0000:03:00.0", "0x028000", "0x168c", "0x0036")):
        d = tmp_path / name; d.mkdir()
        (d / "class").write_text(cls + "\n"); (d / "vendor").write_text(vendor + "\n"); (d / "device").write_text(dev + "\n")
    assert broadcom.broadcom_wifi_devices_sysfs(str(tmp_path)) == ["Broadcom WiFi [14e4:4727]"]


def test_broadcom_wifi_short_name_resolves_to_dkms_and_the_kernel_headers(monkeypatch):
    monkeypatch.setattr(broadcom, "headers_package", lambda **kw: "linux-headers")
    pkgs, services, matched = software.resolve(["broadcom-wifi"])
    assert pkgs == ["broadcom-wl-dkms", "linux-headers"] and matched == ["broadcom-wifi"] and services == []
