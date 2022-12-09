import imgui
import tkinter as tk
from tkinter import filedialog
import Channel
import Bookmark
import numpy as np
import pickle

import DataControl
import IconLib
import Renderer
import GUI_Config as cfg
import Input
import Parameters as prm
from DataControl import *
import AcquisitionControl
import ASIStage
import CryoStage
import Utility
import StageController

tkroot = tk.Tk()
tkroot.withdraw()


windowNeedsRefocus = False

def OnUpdate():
    if imgui.get_io().want_capture_keyboard:
        return False # Don't process shortcut input when imgui is expecting keyboard input.
    if Input.getKeyPressed(Input.KEY_Q):
        info("Q - retracting lens")
        ASIStage.Safe()
    elif Input.getKeyPressed(Input.KEY_ESCAPE):
        info("ESC - cancelling acquisition")
        if prm.mode == "acquiring" or prm.mode == "searching" or prm.mode == "snapping" or prm.mode == "mapping":
            AcquisitionControl.AcquireCancel()
    elif Input.getKeyPressed(Input.KEY_SPACE):
        info("SPACE - toggle live")
        clb_LiveButton()
    elif Input.getKeyPressed(Input.KEY_S):
        info("S - start/cancel snap")
        clb_SnapButton()
    elif Input.getKeyPressed(Input.KEY_A):
        info("A - start/cancel acquisition")
        clb_AcquireButton()
    elif Input.getKeyPressed(Input.KEY_P):
        info("P - pause/unpause")
        if prm.mode == "acquiring":
            AcquisitionControl.AcquirePause()
        elif prm.mode == "acquiring paused":
            AcquisitionControl.AcquireUnpause()
        elif prm.mode == "searching" or prm.mode == "snapping":
            AcquisitionControl.Search()
    cfg.updateIntervalCtr -= prm.dt
    if cfg.updateIntervalCtr < 0:
        cfg.updateIntervalCtr = cfg.updateInterval
        OnInterval()
    if prm.bookmarks_changed:
        saveBookmarks()

def OnInterval():
    # get stage temperature
    prm.cryostage_temperatures = CryoStage.getTemperature()
    prm.cameraTemperatures = pcoCamera.getTemperature()

def MainControl():
    fullWindowWidth = imgui.get_window_content_region_width()
    def _fileSaveConfig():
        global windowNeedsRefocus
        imgui.text("Working directory:")
        _, prm.workingDirectory = imgui.input_text("", prm.workingDirectory, 200, imgui.INPUT_TEXT_AUTO_SELECT_ALL)
        imgui.same_line(spacing = cfg.defaultSpacing)
        if imgui.button("browse"):
            prm.workingDirectory = filedialog.askdirectory()
            windowNeedsRefocus = True
        imgui.text("Experiment title:")
        imgui.push_item_width(cfg.acquisitionTitle_width)
        _, prm.acquisitionTitle = imgui.input_text(" ", prm.acquisitionTitle, 200, imgui.INPUT_TEXT_AUTO_SELECT_ALL)
        imgui.pop_item_width()
        imgui.text("Experiment notes:")
        _, prm.acquisitionNotes = imgui.input_text_multiline("   ", prm.acquisitionNotes, prm.notes_bufferSize, width = cfg.acquisitionNotes_width, height = cfg.acquisitionNotes_height)

    def _mainButtons():
        def _pushActiveColor(condition):
            if condition:
                imgui.push_style_color(imgui.COLOR_BUTTON, *cfg.clr_active_mode)
                imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, *cfg.clr_emphasis_button_hovered)
                imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, *cfg.clr_active_mode)
            else:
                imgui.push_style_color(imgui.COLOR_BUTTON, *cfg.clr_emphasis_button)
                imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, *cfg.clr_emphasis_button_hovered)
                imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, *cfg.clr_emphasis_button)

        def _popActiveColor():
                imgui.pop_style_color(3)

        def _progressBar():
            if prm.mode == "acquiring" or prm.mode == "acquisition paused":
                imgui.spacing()
                imgs_acquired = prm.acquisitionAcquiredSoFar
                imgs_expected = prm.acquisitionTotalToAcquire
                progressWidth = int(cfg.progressBar_width * (imgs_acquired / max((1, imgs_expected))))
                drawList = imgui.get_window_draw_list()
                # background rectangle
                drawList.add_rect_filled(*cfg.progressBar_size, imgui.get_color_u32_rgba(*cfg.clr_imgui_background_default, 1.0))
                drawList.add_rect_filled(cfg.progressBar_size[0], cfg.progressBar_size[1], cfg.progressBar_size[0] + progressWidth, cfg.progressBar_size[3], imgui.get_color_u32_rgba(*cfg.clr_active_mode, 1.0))

        _pushActiveColor(prm.mode == "acquiring")
        acquireButtonLabel = "   Start   \nacquisition" if not prm.mode == "acquiring" else "    Stop   \nacquisition"
        if imgui.button(acquireButtonLabel, width=cfg.mainButtons_width, height=cfg.mainButtons_height):
            clb_AcquireButton()
        _popActiveColor()
        _pushActiveColor(prm.mode == "snapping")
        imgui.same_line(spacing=(fullWindowWidth - 3 * cfg.mainButtons_width) / 2)
        snapButtonLabel = " Snap \nzstack" if prm.zStack_active else "Snap"
        if imgui.button(snapButtonLabel, width=cfg.mainButtons_width, height=cfg.mainButtons_height):
            clb_SnapButton()
        _popActiveColor()
        _pushActiveColor(prm.mode == "searching")
        imgui.same_line(spacing=(fullWindowWidth - 3 * cfg.mainButtons_width) / 2)
        if imgui.button("Live", width=cfg.mainButtons_width, height=cfg.mainButtons_height):
            clb_LiveButton()
        _popActiveColor()
        _progressBar()

    def _roiButtons():
        def _roiSizeButton(size):
            colorsOn = False
            if prm.currentRoi == size:
                colorsOn = True
                imgui.push_style_color(imgui.COLOR_BUTTON, *cfg.clr_emphasis_button_2)
                imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, *cfg.clr_emphasis_button_2)
                imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE    , *cfg.clr_emphasis_button_2)
            if imgui.button(f"{size}x{size}", width=cfg.roiButtons_width, height=cfg.roiButtons_height):
                clb_SetROI(size)
            if colorsOn:
                imgui.pop_style_color(3)

        cfg.header_ROI, _ = imgui.collapsing_header("Camera settings", None)
        if cfg.header_ROI:
            # Fan speed settings
            imgui.text("Fan control")
            imgui.push_item_width(cfg.focusStepButton_width)
            _changedSpeed, prm.fanspeed = imgui.input_int("##fanspeed", prm.fanspeed, 1, 10)
            prm.fanspeed = min([max([prm.fanspeed, 0]), 100])
            imgui.pop_item_width()
            imgui.same_line()
            _changedMode, prm.fanmode = imgui.checkbox("manual control", prm.fanmode)
            if prm.fanmode and (_changedSpeed or _changedMode):
                pcoCamera.setFanSpeed(prm.fanspeed)
            elif _changedMode and not prm.fanmode:
                pcoCamera.setFanSpeed(None)
                debug("Setting fanspeed back to auto")
            # Temperatures
            imgui.text("Camera temperatures:")
            imgui.text("Sensor:\t {:.1f} °C".format(prm.cameraTemperatures[0]))
            imgui.text("Camera:\t {:.1f} °C".format(prm.cameraTemperatures[1]))
            imgui.text("Power: \t {:.1f} °C".format(prm.cameraTemperatures[2]))
            imgui.separator()
            imgui.text("ROI size:")
            imgui.new_line()
            imgui.same_line(position = cfg.roiButtons_top_row_offset)
            _roiSizeButton(2048)
            imgui.same_line(spacing = cfg.roiButtons_separation)
            _roiSizeButton(1024)
            imgui.same_line(spacing=cfg.roiButtons_separation)
            _roiSizeButton(512)
            imgui.new_line()
            imgui.same_line(position=cfg.roiButtons_top_row_offset)
            _roiSizeButton(256)
            imgui.same_line(spacing=cfg.roiButtons_separation)
            _roiSizeButton(128)
            imgui.same_line(spacing=cfg.roiButtons_separation)
            _roiSizeButton(64)



    def _autofocusSettings():
        cfg.header_Focus, _ = imgui.collapsing_header("ASI stage", None, flags=imgui.TREE_NODE_DEFAULT_OPEN)
        if cfg.header_Focus:
            imgui.text(f"Current ASI stage state\nFocus:\t {prm.currentFocusPosition} um\nFilter:\t{prm.filterCubes[prm.currentFilter]}")
            imgui.spacing()
            imgui.new_line()
            imgui.same_line(spacing=(fullWindowWidth - cfg.autofocusButtonWidth) / 2)
            imgui.push_item_width(cfg.autofocusButtonWidth)
            _, prm.focusStepOptionCurrent = imgui.combo("Focus step", prm.focusStepOptionCurrent, prm.focusStepOptions)
            imgui.pop_item_width()
            prm.focusStep = prm.focusStepOptionsValue[prm.focusStepOptionCurrent]
            imgui.new_line()
            imgui.same_line(spacing = (fullWindowWidth - cfg.autofocusButtonWidth) / 2)
            imgui.same_line(spacing=(fullWindowWidth - cfg.autofocusButtonWidth) / 2)
            if imgui.button("Retract lens", width = cfg.autofocusButtonWidth, height = cfg.autofocusButtonHeight):
                ASIStage.Safe()


    def _stageInfo():
        any_temperature_warning = False
        for i in range(3):
            any_temperature_warning = any_temperature_warning or (prm.cryostage_temperatures[i] > prm.cryostage_temperature_high_warnings[i])
        if any_temperature_warning:
            imgui.push_style_color(imgui.COLOR_HEADER, *cfg.clr_warning)
            imgui.push_style_color(imgui.COLOR_HEADER_ACTIVE, *cfg.clr_warning)
            imgui.push_style_color(imgui.COLOR_HEADER_HOVERED, *cfg.clr_warning)
        cfg.header_CryostageInfo, _ = imgui.collapsing_header("Cryostage info", None, flags=imgui.TREE_NODE_DEFAULT_OPEN)
        if any_temperature_warning:
            imgui.pop_style_color(3)
        if cfg.header_CryostageInfo:
            if prm.cryostage_temperatures[2] > prm.cryostage_temperature_high_warnings[2]:
                imgui.push_style_color(imgui.COLOR_TEXT, *cfg.clr_warning)
            else:
                imgui.push_style_color(imgui.COLOR_TEXT, *cfg.clr_text_default)
            imgui.text("Bridge temp:    \t {:.1f} °C".format(prm.cryostage_temperatures[2]))
            imgui.pop_style_color(1)
            if prm.cryostage_temperatures[1] > prm.cryostage_temperature_high_warnings[1]:
                imgui.push_style_color(imgui.COLOR_TEXT, *cfg.clr_warning)
                _pop=1
            else:
                imgui.push_style_color(imgui.COLOR_TEXT, *cfg.clr_text_default)
            imgui.text("Chamber temp:   \t {:.1f} °C".format(prm.cryostage_temperatures[1]))
            imgui.pop_style_color(1)
            if prm.cryostage_temperatures[0] > prm.cryostage_temperature_high_warnings[0]:
                imgui.push_style_color(imgui.COLOR_TEXT, *cfg.clr_warning)
            else:
                imgui.push_style_color(imgui.COLOR_TEXT, *cfg.clr_text_default)
            imgui.text("Dewar temp:     \t {:.1f} °C".format(prm.cryostage_temperatures[0]))
            imgui.pop_style_color(1)
            imgui.spacing()
            imgui.text("Position:")
            imgui.text("\t(x, y) = ({:.1f}, {:.1f})".format(prm.currentPosition[0], prm.currentPosition[1]))
            imgui.spacing()
            imgui.text("Condenser:")
            imgui.new_line()
            imgui.same_line(spacing = cfg.condenserPowerInputOffset)
            imgui.push_item_width(cfg.condenserPowerInputWidth)
            useCondenserColorStyle = False
            if prm.currentCondenserPower > 0:
                useCondenserColorStyle = True
                imgui.push_style_color(imgui.COLOR_FRAME_BACKGROUND, cfg.clr_condenser_on[0] * 0.5, cfg.clr_condenser_on[1] * 0.5, cfg.clr_condenser_on[2] *0.5)
                imgui.push_style_color(imgui.COLOR_BUTTON, *cfg.clr_condenser_on)
                imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, *cfg.clr_condenser_on)
                imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, *cfg.clr_condenser_on)
            _condenserChanged, prm.currentCondenserPower = imgui.input_int("Condenser power", prm.currentCondenserPower, step = 5, step_fast = 100)
            if useCondenserColorStyle:
                imgui.pop_style_color(4)
            imgui.pop_item_width()
            if _condenserChanged:
                prm.currentCondenserPower = min([max([0, prm.currentCondenserPower]), 100])
                CryoStage.setCondenser(prm.currentCondenserPower)

    def _zstackSettings():
        cfg.header_ZStack, _ = imgui.collapsing_header("ZStack", None)
        if cfg.header_ZStack:
            _, prm.zStack_active = imgui.checkbox("Take stack?", prm.zStack_active)
            imgui.same_line(spacing = cfg.defaultSpacing)
            imgui.push_item_width(cfg.zStackCombo_width)
            _, prm.zStack_options_active = imgui.combo("##range mode", prm.zStack_options_active, prm.zStack_options)
            imgui.pop_item_width()
            imgui.separator()
            imgui.spacing()
            if prm.zStack_options_active == 0:
                num_slices = 1 + int((prm.zStack_top - prm.zStack_bottom) / (prm.zStack_step / 1000.0))
                imgui.text("Top:")
                imgui.same_line(position = cfg.zStackInputFloat_position)
                imgui.push_item_width(cfg.zStackInputFloat_width)
                _, prm.zStack_top = imgui.input_float("##topPos", prm.zStack_top, format = "%.2f")
                imgui.pop_item_width()
                imgui.same_line(spacing = 5)
                imgui.text("um")
                imgui.same_line(spacing = cfg.defaultSpacing)
                imgui.push_id("top buttons")
                btn_setTop = imgui.button('set', width = cfg.zStackSetZButton_width, height = cfg.zStackSetZButton_height)
                imgui.same_line(spacing=cfg.defaultSpacing)
                btn_gotoTop = imgui.button('goto', width=cfg.zStackSetZButton_width, height=cfg.zStackSetZButton_height)
                imgui.pop_id()
                imgui.text("Bottom:")
                imgui.same_line(position = cfg.zStackInputFloat_position)
                imgui.push_item_width(cfg.zStackInputFloat_width)
                _, prm.zStack_bottom = imgui.input_float("##botPos", prm.zStack_bottom, format = "%.2f")
                imgui.pop_item_width()
                imgui.same_line(spacing=5)
                imgui.text("um")
                imgui.same_line(spacing=cfg.defaultSpacing)
                imgui.push_id("bot buttons")
                btn_setBot = imgui.button('set', width=cfg.zStackSetZButton_width, height=cfg.zStackSetZButton_height)
                imgui.same_line(spacing=cfg.defaultSpacing)
                btn_gotoBot = imgui.button('goto', width=cfg.zStackSetZButton_width, height=cfg.zStackSetZButton_height)
                imgui.pop_id()
                imgui.text("Step:")
                imgui.same_line(position=cfg.zStackInputFloat_position)
                imgui.push_item_width(cfg.zStackInputInt_width)
                _, prm.zStack_step = imgui.input_int("nm", prm.zStack_step, step = 50, step_fast = 1000)
                imgui.pop_item_width()
                imgui.text(f"Number of slices: {num_slices}")
                if btn_setTop:
                    prm.zStack_top = ASIStage.getPosition()
                    info(f"Set zStack top to {prm.zStack_top}")
                elif btn_setBot:
                    prm.zStack_bottom = ASIStage.getPosition()
                    info(f"Set zStack bottom to {prm.zStack_top}")
                elif btn_gotoTop:
                    ASIStage.setPosition(prm.zStack_top)
                    info(f"Goto zStack top {prm.zStack_top}")
                elif btn_gotoBot:
                    ASIStage.setPosition(prm.zStack_bottom)
                    info(f"Goto zStack bottom {prm.zStack_top}")
            elif prm.zStack_options_active == 1:
                num_slices = 1 + int((prm.zStack_delta_up - prm.zStack_delta_down) / prm.zStack_step)
                imgui.text("Top:")
                imgui.same_line(position=cfg.zStackInputFloat_position)
                imgui.push_item_width(cfg.zStackInputInt_width)
                _, prm.zStack_delta_up = imgui.input_int("##upRange", prm.zStack_delta_up, step = 100, step_fast = 1000)
                imgui.pop_item_width()
                imgui.same_line(spacing=5)
                imgui.text("nm")
                imgui.text("Bottom:")
                imgui.same_line(position=cfg.zStackInputFloat_position)
                imgui.push_item_width(cfg.zStackInputInt_width)
                _, prm.zStack_delta_down = imgui.input_int("##downRange", prm.zStack_delta_down, step=100, step_fast=1000)
                imgui.pop_item_width()
                imgui.same_line(spacing=5)
                imgui.text("nm")
                imgui.text("Step:")
                imgui.same_line(position=cfg.zStackInputFloat_position)
                imgui.push_item_width(cfg.zStackInputInt_width)
                _, prm.zStack_step = imgui.input_int("nm", prm.zStack_step, step=50, step_fast=1000)
                imgui.pop_item_width()
                prm.zStack_delta_down = min([prm.zStack_delta_down, 0])
                prm.zStack_delta_up = max([prm.zStack_delta_up, 0])
                imgui.text(f"Number of slices: {num_slices}")
            prm.zStack_step = max([prm.zStack_step, 100])

    def _macroSettings():
        cfg.header_macros, _ = imgui.collapsing_header("Macros", None)
        if cfg.header_macros:
            imgui.new_line()
            imgui.same_line(spacing=(fullWindowWidth - cfg.macroButtonWidth) / 2)
            if imgui.button("Thickness image", width=cfg.macroButtonWidth, height=cfg.macroButtonHeight):
                clb_ThicknessImageMacro()
            imgui.new_line()
            imgui.same_line(spacing=(fullWindowWidth - cfg.macroButtonWidth) / 2)
            if imgui.button("Toggle live channels", width=cfg.macroButtonWidth, height=cfg.macroButtonHeight):
                clb_ToggleLiveChannelsMacro()
    def _log():
        cfg.header_log, _ = imgui.collapsing_header("Log", None)
        if cfg.header_log:
            _, cfg.log_level = imgui.combo("log level", cfg.log_level, cfg.log_level_options)
            logtext = ""
            for i in range(max([0, len(cfg.log_lines)-cfg.log_lines_shown]), len(cfg.log_lines)):
                logtext += (cfg.log_lines[i]+"\n")
            imgui.input_text_multiline("##log text", logtext, 4096, cfg.logWindowWidth, cfg.logWindowHeight, flags = imgui.INPUT_TEXT_READ_ONLY)
    # Start main function body #
    _fileSaveConfig()
    imgui.separator()
    _mainButtons()
    imgui.separator()
    _roiButtons()
    _autofocusSettings()
    _stageInfo()
    _zstackSettings()
    _macroSettings()
    _log()

def clb_ThicknessImageMacro():
    ## Add reflection channels if not already there.
    channel_R = False
    channel_G = False
    channel_B = False
    for channel in prm.liveChannels:
        if channel.title == "Reflection 528 (macro)":
            channel_R = True
        elif channel.title == "Reflection 470 (macro)":
            channel_G = True
        elif channel.title == "Reflection 405 (macro)":
            channel_B = True
        else:
            channel.enable = False
    if not channel_R:
        prm.liveChannels.append(Channel.Channel())
        prm.liveChannels[-1].title = "Reflection 528 (macro)"
        prm.liveChannels[-1].filterCube = 1
        prm.liveChannels[-1].leds = [False, False, False, False, False, True]
        prm.liveChannels[-1].exposureTime = 100
        prm.liveChannels[-1].color = [1.0, 0.0, 0.0]
        prm.liveChannels[-1].notes = "This standardized reflection\n channel was generated by\n the thickness image macro."
    if not channel_G:
        prm.liveChannels.append(Channel.Channel())
        prm.liveChannels[-1].title = "Reflection 470 (macro)"
        prm.liveChannels[-1].filterCube = 1
        prm.liveChannels[-1].leds = [False, False, False, False, True, False]
        prm.liveChannels[-1].exposureTime = 100
        prm.liveChannels[-1].color = [0.0, 1.0, 0.0]
        prm.liveChannels[-1].notes = "This standardized reflection\n channel was generated by\n the thickness image macro."
    if not channel_B:
        prm.liveChannels.append(Channel.Channel())
        prm.liveChannels[-1].title = "Reflection 405 (macro)"
        prm.liveChannels[-1].filterCube = 1
        prm.liveChannels[-1].leds = [False, False, False, True, False, False]
        prm.liveChannels[-1].exposureTime = 100
        prm.liveChannels[-1].color = [0.0, 0.0, 1.0]
        prm.liveChannels[-1].notes = "This standardized reflection\n channel was generated by\n the thickness image macro."
    prm.live_settingsChanged
    # Channels are now set up, take the image.
    clb_SnapButton()

def clb_ToggleLiveChannelsMacro():
    restartSearch = False
    if prm.mode == "searching":
        AcquisitionControl.Search()
        restartSearch = True
    for channel in prm.liveChannels:
        channel.enable = not channel.enable
    if restartSearch:
        AcquisitionControl.Search()

def clb_AcquireButton():
    if prm.mode == "acquiring":
        AcquisitionControl.AcquireCancel()
    elif prm.mode == "searching" or prm.mode == "snapping":
        AcquisitionControl.Search()
        DataControl.makeAcquisitionFolder()
        AcquisitionControl.AcquireStart()
    elif prm.mode == "idle":
        DataControl.makeAcquisitionFolder()
        AcquisitionControl.AcquireStart()
    else:
        error("Current program mode: "+prm.mode+" is invalid!")

def clb_SnapButton():
    if prm.mode == "acquiring":
        pass  # Do nothing - no interruption of acquisition allowed.
    elif prm.mode == "searching":
        # stop searching:
        AcquisitionControl.Search()
        # start snapping:
        AcquisitionControl.Search(continuous = False)
    elif prm.mode == "snapping":
        # stop snapping
        AcquisitionControl.Search()
    elif prm.mode == "idle":
        if prm.snappingBookmark:
            temp = prm.zStack_active
            prm.zStack_active = False
            AcquisitionControl.Search(continuous=False)
            prm.zStack_active = temp
        else:
            if prm.zStack_active:
                DataControl.makeZStackFolder()
            AcquisitionControl.Search(continuous=False)


    else:
        error("Current program mode: " + prm.mode + " is invalid!")

def clb_LiveButton():
    trace("live button clicked")
    trace(f"current mode = {prm.mode}")
    if prm.mode == "acquiring":
        pass # Do nothing - no interruption of acquisition allowed.
    elif prm.mode == "acquisition paused":
        AcquisitionControl.AcquireFinish()
    elif prm.mode == "searching":
        # stop searching:
        AcquisitionControl.Search()
    elif prm.mode == "snapping":
        # stop snapping
        pass # Do nothing - no interruption of snapping by searching allowed.
    elif prm.mode == "idle":
        if len(prm.liveChannels) == 0:
            newChannel = Channel.Channel()
            prm.liveChannels.append(newChannel)
        AcquisitionControl.Search(continuous=True) # Start searching
    else:
        error("Current program mode: " + prm.mode + " is invalid!")

def clb_SetROI(int_roiSize):
    prm.currentRoi = int_roiSize
    roisize = int(int_roiSize) # make it an int just in case
    _offset = int((prm.sensorSize - roisize) / 2)
    prm.roi = [_offset, _offset, _offset + roisize, _offset + roisize]

def ViewSettings():
    def _histogramFromChannel(channel):
        if not channel.enable or channel.repeater:
            return
        imgui.push_id(str(channel.uid))
        # Change colors when channel.show is false.
        disableColorFac = 1.0
        if not channel.show:
            disableColorFac = cfg.clr_disable_grayscale
        # Channel title and auto-contrast checkbox
        imgui.push_style_color(imgui.COLOR_TEXT, channel.color[0] * disableColorFac, channel.color[1] * disableColorFac, channel.color[2] * disableColorFac)
        imgui.text(f"({cfg.viewChannels.index(channel) + 1}) - " + channel.title)
        imgui.pop_style_color(1)
        imgui.same_line(position = cfg.view_histogram_width - 80)
        _, channel.show = imgui.checkbox("show", channel.show)
        imgui.same_line(position = cfg.view_histogram_width - 12)
        _, channel.contrast_auto = imgui.checkbox("auto", channel.contrast_auto)
        # Plotting the histogram (and subsampling the image to do so)
        subsample = channel.latest_img[512:1536:cfg.histogram_downsample, 512:1536:cfg.histogram_downsample]
        # Selecting the higher bound of the histogram maximum bin:
        _subsamplemax = np.max(subsample)
        histogramRange = (0, ArrayNearestHigherValue(cfg.histogram_range_allowed_max, _subsamplemax))
        # Compute histogram (numpy)
        histogramValues, binEdges = np.histogram(subsample, bins = cfg.histogram_num_bins, range = histogramRange)
        histogramValues = histogramValues.astype('float32')
        histogramValues = np.delete(histogramValues, 0)
        binEdges = np.delete(binEdges, 0)

        imgui.push_style_color(imgui.COLOR_PLOT_HISTOGRAM, channel.color[0] * disableColorFac, channel.color[1] * disableColorFac, channel.color[2] * disableColorFac)
        imgui.push_style_color(imgui.COLOR_PLOT_HISTOGRAM_HOVERED, channel.color[0] * disableColorFac, channel.color[1] * disableColorFac, channel.color[2] * disableColorFac)
        imgui.plot_histogram("##histogram" + str(channel.uid), histogramValues, graph_size = (cfg.view_histogram_width, cfg.view_histogram_height))
        imgui.pop_style_color(2)
        # Indicate the min/max range below the histogram
        if not channel.show:
            imgui.push_style_color(imgui.COLOR_TEXT, cfg.clr_disabled[0], cfg.clr_disabled[1], cfg.clr_disabled[2])
        minStr = "{:.0f}".format(binEdges[0])
        maxStr = "{:.0f}".format(binEdges[-1])
        imgui.text(minStr)
        imgui.same_line(spacing = cfg.view_histogram_width - GetTextWidth(minStr) - GetTextWidth(maxStr) - 3)
        imgui.text(maxStr)
        # User input for contrast
        if channel.contrast_auto:
            _std = np.std(subsample)
            channel.contrast_min = np.min(subsample)
            channel.contrast_max = _subsamplemax
        imgui.push_item_width(cfg.view_histogram_width)
        imgui.push_style_color(imgui.COLOR_SLIDER_GRAB, *channel.color)
        imgui.push_style_color(imgui.COLOR_SLIDER_GRAB_ACTIVE, *channel.color)
        _changedMin, channel.contrast_min = imgui.slider_float("min", channel.contrast_min, 0.0, binEdges[-1], format="%.0f", power=1)
        _changedMax, channel.contrast_max = imgui.slider_float("max", channel.contrast_max, 0.0, binEdges[-1], format="%.0f", power=1)
        imgui.pop_style_color(2)
        imgui.pop_item_width()
        if _changedMin or _changedMax:
            channel.contrast_auto = False
        # Pop channel and that's it.
        if not channel.show:
            imgui.pop_style_color(1)
        imgui.spacing()
        imgui.spacing()
        imgui.pop_id()

    def _headerButtons():
        # Reset zoom
        imgui.push_item_width(cfg.view_histogram_width)
        _, prm.snapSaveTitle = imgui.input_text("Title", prm.snapSaveTitle, 256)
        imgui.pop_item_width()
        imgui.new_line()
        imgui.same_line(spacing = cfg.view_headerButton_hoffset)
        if imgui.button("Zoom to fit", cfg.view_headerButton_width, cfg.view_headerButton_height):
            cfg.cameraZoom = 1.0
        imgui.same_line(spacing = cfg.defaultSpacing)
        # Save latest (snap / live) image
        if imgui.button(("Save latest"), cfg.view_headerButton_width, cfg.view_headerButton_height):
            saveLatestLiveImg(prm.snapSaveTitle, prm.workingDirectory)
        _, prm.autoSaveSnap = imgui.checkbox("autosave snaps", prm.autoSaveSnap)
        imgui.separator()
    _headerButtons()
    currentChannels = None
    for channel in cfg.viewChannels:
        _histogramFromChannel(channel)
        imgui.spacing()


DataAcquisitionSetup_Active = 'Search'
def DataAcquisitionSetup():
    global DataAcquisitionSetup_Active
    if imgui.core.begin_menu_bar():
        if imgui.begin_menu('Acquisition'):
            DataAcquisitionSetup_Active = 'Acquisition'
            imgui.close_current_popup()
            imgui.end_menu()
        elif imgui.begin_menu('Search'):
            DataAcquisitionSetup_Active = 'Search'
            imgui.close_current_popup()
            imgui.end_menu()
        elif imgui.begin_menu('Maps'):
            DataAcquisitionSetup_Active = 'Maps'
            imgui.close_current_popup()
            imgui.end_menu()
        elif imgui.begin_menu('Bookmarks'):
            DataAcquisitionSetup_Active = 'Bookmarks'
            imgui.close_current_popup()
            imgui.end_menu()
        imgui.end_menu_bar()

    if DataAcquisitionSetup_Active == 'Acquisition':
        AcquisitionGUI()
    elif DataAcquisitionSetup_Active == 'Search':
        SearchGUI()
    elif DataAcquisitionSetup_Active == 'Maps':
        MapsGUI()
    elif DataAcquisitionSetup_Active == 'Bookmarks':
        BookmarksGUI()

def clb_cm_moveStage():
    cfg.contextMenu = False
    StageController.moveStageToCursorPosition()

def clb_cm_addBookmark():
    cfg.contextMenu = False
    bookmarkPosition = StageController.cursorToStagePosition()
    prm.bookmarks_changed = True
    newBookmark = Bookmark.Bookmark()
    prm.bookmarks.append(newBookmark)
    newBookmark.position = bookmarkPosition


def ImageViewer():
    # # Handle input here.
    if not imgui.get_io().want_capture_mouse:
        if Input.getKeyPressed(Input.KEY_LEFT_CTRL):
            cfg.cameraZoom += cfg.cameraZoomSpeed * Input.scrollOffset[1]
            cfg.cameraZoom = max([cfg.cameraZoom, 1.0])
            Input.scrollOffset = [0.0, 0.0]
        # if right mouse button clicked
        if Input.getMousePressed(1):
            cfg.contextMenuPos = Input.getMousePosition()
            cfg.contextMenu = True
            cfg.contextMenuCanClose = False
    if not imgui.get_io().want_capture_keyboard:
        for i in range(min([len(cfg.viewChannels), 8])):
            if Input.getKeyPressed(i + 48 + 1): # plus 48 to match glfw.KEYCODES for 0-9
                cfg.viewChannels[i].show = not cfg.viewChannels[i].show
                if prm.mode == "searching":
                    AcquisitionControl.ChangeSearchSettingsWhileLive()
                break

    if cfg.contextMenu:
        imgui.set_next_window_position(cfg.contextMenuPos[0] - 5, cfg.contextMenuPos[1] - 5)
        imgui.set_next_window_size(cfg.contextMenuSize[0], cfg.contextMenuSize[1])
        imgui.push_style_var(imgui.STYLE_WINDOW_ROUNDING, 0.0)
        if imgui.begin("Actions", flags = imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_TITLE_BAR):
            moveStage, _ = imgui.menu_item("Move stage here")
            addBookmark, _ = imgui.menu_item("Place bookmark")

            if moveStage: clb_cm_moveStage()
            elif addBookmark: clb_cm_addBookmark()
            if not imgui.is_window_hovered(imgui.HOVERED_ALLOW_WHEN_BLOCKED_BY_ACTIVE_ITEM):
                if cfg.contextMenuCanClose:
                    cfg.contextMenu = False
                cfg.contextMenuCanClose = True
            imgui.end()
        imgui.pop_style_var(1)
    # Select which channels to view.
    if prm.mode == "acquiring" or cfg.latestAcquisitionMode == "acquiring":
        cfg.viewChannels = prm.acquisitionChannels
    elif prm.mode == "mapping" or cfg.latestAcquisitionMode == "mapping":
        cfg.viewChannels = prm.mapChannels
    else:
        cfg.viewChannels = prm.liveChannels

    Renderer.RenderPrimaryView(cfg.viewChannels)



def AcquisitionGUI():
    def _renderChannels():
        i = 0
        for channel in prm.acquisitionChannels:
            i += 1
            if channel.repeater:
                imgui.set_column_width(-1, cfg.channel_column_width_repeater)
            else:
                imgui.set_column_width(-1, cfg.channel_column_width)
            retcode = ChannelGUI_Full(channel)
            if retcode == "delete":
                prm.acquisitionChannels.pop(prm.acquisitionChannels.index(channel))
            elif retcode == "left":
                ListItemSwapLeft(prm.acquisitionChannels, channel)
            elif retcode == "right":
                ListItemSwapRight(prm.acquisitionChannels, channel)
            imgui.next_column()

    def _addButtonVerticalOffset():
        for i in range(0, cfg.channelAddButtonVerticalSpacingCount):
            imgui.spacing()

    def _channelGUI():
        # Add button
        numChannels = len(prm.acquisitionChannels)
        if numChannels > 0:
            imgui.columns(numChannels + 2, "channelColumns")
            imgui.set_column_width(-1, cfg.addChannelButtonColumnSize)
        else:
            imgui.columns(1, "channelColumns")

        _addButtonVerticalOffset()
        imgui.same_line(spacing=(cfg.addChannelButtonColumnSize - cfg.addChannelButtonSize) / 2 - 8)
        addButtonLeft = imgui.button("+", cfg.addChannelButtonSize, cfg.addChannelButtonSize)
        imgui.next_column()
        # Channels
        if numChannels > 0:
            _renderChannels()
            addButtonRight = False
            if len(prm.acquisitionChannels) > 0:
                _addButtonVerticalOffset()
                imgui.same_line(spacing=(cfg.addChannelButtonColumnSize - cfg.addChannelButtonSize) / 2 - 8)
                imgui.push_id("addButton2")
                addButtonRight = imgui.button("+", cfg.addChannelButtonSize, cfg.addChannelButtonSize)
                imgui.pop_id()
            # button callbacks
            if addButtonRight:
                newChannel = Channel.Channel()
                prm.acquisitionChannels.append(newChannel)
        if addButtonLeft:
            newChannel = Channel.Channel()
            prm.acquisitionChannels.insert(0, newChannel)

    def _overallGUI():
        imgui.text("ACQUISITION SETUP")
        imgui.text("Laser power:")
        i = 0
        imgui.new_line()
        for source in prm.lightSources:
            imgui.same_line(spacing = cfg.laserPowerSlider_offset)
            wavelengthColour = WavelengthToColor(source)
            imgui.push_style_color(imgui.COLOR_TEXT, wavelengthColour[0], wavelengthColour[1], wavelengthColour[2])
            imgui.push_style_color(imgui.COLOR_FRAME_BACKGROUND, cfg.sliderBackgroundColor[0], cfg.sliderBackgroundColor[1], cfg.sliderBackgroundColor[2])
            imgui.push_style_color(imgui.COLOR_SLIDER_GRAB, wavelengthColour[0], wavelengthColour[1], wavelengthColour[2])
            _, prm.acquisitionPower[i] = imgui.slider_float(source+" nm", prm.acquisitionPower[i], 0.0, 100.0, format = "%.0f")
            imgui.pop_style_color(3)
            if not (i == len(prm.lightSources)-1):
                imgui.new_line()
            i+=1
        imgui.spacing()
        imgui.text("Overall settings:")
        imgui.push_item_width(125)
        _, prm.acquisitionRepeats = imgui.input_int("Total repeats", prm.acquisitionRepeats)
        imgui.pop_item_width()
        _, prm.acquisitionPositionSetting_selected = imgui.combo("Position", prm.acquisitionPositionSetting_selected, prm.acquisitionPositionSetting)

        imgui.text("Configuration:")
        if imgui.button("Save setup", cfg.saveConfigButton_width, cfg.saveConfigButton_height):
            saveImagingSetup(prm.acquisitionChannels)
        imgui.same_line(spacing = cfg.defaultSpacing)
        if imgui.button("Load setup", cfg.saveConfigButton_width, cfg.saveConfigButton_height):
            prm.acquisitionChannels = loadImagingSetup(prm.acquisitionChannels)
            for channel in prm.acquisitionChannels:
                channel.reset()
        imgui.same_line(spacing = cfg.defaultSpacing)
        if imgui.button("Clear", cfg.clearConfigButton_width, cfg.saveConfigButton_height):
            prm.acquisitionChannels = list()
            prm.mode == "idle"
    # Overall controls
    imgui.columns(2, 'liveColumns')
    imgui.set_column_width(-1, cfg.bottomPanel_firstColumnWidth)
    _overallGUI()
    imgui.next_column()
    imgui.set_next_window_content_size(len(prm.acquisitionChannels) * cfg.channel_column_width + 500, cfg.channel_column_height)
    imgui.begin_child("liveChannels", width=cfg.channelWindowTotalWidth, height=0.0, border=False, flags=imgui.WINDOW_ALWAYS_HORIZONTAL_SCROLLBAR)

    # Child window with the channel setup.
    _channelGUI()
    imgui.end_child()

def saveImagingSetup(channelList):
    global windowNeedsRefocus
    # first set all the channel id's to a negative value. This ensures that after loading, any newly added channel (with id 0 or higher) still has a unique id.
    i = -1
    channelImgs = list()
    for channel in channelList:
        channel.uid = i
        channelImgs.append(channel.latest_img)
        channel.latest_img = np.zeros((prm.sensorSize, prm.sensorSize))
        i-=1
    fileName = filedialog.asksaveasfilename()
    with open(fileName+".channels", 'wb') as file:
        pickle.dump(channelList, file)
    i = 0
    for channel in channelList:
        channel.latest_img = channelImgs[i]
    windowNeedsRefocus = True

def loadImagingSetup(channelList):
    global windowNeedsRefocus
    fileName = filedialog.askopenfilename()
    windowNeedsRefocus = True
    if fileName == '':
        return channelList
    with open(fileName, 'rb') as file:
        return pickle.load(file)

def SearchGUI():
    def _renderChannels():
        i = 0
        for channel in prm.liveChannels:
            i += 1
            imgui.set_column_width(-1, cfg.channel_column_width)
            retcode = ChannelGUI_Simple(channel)
            if retcode == "delete":
                prm.liveChannels.pop(prm.liveChannels.index(channel))
                if len(prm.liveChannels) == 0:
                    clb_LiveButton()
            elif retcode == "left":
                ListItemSwapLeft(prm.liveChannels, channel)
            elif retcode == "right":
                ListItemSwapRight(prm.liveChannels, channel)
            imgui.next_column()

    def _addButtonVerticalOffset():
        for i in range(0, cfg.channelAddButtonVerticalSpacingCount):
            imgui.spacing()

    def _channelGUI():
        numChannels = len(prm.liveChannels)
        if numChannels > 0:
            imgui.columns(numChannels + 2, "channelColumns")
            imgui.set_column_width(-1, cfg.addChannelButtonColumnSize)
        else:
            imgui.columns(1, "channelColumns")

        _addButtonVerticalOffset()
        imgui.same_line(spacing=(cfg.addChannelButtonColumnSize - cfg.addChannelButtonSize) / 2 - 8)
        addButtonLeft = imgui.button("+", cfg.addChannelButtonSize, cfg.addChannelButtonSize)
        imgui.next_column()
        # Channels
        if numChannels > 0:
            _renderChannels()
            addButtonRight = False
            if len(prm.liveChannels) > 0:
                _addButtonVerticalOffset()
                imgui.same_line(spacing=(cfg.addChannelButtonColumnSize - cfg.addChannelButtonSize) / 2 - 8)
                imgui.push_id("addButton2")
                addButtonRight = imgui.button("+", cfg.addChannelButtonSize, cfg.addChannelButtonSize)
                imgui.pop_id()
            # button callbacks
            if addButtonRight:
                prm.live_settingsChanged = True
                newChannel = Channel.Channel()
                newChannel.filterCube = prm.currentFilter
                prm.liveChannels.append(newChannel)
        if addButtonLeft:
            prm.live_settingsChanged = True
            newChannel = Channel.Channel()
            prm.liveChannels.insert(0, newChannel)

    def _overallGUI():
        imgui.text("SEARCH SETUP")
        imgui.text("Laser power:")
        i = 0
        imgui.new_line()

        for source in prm.lightSources:
            imgui.same_line(spacing = cfg.laserPowerSlider_offset)
            wavelengthColour = WavelengthToColor(source)
            imgui.push_style_color(imgui.COLOR_TEXT, wavelengthColour[0], wavelengthColour[1], wavelengthColour[2])
            imgui.push_style_color(imgui.COLOR_FRAME_BACKGROUND, cfg.sliderBackgroundColor[0], cfg.sliderBackgroundColor[1], cfg.sliderBackgroundColor[2])
            imgui.push_style_color(imgui.COLOR_SLIDER_GRAB, wavelengthColour[0], wavelengthColour[1], wavelengthColour[2])
            _change, prm.livePower[i] = imgui.slider_float(source+" nm", prm.livePower[i], 0.0, 100.0, format = "%.0f")
            prm.live_powerChanged = prm.live_powerChanged or _change
            imgui.pop_style_color(3)
            imgui.new_line()
            i+=1

        for i in range(13):
            imgui.spacing()
        imgui.text("Configuration:")
        if imgui.button("Save setup", cfg.saveConfigButton_width, cfg.saveConfigButton_height):
            saveImagingSetup(prm.liveChannels)
        imgui.same_line(spacing=cfg.defaultSpacing)
        if imgui.button("Load setup", cfg.saveConfigButton_width, cfg.saveConfigButton_height):
            prm.liveChannels = loadImagingSetup(prm.liveChannels)
        imgui.same_line(spacing=cfg.defaultSpacing)
        if imgui.button("Clear", cfg.clearConfigButton_width, cfg.saveConfigButton_height):
            if prm.mode == "searching" or prm.mode == "snapping":
                clb_LiveButton()
                prm.liveChannels = list()

    imgui.columns(2, 'liveColumns')
    imgui.set_column_width(-1, cfg.bottomPanel_firstColumnWidth)
    _overallGUI()
    imgui.next_column()
    imgui.set_next_window_content_size(len(prm.liveChannels) * cfg.channel_column_width + 800, cfg.channel_column_height) # 220408 changed to +800 from +500
    imgui.begin_child("liveChannels", width = cfg.channelWindowTotalWidth, height = 0.0, border = False, flags = imgui.WINDOW_ALWAYS_HORIZONTAL_SCROLLBAR)
    _channelGUI()

    imgui.end_child()

def clb_startMap():
    prm.mode = "mapping"
    prm.maps_image_processed = True # tell DataControl not to expect an image, initially. Conversely, tells AcquisitionControl that it should snap one.
    AcquisitionControl.MapStart()
    DataControl.MapStart()

def clb_copyChannelsMap():
    prm.mapChannels = list()
    for channel in prm.liveChannels:
        prm.mapChannels.append(channel.clone())

def MapsGUI():
    def _header():
        imgui.text("MAPS SETTINGS")
        imgui.input_text("name", prm.maps_title, 256)
        _, prm.maps_mode = imgui.combo("mode ", prm.maps_mode, prm.maps_mode_names)
        _, prm.maps_use_crisp = imgui.checkbox("use CRISP?", prm.maps_use_crisp)
        imgui.spacing()
        for i in range(5):
            imgui.spacing()
        imgui.new_line()
        imgui.same_line(spacing = cfg.maps_startButton_offset)
        _copyButton = imgui.button("Copy live channels", cfg.maps_startButton_width, cfg.maps_copyButton_height)
        imgui.spacing()
        imgui.same_line(spacing=cfg.maps_startButton_offset)
        _startButton = imgui.button("Start imaging", cfg.maps_startButton_width, cfg.maps_startButton_height)


        if _startButton:
            clb_startMap()
        elif _copyButton:
            clb_copyChannelsMap()

    def _coordinate_menu():
        def _roimode():
            imgui.text("work in progress")

        def _centermode():
            imgui.text("         CENTER OF MAP:")
            imgui.new_line()
            centerPosStr = "x = {:.1f}, y = {:.1f}".format(prm.maps_center[0], prm.maps_center[1])
            imgui.same_line(position = (cfg.maps_coordinatePreviewColumnWidth - GetTextWidth(centerPosStr)) / 2)
            imgui.text(centerPosStr)
            imgui.spacing()
            imgui.spacing()
            imgui.new_line()
            imgui.same_line(spacing = cfg.maps_setCenter_button_offset)

            setButton = imgui.button("Set current", cfg.maps_setCenter_button_width, cfg.maps_setCenter_button_height)

            imgui.push_item_width(cfg.maps_setWidthHeight_width)
            imgui.spacing()
            imgui.spacing()
            _, prm.maps_centerMode_width =  imgui.input_int("# images (width)", prm.maps_centerMode_width, 1, 5)
            _, prm.maps_centerMode_height = imgui.input_int("# images (height)", prm.maps_centerMode_height, 1, 5)
            prm.maps_centerMode_width = max([1, prm.maps_centerMode_width])
            prm.maps_centerMode_height   = max([1, prm.maps_centerMode_height])
            imgui.pop_item_width()

            if setButton:
                prm.maps_center = prm.currentPosition
        if prm.maps_mode == 0:
            _roimode()
        elif prm.maps_mode == 1:
            _centermode()

    def _channelGUI():
        def _addButtonVerticalOffset():
            for i in range(0, cfg.channelAddButtonVerticalSpacingCount):
                imgui.spacing()

        def _renderChannels():
            i = 0
            for channel in prm.mapChannels:
                i += 1
                imgui.set_column_width(-1, cfg.channel_column_width)
                retcode = ChannelGUI_Simple(channel, allowCondenser=True)
                if retcode == "delete":
                    prm.mapChannels.pop(prm.mapChannels.index(channel))
                elif retcode == "left":
                    ListItemSwapLeft(prm.mapChannels, channel)
                elif retcode == "right":
                    ListItemSwapRight(prm.mapChannels, channel)
                imgui.next_column()

        numChannels = len(prm.mapChannels)
        if numChannels > 0:
            imgui.columns(numChannels + 2, "channelColumns")
        else:
            imgui.columns(1, "channelColumns")
        _renderChannels()
        if numChannels > 0:
            imgui.set_column_width(-1, cfg.addChannelButtonColumnSize)
        _addButtonVerticalOffset()
        imgui.same_line(spacing=(cfg.addChannelButtonColumnSize - cfg.addChannelButtonSize) / 2 - 8)
        addButton = imgui.button("+", cfg.addChannelButtonSize, cfg.addChannelButtonSize)
        if addButton:
            newChannel = Channel.Channel()
            prm.mapChannels.append(newChannel)

    imgui.columns(3, 'mapsColumns')
    imgui.set_column_width(-1, cfg.maps_firstColumnWidth)
    _header()
    imgui.next_column()
    imgui.set_column_width(-1, cfg.maps_coordinatePreviewColumnWidth)
    _coordinate_menu()
    imgui.next_column()
    imgui.begin_child("mapChannels", width=cfg.channelWindowTotalWidth, height=0.0, border=False,
                      flags=imgui.WINDOW_ALWAYS_HORIZONTAL_SCROLLBAR)
    _channelGUI()
    imgui.end_child()

def saveBookmarks():
    try:
        with open(prm.bookmarkBackupPath, 'wb') as file:
            pickle.dump(prm.bookmarks, file)
    except Exception as e:
        pass

def BookmarksGUI():
    def _headerGUI():
        imgui.text("Position bookmarking")
        imgui.new_line()
        imgui.same_line(spacing = (cfg.bottomPanel_firstColumnWidth - cfg.addBookmark_button_width) / 2 - 8)
        addBookmark = imgui.button("Mark current position", cfg.addBookmark_button_width, cfg.addBookmark_button_height)
        if addBookmark:
            prm.bookmarks_changed = True
            newBookmark = Bookmark.Bookmark()
            prm.bookmarks.append(newBookmark)
            prm.currentPosition = CryoStage.getPosition()
            newBookmark.position = [prm.currentPosition[0], prm.currentPosition[1], ASIStage.getPosition()]
            # If the image currently in the primaryView was taken at the same position as this new bookmark's position, upload it as this bookmark's thumbnail.
            if positionsEqual(prm.live_latestPosition, prm.currentPosition, prm.bookmark_consider_same_position_distance_lim):
                Renderer.CopyCurrentImageToBookmark(newBookmark)
            elif prm.mode == "acquiring":
                Renderer.CopyCurrentImageToBookmark(newBookmark)
        for i in range(10):
            imgui.spacing()
        imgui.same_line(spacing=(cfg.bottomPanel_firstColumnWidth - cfg.addBookmark_button_width) / 2 -8)

        restoreBookmarks = imgui.button("(restore after crash)", cfg.addBookmark_button_width, cfg.restoreBookmarks_button_height)
        if restoreBookmarks:
            with open(prm.bookmarkBackupPath, 'rb') as file:
                prm.bookmarks = pickle.load(file)
                for bookmark in prm.bookmarks:
                    bookmark.refreshThumbnail()

    def _childGUI():
        numBookmarks = len(prm.bookmarks)
        if numBookmarks > 0:
            imgui.columns(numBookmarks + 1, "bookmarkList")

        i = 0
        toDelete = None
        for bookmark in prm.bookmarks:
            i += 1
            imgui.set_column_width(-1, cfg.bookmark_column_width)
            retcode = None
            if bookmark.delete:
                prm.bookmarks.remove(bookmark)
            else:
                retcode = BookmarkGUI(bookmark)
            if retcode == "delete":
                # Can't delete bookmark here, imgui expects it to exist to render it's texture later (not sure how else to fix)
                bookmark.delete = True
            imgui.next_column()
        return toDelete

    imgui.columns(2, 'bookmarkColumns')
    imgui.set_column_width(-1, cfg.bottomPanel_firstColumnWidth)
    _headerGUI()
    imgui.next_column()
    imgui.set_next_window_content_size(len(prm.bookmarks) * cfg.bookmark_column_width + 500, cfg.bookmark_column_height)
    imgui.begin_child("bookmarks", width = cfg.channelWindowTotalWidth, height = 0.0, border = False, flags = imgui.WINDOW_HORIZONTAL_SCROLLING_BAR | imgui.WINDOW_ALWAYS_HORIZONTAL_SCROLLBAR)
    _childGUI()
    imgui.end_child()

def ChannelGUI_Simple(channel, allowCondenser = False):
    imgui.push_id(str(channel.uid))
    # push de-active colour, only gets popped at the very end.
    disabledColorUsed = False
    disableColorGrayscale = 1.0
    if not channel.enable:
        imgui.push_style_color(imgui.COLOR_TEXT, cfg.clr_disabled[0], cfg.clr_disabled[1], cfg.clr_disabled[2])
        imgui.push_style_color(imgui.COLOR_CHECK_MARK, cfg.clr_disabled[0], cfg.clr_disabled[1], cfg.clr_disabled[2])
        disableColorGrayscale = cfg.clr_disable_grayscale
        disabledColorUsed = True
    # Title and enable & close buttons.
    imgui.push_item_width(cfg.channelTitleWidth)
    imgui.push_style_color(imgui.COLOR_TEXT, channel.color[0] * disableColorGrayscale, channel.color[1] * disableColorGrayscale, channel.color[2] * disableColorGrayscale)
    imgui.push_id("channelName"+str(channel.uid))
    _, channel.title = imgui.input_text("", channel.title, 256)
    imgui.pop_id()
    imgui.pop_style_color(1)
    imgui.pop_item_width()
    imgui.same_line(spacing = cfg.channelHeader_separator_minor)
    channel.color = ColorSelector(channel.color, cfg.channelButton_small_size, cfg.channelButton_small_size)
    imgui.same_line(spacing=0)
    _change, channel.enable = imgui.checkbox("", channel.enable)
    prm.live_settingsChanged = prm.live_settingsChanged or _change
    imgui.same_line(spacing = cfg.channelHeader_separator_minor)
    imgui.push_style_color(imgui.COLOR_TEXT, 1.0, 1.0, 1.0)
    deleteButton = imgui.button("x", cfg.channelButton_small_size, cfg.channelButton_small_size)
    if deleteButton:
        prm.live_settingsChanged = True
    imgui.pop_style_color(1)
    imgui.same_line()
    # Light source selection check boxes
    i = 0
    for source in prm.lightSources:
        if i % 3 == 0:
            imgui.new_line()
        else:
            imgui.same_line((i % 3) * 80)
        wavelengthColor = WavelengthToColor(source)
        imgui.push_id(source)
        imgui.push_style_color(imgui.COLOR_TEXT, wavelengthColor[0] * disableColorGrayscale, wavelengthColor[1] * disableColorGrayscale, wavelengthColor[2] * disableColorGrayscale)
        imgui.push_style_color(imgui.COLOR_CHECK_MARK, wavelengthColor[0] * disableColorGrayscale, wavelengthColor[1] * disableColorGrayscale, wavelengthColor[2] * disableColorGrayscale)
        _change, channel.leds[i] = imgui.checkbox(source, channel.leds[i])
        prm.live_settingsChanged = prm.live_settingsChanged or _change
        imgui.pop_style_color(2)
        imgui.pop_id()
        i+=1
        imgui.same_line(spacing = cfg.channelLightSource_separator)
    if allowCondenser:
        imgui.push_id("condenser")
        imgui.push_style_color(imgui.COLOR_TEXT, *cfg.clr_condenser_on)
        imgui.push_style_color(imgui.COLOR_CHECK_MARK, *cfg.clr_condenser_on)
        _change, channel.condenser = imgui.checkbox("white", channel.condenser)
        prm.live_settingsChanged = prm.live_settingsChanged or _change
        imgui.pop_style_color(2)
        imgui.pop_id()
    else:
        imgui.new_line()
    # Exposure time
    _change, channel.exposureTime = imgui.input_int("Exposure (ms)", channel.exposureTime, step = 10, step_fast = 50, flags = imgui.INPUT_TEXT_CHARS_DECIMAL)
    if _change and channel.enable:
        channel.exposureTime = max([channel.exposureTime, prm.minimumExposure])
    prm.live_settingsChanged = prm.live_settingsChanged or _change
    # Filter cube selection
    _change, channel.filterCube = imgui.combo("Filter cube", channel.filterCube, prm.filterCubes)
    prm.live_settingsChanged = prm.live_settingsChanged or _change
    # End of disable color
    # Notes
    imgui.spacing()
    imgui.push_item_width(cfg.channel_column_width - 16)
    _, channel.notes = imgui.input_text_multiline(" ", channel.notes, prm.notes_bufferSize,
                                                  height=cfg.acquisitionChannel_notes_height)
    imgui.pop_item_width()
    # Left / right buttons
    imgui.spacing()
    if disabledColorUsed:
        imgui.pop_style_color(2)
    leftButton = imgui.button("<", cfg.channelButton_small_size, cfg.channelButton_small_size)
    imgui.same_line(position = cfg.channel_column_width - 2 * cfg.channelButton_small_size + 5)
    rightButton = imgui.button(">", cfg.channelButton_small_size, cfg.channelButton_small_size)

    imgui.pop_id()
    # button callbacks:
    if deleteButton:
        return "delete"
    if leftButton:
        prm.live_settingsChanged = True
        return "left"
    if rightButton:
        prm.live_settingsChanged = True
        return "right"

def ChannelGUI_Full(channel):
    imgui.push_id(str(channel.uid))
    # Separator GUI
    if channel.repeater:
        disabledColorUsed = False
        disableColorGrayscale = 1.0
        if not channel.enable:
            imgui.push_style_color(imgui.COLOR_TEXT, cfg.clr_disabled[0], cfg.clr_disabled[1], cfg.clr_disabled[2])
            imgui.push_style_color(imgui.COLOR_CHECK_MARK, cfg.clr_disabled[0], cfg.clr_disabled[1], cfg.clr_disabled[2])
            disableColorGrayscale = cfg.clr_disable_grayscale
            disabledColorUsed = True
        imgui.push_item_width(cfg.channelTitleWidth_repeater)
        imgui.push_style_color(imgui.COLOR_TEXT, channel.color[0] * disableColorGrayscale,
                               channel.color[1] * disableColorGrayscale, channel.color[2] * disableColorGrayscale)
        imgui.push_id("channelName" + str(channel.uid))
        imgui.new_line()
        imgui.same_line(spacing = cfg.repeater_enableCheckbox_offset)
        _, channel.enable = imgui.checkbox("",channel.enable)
        imgui.same_line(spacing = cfg.channelHeader_separator_minor)
        deleteButton = imgui.button("x", cfg.channelButton_small_size, cfg.channelButton_small_size)
        for i in range(cfg.channel_vertical_offset_repeater):
            imgui.spacing()

        imgui.new_line()
        imgui.same_line(cfg.repeaterText_horizontal_offset)
        imgui.text("Segment")
        imgui.new_line()
        imgui.same_line(cfg.repeaterText_horizontal_offset + 1)
        imgui.text("repeats")
        _, channel.segment_repeats = imgui.input_int(" ", channel.segment_repeats, step = 1, step_fast = 10)
        for i in range(cfg.channel_vertical_offset_repeater):
            imgui.spacing()
        imgui.pop_id()
        imgui.pop_style_color(1)
        imgui.pop_item_width()
        # Left right buttons
        leftButton = imgui.button("<", cfg.channelButton_small_size, cfg.channelButton_small_size)
        imgui.same_line(spacing = 10)
        makeChannelButton = imgui.button("O", cfg.channelButton_small_size, cfg.channelButton_small_size)
        imgui.same_line(spacing = 10)
        rightButton = imgui.button(">", cfg.channelButton_small_size, cfg.channelButton_small_size)
        if makeChannelButton:
            channel.repeater = False
        if disabledColorUsed:
            imgui.pop_style_color(2)
        imgui.pop_id()
        if deleteButton:
            return "delete"
        elif leftButton:
            return "left"
        elif rightButton:
            return "right"
    # Normal channel GUI:
    else:
        # push de-active colour, only gets popped at the very end.
        disabledColorUsed = False
        disableColorGrayscale = 1.0
        if not channel.enable:
            imgui.push_style_color(imgui.COLOR_TEXT, cfg.clr_disabled[0], cfg.clr_disabled[1], cfg.clr_disabled[2])
            imgui.push_style_color(imgui.COLOR_CHECK_MARK, cfg.clr_disabled[0], cfg.clr_disabled[1], cfg.clr_disabled[2])
            disableColorGrayscale = cfg.clr_disable_grayscale
            disabledColorUsed = True
        # Title and enable & close buttons.
        imgui.push_item_width(cfg.channelTitleWidth)
        imgui.push_style_color(imgui.COLOR_TEXT, channel.color[0] * disableColorGrayscale,
                               channel.color[1] * disableColorGrayscale, channel.color[2] * disableColorGrayscale)
        imgui.push_id("channelName" + str(channel.uid))
        _, channel.title = imgui.input_text("", channel.title, 256)
        imgui.pop_id()
        imgui.pop_style_color(1)
        imgui.pop_item_width()
        imgui.same_line(spacing=cfg.channelHeader_separator_minor)
        channel.color = ColorSelector(channel.color, cfg.channelButton_small_size, cfg.channelButton_small_size)
        imgui.same_line(spacing=0)
        _, channel.enable = imgui.checkbox("", channel.enable)
        imgui.same_line(spacing=cfg.channelHeader_separator_minor)
        imgui.push_style_color(imgui.COLOR_TEXT, 1.0, 1.0, 1.0)
        deleteButton = imgui.button("x", cfg.channelButton_small_size, cfg.channelButton_small_size)
        imgui.pop_style_color(1)
        imgui.same_line()
        # Light source selection check boxes
        i = 0
        for source in prm.lightSources:
            if i % 3 == 0:
                imgui.new_line()
            else:
                imgui.same_line((i % 3) * 80)
            wavelengthColor = WavelengthToColor(source)
            imgui.push_id(source)
            imgui.push_style_color(imgui.COLOR_TEXT, wavelengthColor[0] * disableColorGrayscale,
                                   wavelengthColor[1] * disableColorGrayscale, wavelengthColor[2] * disableColorGrayscale)
            imgui.push_style_color(imgui.COLOR_CHECK_MARK, wavelengthColor[0] * disableColorGrayscale,
                                   wavelengthColor[1] * disableColorGrayscale, wavelengthColor[2] * disableColorGrayscale)
            _, channel.leds[i] = imgui.checkbox(source, channel.leds[i])
            imgui.pop_style_color()
            imgui.pop_style_color()
            imgui.pop_id()
            i += 1
            imgui.same_line(spacing=cfg.channelLightSource_separator)
        # Exposure time
        imgui.new_line()
        _, channel.exposureTime = imgui.input_int("Exposure (ms)", channel.exposureTime, step=10, step_fast=50, flags=imgui.INPUT_TEXT_CHARS_DECIMAL)

        _, channel.save = imgui.checkbox("Save imgs?", channel.save)
        imgui.same_line()
        imgui.push_item_width(91)
        _, channel.repeats = imgui.input_int("Repeats", channel.repeats, step = 1, step_fast = 10, flags = imgui.INPUT_TEXT_CHARS_DECIMAL)
        imgui.pop_item_width()
        # Filter cube selection
        _, channel.filterCube = imgui.combo("Filter cube", channel.filterCube, prm.filterCubes)
        # End of disable color
        # Notes
        imgui.spacing()
        imgui.push_item_width(cfg.channel_column_width - 16)
        _, channel.notes = imgui.input_text_multiline(" ", channel.notes, prm.notes_bufferSize, height = cfg.acquisitionChannel_notes_height)
        imgui.pop_item_width()
        # Left / right buttons
        imgui.spacing()
        if disabledColorUsed:
            imgui.pop_style_color(2)

        buttonSpacing = (cfg.channel_column_width - 2 * cfg.channelButton_small_size - cfg.makeRepeaterButton_width) / 2 - 8
        leftButton = imgui.button("<", cfg.channelButton_small_size, cfg.channelButton_small_size)
        imgui.same_line(spacing=buttonSpacing)
        makeRepeaterButton = imgui.button("Make repeater", cfg.makeRepeaterButton_width, cfg.channelButton_small_size)
        imgui.same_line(spacing=buttonSpacing)
        rightButton = imgui.button(">", cfg.channelButton_small_size, cfg.channelButton_small_size)


        imgui.pop_id()
        # button callbacks:
        if deleteButton:
            return "delete"
        elif leftButton:
            return "left"
        elif rightButton:
            return "right"
        elif makeRepeaterButton:
            channel.repeater = not channel.repeater
    return ""

def BookmarkGUI(bookmark):
    def _importanceColorStylePush():
        imgui.push_style_color(imgui.COLOR_FRAME_BACKGROUND, importanceColor[0], importanceColor[1], importanceColor[2])
        imgui.push_style_color(imgui.COLOR_FRAME_BACKGROUND_HOVERED, importanceColor[0], importanceColor[1], importanceColor[2])
        imgui.push_style_color(imgui.COLOR_BUTTON, importanceColor[0], importanceColor[1], importanceColor[2])
        imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED,importanceColor[0], importanceColor[1], importanceColor[2])
        imgui.push_style_color(imgui.COLOR_POPUP_BACKGROUND, importanceColor[0], importanceColor[1], importanceColor[2])
        imgui.push_style_color(imgui.COLOR_TEXT, 0.0, 0.0, 0.0)
    def _importanceColorStylePop():
        imgui.pop_style_color(6)
    # Check whether we're at this bookmark's position
    stageAtBookmark = positionsEqual(bookmark.position[0:2], prm.currentPosition, prm.bookmark_consider_same_position_distance_lim)
    # Check whether bookmark is expecting a new snap, and if so process it
    if bookmark.expecting_snap:
        if prm.snappingBookmark_complete:
            prm.snappingBookmark_complete = False
            bookmark.expecting_snap = False
            Renderer.CopyCurrentImageToBookmark(bookmark)
            prm.bookmarks_changed = True
    imgui.push_id("Bookmark "+str(bookmark.uid))
    # Bookmark number, rating, and delete button
    importanceColor = cfg.bookmark_importance_colors[bookmark.importance]
    imgui.push_style_color(imgui.COLOR_TEXT, importanceColor[0], importanceColor[1], importanceColor[2])
    imgui.push_item_width(cfg.bookmark_title_width)
    _ch, bookmark.title = imgui.input_text("", bookmark.title, 256, imgui.INPUT_TEXT_AUTO_SELECT_ALL)
    prm.bookmarks_changed = prm.bookmarks_changed or _ch
    imgui.pop_item_width()
    imgui.same_line(spacing = cfg.defaultSpacing)
    imgui.pop_style_color(1)
    _importanceColorStylePush()
    imgui.push_item_width(cfg.bookmark_rating_width)
    _ch, bookmark.importance = imgui.combo("##  ", bookmark.importance, cfg.bookmark_importance_descriptors)
    if _ch and bookmark.importance == 4:
        prm.centerMarkerPosition = bookmark.position
    prm.bookmarks_changed = prm.bookmarks_changed or _ch
    imgui.pop_item_width()
    imgui.same_line(spacing = cfg.defaultSpacing)
    deleteButton = imgui.button("x", cfg.channelButton_small_size, cfg.channelButton_small_size)
    _importanceColorStylePop()
    # Image and control colums
    imgui.text("(x = {:.0f},y = {:.0f}, z = {:.1f})".format(bookmark.position[0], bookmark.position[1], bookmark.position[2]))
    imgui.push_style_color(imgui.COLOR_SEPARATOR, *cfg.clr_imgui_background_default)
    imgui.push_style_color(imgui.COLOR_SEPARATOR_HOVERED, *cfg.clr_imgui_background_default)
    imgui.push_style_color(imgui.COLOR_SEPARATOR_ACTIVE, *cfg.clr_imgui_background_default)
    imgui.begin_child("bookmark_child"+str(bookmark.uid))
    imgui.columns(2)

    imgui.set_column_width(-1, cfg.bookmark_image_width)
    imgui.image(bookmark.texture.renderer_id, cfg.bookmark_image_width, cfg.bookmark_image_height, uv0 = (0.25, 0.75), uv1 = (0.75, 0.25))
    imgui.next_column()

    gotoButton = imgui.button("Go to", cfg.bookmark_goto_button_width, cfg.bookmark_goto_button_height)
    if not stageAtBookmark:
        imgui.push_style_color(imgui.COLOR_BUTTON, cfg.clr_disabled[0], cfg.clr_disabled[1], cfg.clr_disabled[2])
        imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, cfg.clr_disabled[0], cfg.clr_disabled[1], cfg.clr_disabled[2])
        imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, cfg.clr_disabled[0], cfg.clr_disabled[1], cfg.clr_disabled[2])
    snapButton = imgui.button("Snap", cfg.bookmark_goto_button_width, cfg.bookmark_goto_button_height)
    if not stageAtBookmark:
        imgui.pop_style_color(3)
    _, bookmark.include = imgui.checkbox("Use?", bookmark.include)
    imgui.end_child()
    imgui.pop_style_color(3)
    imgui.pop_id()
    if deleteButton:
        prm.bookmarks_changed = True
        return "delete"
    elif gotoButton:
        CryoStage.setPosition(bookmark.position)
        ASIStage.setPosition(bookmark.position[2])
    elif snapButton:
        if stageAtBookmark:
            bookmark.expecting_snap = True
            prm.snappingBookmark = True
            clb_SnapButton()
    return None

def ColorSelector(currentColor, width, height):
    _, color = imgui.color_edit3(" ", currentColor[0], currentColor[1], currentColor[2], flags = imgui.COLOR_EDIT_NO_INPUTS)
    return color

def WavelengthToColor(wavelength):
    wavelength = wavelength[0:3]
    if wavelength == "405":
        return [244 / 255, 9 / 255, 226 / 255]
    elif wavelength == "470":
        return [0.0, 169 / 255, 1.0]
    elif wavelength == "532":
        return [101 / 255, 1.0, 0.0]
    elif wavelength == "590":
        return [1.0, 223 / 255, 0.0]
    else:
        # source: http://codingmess.blogspot.com/2009/05/conversion-of-wavelength-in-nanometers.html
        w = int(wavelength)

        # colour
        if w >= 380 and w < 440:
            R = -(w - 440.) / (440. - 350.)
            G = 0.0
            B = 1.0
        elif w >= 440 and w < 490:
            R = 0.0
            G = (w - 440.) / (490. - 440.)
            B = 1.0
        elif w >= 490 and w < 510:
            R = 0.0
            G = 1.0
            B = -(w - 510.) / (510. - 490.)
        elif w >= 510 and w < 580:
            R = (w - 510.) / (580. - 510.)
            G = 1.0
            B = 0.0
        elif w >= 580 and w < 645:
            R = 1.0
            G = -(w - 645.) / (645. - 580.)
            B = 0.0
        elif w >= 645 and w <= 780:
            R = 1.0
            G = 0.0
            B = 0.0
        else:
            R = 0.0
            G = 0.0
            B = 0.0

        # intensity correction
        if w >= 380 and w < 420:
            SSS = 0.3 + 0.7 * (w - 350) / (420 - 350)
        elif w >= 420 and w <= 700:
            SSS = 1.0
        elif w > 700 and w <= 780:
            SSS = 0.3 + 0.7 * (780 - w) / (780 - 700)
        else:
            SSS = 0.0
        return [SSS * R, SSS * G, SSS * B]

def ListItemSwapLeft(list, itemInList):
    length = len(list)
    idx1 = list.index(itemInList)
    if idx1 == 0:
        return None
    element1 = list[idx1]
    element2 = list[idx1 - 1]
    list[idx1] = element2
    list[idx1-1] = element1

def ListItemSwapRight(list, itemInList):
    length = len(list)
    idx1 = list.index(itemInList)
    if idx1 >= (length -1):
        return None
    element1 = list.pop(idx1)
    element2 = list.pop(idx1)

    list.insert(idx1, element2)
    list.insert(idx1+1, element1)

def GetTextWidth(text):
    fontSize = imgui.get_font_size() * len(text) / 2
    return fontSize

def ArrayNearestHigherValue(array, input):
    array = np.asarray(array)
    isHigher = array > input
    for idx in range(len(isHigher)):
        if isHigher[idx]:
            return array[idx]
    return array[-1]