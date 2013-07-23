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
UTF8 = "utf-8"

MAX_SHOTS_COUNT = 30
# Max delta for first and last screens
MAX_BOUNDARY_DELTA = 1500
# Max delta for screen in the middle
MAX_INTERMEDIATE_DELTA = 3000

#Change this two lines depending on platform
IS_ON_WINDOWS = False    
BASE_PATH = "/home/dmitry/workspace/TEST-monkeyrunner"
if IS_ON_WINDOWS:
    compareLocation = BASE_PATH+"/im/compare.exe" #windows
    import imp#dirty hack
    junit_xml = imp.load_source('junit_xml', BASE_PATH+'/junit_xml/__init__.py')
    TestSuite = junit_xml.TestSuite
    TestCase = junit_xml.TestCase
else:
    compareLocation = "/usr/bin/compare"         #linux
    from junit_xml import TestSuite, TestCase


#Known browsers
BROWSER_ANDROID = {"package":"com.android.browser",
                   "activity": "com.android.browser.BrowserActivity"}
BROWSER_CHROME = {"package":"com.android.chrome",
                   "activity": "com.google.android.apps.chrome.Main"}
BROWSER_FIREFOX = {"package":"org.mozilla.firefox",
                   "activity": "org.mozilla.firefox.App"}
BROWSER_OPERA = {"package":"com.opera.browser",
                   "activity": "com.opera.Opera"}


# browser component to start
browserToTest = BROWSER_ANDROID # <-CHANGE HERE TO SELECT BROWSER
                                # set None to use system default, but in that case browser won't start clean
if browserToTest is not None :
    runComponent = browserToTest.get("package") + '/' + browserToTest.get("activity")
else:
    runComponent = None
 
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
    
    return device


### Scroll one screen.
### @param compensation:  compensation of previously done over-scroll in pixels
def scrollOneScreen(device, compensation = 0):
    borderGap = 10
    startPoint = height - typicalButtonBar - borderGap
    endPoint = typicalHeader + borderGap
    if compensation > 0:
        endPoint = min(endPoint + compensation, startPoint)
    elif compensation < 0:
        #in case of under we have no more space to operate
        compensationStep = min (-compensation, borderGap)
        #so we over-scroll just a little bit
        endPoint -= compensationStep/2
        startPoint += compensationStep/2
    
    device.drag((1, startPoint),
                (1, endPoint),
                2.4,
                10)
    #Give some time to hide scroll
    MonkeyRunner.sleep(1)


### Open url in browser and wait for load
def openUrlOnDevice(device, url):
    # Runs the component to view URL
    if (runComponent is None):
        device.startActivity(action="android.intent.action.VIEW", data=url) #Old way to test deault sytem browser
    else:
        device.shell('am force-stop ' + browserToTest.get("package"))
        MonkeyRunner.sleep(3)
        device.startActivity(component=runComponent, uri=url) #Launch known browser by package name
    
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
                                 "compare": compareLocation,
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

### Compare two image via imagemagick
### Search small image in the bigger one
### @return: tuple 
###         -difference as a number, or -1 in case of errors
###         -overscroll made by second image, it's negative for underscroll
def searchForIntersection(large, small, result):
    gap = 10 # gap to crop second image from botton and top
    compareStr = '%(compare)s -metric AE -subimage-search '\
                   ' "%(large)s"'\
                   ' "%(small)s"[%(area)s] '\
                   ' "%(result)s"'%{
                                 "area": str(width)+"x"+str(height - typicalHeader - gap*2)+"+0+"+str(typicalHeader + gap),
                                 "compare": compareLocation,
                                 "large": large,
                                 "small": small,
                                 "result": result }
    #system(compareStr) #Old way to run
    process = Popen(shlex.split(compareStr), stderr=PIPE)
    result = process.communicate()
    exit_code = process.wait()
    
    difference = -1
    overscroll = 0
    try:
        (diffStr, offsetStr) = result[1].strip().split(" @ ")
        difference = int(diffStr)
        offset = int(offsetStr.split(",")[1])
        overscroll = offset - typicalHeader - gap
    except:
        print "Bad response:", result
        
    return (difference, overscroll)

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
    filePath = '%(path)s/results/cmp_%(url)s_%(N)i.gif' % {"path":BASE_PATH, 
        "url":convertUriToName(url), 
        "N":shotNumber}
    return filePath.decode(FILENAMES_ENCODING)


### Take snapshot on given device and store it to file
### @return: whether image was captured
def takeSnapshotToFile(device, file):
    image = device.takeSnapshot()
    if image is not None: 
        image.writeToFile(file, 'png')
        return True
    else:
        return False


### Analyze shots comparison
### @return: whether comparison was successful
def analyzeShots(shotDifferences):
    if len(shotDifferences) == 0:
        return False

    # Check first and last
    if shotDifferences[0] > MAX_BOUNDARY_DELTA or shotDifferences[-1] > MAX_BOUNDARY_DELTA:
        return False
    # Then other
    for difference in shotDifferences[1:-1]:
        if difference > MAX_INTERMEDIATE_DELTA:
            return False
    return True


### MAIN METHOD. Prepare samples
def init():
    # Connects to the current device, and stop current browser instance
    device = connectAndSetup()
    
    # Open list of ULS to check
    urlsFile = openUrlsList()
    # Open them one by one
    for url in urlsFile:
        openUrlOnDevice(device, url)
        
        tempResultFile = ('%(path)s/assets/cmp_temp.png'%{ "path":BASE_PATH }).decode(FILENAMES_ENCODING)
        
        shotNumber = 1
        #Loop for multiple screenshots with scroll
        while True:
            oldFile = getSampleFile(url, shotNumber-1)
            newFile = getSampleFile(url, shotNumber)
                        
            # Take a screenshot and write to a file
            if not takeSnapshotToFile(device, newFile):
                print "Unable to take snapshot for:", convertUriToName(url)
                break
            
            print "Prepared", convertUriToName(url), shotNumber
            
            #If it's not our first screen, compare with previous
            if shotNumber != 1:
                difference = compareImages(oldFile, newFile, tempResultFile)
                print "difference", difference
                if difference < MAX_BOUNDARY_DELTA: # end of the page reached
                    try:
                        os.remove(newFile)
                    finally:
                        break
                if shotNumber == MAX_SHOTS_COUNT: # or max number of screen reached
                    break       
            
            # scroll for next show
            scrollOneScreen(device)
            
            shotNumber += 1
    
    urlsFile.close()
    print "Done"
    return#init
    
### MAIN METHOD. Compare samples with current snapshots
def main():
    # Connects to the current device, and stop current browser instance
    device = connectAndSetup()
    
    #Create output object
    outputTestCases = []
    
    # Open list of ULS to check
    urlsFile = openUrlsList()
    
    # Open them one by one
    for url in urlsFile:
        openUrlOnDevice(device, url)
        
        shotDifferences = [] # comparison results for every scroll
        shotNumber = 1
        #Loop for multiple screenshots with scroll
        while True:
            #Compare with default snapshot
            sampleFile = getSampleFile(url, shotNumber)
            shotFile = getShotFile(url, shotNumber)
            resultFile = getResultFile(url, shotNumber)
                   
            # We will go through all samples for that page
            if not path.exists(sampleFile):
                break
            
            # Take a screenshot and write to a file
            if takeSnapshotToFile(device, shotFile):
                
                (difference, overscroll) = searchForIntersection(sampleFile, shotFile, resultFile)       
                shotDifferences.append(difference)
                
                print "Checked", convertUriToName(url), shotNumber, "diff:", difference, "overscroll:", overscroll
                if difference == -1: #Got an error -> stop processing 
                    print "Unable to find similarity between images. Stop further page processing for:", url
                    break
                
                # scroll for next show
                scrollOneScreen(device, overscroll)
                shotNumber += 1
            else: #shot was not taken
                #Set max difference as error and break loop       
                shotDifferences.append(MAX_INTERMEDIATE_DELTA+1)
                print "Unable to take snapshot for:", convertUriToName(url)
                break
        
        #Append page check result to output list
        testCaseInfo = TestCase(url.decode(UTF8))
        if not analyzeShots(shotDifferences):
            testCaseInfo.add_failure_info("Failed comparison")
        outputTestCases.append(testCaseInfo)
        
    #Write result as Junit xml
    outputTestSuite = TestSuite("Screens check test suite".decode(UTF8), outputTestCases)
    junitFile = open(BASE_PATH+"/results/output.xml", 'w')
    TestSuite.to_file(junitFile, [outputTestSuite], prettyprint=False)
    
    junitFile.close()
    urlsFile.close()
    print "Done"
    return#main

# Run our code
if len(sys.argv) > 1 and sys.argv[1] == "init":
    init()
else:
    main()