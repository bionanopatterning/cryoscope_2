import Parameters as prm
import pcoCamera
import CombinedLightSource as LightHUB
import os.path
import PIL
import Arduino
import Map
from Utility import *
import CryoStage
import numpy as np
import ASIStage

import GUI_Config as cfg
def processStream():
    pass

def resetFrameCounter():
    _, metadata = pcoCamera.getLastImage(roi = (1, 1, 2, 2))
    prm.last_image_recording_number = metadata['recorder image number']

def Init():
    info("AcquisitionControl.Init()")
    if pcoCamera.pcoEdge: # do not init when cmera not connected
        Arduino.Send(f"QT1tZ100zRQY")
        resetFrameCounter()
    prm.currentCondenserPower = 0
    CryoStage.setCondenser(prm.currentCondenserPower)
    ASIStage.getFilter()

def LateInitToFixWeirdPcoBug():
    if pcoCamera.pcoEdge:
        Arduino.Send(f"QT1tZ100zRQY")
        resetFrameCounter()

def OnUpdate():
    if prm.mode == "searching":
        if prm.live_settingsChanged:
            ChangeSearchSettingsWhileLive()
            prm.live_settingsChanged = False
        if prm.live_powerChanged:
            LightHUB.setPower(prm.livePower)
            prm.live_powerChanged = False
    elif prm.mode == "mapping":
        MapOnUpdate()

    arduinoSignal = Arduino.Read()
    if arduinoSignal:
        info(arduinoSignal)
    # Filter change:
    if arduinoSignal == "F":
        requestedFilter = int(Arduino.Read())
        if requestedFilter != prm.currentFilter:
            info("Filter change requested!")
            info(f"Requested = {requestedFilter} current = {prm.currentFilter}")
            info(f"ASIStage.setFilter({requestedFilter})")
            prm.changing_filter = True
            ASIStage.setFilter(requestedFilter)
        else:
            Arduino.Send("F")
    # Focus change:
    if arduinoSignal == "H":
        prm.changing_focus = True
        requestedPosition = ""
        newChar = ""
        while newChar != "h":
            newChar = Arduino.Read()
            requestedPosition += newChar
        requestedPosition = float(requestedPosition[:-1])
        ASIStage.setPosition(requestedPosition)
        info(f"Requested focus pos = {requestedPosition}")
    if prm.changing_filter:
        if ASIStage.checkAvailable():
            info("Filter change completed")
            prm.changing_filter = False
            Arduino.Send("F")
    if prm.changing_focus:
        if ASIStage.checkAvailable():
            info("Focus change completed")
            prm.changing_focus = False
            Arduino.Send("H")


def MapOnUpdate():
    if not prm.maps_image_processed:
        # expecting image, is handled by DataControl
        return None
    elif prm.maps_awaiting_position:
        # check if stage has arrived yet
        if positionsEqual(prm.maps_requested_position, prm.currentPosition, 2.0):
            print("Position reached")
            prm.maps_awaiting_position = False
            time.sleep(prm.maps_stage_settle_time)
    else:
        print("next channel!")
        # check what to do next
        task, value = prm.currentMap.next()
        if task == "complete":
            print("Map completed")
            prm.mode = "idle"
            cfg.latestAcquisitionMode = "mapping"
        elif task == "channel":
            # Acquire this channel.
            CryoStage.setCondenser(value.condenser * prm.maps_fixed_condenser_power)
            # Send to arduino
            command = "UQT1tZ"+str(value.exposureTime)+"z"
            command += "F" + str(value.filterCube) + "f"
            if value.leds[0]:
                command += "B"
            if value.leds[1]:
                command += "C"
            if value.leds[2]:
                command += "D"
            if value.leds[3]:
                command += "A"
            if value.leds[4]:
                command += "E"
            command+="QX"
            Arduino.Send(command)
            prm.maps_image_processed = False
        elif task == "position":
            print("Moving to next position")
            prm.maps_requested_position = value
            CryoStage.setPosition(value)
            prm.maps_awaiting_position = True
        else:
            raise RuntimeError("Invalid task type in AcquisitionControl.MapOnUpdate()")
        pass

def MapStart():
    newMap = Map.Map([prm.maps_centerMode_width, prm.maps_centerMode_height], prm.mapChannels)
    prm.currentMap = newMap
    prm.mode = "mapping"
    maps_image_processed = False

def ChangeSearchSettingsWhileLive():
    Arduino.Send("U")
    Search()
    Search()

def UploadSearchSettings(continuous = True):
    LightHUB.setPower(prm.livePower)
    prm.live_activeChannels = list()
    prm.live_activeChannelIndex = 0
    prm.live_numChannels = 0
    for channel in prm.liveChannels:
        if channel.enable:
            prm.live_numChannels += 1
            prm.live_activeChannels.append(channel)
    if prm.live_numChannels == 0:
        prm.mode = "idle"
        return None
    # send acquisition string to arduino
    Arduino.Send("U")
    trace("Assembling instruction string:")
    command = "QT" + str(prm.acquisitionRepeats) + "t"
    for channel in prm.liveChannels:
        if channel.enable:
            command += "Z" + str(channel.exposureTime) + "z"
            command += "F" + str(channel.filterCube) + "f"
            if channel.leds[0]:
                command += "A"
            if channel.leds[1]:
                command += "B"
            if channel.leds[2]:
                command += "C"
            if channel.leds[3]:
                command += "D"
            if channel.leds[4]:
                command += "E"
            if channel.leds[5]:
                command += "I"
            command += "R"
            trace(command)
    command = command[:-1]  # Remove the last "R"
    command += "QX"
    if not continuous:
        command = command[:-2]  # Y signals to enter snapMode. replacing the last char X by Y means we do live mode, but only 1 loop through all channels.
        if not prm.zStack_active:
            command += "QY"
        else:
            command += ZStackCommandString()
            command += "QY"
    prm.live_latestPosition = CryoStage.getPosition()
    Arduino.Send(command)
    if continuous:
        prm.mode = "searching"
    else:
        prm.mode = "snapping"

def ZStackCommandString():
    prm.zStack_latest_position = 0
    prm.zStack_home = prm.currentFocusPosition
    prm.zStack_num_slices = 0
    if prm.zStack_options_active == 0:
        focusMax = max([prm.zStack_top, prm.zStack_bottom])
        focusMin = min([prm.zStack_top, prm.zStack_bottom])
    elif prm.zStack_options_active == 1:
        focusMax = prm.zStack_home + prm.zStack_delta_up / 1000.0
        focusMin = prm.zStack_home + prm.zStack_delta_down / 1000.0
    else:
        return ""
    newPos = focusMin
    prm.zStack_positions = list()
    while newPos <= (focusMax + prm.zStack_step / 2000.0):
        prm.zStack_num_slices += 1
        prm.zStack_positions.append(newPos)
        newPos += prm.zStack_step / 1000.0

    commandStr = ""
    for pos in prm.zStack_positions:
        commandStr += "H"
        commandStr += "{:.3f}".format(pos)
        commandStr += "h"
    return commandStr

def EndZStack():
    ASIStage.setPosition(prm.zStack_home)

def Search(continuous = True):
    if prm.mode != "searching" and prm.mode != "snapping":
        cfg.latestAcquisitionMode = "searching"
        debug("pre reset frame counter")
        resetFrameCounter()
        #pcoCamera.startRecording()
        debug("Uploading search settings")
        if UploadSearchSettings(continuous):
            cfg.latestImagingMode = "searching"
            # prm.last_image_recording_number = -1 # Needs to be here. If after snap only 1 image is taken, its nr. will be 1 - a next snap will also result in 1, and then DataControl.OnUpdate will not recognize it as a new image.
            debug("awaiting first image...")
            pcoCamera.waitForFirstImage()
            debug("got first image")
            return True
        else:
            return False

    else:
        Arduino.Send("U")
        resetFrameCounter()
        #pcoCamera.Stop()
        LightHUB.setState([0, 0, 0, 0, 0])
        prm.mode = "idle"

def restartSearch():
    Search()
    Search()

def AcquireStart():
    resetFrameCounter()
    if prm.mode == "searching" or prm.mode == "snapping":
        Search()
    if not prm.acquisitionChannels:
        return False
    # Set counters to 0, then count how many images to save/acquire, and make lists to know which to save and their title.
    prm.acquisitionTotalToSave = 0
    prm.acquisitionTotalToAcquire = 0
    prm.acquisitionSavedSoFar = 0  # num of images saved
    prm.acquisitionAcquiredSoFar = 0  # num of images acquired
    # Make a list with one entry for each acquired frame, that tells whether the frame should be saved or not.
    prm.acquisitionImageSaveList = list()
    prm.acquisitionImageTitleList = list()
    prm.acquisitionImageChannelList = list()
    Segments = [[], ]
    segment_repeats = 1
    for c in prm.acquisitionChannels:
        c.n_saved = 0
        if c.repeater:
            segment_repeats = c.segment_repeats
            for c in Segments[-1]:
                c.segment_repeats = segment_repeats
            Segments.append([])
        else:
            Segments[-1].append(c)
    if not (prm.acquisitionChannels[-1].repeater):
        #  if ..., then pretend a fake separator was at the end of channels list.
        Segments.append([])
    Segments.pop()  # remove last empty list
    # Channels are now ordered by the segment they are in.
    for R in range(0, prm.acquisitionRepeats):
        for segment in Segments:
            for s in range(0, segment[0].segment_repeats):
                for channel in segment:
                    if channel.enable:
                        for r in range(0, channel.repeats):
                            prm.acquisitionTotalToSave += channel.save
                            prm.acquisitionTotalToAcquire += 1
                            prm.acquisitionImageSaveList.append(channel.save)
                            prm.acquisitionImageTitleList.append(channel.title)
                            prm.acquisitionImageChannelList.append(channel)
    if prm.acquisitionTotalToAcquire == 0:
        return False

    # Set the power of the light source to the user-set acquisition power.
    LightHUB.setPower(prm.acquisitionPower)

    #pcoCamera.startRecording()
    Arduino.Send("U")
    command = "QT"+str(prm.acquisitionRepeats)+"t"
    for channel in prm.acquisitionChannels:
        if channel.enable:
            if channel.repeater:
                command += "K" + str(channel.segment_repeats) + "k"
            else:
                command += "Z" + str(channel.exposureTime) + "z"
                command += "F" + str(channel.filterCube) + "f"
                command += "W" + str(channel.repeats) + "w"
                if channel.leds[0]:
                    command += "A"
                if channel.leds[1]:
                    command += "B"
                if channel.leds[2]:
                    command += "C"
                if channel.leds[3]:
                    command += "D"
                if channel.leds[4]:
                    command += "E"
                if channel.leds[5]:
                    command += "I"
            command += "R"

    command = command[:-1] # Remove the last "R"
    command += "QS"
    Arduino.Send(command)
    prm.mode = "acquiring"
    cfg.latestAcquisitionMode = "acquiring"
    #pcoCamera.waitForFirstImage()

def AcquireFinish():
    Arduino.Send("U")
    prm.mode = "idle"
    prm.acquisitionAcquiredSoFar = 0
    #pcoCamera.Stop()

def AcquireCancel():
    Arduino.Send("U")
    prm.mode = "idle"
    prm.acquisitionAcquiredSoFar = 0
    #pcoCamera.Stop()

def AcquirePause():
    Arduino.Send("P")
    prm.mode = "acquiring paused"

def AcquireUnpause():
    Arduino.Send("P")
    prm.mode = "acquiring"

def numToTag(num):
    tag = ""
    if num < 10:
        tag = "000"+str(num)
    elif num < 100:
        tag = "00"+str(num)
    else:
        tag = "0"+str(num)
    return tag


def save_image(px_data, title, folder = None):
    if folder:
        _folder = folder
    else:
        _folder = prm.workingDirectory


    fullpath = _folder + "/" + title + ".tiff"

    if not os.path.isdir(_folder):
        os.mkdir(_folder)
    _counter = 2
    while os.path.isfile(fullpath):
        if _counter > 99:
            numtag = "_0"+str(_counter)
        elif _counter > 9:
            numtag = "_00"+str(_counter)
        else:
            numtag = "_000"+str(_counter)
        fullpath = _folder + "/" + title + numtag + ".tiff"
        _counter += 1
    _tiff = PIL.Image.fromarray(px_data)
    _tiff = _tiff.crop((prm.roi[0], prm.roi[1], prm.roi[2], prm.roi[3]))
    _tiff.save(fullpath)
