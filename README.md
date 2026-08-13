# LCD-show

> **Warning:** The legacy `*-show` scripts make broad root-level changes to
> boot, X11, package, and startup configuration. Do not run them on a current
> Raspberry Pi OS installation without reviewing them first. See
> [RESEARCH_NOTES.md](RESEARCH_NOTES.md).

The CUQI 3.5-inch hardware tested on Raspberry Pi 5 matches the common
`Display-F` board and is documented in
[HARDWARE_VALIDATION.md](HARDWARE_VALIDATION.md). Its validated driver path is
different from the MHS3528 profile, even though the seller supplied similar
specifications.

## Safer MHS3528 support for Raspberry Pi 5

`MHS35-safe` is an experimental, source-only installer for the MHS3528 board:

- 3.5-inch, 480 x 320 ILI9486 SPI display
- XPT2046 resistive touch controller
- Raspberry Pi 5 with the in-kernel `panel_mipi_dbi` and `ads7846` drivers

It downloads nothing, changes no packages, and does not replace X11, login, or
startup files. It installs one device-tree overlay, one panel command file, and
one marked block in `/boot/firmware/config.txt`. It makes a timestamped backup
and supports targeted removal.

The display initialization commands come from the repository's original
MHS3528 overlay. The replacement uses the Raspberry Pi kernel's DRM MIPI DBI
panel driver in RGB565 mode and the in-kernel ADS7846-compatible touch driver.
Its experimental SPI clock is capped at a conservative 16 MHz. The profile
does not install third-party executables. This profile is not the validated
path for the CUQI `Display-F` board.

Inspect the planned changes first:

```sh
./MHS35-safe --dry-run
```

After you have stable Pi 5 power and cooling, install while the display is
disconnected:

```sh
sudo ./MHS35-safe --install
sudo poweroff
```

Attach the display only after shutdown. This profile still needs hardware
validation on Raspberry Pi 5. To remove it, use `sudo ./MHS35-safe --uninstall`
and reboot.

## Validated CUQI Display-F components

The CUQI board produced a visible desktop with the kernel `fb_ili9486` and
`ads7846` drivers plus the source-only mirror in `modern/lcd-show-mirror`. The
matching user unit is `modern/lcd-show-mirror.service`. The helper uses the
Raspberry Pi OS `wf-recorder` and `wlr-randr` packages; it downloads nothing.
For a headless `NOOP-*` source only, it selects a 960 x 640 mode with 2x scale.
This gives the LCD a 480 x 320 logical desktop. Damage tracking keeps an idle
terminal from consuming CPU continuously.

These files are preserved as validated building blocks, but the safe installer
does not install them yet. Do not run the legacy `LCD35-show` installer to
reproduce the result. See [HARDWARE_VALIDATION.md](HARDWARE_VALIDATION.md) for
the exact live state, dependencies, limitations, and remaining work.

## Archived upstream instructions

The remaining `*-show` scripts are retained only for source review. They are
not supported by this fork. Do not run them on a current installation. The
MHS3528 legacy entry point is disabled and directs users to `MHS35-safe`.

### Install drivers in the Ubuntu system
https://github.com/lcdwiki/LCD-show-ubuntu

### Install drivers in the Kali system
https://github.com/lcdwiki/LCD-show-kali

### Install drivers in the RetroPie system
https://github.com/lcdwiki/LCD-show-retropie



Install drivers in the Raspbian system<br>
====================================================
Update: <br>
  v2.1-20191106<br>
  Update to support MHS35B<br>
Update: <br>
  v2.0-20190704<br>
  Update to support rotate the display direction<br>
Update: <br>
  v1.9-20181204<br>
  Update to support MHS40 & MHS32<br>
Update: <br>
  v1.8-20180907<br>
  Update to support MHS35<br>
Update: <br>
  v1.7-20180320<br>
  Update to support Raspbian Version: March 2018(Release date:2018-03-13)<br>
Update: <br>
  v1.6-20170824<br>
  Update xserver to support Raspbian-2017-08-16<br>
Update: <br>
  v1.5-20170706<br>
  Update to support Raspbian-2017-07-05, Raspbian-2017-06-21<br>
Update: <br>
  v1.3-20170612<br>
  fixed to support Raspbian-2017-03-02, Raspbian-2017-04-10<br>
Update: <br>
  v1.2-20170302<br>
  Add xserver-xorg-input-evdev_1%3a2.10.3-1_armhf.deb to support Raspbian-2017-03-02<br>
Update: <br>
  v1.1-20160815<br><br>


# How to install the LCD driver of Raspberry Pi
  
1.)Step1, Install Raspbian official mirror <br>
====================================================
  a)Download Raspbian official mirror:<br>
  https://www.raspberrypi.org/downloads/<br>
  b)Use“SDFormatter.exe”to Format your TF Card<br>
  c)Use“Win32DiskImager.exe” Burning mirror to TF Card<br>
     
2.) Step2, Clone my repo onto your pi<br>
====================================================
Use SSH to connect the Raspberry Pi, <br>
And Ensure that the Raspberry Pi is connected to the Internet before executing the following commands:
-----------------------------------------------------------------------------------------------------

```sudo rm -rf LCD-show```<br>
```git clone https://github.com/goodtft/LCD-show.git```<br>
```chmod -R 755 LCD-show```<br>
```cd LCD-show/```<br>
  
3.)Step3, According to your LCD's type, excute the corresponding driver:
====================================================

# 2.4” RPi Display (MPI2401):
### Driver install:
sudo ./LCD24-show
### WIKI:
CN: http://www.lcdwiki.com/zh/2.4inch_RPi_Display  <br>
EN: http://www.lcdwiki.com/2.4inch_RPi_Display
 

# 2.4” RPi Display For RPi 3A+ (MPI2411):
### Driver install:
sudo ./LCD24-3A+-show  
### WIKI:
CN: http://www.lcdwiki.com/zh/2.4inch_RPi_Display_For_RPi_3A+   <br>
EN: http://www.lcdwiki.com/2.4inch_RPi_Display_For_RPi_3A+

# 2.8” RPi Display (MPI2801):
### Driver install:
sudo ./LCD28-show 
### WIKI:
CN: http://www.lcdwiki.com/zh/2.8inch_RPi_Display  <br>
EN: http://www.lcdwiki.com/2.8inch_RPi_Display
  
# 3.2” RPi Display (MPI3201):
### Driver install:
sudo ./LCD32-show   
### WIKI:
CN: http://www.lcdwiki.com/zh/3.2inch_RPi_Display  <br>
EN: http://www.lcdwiki.com/3.2inch_RPi_Display

# MHS-3.2” RPi Display (MHS3232):
### Driver install:
sudo ./MHS32-show   
### WIKI:
CN: http://www.lcdwiki.com/zh/MHS-3.2inch_Display  <br>
EN: http://www.lcdwiki.com/MHS-3.2inch_Display

# 3.5” RPi Display(MPI3501):
### Driver install:
sudo ./LCD35-show
### WIKI:
CN: http://www.lcdwiki.com/zh/3.5inch_RPi_Display  <br>
EN: http://www.lcdwiki.com/3.5inch_RPi_Display
   
# 3.5” HDMI Display-B(MPI3508):
### Driver install:
sudo ./MPI3508-show
### WIKI:
CN: http://www.lcdwiki.com/zh/3.5inch_HDMI_Display-B  <br>
EN: http://www.lcdwiki.com/3.5inch_HDMI_Display-B
    
# MHS-3.5” RPi Display(MHS3528):
### Driver install:
./MHS35-safe --dry-run
### WIKI:
CN: http://www.lcdwiki.com/zh/MHS-3.5inch_RPi_Display  <br>
EN:http://www.lcdwiki.com/MHS-3.5inch_RPi_Display

# MHS-3.5” RPi Display-B(MHS35XX):
### Driver install:
sudo ./MHS35B-show
### WIKI:
CN: http://www.lcdwiki.com/zh/MHS-3.5inch_RPi_Display-B  <br>
EN:http://www.lcdwiki.com/MHS-3.5inch_RPi_Display-B

# 4.0" HDMI Display(MPI4008):
### Driver install:
sudo ./MPI4008-show
### WIKI:
CN: http://www.lcdwiki.com/zh/4inch_HDMI_Display-C  <br>
EN: http://www.lcdwiki.com/4inch_HDMI_Display-C
   
# MHS-4.0" HDMI Display-B(MHS4001):
### Driver install:
sudo ./MHS40-show
### WIKI:
CN: http://www.lcdwiki.com/zh/MHS-4.0inch_Display-B  <br>
EN: http://www.lcdwiki.com/MHS-4.0inch_Display-B
  
# 5.0” HDMI Display(Resistance touch)(MPI5008):
### Driver install:
sudo ./LCD5-show
### WIKI:
CN: http://www.lcdwiki.com/zh/5inch_HDMI_Display  <br>
EN: http://www.lcdwiki.com/5inch_HDMI_Display
    
# 5inch HDMI Display-B(Capacitor touch)(MPI5001):
### Driver install:
sudo ./MPI5001-show
### WIKI:
CN: http://www.lcdwiki.com/zh/5inch_HDMI_Display-B  <br>
EN: http://www.lcdwiki.com/5inch_HDMI_Display-B
    
# 7inch HDMI Display-B-800X480(MPI7001):
### Driver install:
sudo ./LCD7B-show
### WIKI:
CN: http://www.lcdwiki.com/zh/7inch_HDMI_Display-B  <br>
EN: http://www.lcdwiki.com/7inch_HDMI_Display-B
   
# 7inch HDMI Display-C-1024X600(MPI7002):
### Driver install:
sudo ./LCD7C-show
### WIKI:
CN: http://www.lcdwiki.com/zh/7inch_HDMI_Display-C  <br>
EN: http://www.lcdwiki.com/7inch_HDMI_Display-C
   
Wait for a moment after executing the above command, then you can use the corresponding raspberry LCD.




# How to rotate the display direction

This method only applies to the Raspberry Pi series of display screens, other display screens do not apply.

### Method 1, If the driver is not installed, execute the following command (Raspberry Pi needs to connected to the Internet):

sudo rm -rf LCD-show<br>
git clone https://github.com/goodtft/LCD-show.git<br>
chmod -R 755 LCD-show<br>
cd LCD-show/<br>
sudo ./XXX-show 90<br>

After execution, the driver will be installed. The system will automatically restart, and the display screen will rotate 90 degrees to display and touch normally.<br>
( ' XXX-show ' can be changed to the corresponding driver, and ' 90 ' can be changed to 0, 90, 180 and 270, respectively representing rotation angles of 0 degrees, 90 degrees, 180 degrees, 270 degrees)<br>

### Method 2, If the driver is already installed, execute the following command:

cd LCD-show/<br>
sudo ./rotate.sh 90<br>

After execution, the system will automatically restart, and the display screen will rotate 90 degrees to display and touch normally.<br>
( ' 90 ' can be changed to 0, 90, 180 and 270, respectively representing rotation angles of 0 degrees, 90 degrees, 180 degrees, 270 degrees)<br>
(If the rotate.sh prompt cannot be found, use Method 1 to install the latest drivers)
