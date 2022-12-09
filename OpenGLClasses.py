from OpenGL.GL import *
from OpenGL.GLUT import *
from itertools import count
import numpy as np

"""All classes here are fairly straightforward implementations of standard OpenGL objects. Some notes:
in Texture/Framebuffer constructor there is a format parameter, which can be any of 'rgbu16', 'ru16', or 'rgba32f'.
For vertex and index buffers, the input vertices/indices data has to be a default python list [x1, y1, z1, x2, y2, ...] 
or [face11, face12, face13, face21, face22, etc.] (for vertex resp. index buffers)
All classes have bind() and unbind()* functions. (* no unbind for Texture). Texture.bind(slot) takes an argument, 
int slot, to allow binding to any texture slot. When doing so, remember to set glActiveTexture(GL_TEXTURE0) later on 
whenever necessary.

"""


class Texture:
    idGenerator = count()
    """Texture takes one of three (for now) possible formats: rgbu16, ru16, or rgba32f"""
    def __init__(self, format = "ru16"):
        self.uid = next(Texture.idGenerator)
        self.renderer_id = glGenTextures(1)
        self.width = 0
        self.height = 0
        self.internalformat = GL_R16UI
        self.format = GL_RED_INTEGER
        self.type = GL_UNSIGNED_SHORT
        if format == "rgbu16":
            self.internalformat = GL_RGB_INTEGER
            self.format = GL_RGB
            self.type = GL_UNSIGNED_SHORT
        if format == "rgba32f":
            self.internalformat = GL_RGBA
            self.format = GL_RGBA
            self.type = GL_FLOAT
        glBindTexture(GL_TEXTURE_2D, self.renderer_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    def bind(self, slot = 0):
        glActiveTexture(GL_TEXTURE0 + int(slot))
        glBindTexture(GL_TEXTURE_2D, self.renderer_id)

    def update(self, pixeldata, width = None, height = None):
        self.bind()
        if width:
            self.width = width
        if height:
            self.height = height
        else:
            self.width = np.shape(pixeldata)[0]
            self.height = np.shape(pixeldata)[1]
        if pixeldata is None:
            glTexImage2D(GL_TEXTURE_2D, 0, self.internalformat, self.width, self.height, 0, self.format, self.type, None)
        else:
            imgdata = pixeldata.flatten().astype(np.uint16)
            glTexImage2D(GL_TEXTURE_2D, 0, self.internalformat, self.width, self.height, 0, self.format, self.type, imgdata)


class Shader:
    """Uniforms can only be uploaded when Shaders is first manually bound by user."""
    def __init__(self, sourcecode):
        self.shaderProgram = glCreateProgram()
        self.compile(sourcecode)

    def compile(self, sourcecode):
        shaderStages = dict()
        shaderObjects = list()
        currentStage = None
        # Parse source into individual shader stages' source code
        with open(sourcecode, 'r') as source:
            for line in source:
                if "#vertex" in line:
                    currentStage = GL_VERTEX_SHADER
                    shaderStages[currentStage] = ""
                elif "#fragment" in line:
                    currentStage = GL_FRAGMENT_SHADER
                    shaderStages[currentStage] = ""
                elif "#geometry" in line:
                    currentStage = GL_GEOMETRY_SHADER
                    shaderStages[currentStage] = ""
                elif "#compute" in line:
                    currentStage = GL_COMPUTE_SHADER
                    shaderStages[currentStage] = ""
                else:
                    shaderStages[currentStage] += line
        # Compile stages
        for key in shaderStages:
            shaderObjects.append(glCreateShader(key))
            glShaderSource(shaderObjects[-1], shaderStages[key])
            glCompileShader(shaderObjects[-1])
            status = glGetShaderiv(shaderObjects[-1], GL_COMPILE_STATUS)
            if status == GL_FALSE:
                if key == GL_VERTEX_SHADER:
                    strShaderType = "vertex"
                elif key == GL_FRAGMENT_SHADER:
                    strShaderType = "fragment"
                elif key == GL_GEOMETRY_SHADER:
                    strShaderType = "geometry"
                elif key == GL_COMPUTE_SHADER:
                    strShaderType = "compute"
                raise RuntimeError("Shaders compilation failure for type "+strShaderType+":\n" + glGetShaderInfoLog(shaderObjects[-1]).decode('utf-8'))
            glAttachShader(self.shaderProgram, shaderObjects[-1])
        glLinkProgram(self.shaderProgram)
        status = glGetProgramiv(self.shaderProgram, GL_LINK_STATUS)
        if status == GL_FALSE:
            raise RuntimeError("Shaders link failure:\n"+glGetProgramInfoLog(self.shaderProgram).decode('utf-8'))
        for shader in shaderObjects:
            glDetachShader(self.shaderProgram, shader)
            glDeleteShader(shader)

    def bind(self):
        glUseProgram(self.shaderProgram)

    def unbind(self):
        glUseProgram(0)

    def uniform1f(self, uniformName, uniformFloatValue):
        uniformLocation = glGetUniformLocation(self.shaderProgram, uniformName)
        glUniform1f(uniformLocation, uniformFloatValue)

    def uniform1i(self, uniformName, uniformIntValue):
        uniformLocation = glGetUniformLocation(self.shaderProgram, uniformName)
        glUniform1i(uniformLocation, uniformIntValue)

    def uniform3f(self, uniformName, uniformFloat3Value):
        uniformLocation = glGetUniformLocation(self.shaderProgram, uniformName)
        glUniform3f(uniformLocation, uniformFloat3Value[0], uniformFloat3Value[1], uniformFloat3Value[2])

    def uniformmat4(self, uniformName, uniformMat4):
        uniformLocation = glGetUniformLocation(self.shaderProgram, uniformName)
        glUniformMatrix4fv(uniformLocation, 1, GL_TRUE, uniformMat4)

class VertexBuffer:
    """Not that vertices must be a default 1d python list. In __init__ it is cast into the required shape."""
    def __init__(self, vertices):
        self.vertexBufferObject = glGenBuffers(1)
        self.vertices = np.asarray([[vertices]], dtype = np.float32)
        self.floatcount = len(vertices)
        glBindBuffer(GL_ARRAY_BUFFER, self.vertexBufferObject)
        glBufferData(GL_ARRAY_BUFFER, self.vertices, GL_STATIC_DRAW)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def bind(self):
        glBindBuffer(self.vertexBufferObject)

    def unbind(self):
        glBindBuffer(0)

class IndexBuffer:
    """Note that indices must be a default python list. It is turned in to a np.array along the 2nd dimension with type np.uint16 before sending to GPU"""
    def __init__(self, indices):
        self.indexBufferObject = glGenBuffers(1)
        self.indices = np.asarray([indices], dtype = np.uint16)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.indexBufferObject)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices, GL_STATIC_DRAW)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

    def bind(self):
        glBindBuffer(self.indexBufferObject)

    def unbind(self):
        glBindBuffer(0)

    def getCount(self):
        return self.indices.size


class VertexArray:
    def __init__(self, vertexBuffer, indexBuffer):
        self.vertexBuffer = vertexBuffer
        self.indexBuffer = indexBuffer
        self.vertexArrayObject = glGenVertexArrays(1)
        glBindVertexArray(self.vertexArrayObject)
        glBindBuffer(GL_ARRAY_BUFFER, vertexBuffer.vertexBufferObject)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, indexBuffer.indexBufferObject)
        glBindVertexArray(0)


    def bind(self):
        glBindVertexArray(self.vertexArrayObject)

    def unbind(self):
        glBindVertexArray(0)


class FrameBuffer:
    """For now, FrameBuffers have one texture (COLOR and DEPTH) only."""
    def __init__(self, width, height):
        # Set up internal parameters
        self.width = width
        self.height = height
        # Set up texture
        self.texture = Texture(format = "rgba32f")
        self.texture.bind()
        self.texture.update(None, self.width, self.height)
        glBindTexture(GL_TEXTURE_2D, 0)
        # Set up depth render buffer
        self.depthRenderbuffer = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, self.depthRenderbuffer)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT, self.width, self.height)
        glBindRenderbuffer(GL_RENDERBUFFER, 0)
        # Set up frame buffer
        self.framebufferObject = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.framebufferObject)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.texture.renderer_id, 0)
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, self.depthRenderbuffer)

        if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
            raise RuntimeError("Framebuffer binding failed, GPU probably does not support this configuration.")
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def clear(self, color):
        glBindFramebuffer(GL_FRAMEBUFFER, self.framebufferObject)
        glClearColor(color[0], color[1], color[2], 1.0)
        glClearDepth(1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def bind(self):
        glBindFramebuffer(GL_FRAMEBUFFER, self.framebufferObject)

    def unbind(self):
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

