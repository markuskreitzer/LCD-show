# CUQI 3.5-inch Display-F validation

Status: hardware display output validated on 2026-08-13. Touch calibration and
desktop scaling are still in progress.

## Hardware identity

The tested unit came from the
[CUQI Raspberry Pi 5 display kit](https://www.amazon.com/dp/B0D1XXW9MF) sold
under Amazon ASIN `B0D1XXW9MF`. The reported and observed properties are:

- 3.5-inch, 480 x 320 SPI TFT
- ILI9486-compatible display controller
- XPT2046-compatible resistive touch controller
- PCB text: `480 x 320 Pixel`, `SPI 180MHz Support`, and
  `XPT2046 Touch Controller`
- 26-pin GPIO header

The PCB text matches boards commonly identified as `3.5 inch Display-F` in
[community hardware reports](https://community.volumio.com/t/resolved-buster-3-beta-3-5-inch-touchscreen-problem-error/47527?page=2).
An independent Display-F report also identifies the repository's `LCD35`
profile as a working match in
[Graphics Muse issue 1035](https://redmine.graphics-muse.org/issues/1035).
This evidence does not establish that every visually similar board is the same.
Keep the Display-F and MHS3528 profiles separate.

## Tested host

- Raspberry Pi 5 Model B Rev 1.0
- Debian 13 / Raspberry Pi OS userspace
- Raspberry Pi kernel `6.18.39+rpt-rpi-2712`
- Labwc 0.9.8 Wayland desktop

## Working live stack

The following stack produced a visible desktop and working touch events:

1. The in-kernel staging drivers `fb_ili9486`, `fbtft`, and `ads7846`.
2. The repository's `usr/tft35a-overlay.dtb` pinout and initialization data,
   installed under the `mhs35` overlay name. The live overlay used a 115 MHz
   display clock; the archived blob defaults to 16 MHz and exposes a `speed`
   override.
3. GPIO 25 for reset, GPIO 24 for data/command, SPI0 CE0 for display, SPI0 CE1
   for touch, and GPIO 17 for the touch interrupt.
4. A 1920 x 1080 Labwc headless output named `NOOP-1`.
5. `modern/lcd-show-mirror`, run by
   `modern/lcd-show-mirror.service`, to scale the Wayland output to RGB565
   480 x 320 and write it to `/dev/fb0` at 15 frames per second.

The running mirror executable matched the repository copy byte for byte when
this record was written. The user service was active and enabled. The mirror
depends on these Raspberry Pi OS packages rather than vendored code:

- `wf-recorder` 0.5.0-2
- `ffmpeg` 7.1.5-0+deb13u1+rpt1
- `labwc` 0.9.8-1+rpt1
- `wlr-randr` 0.4.1-1

The repository SBOM describes repository contents. It does not prove the
provenance or vulnerability status of these installed operating-system
packages. Debian/Raspberry Pi OS package metadata and updates remain the source
of truth for those dependencies.

## Diagnostic evidence

- With the display connected incorrectly, its backlight was solid white and it
  did not respond visibly to display commands.
- After the connector position was corrected and the working stack booted, the
  LCD showed the desktop.
- The ADS7846 device appeared as `/dev/input/event5`. A physical tap increased
  its interrupt count from 1 to 1669, which confirmed the touch power, chip
  select, interrupt line, and GPIO-header connection.
- The touch device reports raw X and Y ranges of 0 through 4095. Libinput
  reported an identity calibration matrix.
- The earlier modern `panel_mipi_dbi` MHS3528 experiment did not produce a
  validated image on this board. The bad connector position invalidated some
  of those observations, so the modern profile remains experimental rather
  than disproved.

The corrected connector was the immediate cause of the last white-screen
failure. The separate change to the legacy framebuffer stack means this test
does not prove that the modern MHS3528 profile works with this Display-F board.

## Known limitations

- Touch coordinates are substantially wrong. Calibration needs physical taps
  at known screen positions and cannot be completed remotely.
- The 1920 x 1080 source desktop is too small after reduction to 480 x 320.
  Output scaling and a larger terminal font are the next software changes.
- At 15 frames per second, `wf-recorder` used about 53% of one CPU while
  `rf-field` used about 91% of one CPU. The measured temperature was 73.6 C and
  `vcgencmd get_throttled` returned `0x0`. This is a functional result, not a
  thermal or performance acceptance test.
- The fan state cannot be verified remotely.
- The safe installer does not yet reproduce the live Display-F overlay and
  mirror service. The legacy root installers remain unsupported and unsafe for
  this host.

## Remaining acceptance checks

1. Add a crash-safe, reversible Display-F installer instead of using a legacy
   root script.
2. Increase desktop and terminal scale for the 480 x 320 panel.
3. Reduce mirror CPU use while keeping terminal interaction acceptable.
4. Calibrate touch with physical top-left and bottom-right reference taps.
5. Verify all four corners, display rotation, touch rotation, fan operation,
   temperature, and throttling under the intended workload.
