import Arduino
import serial
import Parameters
from Utility import *

LED_HI = ["A", "B", "C", "D"]
LED_LO = ["a", "b", "c", "d"]

LedHUB = None
simulated = False


class LedHUBConnectionError(Exception):
    def __init__(self, message):
        self.message = message


class LedHUBCommunicationError(Exception):
    def __init(self, message):
        self.message = message


def Connect():
    if simulated:
        return
    global LedHUB
    active_ports = [comport for comport in serial.tools.list_ports.comports()]
    port = None
    for device in active_ports:
        if "LAA6V4WEA" in device.hwid:
            port = device.device
    if not port:
        raise LedHUBConnectionError("Could not find an Omicron LedHUB device on a COM port")
    connection = serial.Serial(port, 500000)
    info("Connected to LedHUB on port "+port+".")
    LedHUB = connection


def Disconnect():
    if simulated:
        return
    LedHUB.close()
    info("LedHUB serial connection closed.")


def Send(chars):
    if simulated:
        return
    LedHUB.write(bytes(chars, 'utf-8'))
    info("LedHUB send: "+chars)


def Read():
    if simulated:
        return
    string = ""
    char = None
    while not char == b'\r':
        char = LedHUB.read()
        string += char.decode('utf-8')
    return string


def ReadTag(tag, timeout = 9999):
    if simulated:
        return
    ret = ""
    _timeout = 0
    while not ret.startswith(tag) and _timeout < timeout:
        ret = Read()
        _timeout += 1
    if _timeout >= timeout:
        info("LedHUB response timeout - waiting for "+tag)
        return False
    else:
        info("LedHUB response: "+ret)
        return ret


def setState(leds):
    i = 0
    for led in leds:
        if led == True:
            Arduino.Send(LED_HI[i])
        else:
            Arduino.Send(LED_LO[i])
        i+=1


def setPower(leds):
    if simulated:
        return
    Send("?SPP[4]" + str(float(leds[0])) + "\r")
    Send("?SPP[3]" + str(float(leds[1])) + "\r")
    Send("?SPP[2]" + str(float(leds[2])) + "\r")


def getPower():
    if simulated:
        return
    _id = ["1", "2", "3", "4"]
    for i in range(0, 4):
        Send("?GPP["+_id[i]+"]\r")
        ret = ReadTag("!GPP["+_id[i]+"]")
        pwr = int(float(ret[7:-1]))
        Parameters.LED_POWER_CURRENT[i] = pwr
