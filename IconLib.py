from OpenGLClasses import *
from itertools import count
from PIL import Image
import numpy as np

IconTextures = dict()
IconTextures["pin"] = "Icons/pinIcon.png"
IconShader = None
IconVAO = None

def Init():
    global IconShader, IconVAO, IconTextureIDs
    IconShader = Shader("Shaders/iconShader.glsl")
    vertices = [-1.0, 1.0, 1.0, -1.0, -1.0, 1.0, 1.0, -1.0, 1.0, 1.0, 1.0, 1.0]
    indices = [0, 1, 2, 2, 0, 3]
    IconVAO = VertexArray(VertexBuffer(vertices), IndexBuffer(indices))
    for iconType in IconTextures:
        iconPng = Image.open(IconTextures[iconType]).convert("RGBA")
        pixelData = np.asarray(iconPng)
        IconTextures[iconType] = Texture(format = "rgba32f")
        IconTextures[iconType].update(pixelData)

class Icon:
    idGenerator = count(0)

    def __init__(self, position, icon):
        self.id = next(Icon.idGenerator)
        self.position = position
        self.texture = IconTextures[icon]
        self.color = (1.0, 1.0, 1.0)
        self.size = 100.0

    def render(self, cameraMatrix):
        IconVAO.bind()
        IconShader.bind()
        IconShader.uniform3f("color", self.color)
        translationMatrix = np.matrix([
        [1.0, 0.0, 0.0, self.position[0]],
        [0.0, 1.0, 0.0, self.position[1]],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0]])
        scaleMatrix = np.matrix([
            [self.size, 0.0, 0.0, 0.0],
            [0.0, self.size, 0.0, 0.0],
            [0.0, 0.0, self.size, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ])
        IconShader.uniformmat4("mMat", np.matmul(translationMatrix, scaleMatrix))
        IconShader.uniformmat4("vpMat", cameraMatrix)
        self.texture.bind(0)
        glDrawElements(GL_TRIANGLES, IconVAO.indexBuffer.getCount(), GL_UNSIGNED_SHORT, None)
        IconShader.unbind()
        IconVAO.unbind()

