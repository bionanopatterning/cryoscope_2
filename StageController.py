import imgui
import Parameters as prm
import Input
import GUI_Config as cfg
import CryoStage
import ASIStage
import Renderer
import numpy as np
from Utility import *

def cursorToStagePosition():
    # Get inverse camera matrix
    inversePMat = np.linalg.inv(Renderer.projectionMatrix)
    #inverseVMat = Renderer.viewMatrix
    #inverseVMat[0,3] *= -1.0
    #inverseVMat[1,3] *= 1.0 # OpenGL Y coordinate is inverted by default: top of screen is -1, bottom is +1.
    inverseCameraMatrix = inversePMat #np.matmul(inverseVMat, inversePMat)
    # Get cursor pos
    cursorPosition = np.asarray(Input.getMousePosition())
    cursorPosition[0] = (cursorPosition[0] / cfg.width) * 2.0 - 1.0
    cursorPosition[1] = (cursorPosition[1] / cfg.height) * 2.0 - 1.0
    cursorPosition = np.matrix([[cursorPosition[0]], [cursorPosition[1]], [0.0], [1.0]])
    # Calculate world position
    worldPosition = inverseCameraMatrix * cursorPosition
    worldX = float(worldPosition[0])
    worldY = float(worldPosition[1])
    # Calculate stage position from world position
    # Scale
    stagePosition = np.asarray([worldX, worldY]) * cfg.world_to_stage_scale_fac * prm.pixelSize / prm.magnification
    stagePosition[0] -= cfg.cursor_stage_offset[0]
    stagePosition[1] -= cfg.cursor_stage_offset[1]
    # Rotate
    cosA = np.cos(np.rad2deg(prm.xyStageAngle))
    sinA = np.sin(np.rad2deg(prm.xyStageAngle))
    deltaX = cosA * stagePosition[0] + sinA * stagePosition[1]
    deltaY = cosA * stagePosition[1] - sinA * stagePosition[0]
    deltaStagePosition = np.asarray([deltaX, deltaY])
    info("delta stage pos = {:.2f},{:.2f}".format(deltaX, deltaY))
    return prm.currentPosition + deltaStagePosition

def stageToWorldPosition(stagePos):
    return stagePos

def moveStageToCursorPosition():
    newPos = cursorToStagePosition()
    CryoStage.setPosition(newPos)

def OnUpdate():
    if not imgui.get_io().want_capture_mouse:
        if not prm.mode == "acquiring":
            if Input.getDoubleClick():
                newPos = cursorToStagePosition()
                CryoStage.setPosition(newPos)
        if Input.getKeyPressed(Input.KEY_LEFT_SHIFT):
            scrollValue = Input.scrollOffset[1]
            if scrollValue != 0.0:
                ASIStage.Move(scrollValue * prm.focusStep)
                Input.scrollOffset = [0.0, 0.0]
