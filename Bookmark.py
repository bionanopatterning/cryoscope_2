from itertools import count
from OpenGLClasses import Texture

class Bookmark():
    idGenerator = count()

    def __init__(self):
        self.uid = next(Bookmark.idGenerator)
        self.title = "Bookmark "+str(self.uid)
        self.include = True
        self.importance = 0
        self.position = [0, 0, 0]
        self.thumbnail = None
        self.texture = Texture(format = "rgba32f")
        self.notes = "..."
        self.delete = False
        self.expecting_snap = False
        self.icon = None
    def __eq__(self, other):
        return self.uid == other.uid

    def setThumbnail(self, img):
        self.thumbnail = img
        self.texture.update(self.thumbnail)

    def refreshThumbnail(self):
        self.texture = Texture(format = "rgba32f")
        if self.thumbnail:
            self.texture.update(self.thumbnail)