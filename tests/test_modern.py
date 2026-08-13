import importlib.util
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "mipi_dbi_cmd", ROOT / "modern" / "mipi_dbi_cmd.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


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
        self.write("proc/device-tree/model", "Raspberry Pi 5 Model B Rev 1.0\0")
        self.write("etc/os-release", 'ID="debian"\nVERSION_ID="13"\n')
        self.write("boot/firmware/config.txt", "dtparam=audio=on\n")
        (self.system_root / "boot/firmware/overlays").mkdir()
        (self.system_root / "lib/firmware").mkdir(parents=True)

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

    def test_dry_run_lists_only_targeted_changes(self):
        result = self.run_installer("--dry-run")

        self.assertIn("MHS3528: ILI9486", result.stdout)
        self.assertIn("dtoverlay=mhs3528", result.stdout)
        self.assertNotIn("rc.local", result.stdout)
        self.assertNotIn(".bash_profile", result.stdout)

    def test_install_is_idempotent_and_uninstall_is_targeted(self):
        first = self.run_installer("--install")
        config = self.system_root / "boot/firmware/config.txt"
        overlay = self.system_root / "boot/firmware/overlays/mhs3528.dtbo"
        firmware = self.system_root / "lib/firmware/mhs3528.bin"
        state = self.system_root / "var/lib/lcd-show/mhs3528.json"

        self.assertIn("Installed", first.stdout)
        self.assertEqual(config.read_text().count("# BEGIN LCD-show MHS3528"), 1)
        self.assertTrue(overlay.is_file())
        self.assertTrue(firmware.is_file())
        self.assertTrue(state.is_file())
        self.assertIn("already installed", self.run_installer("--install").stdout)

        removed = self.run_installer("--uninstall")
        self.assertIn("Removed", removed.stdout)
        self.assertEqual(config.read_text(), "dtparam=audio=on\n\n")
        self.assertFalse(overlay.exists())
        self.assertFalse(firmware.exists())
        self.assertFalse(state.exists())
        self.assertGreaterEqual(
            len(list((self.system_root / "var/backups/lcd-show").glob("*/config.txt"))),
            2,
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

    def test_refuses_unsupported_system(self):
        self.write("proc/device-tree/model", "Raspberry Pi 4 Model B\0")

        result = self.run_installer("--dry-run", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Raspberry Pi 5", result.stderr)


if __name__ == "__main__":
    unittest.main()
