import Arduino
import LightHUB
import LedHUB
from Utility import *
LED_HI = ["A", "B", "C", "D", "E", "I"]
LED_LO = ["a", "b", "c", "d", "e", "i"]

laser_available = False
led_available = False

def Connect():
    global laser_available, led_available
    info("Connecting to LightHUB")
    laser_available = LightHUB.Connect()
    info("Connecting to LedHUB")
    led_available = LedHUB.Connect()
    return True

def Disconnect():
    LightHUB.Disconnect()
    LedHUB.Disconnect()

def setState(leds):
    """
    :param leds: list of Bools (or ints 0 or 1) - 1 means enable, 0 disable the respective channel - i.e., high or low
    voltage on the enable TTL connection. Which position in the list corresponds to which light source depends on wiring.
    Note: interpret 'leds' as light emitting devices, NOT as LED - this thing addresses both the laser and the led box.
    :return:
    """
    i = 0
    for led in leds:
        if led == True:
            Arduino.Send(LED_HI[i])
        else:
            Arduino.Send(LED_LO[i])
        i += 1

def setPower(leds):
    """
    :param leds: list of six integers between 0 - 100, corresponding to the power level in % of max. power you want to
    set on the light emitting devices. Positions in this list correspond to arduino communication protocol chars 'A, B, C, etc.',
    see the above global definition of LED_HI and LED_LO. Which letter addresses which light source depends on wiring of TTL
    connectors between arduino and light source enable pins.
    :return:
    """
    trace(f"CombinedLightSource.setPower ...\n [{leds[0]}, {leds[1]}, {leds[2]}, {leds[3]}, {leds[4]}, {leds[5]}]")
    trace(f"Devices found:\n\ti) laser {laser_available}\n\tii) led {led_available}")
    if laser_available:
        LightHUB.setPower([leds[0], leds[1], leds[2], leds[3]])
    if led_available:
        LedHUB.setPower([leds[4], leds[5], leds[6]])

