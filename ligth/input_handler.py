import glfw

class InputHandler:
    def __init__(self):
        self.keys = {}

    def key_callback(self, window, key, scancode, action, mods):
        if action == glfw.PRESS:
            self.keys[key] = True
        elif action == glfw.RELEASE:
            self.keys[key] = False

    def process_input(self, window, camera, delta, lightPos, light_speed):
        if self.keys.get(glfw.KEY_ESCAPE):
            glfw.set_window_should_close(window, True)

        move = {
            glfw.KEY_W: "FORWARD", glfw.KEY_S: "BACKWARD",
            glfw.KEY_A: "LEFT",    glfw.KEY_D: "RIGHT",
            glfw.KEY_Q: "DOWN",    glfw.KEY_E: "UP"
        }
        for k, v in move.items():
            if self.keys.get(k):
                camera.move(v, delta)

        if self.keys.get(glfw.KEY_LEFT):  camera.rotate(-delta, 0)
        if self.keys.get(glfw.KEY_RIGHT): camera.rotate(delta, 0)
        if self.keys.get(glfw.KEY_UP):    camera.rotate(0, delta)
        if self.keys.get(glfw.KEY_DOWN):  camera.rotate(0, -delta)
        if self.keys.get(glfw.Z):  camera.rotate(0, -delta)
        if self.keys.get(glfw.C):  camera.rotate(0, -delta)

        if self.keys.get(glfw.KEY_I): lightPos[1] += light_speed * delta
        if self.keys.get(glfw.KEY_K): lightPos[1] -= light_speed * delta
        if self.keys.get(glfw.KEY_J): lightPos[0] -= light_speed * delta
        if self.keys.get(glfw.KEY_L): lightPos[0] += light_speed * delta
        if self.keys.get(glfw.KEY_U): lightPos[2] -= light_speed * delta
        if self.keys.get(glfw.KEY_O): lightPos[2] += light_speed * delta
