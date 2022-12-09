from itertools import count
import numpy as np
from OpenGLClasses import Texture
from PIL import Image

class Channel():
    idGenerator = count()
    def __init__(self):
        self.leds = [False, False, False, False, False, False]
        self.filterCube = 0
        self.save = True
        self.enable = True
        self.exposureTime = 100
        self.repeats = 1
        self.uid = next(Channel.idGenerator)
        self.color = [1.0, 1.0, 1.0]
        self.title = "Channel "+ str(self.uid)
        self.repeater = False
        self.segment_repeats = 1
        self.notes = "..."
        self.latest_img = np.zeros((2048, 2048))
        self.n_saved = 0
        self.texture = Texture(format = "ru16")
        self.show = True
        self.contrast_min = 0
        self.contrast_max = 65535
        self.contrast_auto = True
        self.condenser = 0

    def reset(self):
        self.latest_img = np.zeros((2048, 2048))
        self.n_saved = 0
        self.texture = Texture(format="ru16")
        self.setImage(self.latest_img)

    def __eq__(self, other):
        return self.uid == other.uid # possible error when other is not of type Channel.

    def setImage(self, img):
        self.latest_img = img
        self.texture.update(self.latest_img)

    def clone(self):
        myClone = Channel()
        myClone.leds = self.leds
        myClone.filterCube = self.filterCube
        myClone.save = self.save
        myClone.enable = self.enable
        myClone.exposureTime = self.exposureTime
        myClone.repeats = self.repeats
        myClone.color = self.color
        myClone.title = self.title
        myClone.repeater = self.repeater
        myClone.segment_repeats = self.segment_repeats
        myClone.notes = self.notes
        myClone.show = self.show
        return myClone