from OpenGL.GL import *
import numpy as np

class ShaderProgram:
    def __init__(self, vertex_path, fragment_path):
        self.program = glCreateProgram()
        vertex_code = open(vertex_path).read()
        fragment_code = open(fragment_path).read()
        self._compile_and_attach(vertex_code, GL_VERTEX_SHADER)
        self._compile_and_attach(fragment_code, GL_FRAGMENT_SHADER)
        glLinkProgram(self.program)

        if not glGetProgramiv(self.program, GL_LINK_STATUS):
            raise RuntimeError(glGetProgramInfoLog(self.program).decode())

    def _compile_and_attach(self, src, shader_type):
        shader = glCreateShader(shader_type)
        glShaderSource(shader, src)
        glCompileShader(shader)
        if not glGetShaderiv(shader, GL_COMPILE_STATUS):
            raise RuntimeError(glGetShaderInfoLog(shader).decode())
        glAttachShader(self.program, shader)
        glDeleteShader(shader)

    def use(self):
        glUseProgram(self.program)

    def set_mat4(self, name, mat):
        glUniformMatrix4fv(glGetUniformLocation(self.program, name), 1, GL_FALSE, mat)

    def set_vec3(self, name, vec):
        glUniform3fv(glGetUniformLocation(self.program, name), 1, vec)

    def set_float(self, name, val):
        glUniform1f(glGetUniformLocation(self.program, name), val)
