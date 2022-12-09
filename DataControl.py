import Parameters as prm
import os

import CryoStage
from Utility import *
import PIL
import pcoCamera
import AcquisitionControl
import ASIStage
import GUI_Config as cfg

def OnUpdate():
    def _checkForNewImage():
        image, metadata = pcoCamera.getLastImage(roi = (1, 1, 2, 2))
        if metadata['recorder image number'] != prm.last_image_recording_number:
            if (prm.last_image_recording_number - metadata['recorder image number']) > 1:
                error("IMAGE MISSED")
            prm.last_image_recording_number = metadata['recorder image number']

            prm.databuffer, prm.metadatabuffer = pcoCamera.getLastImage()
            return True
        else:
            return False

    cfg.updateStagePosIntervalCounter -= prm.dt
    if cfg.updateStagePosIntervalCounter < 0:
        cfg.updateStagePosIntervalCounter = cfg.updateStagePosInterval
        UpdateStagePos()

    # If no new image, jump out of function rightaway.
    if prm.mode == "idle":
        return None
    elif not _checkForNewImage():
        return None
    if prm.mode == "acquiring":
        processAcquisitionData()
    elif prm.mode == "searching":
        processSearchData()
    elif prm.mode == "snapping":
        processSnapData()
    elif prm.mode == "mapping":
        processMapData()


def UpdateStagePos():
    mem_log_level = cfg.log_level
    cfg.log_level = 0
    prm.currentPosition = CryoStage.getPosition()
    if not prm.changing_filter and not prm.changing_focus:
        ASIStage.getPosition()
        ASIStage.getFilter()

    cfg.log_level = mem_log_level
def MapStart():
    makeMapFolder()
    prm.mode = "mapping"

def processMapData():
    if not prm.maps_image_processed:
        prm.currentMap.save_image(prm.databuffer)
        prm.maps_image_processed = True
        print("Image saved!")

def makeMapFolder():
    def _writeMapMetadata():
        with open(prm.maps_current_folder + "/md.txt", "w") as mdfile:
            mdfile.write("Map imaged on "+ datestamp() + " " + timestamp())
            mdfile.write("\nTitle: " + prm.maps_title)
            mdfile.write("\nSaved in: " + prm.maps_current_folder)\

            for c in prm.mapChannels:
                cstr = "\n\n"
                if c.enable:
                    cstr += "\t" + c.title + "\n"
                    _i = 0
                    for led in prm.lightSources:
                        if c.leds[_i]:
                            cstr += "\t\tLight source -  " + led + " nm: " + str(prm.acquisitionPower[_i]) + " %\n"
                        _i += 1
                    cstr += "\t\tCondenser " + str(c.condenser) + " %\n"
                    cstr += "\t\tExposure time (ms): "+str(c.exposureTime)
                    cstr += "\n\t\tFilter cube:" + str(c.filterCube)
                    cstr += "\n\t\t\t" + str(prm.filterInfo[c.filterCube]) + "\n"
            mdfile.write(cstr)
        # TO DO: close file after writing

    while prm.maps_title[-1]==" ":
        prm.maps_title = prm.maps_title[:-1]
    path = prm.workingDirectory + "/" + prm.maps_title
    counter = 1
    while os.path.isdir(path):
        numtag = intTo4DigitString(counter)
        path = prm.workingDirectory + "/" + prm.maps_title + "_" + numtag
        counter += 1
    os.makedirs(path)
    prm.maps_current_folder = path
    _writeMapMetadata()

def makeAcquisitionFolder():
    def _writeAcquisitionMetaData():
        with open(prm.acquisitionCurrentFolder + "/md.txt", "w") as mdfile:
            mdfile.write("Acquisition on " + datestamp() + " " + timestamp())
            mdfile.write("\nTitle: " + prm.acquisitionTitle)
            prm.currentPosition = CryoStage.getPosition()
            mdfile.write(f"\nStage position: x = {prm.currentPosition[0]}, y = {prm.currentPosition[1]}")
            if prm.centerMarkerPosition:
                for bookmark in prm.bookmarks:
                    if bookmark.importance == 4:
                        prm.centerMarkerPosition = bookmark.position
                        mdfile.write(f"\nCenter marker stage position: x = {prm.centerMarkerPosition[0]}, y = {prm.centerMarkerPosition[1]}")
            else:
                mdfile.write(f"\nCENTER MARKER STAGE POSITION UNSET")
            mdfile.write("\nTotal repeats: " + str(prm.acquisitionRepeats))
            mdfile.write("\nSaved in: " + prm.acquisitionCurrentFolder)
            mdfile.write("\nNotes: \n"+ prm.acquisitionNotes)
            for c in prm.acquisitionChannels:
                cstr = "\n\n"
                if c.repeater:
                    cstr += "\t\t\t The above segment was repeated {} times".format(c.segment_repeats)
                else:
                    if c.enable:
                        cstr += "\t" + c.title + "\n"
                        _i = 0
                        for led in prm.lightSources:
                            if c.leds[_i]:
                                cstr += "\t\tLED " + led + " nm: " + str(prm.acquisitionPower[_i]) + " %\n"
                            _i += 1
                        cstr += "\t\tRepeats: {}\n\t\tExposure time: {}\n\t\tSave: {}\n".format(c.repeats, c.exposureTime,
                                                                                                c.save)
                        cstr += "\n\t\tFilter cube:" + str(c.filterCube)
                        cstr += "\n\t\t\t" + str(prm.filterInfo[c.filterCube]) + "\n"
                        cstr += "Channel notes: "+c.notes
                mdfile.write(cstr)

    while prm.acquisitionTitle[-1]==" ":
        prm.acquisitionTitle = prm.acquisitionTitle[:-1]
    path = prm.workingDirectory + "/" + prm.acquisitionTitle
    counter = 1
    while os.path.isdir(path):
        numtag = intTo4DigitString(counter)
        path = prm.workingDirectory + "/" + prm.acquisitionTitle + "_" + numtag
        counter += 1
    os.makedirs(path)
    prm.acquisitionCurrentFolder = path
    _writeAcquisitionMetaData()

def makeZStackFolder():
    def _writeZStackMetaData():
        with open(prm.zStack_folder + "/md.txt", "w") as mdfile:
            mdfile.write("ZStack:")
            for z in prm.zStack_positions:
                cstr = f"\t{z}"
                mdfile.write(cstr)
            for c in prm.liveChannels:
                cstr = "\n\n"
                if c.enable:
                    cstr += "\t" + c.title + "\n"
                    _i = 0
                    for led in prm.lightSources:
                        if c.leds[_i]:
                            cstr += "\t\tLED " + led + " nm: " + str(prm.livePower[_i]) + " %\n"
                        _i += 1
                    cstr += "\n\t\tFilter cube:" + str(c.filterCube)
                    cstr += "\n\t\t\t" + str(prm.filterInfo[c.filterCube]) + "\n"
                    cstr += "Channel notes: "+c.notes
                mdfile.write(cstr)

    path = prm.workingDirectory + "/" + "ZStack_" + prm.snapSaveTitle
    counter = 1
    while os.path.isdir(path):
        numtag = intTo4DigitString(counter)
        path = prm.workingDirectory + "/" + "ZStack_" + prm.snapSaveTitle + "_" + numtag
        counter += 1
    os.makedirs(path)
    prm.zStack_folder = path
    _writeZStackMetaData()

def processAcquisitionData():
    def _saveAcquisitionImage(channel):
        # The data for the image can be found in prm.databuffer
        _tiff = PIL.Image.fromarray(prm.databuffer)
        _tiff = _tiff.crop((prm.roi[0], prm.roi[1], prm.roi[2], prm.roi[3]))
        path = prm.acquisitionCurrentFolder + "/img_" + intTo4DigitString(prm.acquisitionSavedSoFar)+ "_" + channel.title + ".tiff"
        prm.acquisitionSavedSoFar += 1
        _tiff.save(path)
    # Find the corresponding channel
    currentChannel = prm.acquisitionImageChannelList[prm.acquisitionAcquiredSoFar]
    info("Current channel: " + str(currentChannel.uid))
    if currentChannel.save:
        info("\tsaved {}".format(currentChannel.n_saved+1))
        _saveAcquisitionImage(currentChannel)
        currentChannel.n_saved += 1
    prm.acquisitionAcquiredSoFar += 1
    currentChannel.setImage(prm.databuffer)
    if prm.acquisitionAcquiredSoFar == prm.acquisitionTotalToAcquire:
        AcquisitionControl.AcquireFinish()

def processSearchData():
    currentChannelActive = False
    while not currentChannelActive:
        currentChannel, _ = getCurrentLiveChannel()
        currentChannelActive = currentChannel.enable
    currentChannel.setImage(prm.databuffer)
    prm.live_latestPosition = prm.currentPosition


def processSnapData():

    def _saveZStackImage():
        _tiff = PIL.Image.fromarray(prm.databuffer)
        _tiff = _tiff.crop((prm.roi[0], prm.roi[1], prm.roi[2], prm.roi[3]))
        path = prm.zStack_folder + "/" + prm.live_activeChannels[prm.live_activeChannelIndex].title + "_Z_" + "{:.2f}".format(prm.zStack_positions[prm.zStack_latest_position]) + ".tiff"
        _tiff.save(path)

    if not prm.zStack_active:
        currentChannel, cycleComplete = getCurrentLiveChannel()
        currentChannel.setImage(prm.databuffer)
        if cycleComplete:
            if prm.snappingBookmark:
                prm.snappingBookmark_complete = True
                prm.snappingBookmark = False
            AcquisitionControl.Search(continuous = False)
            if prm.autoSaveSnap:
                saveLatestLiveImg(prm.snapSaveTitle, prm.workingDirectory)
    else:
        currentChannel = prm.live_activeChannels[prm.live_activeChannelIndex]
        currentChannel.setImage(prm.databuffer)
        _saveZStackImage()
        prm.zStack_latest_position += 1
        print("Next slice")
        if prm.zStack_latest_position >= prm.zStack_num_slices:
            print("Next channel")
            prm.zStack_latest_position = 0
            prm.live_activeChannelIndex += 1
        if prm.live_activeChannelIndex > len(prm.live_activeChannels):
            print("Done")
            AcquisitionControl.Search(continuous = False)
            AcquisitionControl.EndZStack()


def saveLatestLiveImg(title, folder = None):
    if not prm.liveChannels:
        return None
    if folder:
        _folder = folder
    else:
        _folder = prm.workingDirectory

    fullpath = _folder + "/" + title + ".tiff"
    if not os.path.isdir(_folder):
        os.mkdir(_folder)
    _counter = 1
    while os.path.isfile(fullpath):
        fullpath = _folder + "/" + title + "_" + intTo4DigitString(_counter) + ".tiff"
        _counter += 1
    img_list = []
    for channel in prm.liveChannels:
        if channel.enable and not (channel.latest_img is None):
            _tiff = PIL.Image.fromarray(channel.latest_img)
            _tiff = _tiff.crop((prm.roi[0], prm.roi[1], prm.roi[2], prm.roi[3]))
            img_list.append(_tiff)
    img_list[0].save(fullpath, compression=None, save_all=True, append_images=img_list[1:])
    print(fullpath)


def getCurrentLiveChannel():
    retval =  prm.live_activeChannels[prm.live_activeChannelIndex]
    prm.live_activeChannelIndex += 1
    cyclecomplete = False
    if prm.live_activeChannelIndex >= len(prm.live_activeChannels):
        prm.live_activeChannelIndex = 0
        cyclecomplete = True
    return retval, cyclecomplete
