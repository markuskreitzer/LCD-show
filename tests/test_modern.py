import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "modern"))
SPEC = importlib.util.spec_from_file_location(
    "mipi_dbi_cmd", ROOT / "modern" / "mipi_dbi_cmd.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
INSTALLER_SPEC = importlib.util.spec_from_file_location(
    "install_mhs3528", ROOT / "modern" / "install_mhs3528.py"
)
INSTALLER = importlib.util.module_from_spec(INSTALLER_SPEC)
INSTALLER_SPEC.loader.exec_module(INSTALLER)


class MipiDbiCommandTests(unittest.TestCase):
    def test_compiles_commands_and_delays(self):
        result = MODULE.compile_commands("command 0x11\ndelay 120\ncommand 0x29\n")

        self.assertEqual(
            result,
            b"MIPI DBI" + bytes(7) + bytes([1, 0x11, 0, 0, 1, 120, 0x29, 0]),
        )

    def test_rejects_values_larger_than_one_byte(self):
        with self.assertRaisesRegex(ValueError, "not one byte"):
            MODULE.compile_commands("command 0x11 256")


class Mhs3528ProfileTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.system_root = Path(self.temporary_directory.name)
        self.populate_system(self.system_root)

    @staticmethod
    def populate_system(root):
        def write(relative_path, content):
            path = root / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)

        write("proc/device-tree/model", "Raspberry Pi 5 Model B Rev 1.0\0")
        write("etc/os-release", 'ID="debian"\nVERSION_ID="13"\n')
        write("boot/firmware/config.txt", "dtparam=audio=on\n")
        (root / "boot/firmware/overlays").mkdir()
        (root / "lib/firmware").mkdir(parents=True)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def write(self, relative_path, content):
        path = self.system_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def run_installer(self, action, check=True):
        environment = os.environ.copy()
        environment["LCD_SHOW_ROOT"] = str(self.system_root)
        return subprocess.run(
            [ROOT / "MHS35-safe", action],
            check=check,
            capture_output=True,
            text=True,
            env=environment,
        )

    def test_overlay_compiles(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "mhs3528.dtbo"
            subprocess.run(
                [
                    "dtc",
                    "-@",
                    "-I",
                    "dts",
                    "-O",
                    "dtb",
                    "-o",
                    output,
                    ROOT / "modern" / "mhs3528-overlay.dts",
                ],
                check=True,
            )
            self.assertGreater(output.stat().st_size, 0)

    def test_panel_profile_matches_mhs3528_bus_format_and_reset_sequence(self):
        overlay = (ROOT / "modern" / "mhs3528-overlay.dts").read_text()
        commands = (ROOT / "modern" / "mhs3528-panel.txt").read_text()

        self.assertIn('format = "r5g6b5";', overlay)
        self.assertIn("reset-gpios = <&gpio 25 0>;", overlay)
        self.assertIn("command 0x3a 0x55", commands)

    def test_dry_run_exactly_lists_targeted_changes_and_no_op(self):
        result = self.run_installer("--dry-run")

        self.assertEqual(
            result.stdout,
            "\n".join(
                [
                    "MHS3528: ILI9486 display on SPI0 CE0; XPT2046 touch on CE1",
                    f"Would write state atomically: {self.system_root}/var/lib/lcd-show/mhs3528.json",
                    f"Would install atomically: {self.system_root}/boot/firmware/overlays/mhs3528.dtbo",
                    f"Would install atomically: {self.system_root}/lib/firmware/lcdwiki,mhs3528.bin",
                    f"Would update atomically: {self.system_root}/boot/firmware/config.txt",
                    f"Would back up under: {self.system_root}/var/backups/lcd-show/<UTC timestamp>",
                    "Would add:",
                    "# BEGIN LCD-show MHS3528",
                    "[all]",
                    "dtparam=spi=on",
                    "dtoverlay=mhs3528",
                    "# END LCD-show MHS3528",
                    "",
                ]
            ),
        )
        self.assertNotIn("rc.local", result.stdout)
        self.assertNotIn(".bash_profile", result.stdout)

        self.run_installer("--install")
        no_op = self.run_installer("--dry-run")
        self.assertEqual(
            no_op.stdout,
            "MHS3528 profile is already installed; no filesystem changes would be made.\n",
        )

    def test_install_is_idempotent_and_uninstall_is_targeted(self):
        first = self.run_installer("--install")
        config = self.system_root / "boot/firmware/config.txt"
        overlay = self.system_root / "boot/firmware/overlays/mhs3528.dtbo"
        firmware = self.system_root / "lib/firmware/lcdwiki,mhs3528.bin"
        state = self.system_root / "var/lib/lcd-show/mhs3528.json"

        self.assertIn("Installed", first.stdout)
        self.assertEqual(config.read_text().count("# BEGIN LCD-show MHS3528"), 1)
        self.assertTrue(overlay.is_file())
        self.assertTrue(firmware.is_file())
        self.assertTrue(state.is_file())
        self.assertIn("already installed", self.run_installer("--install").stdout)

        removed = self.run_installer("--uninstall")
        self.assertIn("Removed", removed.stdout)
        self.assertEqual(config.read_text(), "dtparam=audio=on\n")
        self.assertFalse(overlay.exists())
        self.assertFalse(firmware.exists())
        self.assertFalse(state.exists())
        self.assertGreaterEqual(
            len(list((self.system_root / "var/backups/lcd-show").glob("*/config.txt"))),
            2,
        )

    def test_preserves_config_bytes_and_keeps_overlay_global(self):
        config = self.system_root / "boot/firmware/config.txt"
        original = "dtparam=audio=on\n[pi4]\nlegacy=value"
        config.write_text(original)

        self.run_installer("--install")
        installed = config.read_text()
        self.assertIn("\n# BEGIN LCD-show MHS3528\n[all]\n", installed)
        self.assertTrue(installed.startswith(original))

        suffix = "[pi5]\nuser=value\n"
        config.write_text(installed + suffix)
        self.assertIn("already installed", self.run_installer("--install").stdout)
        self.run_installer("--uninstall")
        self.assertEqual(config.read_text(), original + suffix)

    def test_recovers_after_each_atomic_write_interruption(self):
        for fail_before in range(1, 6):
            with self.subTest(fail_before=fail_before), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.populate_system(root)
                real_atomic_write = INSTALLER.atomic_write
                calls = 0

                def interrupted(*args, **kwargs):
                    nonlocal calls
                    calls += 1
                    if calls == fail_before:
                        raise OSError("simulated power loss")
                    return real_atomic_write(*args, **kwargs)

                with mock.patch.object(INSTALLER, "atomic_write", side_effect=interrupted):
                    with self.assertRaisesRegex(OSError, "simulated power loss"):
                        INSTALLER.install(root)

                self.assertIn("Installed", INSTALLER.install(root))
                self.assertEqual(
                    INSTALLER.load_state(INSTALLER.paths(root)["state"])["status"],
                    "installed",
                )

    def test_refuses_malformed_markers_without_changing_config(self):
        config = self.system_root / "boot/firmware/config.txt"
        original = "dtparam=audio=on\n# BEGIN LCD-show MHS3528\nkeep=this\n"
        config.write_text(original)

        result = self.run_installer("--install", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("malformed", result.stderr)
        self.assertEqual(config.read_text(), original)
        self.assertFalse((self.system_root / "var/lib/lcd-show/mhs3528.json").exists())

    def test_refuses_unmanaged_artifact_collision(self):
        overlay = self.system_root / "boot/firmware/overlays/mhs3528.dtbo"
        overlay.write_bytes(b"user file")

        result = self.run_installer("--install", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refusing to overwrite unmanaged", result.stderr)
        self.assertEqual(overlay.read_bytes(), b"user file")

    def test_refuses_non_object_state(self):
        self.write("var/lib/lcd-show/mhs3528.json", "[]\n")

        result = self.run_installer("--dry-run", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("installer state is invalid", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_refuses_unsupported_system(self):
        self.write("proc/device-tree/model", "Raspberry Pi 4 Model B\0")

        result = self.run_installer("--dry-run", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Raspberry Pi 5", result.stderr)


if __name__ == "__main__":
    unittest.main()
