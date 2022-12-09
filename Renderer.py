from OpenGLClasses import *
from OpenGL.GL import *
from OpenGL.GLU import *
import Channel
import GUI_Config as cfg
channelShader = None
screenShader = None
vertexArray = None
FBO_A = None
FBO_B = None
FBO_pingpong = 0
FBO_width = 2048
FBO_height = 2048
modelMatrix = None
cameraMatrix = None
viewMatrix = None
projectionMatrix = None
import Bookmark
import Parameters as prm
from PIL import Image, ImageOps
import IconLib

def Init():
    global screenShader, channelShader, vertexArray, FBO_A, FBO_B, screenViewVertexArray
    screenShader = Shader("C:/Users/mgflast/PycharmProjects/Cryoscope v2/Shaders/toScreenShader.glsl")
    channelShader = Shader("C:/Users/mgflast/PycharmProjects/Cryoscope v2/Shaders/primaryShader.glsl")
    vertices = [-1.0, 1.0, 1.0, -1.0, -1.0, 1.0, 1.0, -1.0, 1.0, 1.0, 1.0, 1.0]
    indices = [0, 1, 2, 2, 0, 3]
    vertexBuffer = VertexBuffer(vertices)
    indexBuffer = IndexBuffer(indices)
    vertexArray = VertexArray(vertexBuffer, indexBuffer)
    FBO_A = FrameBuffer(FBO_width, FBO_height)
    FBO_B = FrameBuffer(FBO_width, FBO_height)
    IconLib.Init()

def RenderPrimaryView(channelList):
    global FBO_pingpong
    FBO_pingpong = 0
    FBO_A.clear((0.0, 0.0, 0.0))
    FBO_B.clear((0.0, 0.0, 0.0))

    def _renderChannel(channel):
        global FBO_pingpong
        renderFBO = None
        sampleFBO = None
        if FBO_pingpong == 0:
            renderFBO = FBO_A
            sampleFBO = FBO_B
            FBO_pingpong = 1
        else:
            renderFBO = FBO_B
            sampleFBO = FBO_A
            FBO_pingpong = 0

        # Bind FBO to render to
        renderFBO.bind()
        # Bind VAO
        vertexArray.bind()
        # Bind shader and upload uniforms
        channelShader.bind()
        channelShader.uniform1f("contrastMin", float(channel.contrast_min))
        channelShader.uniform1f("contrastMax", float(channel.contrast_max))
        channelShader.uniform3f("channelColor", channel.color)
        # Bind channel texture to slot 0 for sampling
        channel.texture.bind(0)
        # Bind texture of the other FBO to slot 1 for sampling
        sampleFBO.texture.bind(1)

        glDrawElements(GL_TRIANGLES, vertexArray.indexBuffer.getCount(), GL_UNSIGNED_SHORT, None)
        channelShader.unbind()
        vertexArray.unbind()
        renderFBO.unbind()
        glActiveTexture(GL_TEXTURE0)


    def _renderFBOtoScreen():
        global FBO_pingpong, modelMatrix, cameraMatrix
        # First find out which FBO has the final image.
        finalFBO = None
        if FBO_pingpong == 0:
            finalFBO = FBO_B
        else:
            finalFBO = FBO_A

        # Bind VAO
        vertexArray.bind()
        # Bind shader and upload uniforms
        screenShader.bind()
        screenShader.uniform1f("xMin", cfg.screenView_xRange[0])
        screenShader.uniform1f("xMax", cfg.screenView_xRange[1])
        screenShader.uniform1f("yMin", cfg.screenView_yRange[0])
        screenShader.uniform1f("yMax", cfg.screenView_yRange[1])
        modelMatrix = GetModelMatrix()
        cameraMatrix = GetCameraMatrix()
        screenShader.uniformmat4("mMat", modelMatrix)
        screenShader.uniformmat4("vpMat", cameraMatrix)
        screenShader.uniform1f("roi0", prm.roi[0] / prm.sensorSize)
        screenShader.uniform1f("roi1", prm.roi[1] / prm.sensorSize)
        screenShader.uniform1f("roi2", prm.roi[2] / prm.sensorSize)
        screenShader.uniform1f("roi3", prm.roi[3] / prm.sensorSize)
        finalFBO.texture.bind(0)
        glDrawElements(GL_TRIANGLES, vertexArray.indexBuffer.getCount(), GL_UNSIGNED_SHORT, None)
        screenShader.unbind()
        vertexArray.unbind()
        glActiveTexture(GL_TEXTURE0)
    # First render all channels into one image, stored in a frame buffer.
    glViewport(0, 0, cfg.defaultTextureSize[0], cfg.defaultTextureSize[1])
    for channel in channelList:
        if channel.show and channel.enable and not channel.repeater:
            _renderChannel(channel)

    # Then render this framebuffer to the screen. For this we reset the viewport size and need a camera matrix.
    glViewport(0, 0, cfg.width, cfg.height)

    _renderFBOtoScreen()

    # After rendering stream, render icons.
    # for bookmark in prm.bookmarks:
    #     if bookmark.icon:
    #         bookmark.icon.render(cameraMatrix)

def CopyCurrentImageToBookmark(bookmark):
    global FBO_pingpong
    # First find out which FBO has the final image.
    finalFBO = None
    if FBO_pingpong == 0:
        finalFBO = FBO_B
    else:
        finalFBO = FBO_A
    finalFBO.bind()
    glReadBuffer(GL_COLOR_ATTACHMENT0)
    bookmark.texture.bind(0)
    glCopyTexImage2D(GL_TEXTURE_2D, 0, bookmark.texture.internalformat, 0, 0, FBO_width, FBO_height, 0)
    finalFBO.unbind()

def GetCameraMatrix():
    global projectionMatrix, viewMatrix
    def _orthographicMatrix(l, r, b, t, n, f):
        dx = r - l
        dy = t - b
        dz = f - n
        rx = -(r + l) / (r - l)
        ry = -(t + b) / (t - b)
        rz = -(f + n) / (f - n)
        return np.matrix([[2.0 / dx, 0, 0, rx],
                          [0, 2.0 / dy, 0, ry],
                          [0, 0, -2.0 / dz, rz],
                          [0, 0, 0, 1]])

    translationMatrix = np.matrix([
        [1.0, 0.0, 0.0, -prm.currentPosition[0] - (1.0 - 2.0 * cfg.screenView_flipHorizontal) * cfg.cameraOffsetX / cfg.cameraZoom],
        [0.0, 1.0, 0.0, -prm.currentPosition[1] - (1.0 - 2.0 * cfg.screenView_flipVertical) * cfg.cameraOffsetY / cfg.cameraZoom],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0]])
    zoomMatrix = np.matrix([
        [cfg.cameraZoom, 0.0, 0.0, 1.0],
        [0.0, cfg.cameraZoom, 0.0, 1.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ])
    viewMatrix = np.matmul(zoomMatrix, translationMatrix)
    projection_Vertical = (1.0 - 2.0 * cfg.screenView_flipVertical) * cfg.height
    proejction_Horizontal = (1.0 - 2.0 * cfg.screenView_flipHorizontal) * cfg.width
    projectionMatrix = _orthographicMatrix(-proejction_Horizontal, proejction_Horizontal, -projection_Vertical, projection_Vertical, -100, 100)
    cameraMatrix = np.matmul(projectionMatrix, viewMatrix)

    return cameraMatrix

def GetModelMatrix():
    translationMatrix = np.matrix([
        [1.0, 0.0, 0.0, prm.currentPosition[0]],
        [0.0, 1.0, 0.0, prm.currentPosition[1]],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0]])
    totalZoom = cfg.screenView_base_zoom * cfg.screenView_zoom
    scaleMatrix = np.matrix(
        [[totalZoom * 1000.0, 0.0, 0.0, 0.0], [0.0, totalZoom * 1000.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0],
         [0.0, 0.0, 0.0, 1.0]])
    return np.matmul(translationMatrix, scaleMatrix)