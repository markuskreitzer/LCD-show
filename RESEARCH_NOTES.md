# Security and suitability review of `goodtft/LCD-show`

Reviewed 2026-08-12 at commit [`3fdfac02b914a7597a8010ece5b7082b9f5836e8`](https://github.com/goodtft/LCD-show/commit/3fdfac02b914a7597a8010ece5b7082b9f5836e8). This was a static review. No repository script or bundled program was run.

## Verdict

I found **no evidence that this repository is spyware**. The tracked installer scripts do not read credentials, alter SSH keys, create users, open listeners, or upload data. Their explicit network activity consists of connectivity checks to CMake, GitHub, PyPI, and a Zhejiang University mirror, plus an unpinned clone of `tasanakorn/rpi-fbcp`. The Chinese mirror is contacted by an HTTP `wget --spider` check; the script then uses the system's configured APT sources. See [`LCD35-show` lines 59-140](https://github.com/goodtft/LCD-show/blob/3fdfac02b914a7597a8010ece5b7082b9f5836e8/LCD35-show#L59-L140).

That does **not** make the installer safe. I recommend that you **do not run its one-shot root scripts on this Pi**. They are invasive, weakly maintained, and likely to damage a modern Raspberry Pi OS installation. The main risk is poor engineering and excessive privilege, not evidence of espionage.

The LCD is worth testing again, but only after the power and cooling problems are fixed. Use a minimal, model-specific Raspberry Pi configuration instead of the vendor installer.

## Evidence from the repository

- The public repository has existed since August 2016, has about 2,700 stars and 895 forks, and was last pushed in November 2025. It has no releases and no declared license. Most commits come from one account. These facts show long public exposure, but they are not a security audit or a trust guarantee. [GitHub repository metadata](https://api.github.com/repos/goodtft/LCD-show), [contributors](https://api.github.com/repos/goodtft/LCD-show/contributors), [releases](https://api.github.com/repos/goodtft/LCD-show/releases).
- The checked-out tip matches `origin/master`. The recent commits are not cryptographically signed. This weakens provenance.
- The install scripts run with root access and replace boot, X11, module, and startup configuration. For example, `LCD35-show` copies a device-tree blob, replaces `/boot/config.txt`, changes display settings, installs software, places `fbcp` in `/usr/local/bin`, replaces `/etc/rc.local`, and reboots. [`LCD35-show` lines 3-42](https://github.com/goodtft/LCD-show/blob/3fdfac02b914a7597a8010ece5b7082b9f5836e8/LCD35-show#L3-L42), [`LCD35-show` lines 64-96](https://github.com/goodtft/LCD-show/blob/3fdfac02b914a7597a8010ece5b7082b9f5836e8/LCD35-show#L64-L96), [`LCD35-show` lines 147-157](https://github.com/goodtft/LCD-show/blob/3fdfac02b914a7597a8010ece5b7082b9f5836e8/LCD35-show#L147-L157).
- The so-called backup helper deletes the whole `/etc/X11/xorg.conf.d` directory without copying its full contents, replaces the boot configuration with a bundled template, replaces `/etc/rc.local` and `/etc/modules`, removes `fbcp`, and can purge the EVDEV package. [`system_backup.sh` lines 8-23](https://github.com/goodtft/LCD-show/blob/3fdfac02b914a7597a8010ece5b7082b9f5836e8/system_backup.sh#L8-L23), [`system_backup.sh` lines 38-80](https://github.com/goodtft/LCD-show/blob/3fdfac02b914a7597a8010ece5b7082b9f5836e8/system_backup.sh#L38-L80), [`system_backup.sh` lines 91-101](https://github.com/goodtft/LCD-show/blob/3fdfac02b914a7597a8010ece5b7082b9f5836e8/system_backup.sh#L91-L101).
- On Debian versions later than 13.1, several installers overwrite the user's `.bash_profile` with a file that runs `startx` at every login. This can break SSH sessions. [`LCD35-show` lines 40-45](https://github.com/goodtft/LCD-show/blob/3fdfac02b914a7597a8010ece5b7082b9f5836e8/LCD35-show#L40-L45), [shipped `.bash_profile`](https://github.com/goodtft/LCD-show/blob/3fdfac02b914a7597a8010ece5b7082b9f5836e8/etc/.bash_profile), [direct user report #429](https://github.com/goodtft/LCD-show/issues/429).
- The scripts compile the current, unpinned head of another GitHub repository as root. If the network is unavailable, they compile a bundled copy instead. This is a supply-chain weakness. [`LCD35-show` lines 73-89](https://github.com/goodtft/LCD-show/blob/3fdfac02b914a7597a8010ece5b7082b9f5836e8/LCD35-show#L73-L89).
- The repository contains five old Debian packages and an old PyMouse source archive. Three package files used on `all` or `arm64` systems exactly match files archived by Debian, based on their SHA-1 file keys: [`python-xlib`](https://snapshot.debian.org/mr/file/78a33fc8a7e749069565a32142462b66c27d1c38/info), [`xinput-calibrator`](https://snapshot.debian.org/mr/file/b3385a210db064bfa6023b6dfd50d1a1359c2722/info), and [`xserver-xorg-input-evdev`](https://snapshot.debian.org/mr/file/224867f831d2f986cfd2f7f2ec91898280e80a5c/info). I did not establish official archive matches for the two `armhf` files or the PyMouse archive.
- The bundled device-tree blobs decompile to expected display and touch declarations such as `ilitek,ili9486`, `ilitek,ili9340`, `ti,ads7846`, `goodix,gt9271`, and `sitronix,st7789v`. Device-tree blobs are configuration data, not executable programs.
- Open issues report damaged desktop/configuration setups and incompatibility with modern KMS. These reports match the reviewed script behavior. [Issue #428](https://github.com/goodtft/LCD-show/issues/428), [issue #423](https://github.com/goodtft/LCD-show/issues/423).

Static analysis cannot prove that software is harmless, and GitHub popularity cannot prove trust. However, the visible behavior is consistent with a dated, over-broad display installer rather than spyware. The product's country of origin is not evidence of malicious behavior.

## A safer driver route

Raspberry Pi already ships kernel support for common controllers used by these displays. Its official `fbtft` overlay supports SPI displays and controllers such as ILI9341 and ILI9486, with parameters for pins, speed, and rotation. [Official overlay documentation](https://raw.githubusercontent.com/raspberrypi/firmware/master/boot/overlays/README) (the `fbtft` section starts at line 1275). The Raspberry Pi kernel also includes generic ILI9486 support. [Official kernel Kconfig](https://github.com/raspberrypi/linux/blob/rpi-6.12.y/drivers/staging/fbtft/Kconfig#L77-L81).

`fbtft` is in the kernel staging area, so it is not a high-quality modern interface. Raspberry Pi also provides the newer `mipi-dbi-spi` DRM/KMS overlay, but it needs the exact panel initialization data. [Official `mipi-dbi-spi` documentation](https://raw.githubusercontent.com/raspberrypi/firmware/master/boot/overlays/README) (starts at line 3387), [official driver source](https://github.com/raspberrypi/linux/blob/rpi-6.12.y/drivers/gpu/drm/tiny/panel-mipi-dbi.c). Do not guess the controller, wiring, or initialization data. The exact Amazon product/model number or a clear photo of its label is needed before choosing a configuration.

## Current Pi health and reconnect recommendation

This machine identifies as a **Raspberry Pi 5 Model B**. During this review:

- `vcgencmd pmic_read_adc EXT5V_V` reported **5.163 V**.
- `vcgencmd get_throttled` reported **`0xe0006`**.
- CPU temperature was **85-86°C**.

Raspberry Pi defines `0x2` as current Arm frequency capping and `0x4` as current throttling. The high bits in `0xe0006` record earlier frequency capping, throttling, and a soft-temperature-limit event. No current or historical undervoltage bit was set in this reading. [Official `get_throttled` bit table](https://www.raspberrypi.com/documentation/computers/os.html#vcgencmd).

The Pi is therefore **thermally throttling now**. Keep the LCD disconnected. Fix cooling and reduce sustained load first. Also replace the unstable supply with a good USB-C cable and a model-correct supply. Raspberry Pi recommends **5 V at 5 A (27 W)** for Pi 5; a 5 V/3 A supply limits peripheral current to 600 mA. [Official power guidance](https://www.raspberrypi.com/documentation/computers/getting-started.html#power-supply). Raspberry Pi also requires the supply to remain above 4.8 V and says that a drop below 4.63 V causes throttling. [Official voltage guidance](https://www.raspberrypi.com/documentation/computers/config_txt.html#monitoring-voltage).

Recommended sequence:

1. Use a stable 27 W Pi 5 supply and adequate active cooling. Confirm a normal temperature and `throttled=0x0` under the intended workload.
2. Back up important data. Prior hard crashes can corrupt storage.
3. Power off, attach the LCD, and boot without running any vendor script. If it is HDMI with USB touch, standard kernel drivers may already be sufficient.
4. If it is a GPIO/SPI panel, identify its exact model, controller, touch controller, and pinout. Apply only the required official overlay or a manually reviewed panel-specific overlay.
5. If the vendor script is the only workable option, test it on a disposable SD card with no sensitive data. Do not use it on the current installation.

