from itertools import count
import numpy as np
from OpenGLClasses import Texture
from PIL import Image
import Channel
import Parameters as prm

class Map:
    idGenerator = count()

    def __init__(self, num_images_2d, channels):
        self.uid = next(Map.idGenerator)

        # Fill position list
        self.n_positions = 0
        self.positions = list()
        self.pos_index = list()
        roi_w = (num_images_2d[0] * prm.numPixels * prm.pixelSize / prm.magnification) * (1.0 - prm.maps_image_overlap)
        roi_h = (num_images_2d[1] * prm.numPixels * prm.pixelSize / prm.magnification) * (1.0 - prm.maps_image_overlap)
        x = 0
        center = prm.maps_center
        for w in np.linspace(-roi_w/2, roi_w/2, num_images_2d[0]):
            y = 0
            for h in np.linspace(-roi_w / 2, roi_w / 2, num_images_2d[1]):
                self.positions.append([center[0] + w, center[1] + h])
                self.pos_index.append([x, y])
                self.n_positions += 1
                y+=1
            x+=1

        self.channels = list()
        for channel in channels:
            if channel.enable:
                self.channels.append(channel)

        self.n_channels = len(self.channels)
        print("Map has {} channels".format(self.n_channels))
        self.n_images = self.n_channels * self.n_positions
        self.c_channel = self.n_channels
        self.c_position = -1
    def next(self):
        # Returns the next 'task', which is either:
        # - nothing, in case the map is complete
        # - position, in case all channels have been acquired at the current position.
        # - channel, in case not all channels have been acquired at the current position yet.
        self.c_channel += 1
        if self.c_channel >= self.n_channels:
            self.c_channel = -1
            self.c_position += 1
            if self.c_position == self.n_positions:
                print("Returning: complete, None")
                return ("complete", None)
            else:
                print("Returning:\n\t'position'")
                print(self.positions[self.c_position])
                return ("position",  self.positions[self.c_position])
        else:
            print("Returning: ('channel', "+self.channels[self.c_channel].title+")")
            return ("channel", self.channels[self.c_channel])

    def save_image(self, img):
        print(self.c_channel)
        self.channels[self.c_channel].setImage(img)
        folder = prm.maps_current_folder
        title = self.channels[self.c_channel].title
        pos_idx = self.pos_index[self.c_position]
        image = Image.fromarray(img)
        filename = "xidx_{}_yidx_{}_cidx_{}_".format(pos_idx[0], pos_idx[1], self.c_channel) + "_"+self.channels[self.c_channel].title+".tiff"
        image.save(folder + "/" + filename)
