from ctypes import *
import Parameters as prm
lsdk = None
stageHandle = c_int(0)
linkamProcessMessageCommon = None
stageLims = [(100.0, 10000.0), (100.0, 2600.0)]
connection = False
simulated = False
simulatedPosition = [0.0, 0.0]
from Utility import *
from os import system

class CommsInfo(Structure):
    _fields_ = [
        ('info', c_char*124),
    ]

class USBCommsInfo(Structure):
    _fields_ = [
        ('vendorID', c_uint16),
        ('productID', c_uint16),
        ('serialNumber', c_char*17),
        ('padding', c_uint8*3),
        ('timeout', c_uint32),
        ('padding2', c_uint8*96)
    ]

    def __str__(self):
        return "USBCommsInfo object:\nvendorID = {}\nproductID = {}\nserialNumber = {}\npadding = {}\ntimeout = {}\npadding2 = {}\n".format(self.vendorID, self.productID, self.serialNumber, self.padding, self.timeout, self.padding2)

class ConnectionStatus(Structure):
    _fields_ = [("flags", c_bool*32), ("value", c_uint32)]

class CMSStatus(Structure):
    _fields_ = [("flags", c_bool*32), ("value", c_uint32)]

    def __str__(self):
        bitMeaning = ["on", "on but needs lN2", "entered first filling cycle", "autoTopUp", "warmingUp", "warmingUpFromCupboard", "unused", "unused", "chamber LED on", "sample dewar filling", "main dewar refilling"]
        retstr = "CMS Status:\n"
        for i in range(11):
            retstr += bitMeaning[i] + ": \t" + str(self.flags[i]) + "\n"
        return retstr

class CMSError(Structure):
    _fields_ = [("flags", c_bool*32),("value", c_uint32)]

    def __str__(self):
        bitMeaning = ["Main sensor at 0C", "Main sensor reads over temperature (?)", "lN2 switch sensor at 0C", "lN2 switch sensor reads over temperature (?)", "dewar sensor at 0C", "dewar sensor reads over temperature (?)", "base sensor at 0C", "base sensor reads over temperature (?)", "dewar empty", "motor position is in error"]
        retstr = "CMS Status:\n"
        for i in range(10):
            retstr += bitMeaning[i] + ": \t" + str(self.flags[i]) + "\n"
        return retstr

class MDSStatus(Structure):
    _fields_ = [("flags", c_bool*32), ("value", c_uint32)]

    def __str__(self):
        retstr = "uint32 repr: {}".format(self.value) + "\n"
        for i in range(32):
            retstr += str(self.flags[i]) + "\n"

        return retstr

class LSDKError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

def Connect():
    global lsdk, stageHandle, linkamProcessMessageCommon, connection
    if simulated:
        info("Linkam Cryostage is in simulated mode")
        return None
    # _date = datestr()
    # system("date 01-12-2021") # set date to 1 dec 2021, which was when the linkam 30 day trial started.
    lsdk = CDLL("sdk/bin/Release/x64/LinkamSDK.dll", winmode = 0)
    linkamProcessMessageCommon = getattr(lsdk, "linkamProcessMessageCommon")
    # Initialise SDK
    linkamInitialiseSDK = getattr(lsdk, "linkamInitialiseSDK")
    linkamInitialiseSDK.restype = c_bool
    linkamInitialiseSDK.argtype = [c_char_p, c_char_p, c_bool]
    status = linkamInitialiseSDK(None, None, False)
    if not status:
        error("Linkam SDK could not initialize.")
        return False

    # Set logging level
    linkamProcessMessageCommon.argtype = [c_int, c_uint64, c_bool, c_uint32, None, None]
    linkamProcessMessageCommon.restype = c_bool
    logLevel = c_uint32(1) # LOGGING_LEVEL_MINIMAL, LOGGING_LEVEL_INFORMATIVE, LOGGING_LEVEL_VERBOSE, or LOGGING_LEVEL_INVESTIGATION.
    result = c_bool()
    linkamProcessMessageCommon(c_int(119), c_uint64(0), byref(result), logLevel, None, None)

    # Initialise USBCommsInfo
    linkamInitialiseUSBCommsInfo = getattr(lsdk, "linkamInitialiseUSBCommsInfo")
    linkamInitialiseUSBCommsInfo.argtype = (POINTER(CommsInfo), c_char_p)
    linkamInitialiseUSBCommsInfo.restype = None
    m_CommsInfo = CommsInfo()
    linkamInitialiseUSBCommsInfo(POINTER(CommsInfo)(m_CommsInfo), None)

    # Turn m_CommsInfo into a USBCommsInfo object
    linkamGetUSBCommsInfo = getattr(lsdk, "linkamGetUSBCommsInfo")
    linkamGetUSBCommsInfo.argtype = (POINTER(CommsInfo))
    linkamGetUSBCommsInfo.restype = USBCommsInfo
    m_USBCommsInfo = linkamGetUSBCommsInfo(POINTER(CommsInfo)(m_CommsInfo))

    linkamProcessMessageCommon.argtype = [c_int, c_uint64, POINTER(ConnectionStatus), POINTER(CommsInfo), POINTER(c_uint32), None]
    linkamProcessMessageCommon.restype = c_bool
    m_ConnectionStatus = ConnectionStatus()
    infoptr = POINTER(CommsInfo)(m_CommsInfo)
    commsHandle = c_uint64()
    val = linkamProcessMessageCommon(c_int(1), c_uint64(0), byref(m_ConnectionStatus), infoptr, byref(commsHandle), None)
    stageHandle = commsHandle.value
    startMotor(0)
    startMotor(1)
    connection = True
    # system("date " + _date)
    return True

def Disconnect():
    info("Fake exit linkam sdk")
    return True

def getTemperature():
    trace(f"Cryostage.getTemperature()")
    if not connection:
        return [0.0, 0.0, 0.0]
    global linkamProcessMessageCommon
    # Relevant stage value codes: eStageValueTypeHeater1Temp(0) is bridge temperature, Heater2Temp(5) is chamber temperature, Heater3Temp(44) is bottom dewar temperature.
    linkamProcessMessageCommon.argtype = [c_uint32, c_uint64, c_float, c_uint32, c_uint32, c_uint32]
    linkamProcessMessageCommon.restype = c_bool

    t_dewar = c_float(0)
    t_chamber = c_float(0)
    t_bridge = c_float(0)
    _sa = linkamProcessMessageCommon(c_int(21), c_uint64(stageHandle), byref(t_dewar), c_uint32(44), c_uint32(0), c_uint32(0))
    _sb = linkamProcessMessageCommon(c_int(21), c_uint64(stageHandle), byref(t_chamber), c_uint32(5), c_uint32(0), c_uint32(0))
    _sc = linkamProcessMessageCommon(c_int(21), c_uint64(stageHandle), byref(t_bridge), c_uint32(0), c_uint32(0), c_uint32(0))
    if not _sa or not _sb or not _sc:
        error("Error in getTemperature() using linkamProcessMessageCommon(...)")
    return [t_dewar.value, t_chamber.value, t_bridge.value]

def getCondenser():
    info(f"Cryostage.getCondenser()")
    if not connection:
        return None
    global linkamProcessMessageCommon
    linkamProcessMessageCommon.argtype = [c_uint32, c_uint64, c_uint16, c_uint, c_uint16, c_uint16]
    linkamProcessMessageCommon.restype = c_bool

    condenser_intensity = c_uint16(0)
    _sa = linkamProcessMessageCommon(c_int(21), c_uint64(stageHandle), byref(condenser_intensity), c_uint(61), c_uint16(0), c_uint16(0))
    if not _sa:
        error("Error getting condenser intensity")
    return condenser_intensity.value

def setCondenser(condenserIntensityPctInt):
    info(f"CryoStage.setCondenser({condenserIntensityPctInt})")
    if not connection:
        return None
    global linkamProcessMessageCommon
    linkamProcessMessageCommon.argtype = [c_uint32, c_uint64, c_uint16, c_uint, c_uint16, c_uint16]
    linkamProcessMessageCommon.restype = c_bool

    condenser_intensity = c_uint16(0)
    _sa = linkamProcessMessageCommon(c_int(22), c_uint64(stageHandle), byref(condenser_intensity), c_uint(61),
                                     c_uint16(condenserIntensityPctInt), c_uint16(0))
    if not _sa:
        error("Error setting condenser intensity")
    return True

def getPosition():
    info(f"CryoStage.getPosition()")
    if not connection or simulated:
        return simulatedPosition
    global linkamProcessMessageCommon
    # Relevant valueTypes: eStageValueTypeMotorPosX (16) X position, eStageValueTypeMotorPosY (19) Y position.
    linkamProcessMessageCommon.argtype = [c_uint32, c_uint64, c_float, c_uint32, c_uint32, c_uint32]
    linkamProcessMessageCommon.restype = c_bool

    pos_x = c_float(0)
    pos_y = c_float(0)
    _sa = linkamProcessMessageCommon(c_int(21), c_uint64(stageHandle), byref(pos_x), c_uint32(16), c_uint32(0), c_uint32(0))
    _sb = linkamProcessMessageCommon(c_int(21), c_uint64(stageHandle), byref(pos_y), c_uint32(19), c_uint32(0), c_uint32(0))
    if not _sa or not _sb:
        error("Error in getPosition() using linkamProcessMessageCommon(...)")
    return [pos_x.value, pos_y.value]

def startMotor(axis):
    info(f"CryoStage.startMotor({axis})")
    global linkamProcessMessageCommon
    linkamProcessMessageCommon.argtype = [c_int, c_uint64, c_bool, c_bool, c_int, None]
    linkamProcessMessageCommon.restype = c_bool

    motor = c_int(axis)
    result = c_bool()
    _sa = linkamProcessMessageCommon(c_int(20), c_uint64(stageHandle), byref(result), c_bool(True), motor, None)
    if not _sa:
        raise LSDKError("Couldn't start motor {}".format(axis))

def stopMotor(axis):
    info(f"CryoStage.stopMotor({axis})")
    global linkamProcessMessageCommon
    linkamProcessMessageCommon.argtype = [c_int, c_uint64, c_bool, c_bool, c_int, None]
    linkamProcessMessageCommon.restype = c_bool

    motor = c_int(axis)
    result = c_bool()
    _sa = linkamProcessMessageCommon(c_int(20), c_uint64(stageHandle), byref(result), c_bool(False), motor, None)

    if not _sa:
        error("Couldn't stop motor {}".format(axis))

def setPosition(xyPos):
    info(f"CryoStage.setPosition({xyPos})")
    global linkamProcessMessageCommon, simulatedPosition
    simulatedPosition = xyPos
    if simulated:
        return None
    stopMotor(0)
    stopMotor(1)
    linkamProcessMessageCommon.argtype = [c_uint32, c_uint64, c_bool, c_float, c_uint32, c_uint32]
    linkamProcessMessageCommon.restype = c_bool
    if (xyPos[0] < stageLims[0][0]):
        xyPos[0] = stageLims[0][0]
        info("Requested X pos too low")
    elif (xyPos[0] > stageLims[0][1]):
        xyPos[0] = stageLims[0][1]
        info("Requested X pos too high")
    if (xyPos[1] < stageLims[1][0]):
        xyPos[1] = stageLims[1][0]
        info("Requested Y pos too low")
    elif (xyPos[1] > stageLims[1][1]):
        xyPos[1] = stageLims[1][1]
        info("Requested Y pos too high")
    pos_x = c_float(float(xyPos[0]))
    pos_y = c_float(float(xyPos[1]))
    garbage = c_bool(1)
    _sa = linkamProcessMessageCommon(c_int(22), c_uint64(stageHandle), byref(garbage), c_uint32(18), pos_x, None)  # Motor X setpoint
    _sc = linkamProcessMessageCommon(c_int(22), c_uint64(stageHandle), byref(garbage), c_uint32(21), pos_y, None)  # Motor Y setpoint
    linkamProcessMessageCommon.argtype = [c_uint32, c_uint64, c_bool, c_uint32, c_uint32, c_uint32]
    vel_x = c_float(float(prm.stageMovementSpeed))
    vel_y = c_float(float(prm.stageMovementSpeed))
    _sb = linkamProcessMessageCommon(c_int(22), c_uint64(stageHandle), byref(garbage), c_uint32(17), vel_x, None)  # Motor X velocity
    _sd = linkamProcessMessageCommon(c_int(22), c_uint64(stageHandle), byref(garbage), c_uint32(20), vel_y, None)  # Motor Y velocity
    startMotor(0)
    startMotor(1)
    if not _sa or not _sb or not _sc or not _sd:
        raise LSDKError("Error in setPosition() using linkamProcessMessageCommon(...)")
    return True

def getMotorParams():
    info(f"CryoStage.getMotorParams()")
    global linkamProcessMessageCommon
    linkamProcessMessageCommon.argtype = [c_uint32, c_uint64, c_float, c_uint32, None, None] # messageType, deviceHandle, ptr_to_result_holder, valueType, param2, param2.
    linkamProcessMessageCommon.restype = c_bool

    prm_pos_x = c_float(0)
    prm_vel_x = c_float(0)
    prm_spt_x = c_float(0)
    _sa = linkamProcessMessageCommon(c_int(21), c_uint64(stageHandle), byref(prm_pos_x), c_uint32(16), None, None)
    _sb = linkamProcessMessageCommon(c_int(21), c_uint64(stageHandle), byref(prm_vel_x), c_uint32(17), None, None)
    _sc = linkamProcessMessageCommon(c_int(21), c_uint64(stageHandle), byref(prm_spt_x), c_uint32(18), None, None)
    if not _sa or not _sb or not _sc:
        raise LSDKError("Error reading motor parameters.")
    return [prm_pos_x, prm_vel_x, prm_spt_x]

def getStatusFlags():
    info(f"CryoStage.getStatusFlags()")
    global linkamProcessMessageCommon
    linkamProcessMessageCommon.argtyp = [c_uint32, c_uint64, POINTER(CMSStatus), c_uint32, None, None]
    flags = CMSStatus()
    _sa = linkamProcessMessageCommon(c_int(21), c_uint64(stageHandle), byref(flags), c_uint32(56), None, None)
    if not _sa:
        raise LSDKError("Error getting CMS Status flags")
    return flags

def getErrorFlags():
    info(f"CryoStage.getErrorFlags()")
    global linkamProcessMessageCommon
    linkamProcessMessageCommon.argtyp = [c_uint32, c_uint64, POINTER(CMSError), c_uint32, None, None]
    flags = CMSError()
    _sa = linkamProcessMessageCommon(c_int(21), c_uint64(stageHandle), byref(flags), c_uint32(57), None, None)
    if not _sa:
        raise LSDKError("Error getting CMS Error flags")
    return flags

def getMotorDriverFlags():
    info(f"CryoStage.getMotorDriverFlags()")
    global linkam
    linkamProcessMessageCommon.argtyp = [c_int, c_uint64, POINTER(MDSStatus), c_uint32, None, None]
    flags = MDSStatus()
    _sa = linkamProcessMessageCommon(c_int(21), c_uint64(stageHandle), byref(flags), c_uint(25), None, None)
    return flags