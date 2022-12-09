import serial
import serial.tools.list_ports
import time
import Parameters as prm
ASIStage = None
ASIStageON = False
ASI_SN = "CEAE41C539CDEB118C411EF6E83FD3F1"
from Utility import *

simulated = False
### ERROR CODES ###
# :N-1	Unknown Command (Not Issued in TG-1000)
# :N-2	Unrecognized Axis Parameter (valid axes are dependent on the controller)
# :N-3	Missing parameters (command received requires an axis parameter such as x=1234)
# :N-4	Parameter Out of Range
# :N-5	Operation failed
# :N-6	Undefined Error (command is incorrect, but for none of the above reasons)
# :N-7	Invalid card address
# :N-8..:N-10	Reserved
# :N-11..:N-20	Reserved for filterwheel
# :N-21	Serial Command halted by the HALT command

def Connect():
    global ASIStage, ASIStageON
    if simulated:
        return False
    try:
        active_ports = [comport for comport in serial.tools.list_ports.comports()]
        port = None
        for device in active_ports:
            if ASI_SN == device.serial_number:
                port = device.device
                info("ASI Port: "+str(port))
        if not port:
            error("Could not connect to ASIStage - no comport for a device with serial nr. "+ASI_SN+" found.")
        connection = serial.Serial(port, 115200, timeout = 1)
        info("ASI stage serial connection opened on port " + port + ".")
        ASIStage = connection
        info("Checking whether ASI controller is actually on.")
        ASIStage.reset_input_buffer()
        ASIStage.write(bytes("/\r", "ascii"))
        response = ASIStage.readline()
        ASIStageON = not (response == b'')
        ASIStage.reset_input_buffer()
        ASIStage.close()
        if ASIStageON:
            connection = serial.Serial(port, 115200)
            ASIStage = connection
            prm.currentFocusPosition = getPosition()
            # Set movement speed
            Send(f"SPEED f={prm.filterStageSpeed}\r")
            Send(f"ACCEL f={prm.filterStageAcceleration}\r")
            info("Connection to ASI stage established & controller powered")
            return True
        else:
            error("ASI Stage not connected - presumably the controller is off!")
    except Exception as e:
        return False

def Disconnect():
    global ASIStage
    ASIStage.close()
    info("Disconnected from ASI stage.")

def Send(chars):
    if not simulated:
        if ASIStageON:
            ASIStage.write(bytes(chars, "ascii"))
            trace("ASIStage.Send(): "+chars)

def Read():
    if not simulated:
        response = None
        if ASIStageON:
            response = ASIStage.readline()
            response = response.decode(encoding="ascii")
            trace("ASIStage.Read(): " + response)
        return response

def getPosition():
    if checkAvailable():
        Send(f"WHERE z\r")
        response = Read()
        prm.currentFocusPosition = int(response.split(" ")[1]) / 10.0
        return prm.currentFocusPosition
    else:
        return -1.0

def getFilter():
    if checkAvailable():
        Send(f"WHERE F\r")
        response = Read()
        prm.currentFilter = int(''.join(filter(str.isdigit, response))) - 1
        return prm.currentFilter
    else:
        return None

def setFilter(filterpos):
    if checkAvailable():
        prm.currentFilter = filterpos
        Send(f"MOVE F={filterpos+1}\r")


def setPosition(pos):
    # TODO make stage go a little bit slower
    """pos is an int for the absolute z position, in units microns from current origin."""
    if checkAvailable():
        zpos = int(pos * 10)
        Send(f"MOVE z={zpos}\r")

def Move(step):
    """
    :param step: distance to move in units of microns.
    :return:
    """
    if checkAvailable():
        zstep = int(step * 10)
        print(zstep)
        Send(f"MOVREL z={zstep}\r")
        Read()

def checkAvailable():
    if not simulated:
        if not ASIStageON:
            return False
        ASIStage.reset_input_buffer()
        Send("/\r")
        response = Read()
        ASIStage.reset_input_buffer()
        if "N" in response:
            return True
        else:
            return False

def waitFor():
    if not simulated:
        status = " "
        while not "N" in status:
            Send(f"/\r")
            status = Read()
            print(status)
        ASIStage.reset_input_buffer()
        return True

def Safe():
    Send("! z\r")
    Read()

