import sys
import math
import glfw
from OpenGL.GL import *
import numpy as np
from camera import Camera
from sphere import *

try:
    import pyrr
except ImportError:
    print("Program wymaga pyrr (pip install pyrr)")
    sys.exit(1)

# Ustawienia okna
WIDTH, HEIGHT = 800, 600
if not glfw.init():
    print("Nie można zainicjalizować GLFW")
    sys.exit(1)
glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
window = glfw.create_window(WIDTH, HEIGHT, "Phong Lighting Example", None, None)
if not window:
    glfw.terminate()
    print("Nie można utworzyć okna GLFW")
    sys.exit(1)
glfw.make_context_current(window)
glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)  # chowanie kursora

# Wczytanie shaderów (GLSL 3.3) – vertex przesuwa wierzchołki, fragment oblicza Phonga
vertex_src = """
#version 330 core
layout(location=0) in vec3 a_position;
layout(location=1) in vec3 a_normal;
uniform mat4 model, view, projection;
out vec3 FragPos;
out vec3 Normal;
void main(){
    FragPos = vec3(model * vec4(a_position, 1.0));
    Normal  = mat3(transpose(inverse(model))) * a_normal;
    gl_Position = projection * view * vec4(FragPos, 1.0);
}
"""
fragment_src = """
#version 330 core
struct Material { vec3 ambient, diffuse, specular; float shininess; };
struct Light { vec3 position, ambient, diffuse, specular; };
in vec3 FragPos, Normal;
out vec4 FragColor;
uniform vec3 viewPos;
uniform Material material;
uniform Light light;
void main(){
    // Ambient
    vec3 ambient = light.ambient * material.ambient;
    // Diffuse
    vec3 norm = normalize(Normal);
    vec3 lightDir = normalize(light.position - FragPos);
    float diff = max(dot(norm, lightDir), 0.0);
    vec3 diffuse = light.diffuse * (diff * material.diffuse);
    // Specular
    vec3 viewDir = normalize(viewPos - FragPos);
    vec3 reflectDir = reflect(-lightDir, norm);
    float spec = pow(max(dot(viewDir, reflectDir), 0.0), material.shininess);
    vec3 specular = light.specular * (spec * material.specular);
    vec3 result = ambient + diffuse + specular;
    FragColor = vec4(result, 1.0);
}
"""
# Kompilacja shaderów
def compile_shader(src, shader_type):
    shader = glCreateShader(shader_type)
    glShaderSource(shader, src); glCompileShader(shader)
    if not glGetShaderiv(shader, GL_COMPILE_STATUS):
        print("Błąd kompilacji shader:", glGetShaderInfoLog(shader).decode())
        sys.exit(1)
    return shader

shader_prog = glCreateProgram()    
vs = compile_shader(vertex_src, GL_VERTEX_SHADER)
fs = compile_shader(fragment_src, GL_FRAGMENT_SHADER)
glAttachShader(shader_prog, vs); glAttachShader(shader_prog, fs)
glLinkProgram(shader_prog)
if not glGetProgramiv(shader_prog, GL_LINK_STATUS):
    print("Błąd linkowania programów:", glGetProgramInfoLog(shader_prog))
    sys.exit(1)
glDeleteShader(vs); glDeleteShader(fs)

# Utworzenie kuli i VAO/VBO
vertices, normals = create_sphere(radius=1.0, sectors=40, stacks=40)
vao = glGenVertexArrays(1)
vbo = glGenBuffers(2)
glBindVertexArray(vao)
# Bufor wierzchołków
glBindBuffer(GL_ARRAY_BUFFER, vbo[0])
glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
glEnableVertexAttribArray(0)
# Bufor normalnych
glBindBuffer(GL_ARRAY_BUFFER, vbo[1])
glBufferData(GL_ARRAY_BUFFER, normals.nbytes, normals, GL_STATIC_DRAW)
glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, None)
glEnableVertexAttribArray(1)
glBindVertexArray(0)


# Parametry światła
lightPos = np.array([5.0, 5.0, 5.0], dtype=np.float32)
lightAmbient = np.array([0.2, 0.2, 0.2], dtype=np.float32)
lightDiffuse = np.array([1.0, 1.0, 1.0], dtype=np.float32)
lightSpec  = np.array([1.0, 1.0, 1.0], dtype=np.float32)
light_speed = 5.0  #
# Cztery kule z różnymi materiałami
base_color = np.array([0.85, 0.95, 0.65], dtype=np.float32)
ambient = base_color * 0.1

spheres = []
num_spheres = 9
start_x = -12.0
end_x = 12.0

for i in range(num_spheres):
    t = i / (num_spheres - 1)  # od 0 do 1

    # Ekstremalne wartości
    diffuse_strength = 0.05 + 0.95 * t     # od 0.05 do 1.0
    specular_strength = 1.0 - t            # od 1.0 do 0.0

    diffuse = base_color * diffuse_strength
    specular = np.array([1.0, 1.0, 1.0]) * specular_strength  # biały refleks

    shininess = 256.0 * (1.0 - t) + t

    position = (start_x + (end_x - start_x) * t, 0.0, 0.0)

    spheres.append(Sphere(position, ambient, diffuse, specular, shininess))
    
camera = Camera((0,1,30), (0,1,0), yaw=-90, pitch=0)

# Zmienne do czasu (dla stałej prędkości ruchu)
last_time = glfw.get_time()
keys = {}
def key_callback(window, key, scancode, action, mods):
    global keys
    if action == glfw.PRESS: keys[key] = True
    elif action == glfw.RELEASE: keys[key] = False

    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)

glfw.set_key_callback(window, key_callback)

glEnable(GL_DEPTH_TEST)

# Główna pętla renderowania
while not glfw.window_should_close(window):
    current_time = glfw.get_time()
    delta = current_time - last_time
    last_time = current_time
    # Obsługa ruchu kamery (WSAD)

    # Przykład
    if keys.get(glfw.KEY_W): camera.move("FORWARD", delta)
    if keys.get(glfw.KEY_S): camera.move("BACKWARD", delta)
    if keys.get(glfw.KEY_A): camera.move("LEFT", delta)
    if keys.get(glfw.KEY_D): camera.move("RIGHT", delta)
    if keys.get(glfw.KEY_E): camera.move("UP", delta)
    if keys.get(glfw.KEY_Q): camera.move("DOWN", delta)

    # Rotacja
    if keys.get(glfw.KEY_Z): camera.rotate(0, 0, delta)    # roll w prawo
    if keys.get(glfw.KEY_C): camera.rotate(0, 0, -delta)   # roll w lewo
    if keys.get(glfw.KEY_LEFT):  camera.rotate(-delta, 0)  # yaw w lewo
    if keys.get(glfw.KEY_RIGHT): camera.rotate(delta, 0)   # yaw w prawo
    if keys.get(glfw.KEY_UP):    camera.rotate(0,  delta)   # pitch w górę
    if keys.get(glfw.KEY_DOWN):  camera.rotate(0, -delta)  # pitch w dół

    # Ruch światła
    if keys.get(glfw.KEY_I): lightPos[1] += light_speed * delta  # w górę (Y+)
    if keys.get(glfw.KEY_K): lightPos[1] -= light_speed * delta  # w dół (Y-)
    if keys.get(glfw.KEY_J): lightPos[0] -= light_speed * delta  # w lewo (X-)
    if keys.get(glfw.KEY_L): lightPos[0] += light_speed * delta  # w prawo (X+)
    if keys.get(glfw.KEY_U): lightPos[2] -= light_speed * delta  # bliżej (Z-)
    if keys.get(glfw.KEY_O): lightPos[2] += light_speed * delta  # dalej (Z+)

    # Czyszczenie ekranu
    glClearColor(0.1, 0.1, 0.1, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glUseProgram(shader_prog)
    # Obliczenie macierzy widoku i projekcji
    view = camera.get_view_matrix()
    proj = pyrr.matrix44.create_perspective_projection_matrix(45.0, WIDTH/HEIGHT, 0.1, 100.0, dtype=np.float32)
    glUniformMatrix4fv(glGetUniformLocation(shader_prog, "view"), 1, GL_FALSE, view)
    glUniformMatrix4fv(glGetUniformLocation(shader_prog, "projection"), 1, GL_FALSE, proj)
    # Jedno źródło światła – ustawienie uniformów
    glUniform3fv(glGetUniformLocation(shader_prog, "light.position"), 1, lightPos)
    glUniform3fv(glGetUniformLocation(shader_prog, "light.ambient"),  1, lightAmbient)
    glUniform3fv(glGetUniformLocation(shader_prog, "light.diffuse"),  1, lightDiffuse)
    glUniform3fv(glGetUniformLocation(shader_prog, "light.specular"), 1, lightSpec)
    glUniform3fv(glGetUniformLocation(shader_prog, "viewPos"), 1, camera.position)
    # Rysowanie kul
    glBindVertexArray(vao)
    for sph in spheres:
        # Macierz modelu – przesunięcie kuli
        model = pyrr.matrix44.create_from_translation(sph.position, dtype=np.float32)
        glUniformMatrix4fv(glGetUniformLocation(shader_prog, "model"), 1, GL_FALSE, model)
        # Ustawienie parametrów materiału dla aktualnej kuli
        glUniform3fv(glGetUniformLocation(shader_prog, "material.ambient"), 1, sph.ambient)
        glUniform3fv(glGetUniformLocation(shader_prog, "material.diffuse"), 1, sph.diffuse)
        glUniform3fv(glGetUniformLocation(shader_prog, "material.specular"),1, sph.specular)
        glUniform1f( glGetUniformLocation(shader_prog, "material.shininess"), sph.shininess)
        # Rysuj wszystkie wierzchołki kuli (GL_TRIANGLES)
        glDrawArrays(GL_TRIANGLES, 0, len(vertices)//3)
    glBindVertexArray(0)
    glfw.swap_buffers(window)
    glfw.poll_events()

glfw.terminate()
