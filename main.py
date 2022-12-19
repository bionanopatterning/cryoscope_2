# -*- coding: utf-8 -*-
import glfw
import OpenGL.GL as gl
import imgui
import GUI_Config as cfg
from imgui.integrations.glfw import GlfwRenderer
import GUI_Modules
import Renderer
import Input
import Parameters as prm
import pcoCamera
import Arduino
import CombinedLightSource as LightHUB
import CryoStage
import DataControl
import AcquisitionControl
import StageController
import ASIStage
from Utility import *

def impl_glfw_init():
    width, height = cfg.width, cfg.height
    window_name = "minimal ImGui/GLFW3 example"

    if not glfw.init():
        print("Could not initialize OpenGL context")
        exit(1)

    # OS X supports only forward-compatible core profiles from 3.2
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, gl.GL_TRUE)

    if cfg.fullscreen:
        window = glfw.create_window(int(width), int(height), "Cryoscope", glfw.get_primary_monitor(), None)
    else:
        window = glfw.create_window(int(width), int(height), "Cryoscope", None, None)
    glfw.make_context_current(window)
    Input.Init(window)
    if not window:
        glfw.terminate()
        print("Could not initialize Window")
        exit(1)

    return window

imgui.create_context()
window = impl_glfw_init()
impl = GlfwRenderer(window)

def ConnectDevices():
    print("To do: if prm.requestedStagePosition != currentposition within error, move to requested pos (dumping this print statement here so that every init reminds me)")
    #prm.cameraConnected = pcoCamera.Connect()
    prm.lightsourceConnected = LightHUB.Connect()
    prm.controllerConnected = Arduino.Connect()
    prm.cryoStageConnected = CryoStage.Connect()
    prm.asiStageConnected = ASIStage.Connect()

def DisconnectDevices():
    Arduino.Disconnect()
    pcoCamera.Disconnect()
    LightHUB.Disconnect()
    CryoStage.Disconnect()
    ASIStage.Disconnect()

def FocusMainWindow():
    glfw.restore_window(window)
    GUI_Modules.windowNeedsRefocus = False

def MAINLoop():
    itnr = 0
    while not glfw.window_should_close(window):
        AcquisitionControl.OnUpdate()
        DataControl.OnUpdate()
        StageController.OnUpdate()
        impl.process_inputs()
        Input.OnUpdate()
        GUI_Modules.OnUpdate()
        imgui.push_style_color(imgui.COLOR_TITLE_BACKGROUND, *cfg.clr_default_imgui_dark_blue)
        imgui.push_style_color(imgui.COLOR_TITLE_BACKGROUND_ACTIVE, *cfg.clr_default_imgui_dark_blue)
        imgui.push_style_var(imgui.STYLE_WINDOW_ROUNDING, 0.0)
        if GUI_Modules.windowNeedsRefocus:
            FocusMainWindow()
        imgui.new_frame()

        if imgui.begin_main_menu_bar():
            if imgui.begin_menu("Exit", True):
                exitConfirmed, _ = imgui.menu_item("Confirm exit")
                if exitConfirmed:
                    DisconnectDevices()
                    exit(1)
                imgui.end_menu()
            if imgui.begin_menu("Devices", True):
                def _connectedTag(connectedBool):
                    if connectedBool:
                        return " (connected)"
                    else:
                        return " (no connection)"
                connectCamera, _ = imgui.menu_item(prm.camera + _connectedTag(prm.cameraConnected))
                connectLightsource, _ = imgui.menu_item(prm.lightsource + _connectedTag(prm.lightsourceConnected))
                connectController, _ = imgui.menu_item(prm.controller + _connectedTag(prm.controllerConnected))
                connectCryoStage, _ = imgui.menu_item(prm.cryoStage + _connectedTag(prm.cryoStageConnected))
                connectASIStage, _ = imgui.menu_item(prm.asiStage + _connectedTag(prm.asiStageConnected))
                if connectCamera and not prm.cameraConnected:
                    prm.cameraConnected = pcoCamera.Connect()
                    AcquisitionControl.LateInitToFixWeirdPcoBug()
                elif connectLightsource and not prm.lightsourceConnected:
                    prm.lightsourceConnected = LightHUB.Connect()
                elif connectController and not prm.controllerConnected:
                    prm.arduinoConnected = Arduino.Connect()
                elif connectCryoStage and not prm.cryoStageConnected:
                    prm.cryoStageConnected = CryoStage.Connect()
                elif connectASIStage and not prm.asiStageConnected:
                    prm.asiStageConnected = ASIStage.Connect()
                imgui.end_menu()
            if imgui.begin_menu("Shortcuts?", True):
                for shortcut in cfg.shortcuts:
                    imgui.menu_item(shortcut)
                imgui.end_menu()
            imgui.end_main_menu_bar()

        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        # Render acquired images
        GUI_Modules.ImageViewer()
        imgui.begin("Main control", False, flags = imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_TITLE_BAR)
        GUI_Modules.MainControl()
        imgui.end()
        imgui.begin("View settings", False, flags = imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_TITLE_BAR)
        GUI_Modules.ViewSettings()
        imgui.end()
        imgui.begin("Data acquisition setup",False, flags = imgui.WINDOW_NO_MOVE | imgui.WINDOW_MENU_BAR | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_TITLE_BAR)
        GUI_Modules.DataAcquisitionSetup()
        imgui.end()

        imgui.pop_style_color(2)
        imgui.pop_style_var(0)
        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)
        itnr += 1
        if itnr == 10:
            prm.cameraConnected = pcoCamera.Connect()
            AcquisitionControl.LateInitToFixWeirdPcoBug()

    impl.shutdown()
    glfw.terminate()

def main():
    startlog()
    Renderer.Init()
    ConnectDevices()
    AcquisitionControl.Init()
    MAINLoop()
    DisconnectDevices()

if __name__ == "__main__":
    main()