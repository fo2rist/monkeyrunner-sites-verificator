# -*- coding: utf-8
#######################################
# Created by Dmitry <fo2rist> Sitnikov
# Licensed under LGPL v 
#######################################

# This is the config file  
# Change any parameter to suit your needs.

# Known browsers
###Standard browser for emulator and some vendors.
BROWSER_ANDROID = {"package":"com.android.browser",
                   "activity": "com.android.browser.BrowserActivity"}
###Standard browser for latest android version for all Nexus devices
BROWSER_CHROME = {"package":"com.android.chrome",
                   "activity": "com.google.android.apps.chrome.Main"}
BROWSER_FIREFOX = {"package":"org.mozilla.firefox",
                   "activity": "org.mozilla.firefox.App"}
BROWSER_OPERA = {"package":"com.opera.browser",
                   "activity": "com.opera.Opera"}
###Special light-weight browser for tests, that can be automatically installed on any device.
BROWSER_TEST = {"package":"com.github.fo2rist.testbrowser",
                   "activity": "com.github.fo2rist.testbrowser.MainActivity"}

### Browser component to start
### Use one of known browsers or
### set None to use system default, but in that case browser won't start clean
BROWSER_TO_TEST = BROWSER_TEST

### Max count of scrolls/shots, allow to limit scrolling of infinite pages
MAX_SHOTS_COUNT = 30
### Max allowed delta between two shots for first and last screens
MAX_BOUNDARY_DELTA = 500
### Max allowed delta between two shots for screen in the middle
MAX_INTERMEDIATE_DELTA = 3500


# Path to "compare" utility from Image Magick package.    
#IM_COMPARE_PATH = "C:/Progra~1/ImageMagick/compare.exe" #windows typical path
IM_COMPARE_PATH = "/usr/bin/compare" #linux typical path

# Typical device parameters.
### Height of bar that script will ignore at the top of screen
HEADER_HEIGHT = 144
### Height of bar that script will ignore at the bottom of screen (will be 0 for devices with hardware buttons)  
BUTTON_BAR_HEIGHT = 96