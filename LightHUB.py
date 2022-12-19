import Arduino
import serial
import Parameters as prm
from Utility import *

LED_HI = ["A", "B", "C", "D"]
LED_LO = ["a", "b", "c", "d"]

# LightHUB has four channels: 405, 470, 532, 561.
# uses three com ports. Serials are: LAH7ZC3TA, LAHEHVQKA, LAHI8YC9A,  LOCATION=1-11.4:x.0
USB_SERIALS = ["LAHEHVQKA", "LAHI8YC9A", "LAH7ZC3TA", " LOCATION=1-11.4:x.0"]
Ports = [None, None, None, None]
Serial = [None, None, None, None]

class LightHUBConnectionError(Exception):
    def __init__(self, message):
        self.message = message


class LightHUBCommunicationError(Exception):
    def __init(self, message):
        self.message = message


def Connect():
    try:
        active_ports = [comport for comport in serial.tools.list_ports.comports()]
        PortSerialDict = dict()
        for device in active_ports:
            print(device.hwid)
            for id in USB_SERIALS:
                if id in device.hwid:
                    PortSerialDict[id] = device.device
        info("LightHUB ports and serial nrs:")
        info(str(PortSerialDict))
        Serial[0] = serial.Serial(PortSerialDict["LAHEHVQKA"], 500000)
        Serial[1] = serial.Serial(PortSerialDict["LAHI8YC9A"], 500000)
        Serial[2] = serial.Serial(PortSerialDict["LAH7ZC3TA"], 115200)
        Serial[3] = serial.Serial(PortSerialDict[" LOCATION=1-11.4:x.0"], 115200)
        info("serial connections:")
        for con in Serial:
            info(str(con))
        #AutoStart()
        return True
    except Exception as e:
        return False

def Disconnect():
    for connection in Serial:
        try:
            connection.close()
        except:
            pass
    info("LightHUB serial connections closed.")

def Send(serialConnection, chars):
    serialConnection.write(bytes(chars, 'utf-8'))

def Read(serialConnection):
    string = ""
    char = None
    while not char == b'\r':
        char = serialConnection.read()
        string += char.decode('utf-8')
    return string

def ReadTag(serialConnection, tag, timeout=9999):
    ret = ""
    _timeout = 0
    while not ret.startswith(tag) and _timeout < timeout:
        ret = Read(serialConnection)
        _timeout += 1
    if _timeout >= timeout:
        info("LightHUB response timeout - waiting for " + tag)
        return False
    else:
        return ret

def setState(leds):
    i = 0
    for led in leds:
        if led == True:
            Arduino.Send(LED_HI[i])
        else:
            Arduino.Send(LED_LO[i])
        i += 1

def setPower(leds):
    # TO DO: check actual power after changing it?
    # Channel 0
    # LightHUB does not have a channel 0 (365 nm in LedHUB)

    # Channel 1
    Send(Serial[0], "?SPP"+(str(float(leds[0])))+"\r")

    # Channel 2
    Send(Serial[1], "?SPP" + (str(float(leds[1]))) + "\r")

    # Channel 3
    Send(Serial[2], f"p {float(leds[2]) / 100.0 * prm.lightSourcesNominalPower[2] / 1000.0}\r")
    Read(Serial[2])

    # Channel 4 TODO
    Send(Serial[3], f"SOURce:POWer:LEVel:IMMediate:AMPLitude {float(leds[3]) / 100.0 * prm.lightSourcesNominalPower[3] / 1000.0}\r")
    Read(Serial[3])

def getPower():
    """getPower function is deprecated - remains here for debugging purposes"""
    # Channel 1 - 405 nm
    Send(Serial[0], "?GPP\r")
    ret = ReadTag(Serial[0], "!GPP", timeout = 5)
    pwr = int(float(ret[4:-1]))
    print(f"405 nm channel - power {pwr / 100.0 * prm.lightSourcesNominalPower[0]} mW")

    # Channel 2 - 470 nm
    Send(Serial[1], "?GPP\r")
    ret = ReadTag(Serial[1], "!GPP", timeout=5)
    pwr = int(float(ret[4:-1]))
    print(f"470 nm channel - power {pwr / 100.0 * prm.lightSourcesNominalPower[1]} mW")

    # Channel 3 - 532 nm
    Send(Serial[2], "p?\r")
    ret = Read(Serial[2])
    pwr = float(ret)*1000.0
    print(f"532 nm channel - power {pwr} mW")

    # Channel 4 - 561 nm
    Send(Serial[3], "SOURce:POWer:LEVel:IMMediate:AMPLitude?\r")
    ret = Read(Serial[3])
    pwr = float(ret) * 1000.0
    print(f"561 nm channel - power {pwr} mW")



def AutoStart():
    info("Enabling 'AutoStart' on LightHUB")
    Send(Serial[0], "?SAS1\r")
    ret = ReadTag(Serial[0], "!SAS", timeout = 10)
    info("Laser 405: auto start " + ret)
    Send(Serial[1], "?SAS1\r")
    ret = ReadTag(Serial[1], "!SAS", timeout = 10)
    info("Laser 470: auto start " + ret)

if __name__ == "__main__":
    Connect()
    setPower([30.0, 30.0, 30.0, 30.0])
    getPower()
