import time
from datetime import datetime
import GUI_Config as cfg

tictocTime = 0.0

def tic():
    global tictocTime
    tictocTime = time.time()

def toc():
    global tictocTime
    timeElapsed = (time.time() - tictocTime) * 1000.0
    return timeElapsed

def timestamp():
    now = datetime.now()
    timestamp = now.strftime("%H%M%S")
    return timestamp

def timestampms():
    now = datetime.now()
    timestampms = now.strftime("%H%M%S.%f")[:-3]
    return timestampms

def datestamp():
    now = datetime.now()
    datestamp = now.strftime("%Y%m%d")
    return datestamp

def datestr():
    now = datetime.now()
    datestr = now.strftime("%d-%m-%Y")
    return datestr

def intTo4DigitString(num):
    if num > 999:
        return "0"+str(num)
    elif num > 99:
        return "00"+str(num)
    elif num > 9:
        return "000"+str(num)
    else:
        return "0000"+str(num)


def positionsEqual(posA, posB, maxumerror):
    if (posA[0]-posB[0])**2+(posA[1]-posB[1])**2 < maxumerror**2:
        return True
    else:
        return False


def startlog():
    if cfg.write_log_file:
        cfg.log_file = open(cfg.log_path+datestamp()+timestamp()+".txt","a+")


def logprint(message, level = 2):
    if level <= cfg.log_level:
        if cfg.write_log_file:
            cfg.log_file.write(message + "\n")
        cfg.log_lines.append(message)
        print(message)


def error(message):
    logprint(timestampms() + ": " + message, level = 0)

def debug(message):
    logprint(timestampms() + ": " + message, level = 1)

def info(message):
    logprint(timestampms() + ": " + message, level = 2)

def trace(message):
    logprint(timestampms() + ": " + message, level = 3)