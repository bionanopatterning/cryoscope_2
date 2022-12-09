import serial
import serial.tools.list_ports
import time
import Parameters as prm
from Utility import *

class ArduinoConnectionError(Exception):
    def __init__(self, message):
        self.message = message

Arduino = None

def Connect():
    try:
        global Arduino
        active_ports = [comport for comport in serial.tools.list_ports.comports()]
        port = None
        for device in active_ports:
            if "Arduino Leonardo" in device.description:
                port = device.device
        if not port:
            error("Could not find an Arduino Leonardo device on a COM port")
        connection = serial.Serial(port, 9600, timeout = prm.arduinoTimeout)
        info("Connected to Arduino on port "+port+".")
        Arduino = connection
        Send("U")
        return True
    except Exception:
        return False

def Send(chars):
    info("Arduino send: " + chars)
    Arduino.write(bytes(chars, 'utf-8'))


def Read():
    _char = Arduino.read().decode('utf-8')
    if _char:
        trace("Arduino read: " + _char)
    return _char

def Disconnect():
    Send("Uabcd")
    time.sleep(1)
    Arduino.close()
    info("Arduino serial connection closed.")

def toggleTestLed():
    Send("G")



