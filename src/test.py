# -*- coding: utf-8
# Imports the monkeyrunner modules used by this program
from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice

from os import system
from os import path
import os
import shlex
from subprocess import Popen, PIPE
import sys
import urllib

FILENAMES_ENCODING = "utf-8"

MAX_SHOTS_COUNT = 30

BASE_PATH = "/home/dmitry/workspace/TEST-monkeyrunner"
#COMPARE_LOCATION = BASE_PATH+"/im/compare.exe" #windows
COMPARE_LOCATION = "/usr/bin/compare"         #linux

# browser package's internal name
package = 'com.android.browser'
# browser Activity in the package
activity = 'com.android.browser.BrowserActivity'
# browser component to start
runComponent = package + '/' + activity


#Device screen size should be set up
height = 0
width = 0
typicalHeader = 144
typicalButtonBar = 96
    

### Open file with list of URLs
def openUrlsList():
    return open(BASE_PATH + "/assets/urls.txt", 'r')


### Wait for monkey device, set global device info and kill current browser instance.
### @return:  device
def connectAndSetup():
    # Connects to the current device, returning a MonkeyDevice object
    device = MonkeyRunner.waitForConnection()
    
    global height
    height = int(device.getProperty("display.height"))
    global width
    width = int(device.getProperty("display.width"))
    
    # kill current instance
    device.shell('am force-stop ' + package)
    
    return device


### Scroll one screen.
def scrollBasedOnHeight(device):
    device.drag((1, height - typicalButtonBar - 4),
                (1, typicalHeader + 4),
                2.4,
                10)


### Open url in browser and wait for load
def openUrlOnDevice(device, url):
    # Runs the component to view URL
    device.startActivity(action="android.intent.action.VIEW", component=runComponent, data=url)
    # Wait for load
    MonkeyRunner.sleep(12)


### Compare two image via imagemagick
### @return: difference as a number, or -1 in case of errors
def compareImages(first, second, result):
    compareStr = '%(compare)s -metric AE -extract %(area)s '\
                   ' "%(first)s"'\
                   ' "%(second)s"'\
                   ' "%(result)s"'%{
                                 "area": str(width)+"x"+str(height-typicalHeader)+"+0+"+str(typicalHeader),
                                 "compare": COMPARE_LOCATION,
                                 "first": first,
                                 "second": second,
                                 "result": result }
    #system(compareStr) #Old way to run
    process = Popen(shlex.split(compareStr), stderr=PIPE)
    result = process.communicate()
    exit_code = process.wait()
    
    difference = -1
    try:
        difference = int(result[1])
    except:
        print "Bad response:", result
        
    return difference


### Extract host and path, and replace denied symbols.        
def convertUriToName(uri):
    return urllib.unquote(uri).replace("http://", "")\
            .replace("https://", "")\
            .replace("/", "_")\
            .replace("\\", "_")\
            .replace(":", "_")\
            .replace(";", "_")\
            .replace("~", "_")\
            .replace("?", "_")\
            .replace("\r", "")\
            .replace("\n","")


### Get filename for snaposhot in samples dir
def getSampleFile(url, shotNumber):
    filePath = '%(path)s/assets/%(url)s_%(N)i.png' % {"path":BASE_PATH,
        "url":convertUriToName(url),
        "N":shotNumber }
    return filePath.decode(FILENAMES_ENCODING)


### Get filename for snaposhot in results dir
def getShotFile(url, shotNumber):
    filePath = '%(path)s/results/%(url)s_%(N)i.png' % {"path":BASE_PATH, 
        "url":convertUriToName(url), 
        "N":shotNumber}
    return filePath.decode(FILENAMES_ENCODING)


### Get filename for comparison file in results dir
def getResultFile(url, shotNumber):
    filePath = '%(path)s/results/cmp_%(url)s_%(N)i.jpg' % {"path":BASE_PATH, 
        "url":convertUriToName(url), 
        "N":shotNumber}
    return filePath.decode(FILENAMES_ENCODING)


### MAIN METHOD. Prepare samples
def init():
    # Connects to the current device, and stop current browser instance
    device = connectAndSetup()
    # Open list of ULS to check
    urlsFile = openUrlsList()
    # Open them one by one
    for url in urlsFile:
        openUrlOnDevice(device, url)
        
        tempResultFile = ('%(path)s/assets/cmp_temp.png'%{ "path":BASE_PATH }).decode("utf-8")
        
        shotNumber = 1
        #Loop for multiple screenshots with scroll
        while True:
            oldFile = getSampleFile(url, shotNumber-1)
            newFile = getSampleFile(url, shotNumber)
                        
            # Take a screenshot and write to a file
            device.takeSnapshot().writeToFile(newFile, 'png')
            
            # scroll for next show
            scrollBasedOnHeight(device)
            
            print "Prepared", convertUriToName(url), shotNumber
            
            #If it's not our first screen, compare with previous
            if shotNumber != 1:
                difference = compareImages(oldFile, newFile, tempResultFile)
                if difference < 100: # end of the page reached
                    try:
                        os.remove(newFile)
                    finally:
                        break
                if shotNumber == MAX_SHOTS_COUNT: # or max number of screen reached
                    break       
            
            shotNumber += 1
    return
    
### MAIN METHOD. Compare samples with current snapshots
def main():
    # Connects to the current device, and stop current browser instance
    device = connectAndSetup()
    
    # Open list of ULS to check
    urlsFile = openUrlsList()
    
    # Open them one by one
    for url in urlsFile:
        openUrlOnDevice(device, url)
        
        shotNumber = 1
        #Loop for multiple screenshots with scroll
        while True:
            #Compare with default snapshot
            sampleFile = getSampleFile(url, shotNumber)
            shotFile = getShotFile(url, shotNumber)
            resultFile = getResultFile(url, shotNumber)
                   
            # We will go through all samples for that page
            if not path.exists(sampleFile):
                break;
            
            # Take a screenshot and write to a file
            device.takeSnapshot().writeToFile(shotFile, 'png')
             
            # scroll for next show
            scrollBasedOnHeight(device)
            
            difference = compareImages(sampleFile, shotFile, resultFile)       
            print "Checked", convertUriToName(url), "diff:",difference
            
            shotNumber += 1


# Run our code
if len(sys.argv) > 1 and sys.argv[1] == "init":
    init()
else:
    main()