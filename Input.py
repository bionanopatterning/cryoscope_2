import glfw
import Parameters as prm
window = None
import GUI_Config as cfg
from Utility import *
cursorPos = [0.0, 0.0]
cursorOffset = [0.0, 0.0]
scrollOffset = [0.0, 0.0]

KEY_LEFT_SHIFT = glfw.KEY_LEFT_SHIFT
KEY_SPACE = glfw.KEY_SPACE
KEY_S = glfw.KEY_S
KEY_A = glfw.KEY_A
KEY_P = glfw.KEY_P
KEY_Q = glfw.KEY_Q
KEY_LEFT_CTRL = glfw.KEY_LEFT_CONTROL
KEY_ESCAPE = glfw.KEY_ESCAPE
doubleClickTimer = 0.0
doubleClickPossible = False
buttonPressReset = 30
memTime = None
#TODO glfw mouseScrollCallback blocks scroll event from reaching imgui. See: https://github.com/ocornut/imgui/issues/1759
def Init(glfwwindow):
    global window, time_prev, memTime
    window = glfwwindow
    glfw.set_scroll_callback(window, scrollCallback)
    memTime = glfw.get_time()

def OnUpdate():
    global cursorPos, cursorOffset, scrollOffset, buttonPressReset, memTime, doubleClickTimer, doubleClickPossible
    ## update time
    newTime = glfw.get_time()
    prm.dt = newTime - memTime
    memTime = newTime
    buttonPressReset = buttonPressReset - 1 # ugly, better use glfw callback with GL_PRESSED = True or so, but this works for now.
    if buttonPressReset < 0:
        buttonPressReset = 0
    glfw.poll_events()
    glfw.set_scroll_callback(window, scrollCallback)
    newCursorPos = getMousePosition()
    cursorOffset = [newCursorPos[0] - cursorPos[0], newCursorPos[1] - cursorPos[1]]
    cursorPos = newCursorPos

    if getMousePressed(0) and not doubleClickPossible:
        doubleClickTimer = cfg.doubleClickInterval
    if not doubleClickPossible and not getMousePressed(0):
        if doubleClickTimer > 0.0:
            doubleClickPossible = True
    if doubleClickTimer < 0.0:
        doubleClickPossible = False
    doubleClickTimer -= prm.dt

def getDoubleClick():
    global timeSinceLastMouseRelease, doubleClickPossible
    if doubleClickPossible:
        if getMousePressed(0):
            doubleClickPossible = False
            return True
    return False

def getMousePressed(button):
    """Returns True is the selected button is pressed (can be pressed for many frames)"""
    state = glfw.get_mouse_button(window, button)
    if state == glfw.PRESS:
        return True
    return False

def getMouseReleased(button):
    """Returns True is the button was clicked and is no longer clicked (returns True in only 1 frame)"""
    state = glfw.get_mouse_button(window, button)
    if state == glfw.RELEASE:
        print(state)
        return True
    return False

def getMousePosition():
    position = glfw.get_cursor_pos(window)
    return position

def scrollCallback(window, scrollx, scrolly):
    global scrollOffset
    scrolledInThisFrame = True
    scrollOffset = [scrollx, scrolly]

def getKeyPressed(button):
    global buttonPressReset
    """Button must be one of Input.KEYCODE - see definitions in Input.py"""
    glfw.KEY_0
    if buttonPressReset != 0:
        return False
    else:
        buttonPressed =  glfw.get_key(window, button)
        if buttonPressed:
            buttonPressReset = 10
        return buttonPressed
