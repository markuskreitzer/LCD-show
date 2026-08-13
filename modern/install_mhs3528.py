#!/usr/bin/env python3

import argparse
import errno
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from mipi_dbi_cmd import compile_commands


BEGIN = "# BEGIN LCD-show MHS3528"
END = "# END LCD-show MHS3528"
BLOCK = f"{BEGIN}\ndtparam=spi=on\ndtoverlay=mhs3528\n{END}\n"
PROFILE = "mhs3528"
SOURCE_DIR = Path(__file__).resolve().parent


class InstallError(Exception):
    pass


def system_path(root: Path, path: str) -> Path:
    return root / path.removeprefix("/")


def paths(root: Path) -> dict[str, Path]:
    return {
        "config": system_path(root, "/boot/firmware/config.txt"),
        "overlay": system_path(root, "/boot/firmware/overlays/mhs3528.dtbo"),
        "firmware": system_path(root, "/lib/firmware/mhs3528.bin"),
        "state": system_path(root, "/var/lib/lcd-show/mhs3528.json"),
        "backups": system_path(root, "/var/backups/lcd-show"),
    }


def parse_os_release(path: Path) -> dict[str, str]:
    values = {}
    for line in path.read_text().splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value.strip('"')
    return values


def check_system(root: Path) -> None:
    model_path = system_path(root, "/proc/device-tree/model")
    os_release_path = system_path(root, "/etc/os-release")
    config_path = paths(root)["config"]
    if not model_path.exists() or "Raspberry Pi 5" not in model_path.read_text():
        raise InstallError("this profile is validated only for Raspberry Pi 5")
    if not os_release_path.exists():
        raise InstallError("/etc/os-release does not exist")
    release = parse_os_release(os_release_path)
    if release.get("ID") not in {"debian", "raspbian"}:
        raise InstallError("this profile requires Debian or Raspberry Pi OS")
    if release.get("VERSION_ID", "").split(".")[0] != "13":
        raise InstallError("this profile is validated only for Debian 13")
    if not config_path.is_file() or config_path.is_symlink():
        raise InstallError("/boot/firmware/config.txt is missing or is a link")
    if shutil.which("dtc") is None:
        raise InstallError("dtc is required (Debian package: device-tree-compiler)")
    if root == Path("/"):
        for module in ("panel_mipi_dbi", "ads7846"):
            result = subprocess.run(
                ["modinfo", module], capture_output=True, check=False
            )
            if result.returncode:
                raise InstallError(f"the running kernel does not provide {module}")


def managed_span(text: str) -> tuple[int, int] | None:
    lines = text.splitlines(keepends=True)
    begins = [index for index, line in enumerate(lines) if line.rstrip("\r\n") == BEGIN]
    ends = [index for index, line in enumerate(lines) if line.rstrip("\r\n") == END]
    if not begins and not ends:
        return None
    if len(begins) != 1 or len(ends) != 1 or begins[0] >= ends[0]:
        raise InstallError("config.txt has malformed MHS3528 markers")
    return begins[0], ends[0]


def remove_block(text: str) -> str:
    lines = text.splitlines(keepends=True)
    span = managed_span(text)
    if span is None:
        return text
    start, end = span
    return "".join(lines[:start] + lines[end + 1 :])


def add_block(text: str) -> str:
    clean = remove_block(text).rstrip("\n")
    return f"{clean}\n\n{BLOCK}" if clean else BLOCK


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    except OSError as error:
        if error.errno not in {errno.EINVAL, errno.ENOTSUP}:
            raise
    finally:
        os.close(descriptor)


def atomic_write(path: Path, data: bytes, reference: Path | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            if reference is not None:
                details = reference.stat()
                os.fchmod(stream.fileno(), stat.S_IMODE(details.st_mode))
                os.fchown(stream.fileno(), details.st_uid, details.st_gid)
            else:
                os.fchmod(stream.fileno(), 0o644)
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        fsync_directory(path.parent)
    finally:
        if temporary.exists():
            temporary.unlink()


def build_artifacts() -> dict[str, bytes]:
    with tempfile.TemporaryDirectory(prefix="lcd-show-build-") as directory:
        overlay = Path(directory) / "mhs3528.dtbo"
        subprocess.run(
            [
                "dtc",
                "-@",
                "-I",
                "dts",
                "-O",
                "dtb",
                "-o",
                overlay,
                SOURCE_DIR / "mhs3528-overlay.dts",
            ],
            check=True,
        )
        firmware = compile_commands((SOURCE_DIR / "mhs3528-panel.txt").read_text())
        return {"overlay": overlay.read_bytes(), "firmware": firmware}


def load_state(state_path: Path) -> dict | None:
    if not state_path.exists():
        return None
    if state_path.is_symlink() or not state_path.is_file():
        raise InstallError("installer state is not a regular file")
    try:
        state = json.loads(state_path.read_text())
    except (json.JSONDecodeError, OSError) as error:
        raise InstallError("installer state is invalid") from error
    if state.get("profile") != PROFILE or state.get("status") not in {"pending", "installed"}:
        raise InstallError("installer state is invalid")
    artifacts = state.get("artifacts")
    if not isinstance(artifacts, dict) or set(artifacts) != {"overlay", "firmware"}:
        raise InstallError("installer state is invalid")
    if any(
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
        for value in artifacts.values()
    ):
        raise InstallError("installer state is invalid")
    return state


def artifact_hashes(artifacts: dict[str, bytes]) -> dict[str, str]:
    return {name: sha256_bytes(data) for name, data in artifacts.items()}


def validate_artifacts(targets: dict[str, Path], expected: dict[str, str], allow_missing: bool) -> None:
    for name in ("overlay", "firmware"):
        target = targets[name]
        if not target.exists():
            if target.is_symlink():
                raise InstallError(f"managed artifact is a dangling link: {target}")
            if allow_missing:
                continue
            raise InstallError(f"managed artifact is missing: {target}")
        if target.is_symlink() or not target.is_file():
            raise InstallError(f"managed artifact is not a regular file: {target}")
        if sha256_file(target) != expected[name]:
            raise InstallError(f"managed artifact was modified: {target}")


def new_backup_directory(base: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    backup = base / stamp
    backup.mkdir(parents=True, exist_ok=False)
    return backup


def backup_files(backup: Path, targets: dict[str, Path]) -> None:
    for name in ("config", "overlay", "firmware", "state"):
        source = targets[name]
        if source.exists():
            if source.is_symlink() or not source.is_file():
                raise InstallError(f"cannot back up non-regular file: {source}")
            shutil.copy2(source, backup / source.name)


def install(root: Path) -> str:
    check_system(root)
    targets = paths(root)
    original_config = targets["config"].read_text()
    updated_config = add_block(original_config)
    artifacts = build_artifacts()
    expected = artifact_hashes(artifacts)
    state = load_state(targets["state"])
    if state is None:
        collisions = [
            str(targets[name])
            for name in ("overlay", "firmware")
            if targets[name].exists() or targets[name].is_symlink()
        ]
        if collisions:
            raise InstallError("refusing to overwrite unmanaged files: " + ", ".join(collisions))
    else:
        if state.get("artifacts") != expected:
            raise InstallError("installed profile differs; uninstall it before updating")
        validate_artifacts(targets, expected, allow_missing=state["status"] == "pending")
        if (
            state["status"] == "installed"
            and updated_config == original_config
            and all(targets[name].exists() for name in ("overlay", "firmware"))
        ):
            return "MHS3528 profile is already installed."
    backup = new_backup_directory(targets["backups"])
    backup_files(backup, targets)
    pending = {"profile": PROFILE, "status": "pending", "artifacts": expected}
    atomic_write(targets["state"], (json.dumps(pending, sort_keys=True) + "\n").encode())
    atomic_write(targets["overlay"], artifacts["overlay"])
    atomic_write(targets["firmware"], artifacts["firmware"])
    if updated_config != original_config:
        atomic_write(targets["config"], updated_config.encode(), targets["config"])
    installed = {"profile": PROFILE, "status": "installed", "artifacts": expected}
    atomic_write(targets["state"], (json.dumps(installed, sort_keys=True) + "\n").encode())
    return f"Installed the MHS3528 profile. Backup: {backup / 'config.txt'}"


def uninstall(root: Path) -> str:
    targets = paths(root)
    if not targets["config"].is_file() or targets["config"].is_symlink():
        raise InstallError("/boot/firmware/config.txt is missing or is a link")
    original_config = targets["config"].read_text()
    updated_config = remove_block(original_config)
    state = load_state(targets["state"])
    if state is None:
        unmanaged = [
            str(targets[name])
            for name in ("overlay", "firmware")
            if targets[name].exists() or targets[name].is_symlink()
        ]
        if updated_config != original_config or unmanaged:
            raise InstallError("MHS3528 files exist without installer state; refusing removal")
        return "MHS3528 profile is already removed."
    expected = state["artifacts"]
    validate_artifacts(targets, expected, allow_missing=True)
    backup = new_backup_directory(targets["backups"])
    backup_files(backup, targets)
    if updated_config != original_config:
        atomic_write(targets["config"], updated_config.encode(), targets["config"])
    for name in ("overlay", "firmware"):
        target = targets[name]
        if target.exists():
            target.unlink()
            fsync_directory(target.parent)
    targets["state"].unlink()
    fsync_directory(targets["state"].parent)
    return f"Removed the MHS3528 profile. Backup: {backup / 'config.txt'}"


def dry_run(root: Path) -> str:
    check_system(root)
    targets = paths(root)
    original = targets["config"].read_text()
    updated = add_block(original)
    artifacts = build_artifacts()
    state = load_state(targets["state"])
    if state is None:
        collisions = [
            str(targets[name])
            for name in ("overlay", "firmware")
            if targets[name].exists() or targets[name].is_symlink()
        ]
        if collisions:
            raise InstallError("refusing to overwrite unmanaged files: " + ", ".join(collisions))
    else:
        expected = artifact_hashes(artifacts)
        if state["artifacts"] != expected:
            raise InstallError("installed profile differs; uninstall it before updating")
        validate_artifacts(targets, expected, allow_missing=state["status"] == "pending")
    lines = [
        "MHS3528: ILI9486 display on SPI0 CE0; XPT2046 touch on CE1",
        f"Would install: {targets['overlay']}",
        f"Would install: {targets['firmware']}",
        f"Would update atomically: {targets['config']}",
        f"Would back up under: {targets['backups']}/<UTC timestamp>",
    ]
    if updated == original:
        lines.append("config.txt already contains the managed block.")
    else:
        lines.extend(("Would add:", BLOCK.rstrip()))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        usage="sudo ./MHS35-safe {--dry-run|--install|--uninstall}"
    )
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--dry-run", action="store_true")
    action.add_argument("--install", action="store_true")
    action.add_argument("--uninstall", action="store_true")
    args = parser.parse_args()
    root = Path(os.environ.get("LCD_SHOW_ROOT", "/"))
    if not root.is_absolute():
        raise InstallError("LCD_SHOW_ROOT must be absolute")
    root = root.resolve()
    if root == Path("/") and (args.install or args.uninstall) and os.geteuid() != 0:
        raise InstallError("install and uninstall require root")
    if args.dry_run:
        print(dry_run(root))
    elif args.install:
        print(install(root))
        print("Power off before attaching the display. This command does not reboot.")
    else:
        print(uninstall(root))
        print("Reboot to finish removal.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (InstallError, OSError, subprocess.CalledProcessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1)
