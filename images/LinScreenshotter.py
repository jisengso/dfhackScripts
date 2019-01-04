#!/usr/bin/env python3

import os
import sys
import shlex
import time
import signal
from subprocess import Popen, PIPE
from multiprocessing import Pool

def execute(command):
    print("execute: " + command)
    process = Popen(command, shell=True)
    exitCode = process.wait()
    exit()

class LinScreenshotter:
    def __init__(self, windowName):
        self.printDebug = True
        self.windowName = windowName
        self.imageCount = 0
        self.digits = 10
        self.prefix = windowName
        self.fileSuffix = ".png"
        curDate = time.localtime()
        self.dateStr = f"{curDate.tm_year:04}{curDate.tm_mon:02}{curDate.tm_mday:02}-{curDate.tm_hour:02}{curDate.tm_min:02}{curDate.tm_sec:02}"
        self.dirName = f"{self.prefix}-{self.dateStr}"
        self.windowIDCommand = f"xwininfo -root -tree | grep {windowName}"
        self.windowID = ""
        self.screenshotCommand = "import -window {} {}"
        self.interval = 1
        self.exitNext = False
        self.shouldCompressMore = False
        self.shouldCompressNext = False
        self.compressProcessesMax = 6
        self.compressPool = Pool(processes=self.compressProcessesMax)
        self.compressCommand = "pngout {}"
        self.shouldDeduplicate = True
        self.hashCommand = "shasum {}"
        self.hashes = set()
        self.exitPressed = 0

    def initDir(self):
        self.debug("initDir")
        cmd = "mkdir {}".format(self.dirName)
        process = Popen(cmd, shell=True)
        exitCode = process.wait()

    def setExit(self, bleh, blah):
        self.debug("setExit")
        self.exitNext = True
        self.exitPressed += 1
        signal.signal(signal.SIGINT, self.setExit) # In case CTRL-C is pressed again.
        if (self.exitPressed > 5):
            exit()
        self.compressPool.close()
        self.compressPool.join()


    def getID(self):
        self.debug("getID")
        cmd = self.windowIDCommand
        while True:
            process = Popen(cmd, stdout=PIPE, shell=True, stdin=None, stderr=None)
            theOutput = process.communicate()[0]
            exitCode = process.wait()
            if theOutput:
                self.windowID = str(theOutput.split()[0])[1:]
                self.debug(self.windowID)
            else:
                self.debug("Could not get windowID.")
                time.sleep(self.interval)
            if exitCode != 0:
                self.debug("Error: " + str(exitCode))
                time.sleep(self.interval)
            elif exitCode == 0 and theOutput:
                break

    def getScreenshot(self):
        self.debug("getScreenshot")
        shotFilename = os.path.join(self.dirName, "".join([self.prefix, str(self.imageCount).zfill(self.digits), self.fileSuffix]))
        cmd = self.screenshotCommand.format(self.windowID, shotFilename)
        self.debug(cmd)
        process = Popen(cmd, shell=True)
        exitCode = process.wait()
        if not exitCode:
            if self.shouldDeduplicate:
                self.deduplicate(shotFilename)
            else:
                self.imageCount += 1
            if self.shouldCompressMore and self.shouldCompressNext:
                self.compressMore(shotFilename)
        if self.exitNext:
            exit()
        else:
            time.sleep(self.interval)

    def compressMore(self, shotFilename):
        self.debug("compressMore")
        compressCmd = self.compressCommand.format(shotFilename)
        result = self.compressPool.apply_async(execute, (compressCmd,))

    def deduplicate(self, shotFilename):
        self.debug("deduplicate")
        hashCmd = self.hashCommand.format(shotFilename)
        process = Popen(hashCmd, stdout=PIPE, shell=True)
        newHash = process.communicate()[0].split()[0]
        exitCode = process.wait()
        print(newHash)
        if not exitCode and newHash not in self.hashes:
            self.imageCount += 1
            self.hashes.add(newHash)
            self.shouldCompressNext = True
        else:
            self.shouldCompressNext = False

    def debug(self, message):
        if self.printDebug:
            print(message)

    def run(self):
        self.initDir()
        while True:
            try:
                self.getID()
                self.getScreenshot()
            except:
                self.debug("Error occurred.")
                time.sleep(self.interval)
            if self.exitNext:
                exit()

if __name__ == "__main__":
    capturer = LinScreenshotter(sys.argv[1])
    signal.signal(signal.SIGINT, capturer.setExit)
    capturer.run()
