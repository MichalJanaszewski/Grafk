from constants import SCREEN_WIDTH, SCREEN_HEIGHT, FOV_DEFAULT, FOV_LIMITS
from scipy.spatial.transform import Rotation as R
import numpy as np

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

    def perspective_matrix(self, fov, aspect_ratio, near, far):
        tan_fov = np.tan(np.radians(fov) / 2)
        return np.array([
            [1 / (aspect_ratio * tan_fov),  0,              0,                                  0],
            [0,                             1 / tan_fov,    0,                                  0],
            [0,                             0,              -(far + near) / (far - near),      -1],
            [0,                             0,              -(2 * far * near) / (far - near),   0]
        ], dtype=np.float32)

    def zoom(self, delta):
        self.fov = np.clip(self.fov + delta, *FOV_LIMITS)

    def get_projection_matrix(self):
        return self.perspective_matrix(self.fov, self.aspect_ratio, self.near, self.far)

    def get_camera_screen_size(self):
        return SCREEN_WIDTH * self.camera_screen_scale, SCREEN_HEIGHT * self.camera_screen_scale