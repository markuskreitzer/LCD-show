import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "mipi_dbi_cmd", ROOT / "modern" / "mipi-dbi-cmd.py"
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
        result = subprocess.run(
            [ROOT / "MHS35-safe", "--dry-run"],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("MHS3528: ILI9486", result.stdout)
        self.assertIn("dtoverlay=mhs3528", result.stdout)
        self.assertNotIn("rc.local", result.stdout)
        self.assertNotIn(".bash_profile", result.stdout)


if __name__ == "__main__":
    unittest.main()
