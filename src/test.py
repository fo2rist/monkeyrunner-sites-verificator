# -*- coding: utf-8
# Imports the monkeyrunner modules used by this program
from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice

#from os import system
from os import path
import os
import re
import shlex
from subprocess import Popen, PIPE
import sys
import urllib

### Encoding for filenames. By default utf-8
FILENAMES_ENCODING = "utf-8"

#Device screen size. Will be detected during connection
height = 0
width = 0

filepath = path.split(os.path.realpath(__file__))[0]
BASE_PATH = path.split(filepath)[0].encode(FILENAMES_ENCODING)

try:
    import config
    from junit_xmls import TestSuite, TestCase
except ImportError:
    #dirty hack that loads 3rd party modules from script's dir not from working dir, which is always changed by windows monkeyrynner
    import imp
    
    config = imp.load_source('config', BASE_PATH+'/src/config.py')
    junit_xml = imp.load_source('junit_xml', BASE_PATH+'/src/junit_xml/__init__.py')
    TestSuite = junit_xml.TestSuite
    TestCase = junit_xml.TestCase


if config.BROWSER_TO_TEST is not None :
    runComponent = config.BROWSER_TO_TEST.get("package") + '/' + config.BROWSER_TO_TEST.get("activity")
else:
    runComponent = None


### Wait for monkey device, set global device info such as screen size
### Check preconditions for test run
### @param lastChance used to retry connection once in case of fast failure
### @return:  device or None if device not connected or preconditions are not meet. 
def connectAndSetup(lastChance = False):
    #Prepare folders
    assetsFolder = path.join(BASE_PATH, "assets")
    if not path.exists(assetsFolder):
        os.makedirs(assetsFolder)
    resultsFolder = path.join(BASE_PATH, "results")
    if not path.exists(resultsFolder):
        os.makedirs(resultsFolder)
    if not path.exists(config.IM_COMPARE_PATH):
        print "ImageMagick Compare wasn't found at '%s'. Please set correct IM_COMPARE_PATH."%config.IM_COMPARE_PATH
        return None
    
    print "Waiting for device..."
    device = MonkeyRunner.waitForConnection()
    print "Device connected. "
    #Wake device and unlock the screen
    device.wake()
    if (isLocked(device)):
        print "Unlocking..."
        device.press("KEYCODE_MENU", MonkeyDevice.DOWN_AND_UP) #Android's hacky way to unlock
    #Try to get device info
    try:
        global height
        height = int(device.getProperty("display.height"))
        global width
        width = int(device.getProperty("display.width"))
    except:
        if (not lastChance):
            print "Device setup failed. Trying to reconnect."
            return connectAndSetup(True) # Give a last chance
        else:
            print "Can't get device screen size. Unable to test."
            return None
    
    #Check selected browser existence (if browser not set to default)
    if (runComponent is not None):
        packagePath = device.shell('pm path ' + config.BROWSER_TO_TEST.get("package"))
        if (not packagePath.startswith("package:")):
            print "Browser '%s' is not installed. Unable to test."%config.BROWSER_TO_TEST.get("package")
            return None;
    
    return device


### Checks if the device screen is locked.
### @return True if the device screen is locked
def isLocked(device):
    lockScreenRegexp = re.compile('mShowingLockscreen=(true|false)')
    result = lockScreenRegexp.search(device.shell('dumpsys window policy'))
    if result:
        return (result.group(1) == 'true')
    raise RuntimeError("Couldn't determine screen lock state")


### Open file with list of URLs
def openUrlsList():
    #import codecs
    #return codecs.open(BASE_PATH + "/assets/urls.txt", "r", "CP1251")
    return open(BASE_PATH + "/assets/urls.txt", 'r')


### Scroll one screen.
### @param compensation:  compensation of previously done over-scroll in pixels
def scrollOneScreen(device, compensation = 0):
    borderGap = 10
    startPoint = height - config.BUTTON_BAR_HEIGHT - borderGap
    endPoint = config.HEADER_HEIGHT + borderGap
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
    #Android
    #2.4,
    #10
    #Opera
    #0.4
    #20
    #Firefox
    #0.4
    #20
    
    #Give some time to hide scroll
    MonkeyRunner.sleep(1)


### Open url in browser and wait for load
def openUrlOnDevice(device, url):
    # Runs the component to view URL
    if (runComponent is None):
        #Launch default system browser
        device.startActivity(action="android.intent.action.VIEW", data=url)
    else:
        #Re-launch known browser by package name
        device.shell('am force-stop ' + config.BROWSER_TO_TEST.get("package"))
        MonkeyRunner.sleep(3)
        
        device.startActivity(component=runComponent, uri=url)
    
    # Wait for load
    MonkeyRunner.sleep(12)


### Compare two image via ImageMagick
### @return: difference as a number, or -1 in case of errors
def compareImages(first, second, result):
    compareStr = '%(compare)s -metric RMSE -extract %(area)s '\
                   ' "%(first)s"'\
                   ' "%(second)s"'\
                   ' "%(result)s"'%{
                                 "area": str(width)+"x"+str(height-config.HEADER_HEIGHT)+"+0+"+str(config.HEADER_HEIGHT),
                                 "compare": config.IM_COMPARE_PATH,
                                 "first": first,
                                 "second": second,
                                 "result": result }
    #system(compareStr) #Old way to run
    process = Popen(shlex.split(compareStr), stderr=PIPE)
    result = process.communicate()
    exit_code = process.wait()
    
    difference = -1
    try:
        difference = float(result[1].split(" ")[0])
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
    compareStr = '%(compare)s -metric RMSE -subimage-search -dissimilarity-threshold 0.5'\
                   ' "%(large)s"'\
                   ' "%(small)s"[%(area)s]'\
                   ' "%(result)s"'%{
                                 "area": str(width)+"x"+str(height - config.HEADER_HEIGHT - gap*2)+"+0+"+str(config.HEADER_HEIGHT + gap),
                                 "compare": config.IM_COMPARE_PATH,
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
        difference = float(diffStr.split(" ")[0])
        offset = int(offsetStr.split(",")[1])
        #Offset may be 0 se we'll just ignore it
        overscroll =  0 if (offset == 0) else offset - config.HEADER_HEIGHT - gap
    except:
        print "Bad response:", result
        
    return (difference, overscroll)

### Extract host and path, and replace denied symbols.
def convertUriToName(uri):
    return urllib.unquote(uri)\
            .replace("http://", "")\
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
    image = None
    #will try to take screen N times
    triesLeft = 3
    while triesLeft > 0:
        try:
            image = device.takeSnapshot()
            image.writeToFile(file, 'png')
            return True
        except:
            #try to reconnect
            triesLeft -= 1
            print "Unable to take snapshot, trying to reconnect. Tries left:", triesLeft
            device = MonkeyRunner.waitForConnection(4) #4 seconds

    return False


### Analyze shots comparison
### @return: whether comparison was successful
def analyzeShots(shotDifferences):
    if len(shotDifferences) == 0:
        return False

    # Check first and last
    if shotDifferences[0] > config.MAX_BOUNDARY_DELTA or shotDifferences[-1] > config.MAX_BOUNDARY_DELTA:
        return False
    # Then other
    for difference in shotDifferences[1:-1]:
        if difference > config.MAX_INTERMEDIATE_DELTA:
            return False
    return True


### MAIN METHOD. Prepare samples
def init():
    device = connectAndSetup()
    if (device is None):
        return
    
    # Open list of ULS to check
    urlsFile = openUrlsList()
    # Open them one by one
    for url in urlsFile:
    	#DEBUG
        #url = url.encode("utf-8")
        url = url.strip()
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
                
                if difference == -1: #got difference calculation error, that's ok for scrolling
                    pass
                elif difference < config.MAX_BOUNDARY_DELTA: # end of the page reached
                    try:
                        os.remove(newFile)
                    finally:
                        break
                if shotNumber == config.MAX_SHOTS_COUNT: # or max number of screen reached
                    break       
            
            # scroll for next show
            scrollOneScreen(device)
            
            shotNumber += 1
    
    urlsFile.close()
    print "Done"
    return#init
    
### MAIN METHOD. Compare samples with current snapshots
def main():
    device = connectAndSetup()
    if (device is None):
        return
    
    #Create output object
    outputTestCases = []
    
    # Open list of ULS to check
    urlsFile = openUrlsList()
    
    # Open them one by one
    for url in urlsFile:
        #DEBUG
        #url = url.encode("utf-8")
        url = url.strip()
        openUrlOnDevice(device, url)
        
        shotDifferences = [] # comparison results for every scroll
        shotNumber = 1
        #Loop for multiple screenshots with scroll
        while True:
            # Resolve names of sample file, current snapshot and comparison result file
            sampleFile = getSampleFile(url, shotNumber)
            shotFile = getShotFile(url, shotNumber)
            resultFile = getResultFile(url, shotNumber)
                   
            # Stop processing if don't have a sample
            if not path.exists(sampleFile):
                if (shotNumber == 1):
                    print "You don't have any sample for '%s'. Didn't you forget to call 'test init'?"%url
                break
            
            # Take a screenshot and write to a file
            if takeSnapshotToFile(device, shotFile):
                #Compare with default snapshot
                (difference, overscroll) = searchForIntersection(sampleFile, shotFile, resultFile)       
                shotDifferences.append(difference)
                
                print "Checked", convertUriToName(url), shotNumber, "diff:", difference, "overscroll:", overscroll
                if difference == -1: #Got an error -> stop processing
                    print "Unable to find similarity between images. WARNING"
                    #print "Unable to find similarity between images. Stop further page processing for:", url
                    #break
                
                # scroll for next show
                scrollOneScreen(device, overscroll)
                shotNumber += 1
            else: #shot was not taken
                #Set max difference as error and break loop       
                shotDifferences.append(config.MAX_INTERMEDIATE_DELTA+1)
                print "Unable to take snapshot for:", convertUriToName(url)
                break
        
        #Append page check result to output list
        testCaseInfo = TestCase(url.decode("utf-8"))
        if not analyzeShots(shotDifferences):
            testCaseInfo.add_failure_info("Failed comparison")
        outputTestCases.append(testCaseInfo)
        
    #Write result as Junit xml
    outputTestSuite = TestSuite("Screens check test suite".decode("utf-8"), outputTestCases)
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