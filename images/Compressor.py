#!/usr/bin/env python3

import os
import sys
from subprocess import Popen, PIPE
from multiprocessing import Pool

def execute(command):
    print("execute: " + command)
    process = Popen(command, shell=True)
    exitCode = process.wait()
    exit()

class Compressor:
    def __init__(self, dirName):
        self.fileSuffix = ".png"
        self.compressCommand = "pngout \"{}\""
        self.dirName = dirName
        fileList = os.listdir(dirName)
        self.fileList = []
        for file in fileList:
            if file.endswith(self.fileSuffix):
                self.fileList.append(file)
        self.fileList.sort()
        self.compressProcessesMax = 7

    def run(self):
        with Pool(processes=self.compressProcessesMax) as thePool:
            for file in self.fileList:
                cmd = self.compressCommand.format(os.path.join(self.dirName, file))
                thePool.apply_async(execute, (cmd,))
            thePool.close()
            thePool.join()

if __name__ == "__main__":
    compressyThing = Compressor(sys.argv[1])
    compressyThing.run()
