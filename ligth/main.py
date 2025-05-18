import sys
import math
import glfw
import numpy as np
from OpenGL.GL import *
from pyrr import matrix44

from camera import Camera
from input_handler import InputHandler
from sphere import create_sphere, Sphere
from material import Material
from shader import ShaderProgram

WIDTH, HEIGHT = 800, 600
if not glfw.init():
    print("Nie można zainicjalizować GLFW")
    sys.exit(1)
glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

window = glfw.create_window(WIDTH, HEIGHT, "Phong Lighting", None, None)
if not window:
    glfw.terminate()
    print("Nie można utworzyć okna GLFW")
    sys.exit(1)
glfw.make_context_current(window)

camera = Camera((0, 1, 30), (0, 1, 0), yaw=-90, pitch=0)
input_handler = InputHandler()
glfw.set_key_callback(window, input_handler.key_callback)

shader = ShaderProgram("shaders/vertex_shader.glsl", "shaders/fragment_shader.glsl")

vertices, normals = create_sphere(radius=1.0, sectors=25, stacks=25)
vao = glGenVertexArrays(1)
vbo = glGenBuffers(2)

glBindVertexArray(vao)

glBindBuffer(GL_ARRAY_BUFFER, vbo[0])
glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
glEnableVertexAttribArray(0)

glBindBuffer(GL_ARRAY_BUFFER, vbo[1])
glBufferData(GL_ARRAY_BUFFER, normals.nbytes, normals, GL_STATIC_DRAW)
glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, None)
glEnableVertexAttribArray(1)

glBindVertexArray(0)

# Light
lightPos = np.array([5.0, 5.0, 5.0], dtype=np.float32)
light_speed = 5.0

lightAmbient = np.array([0.3, 0.3, 0.3], dtype=np.float32)
lightDiffuse = np.array([6.0, 6.0, 6.0], dtype=np.float32)
lightSpecular = np.array([3.0, 3.0, 3.0], dtype=np.float32)

def create_spheres(poz_y, base_color):
    num_spheres = 5
    start_x = -12.0
    end_x = 12.0

    ambient = base_color * 0.3  

    for i in range(num_spheres):
        t = i / (num_spheres - 1)

        position = (start_x + (end_x - start_x) * t, poz_y, 0.0)

        if i == 0:
            diffuse = base_color * 0.2
            specular = np.array([1.0, 1.0, 1.0])
            shininess = 512.0
        elif i == num_spheres - 1:
            diffuse = base_color * 1.5
            specular = np.array([0.0, 0.0, 0.0])
            shininess = 1.0
        else:
            specular_strength = 1.0 - t
            diffuse_strength = 0.2 + 1.3 * t
            diffuse = base_color * diffuse_strength
            specular = np.array([1.0, 1.0, 1.0]) * specular_strength
            shininess = 256.0 * specular_strength + 1.0 * (1 - specular_strength)

        mat = Material(ambient, diffuse, specular, shininess)
        spheres.append(Sphere(position, mat))

red = np.array([0.4, 0.1, 0.1], dtype=np.float32)
green = np.array([0.1, 0.4, 0.1], dtype=np.float32)
blue = np.array([0.1, 0.1, 0.4], dtype=np.float32)
spheres = []

y_poz = 5

create_spheres(0, red)
create_spheres(y_poz, blue)
create_spheres(-y_poz, green)

glEnable(GL_DEPTH_TEST)
last_time = glfw.get_time()

while not glfw.window_should_close(window):
    current_time = glfw.get_time()
    delta = current_time - last_time
    last_time = current_time

    input_handler.process_input(window, camera, delta, lightPos, light_speed)

    glClearColor(0.1, 0.1, 0.1, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    shader.use()
    view = camera.get_view_matrix()
    proj = matrix44.create_perspective_projection_matrix(45.0, WIDTH / HEIGHT, 0.1, 100.0)

    shader.set_mat4("view", view)
    shader.set_mat4("projection", proj)
    shader.set_vec3("viewPos", camera.position)

    shader.set_vec3("light.position", lightPos)
    shader.set_vec3("light.ambient", lightAmbient)
    shader.set_vec3("light.diffuse", lightDiffuse)
    shader.set_vec3("light.specular", lightSpecular)

    glBindVertexArray(vao)
    for sph in spheres:
        model = matrix44.create_from_translation(sph.position)
        shader.set_mat4("model", model)

        mat = sph.material
        shader.set_vec3("material.ambient", mat.ambient)
        shader.set_vec3("material.diffuse", mat.diffuse)
        shader.set_vec3("material.specular", mat.specular)
        shader.set_float("material.shininess", mat.shininess)

        glDrawArrays(GL_TRIANGLES, 0, len(vertices) // 3)
    glBindVertexArray(0)

    glfw.swap_buffers(window)
    glfw.poll_events()

glDeleteVertexArrays(1, [vao])
glDeleteBuffers(2, vbo)
glDeleteProgram(shader.program)
glfw.terminate()
