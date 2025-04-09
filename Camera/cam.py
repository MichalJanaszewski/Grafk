import pygame
import numpy as np
from scipy.spatial.transform import Rotation as R
import math
import json

# --- Ustawienia ---
SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 900

HOLD_START_DELAY = 400
HOLD_REPEAT_INTERVAL = 50

FOV_DEFAULT = 90
MOVE_SPEED = 1
ROT_SPEED = {
    'x': math.pi / 60,
    'y': math.pi / 40,
    'z': math.pi / 20
}
ZOOM_STEP = 5
FOV_LIMITS = (20, 120)
CLIP_RECT = [0, 0, SCREEN_WIDTH, SCREEN_HEIGHT]


def load_prisms_from_file(path):
    with open(path, 'r') as f:
        data = json.load(f)

    prisms = []
    for item in data:
        size = item.get("size", [1, 1, 1])
        position = item.get("position", [0, 0, 0])
        prisms.append(Prism(size, position))
    return prisms

def perspective_matrix(fov, aspect_ratio, near, far):
    tan_fov = np.tan(np.radians(fov) / 2)
    return np.array([
        [1 / (aspect_ratio * tan_fov),  0,              0,                                  0],
        [0,                             1 / tan_fov,    0,                                  0],
        [0,                             0,              -(far + near) / (far - near),      -1],
        [0,                             0,              -(2 * far * near) / (far - near),   0]
    ], dtype=np.float32)

def create_rectangular_prism(width=1, depth=1, height=1):
    return np.array([
        [-width/2, -height/2, -depth/2, 1],
        [ width/2, -height/2, -depth/2, 1],
        [ width/2,  height/2, -depth/2, 1],
        [-width/2,  height/2, -depth/2, 1],
        [-width/2, -height/2,  depth/2, 1],
        [ width/2, -height/2,  depth/2, 1],
        [ width/2,  height/2,  depth/2, 1],
        [-width/2,  height/2,  depth/2, 1]
    ], dtype=np.float32)

class Camera:
    def __init__(self):
        self.rotation = R.from_quat([0, 0, 0, 1])
        self.fov = FOV_DEFAULT
        self.aspect_ratio = SCREEN_WIDTH / SCREEN_HEIGHT
        self.near = 0.1
        self.far = 100.0

    def translate(self, dx, dy, dz):
        move_vec = np.array([dx, dy, dz, 0], dtype=np.float32)
        inverse_rotation = self.rotation.inv()
        move_vec = inverse_rotation.apply(move_vec[:3])
        
        return move_vec

    def rotate(self, axis_index, angle):
        axis_vector = np.zeros(3)
        axis_vector[axis_index] = 1
        delta_rotation = R.from_rotvec(axis_vector * angle)
        self.rotation = delta_rotation * self.rotation

    def zoom(self, delta):
        self.fov = np.clip(self.fov + delta, *FOV_LIMITS)

    def get_projection_matrix(self):
        return perspective_matrix(self.fov, self.aspect_ratio, self.near, self.far)

    def get_camera_screen_size(self):
        return SCREEN_WIDTH * self.camera_screen_scale, SCREEN_HEIGHT * self.camera_screen_scale

class Prism:
    def __init__(self, size, position):
        self.vertices = create_rectangular_prism(*size)
        self.position = np.array(position)

    def transformed_vertices(self):
        transformed = self.vertices.copy()
        transformed[:, :3] += self.position
        return transformed

class Renderer:
    def __init__(self, screen, camera, prisms):
        self.screen = screen
        self.camera = camera
        self.prisms = prisms
        self.edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),
            (4, 5), (5, 6), (6, 7), (7, 4),
            (0, 4), (1, 5), (2, 6), (3, 7)
        ]

    def apply_transformations(self, vertices):
        rotated = self.camera.rotation.apply(vertices[:, :3])
        rotated = np.hstack((rotated, vertices[:, 3:]))
        projection = self.camera.get_projection_matrix()
        projected = rotated @ projection.T

        w = projected[:, 3]
        if np.all(w <= 0.01):

            return None
        
        valid_mask = np.abs(w) > (0.2)
        w_clamped = np.clip(w, 0.1, None)
        screen_vertices = np.full_like(projected[:, :2], np.nan)
        screen_vertices[valid_mask] = projected[valid_mask, :2] / w_clamped[valid_mask, None]

        return screen_vertices

    def cohen_sutherland_clip(self, p1, p2, clip_rect):
        def compute_code(x, y, rect):
            code = 0
            if y > rect[3]:
                code |= 0x8
            elif y < rect[1]:
                code |= 0x4
            if x > rect[2]:
                code |= 0x2
            elif x < rect[0]:
                code |= 0x1
            return code

        code1 = compute_code(p1[0], p1[1], clip_rect)
        code2 = compute_code(p2[0], p2[1], clip_rect)

        while True:
            if code1 == 0 and code2 == 0:
                return [p1, p2]
            
            elif (code1 & code2) != 0:
                return None
            
            else:
                x, y = 0, 0
                code_out = code1 if code1 != 0 else code2

                if code_out & 0x8:
                    x = p1[0] + (p2[0] - p1[0]) * (clip_rect[3] - p1[1]) / (p2[1] - p1[1])
                    y = clip_rect[3]
                elif code_out & 0x4:
                    x = p1[0] + (p2[0] - p1[0]) * (clip_rect[1] - p1[1]) / (p2[1] - p1[1])
                    y = clip_rect[1]
                elif code_out & 0x2:
                    y = p1[1] + (p2[1] - p1[1]) * (clip_rect[2] - p1[0]) / (p2[0] - p1[0])
                    x = clip_rect[2]
                elif code_out & 0x1:
                    y = p1[1] + (p2[1] - p1[1]) * (clip_rect[0] - p1[0]) / (p2[0] - p1[0])
                    x = clip_rect[0]

                if code_out == code1:
                    p1 = [x, y]
                    code1 = compute_code(p1[0], p1[1], clip_rect)
                else:
                    p2 = [x, y]
                    code2 = compute_code(p2[0], p2[1], clip_rect)

    def render(self):
        self.screen.fill((0, 0, 0))
        for prism in self.prisms:
            transformed = prism.transformed_vertices()
            screen_verts = self.apply_transformations(transformed)
            if screen_verts is None:
                continue
            screen_pts = [(int((v[0] + 1) * 0.5 * SCREEN_WIDTH),
                        int((1 - (v[1] + 1) * 0.5) * SCREEN_HEIGHT))
                        for v in screen_verts if not np.isnan(v).any()]

            for edge in self.edges:
                try:
                    p1 = screen_pts[edge[0]]
                    p2 = screen_pts[edge[1]]
                    if not any(np.isnan(p1)) and not any(np.isnan(p2)):
                        clipped_edge = self.cohen_sutherland_clip(p1, p2, CLIP_RECT)
                        if clipped_edge:
                            pygame.draw.line(self.screen, (255, 255, 255), clipped_edge[0], clipped_edge[1], 2)
                except IndexError:
                    continue

        pygame.display.flip()

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    camera = Camera()
    prisms = load_prisms_from_file("prisms.json")
    renderer = Renderer(screen, camera, prisms)

    renderer.render()

    key_map = {
        pygame.K_LEFT: lambda: camera.rotate(1, -ROT_SPEED['y']),
        pygame.K_RIGHT: lambda: camera.rotate(1, ROT_SPEED['y']),
        pygame.K_UP: lambda: camera.rotate(0, -ROT_SPEED['x']),
        pygame.K_DOWN: lambda: camera.rotate(0, +ROT_SPEED['x']),
        pygame.K_z: lambda: camera.rotate(2, ROT_SPEED['z']),
        pygame.K_c: lambda: camera.rotate(2, -ROT_SPEED['z']),
        pygame.K_w: lambda: shift_prisms(prisms, camera.translate(0, 0, MOVE_SPEED)),
        pygame.K_s: lambda: shift_prisms(prisms, camera.translate(0, 0, -MOVE_SPEED)),
        pygame.K_a: lambda: shift_prisms(prisms, camera.translate(MOVE_SPEED, 0, 0)),
        pygame.K_d: lambda: shift_prisms(prisms, camera.translate(-MOVE_SPEED, 0, 0)),
        pygame.K_q: lambda: shift_prisms(prisms, camera.translate(0, MOVE_SPEED, 0)),
        pygame.K_e: lambda: shift_prisms(prisms, camera.translate(0, -MOVE_SPEED, 0)),
        pygame.K_EQUALS: lambda: camera.zoom(-ZOOM_STEP),
        pygame.K_MINUS: lambda: camera.zoom(ZOOM_STEP),
    }

    key_states = {
        key: {
            "pressed": False,
            "start_time": 0,
            "last_repeat": 0
        } for key in key_map
    }

    running = True
    while running:
        dt = clock.tick(60)
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in key_map and not key_states[event.key]["pressed"]:
                    key_map[event.key]()
                    key_states[event.key]["pressed"] = True
                    key_states[event.key]["start_time"] = current_time
                    key_states[event.key]["last_repeat"] = current_time
                    renderer.render()
            elif event.type == pygame.KEYUP:
                if event.key in key_states:
                    key_states[event.key]["pressed"] = False

        keys = pygame.key.get_pressed()
        any_action = False

        for key, state in key_states.items():
            if state["pressed"] and keys[key]:
                if current_time - state["start_time"] > HOLD_START_DELAY:
                    if current_time - state["last_repeat"] > HOLD_REPEAT_INTERVAL:
                        key_map[key]()
                        state["last_repeat"] = current_time
                        any_action = True

        if any_action:
            renderer.render()

    pygame.quit()

def shift_prisms(prisms, vec):
    for prism in prisms:
        prism.position += vec

if __name__ == "__main__":
    main()