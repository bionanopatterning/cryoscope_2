import Arduino
import time
import pco
from Utility import *
pcoEdge = None
firstImage = False
import Parameters as prm

def Connect():
    global pcoEdge, pcoSDK
    try:
        print("Busy connecting to pco camera ...")
        pcoEdge = pco.Camera(debuglevel = 'verbose', timestamp='on')
        pcoEdge.configuration = {'trigger': 'external exposure control'}
        print(pcoEdge.configuration)
        print("Connected to pco camera.")
        time.sleep(2)
        pcoEdge.sdk.set_hwio_signal(index=3,  # HWIO Signal number
                                enabled='on',  # 'on' / 'off'
                                signal_type='TTL',
                                polarity='high level',  # 'high level' / 'low level'
                                filter_type='off',
                                selected=0,  # signal for this signal line
                                parameter=[2, 0, 0, 0])  # Extended Signal Timing (GLOBAL)
        debug("hwio signal set")
        pcoEdge.sdk.arm_camera()
        debug("camera armed")
        startRecording()
        debug("recording started")
        setFanSpeed(speed=prm.fanspeed)
        debug("fanspeed set")
        return True
    except Exception as e:
        print("EXCEPTION IN PCOCAMERA CONNECT:\n"+str(e))
        raise e

def Disconnect():
    try:
        Stop()
        pcoEdge.close()
        print("Disconnected pco camera.")
    except Exception:
        return False

def getTemperature():
    if pcoEdge:
        temperatures = pcoEdge.sdk.get_temperature()
        return (temperatures['sensor temperature'], temperatures['camera temperature'], temperatures['power temperature'])
    else:
        return (-1, -1, -1)

def getFanSpeed():
    if pcoEdge:
        fanParams = pcoEdge.sdk.get_fan_control_parameters()
        return fanParams['value']
    else:
        return -1

def setFanSpeed(speed = None):
    if pcoEdge:
        if speed:
            pcoEdge.sdk.set_fan_control_parameters(mode = 'user', value = int(speed))
            debug(f"Set fan mode to 'user', speed {speed}")
        else:
            pcoEdge.sdk.set_fan_control_parameters(mode = 'auto', value = 80)
            debug("Reset pcoCamera fanmode auto, speed 80 (default)")

def setROI(left, right, top, bottom):
    if pcoEdge:
        pcoEdge.configuration = {'roi': (left, right, top, bottom)}

def setBinning(binning):
    if pcoEdge:
        pcoEdge.configuration = {'binning': (binning, binning)}


def startRecording():
    if pcoEdge:
        print(pcoEdge)
        debug("trying to start pco edge recording")
        pcoEdge.record(number_of_images= 20, mode = 'ring buffer')
        debug("pco edge started recording")

def waitForFirstImage():
    global firstImage
    if pcoEdge:
        pcoEdge.wait_for_first_image()
        firstImage = True


def Stop():
    if pcoEdge:
        pcoEdge.stop()


def setExposure(ms):
    Arduino.Send("Z" + str(ms) + "z")


def setRepeats(n):
    Arduino.Send("W" + str(n) + "w")


def snap():
    Arduino.Send("Y")

def acquire():
    Arduino.Send("V")
    while not (Arduino.Read() == bytes('v', 'utf-8')):
        time.sleep(0.001)

def getLastImage(roi = [1, 1, 2048, 2048]):
    if pcoEdge:
        if not firstImage:
            waitForFirstImage()
        return pcoEdge.image(image_number = 4294967295, roi = (roi[0], roi[1], roi[2], roi[3]))