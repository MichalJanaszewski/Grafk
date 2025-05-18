import math
from OpenGL.GL import *
import numpy as np
import pyrr

class Camera:
    def __init__(self, position, up, yaw, pitch):
        self.position = np.array(position, dtype=np.float32)
        self.world_up = pyrr.Vector3([0.0, 1.0, 0.0])
        self.yaw = yaw
        self.pitch = pitch
        self.orientation = pyrr.Quaternion()
        self.front = pyrr.vector3.create(0.0, 0.0, -1.0)

        self.move_speed = 30.0
        self.rotation_speed = 60.0

        self.sensitivity = 0.1
        self.roll = 0.0

        self.update_vectors()

    def update_vectors(self):
        base_front = pyrr.Vector3([0.0, 0.0, -1.0])
        base_up = pyrr.Vector3([0.0, 1.0, 0.0])

        self.front = pyrr.quaternion.apply_to_vector(self.orientation, base_front)
        self.front = pyrr.vector.normalize(self.front)

        self.up = pyrr.quaternion.apply_to_vector(self.orientation, base_up)
        self.up = pyrr.vector.normalize(self.up)

        self.right = pyrr.vector3.cross(self.front, self.up)
        self.right = pyrr.vector.normalize(self.right)

    def move(self, direction, deltaTime):
        velocity = self.move_speed * deltaTime
        if direction == "FORWARD":  self.position += self.front * velocity
        elif direction == "BACKWARD": self.position -= self.front * velocity
        elif direction == "LEFT":     self.position -= self.right * velocity
        elif direction == "RIGHT":    self.position += self.right * velocity
        elif direction == "UP":       self.position += self.up * velocity
        elif direction == "DOWN":     self.position -= self.up * velocity

    def rotate(self, yaw_offset, pitch_offset, roll_offset=0.0):
        yaw_rad = math.radians(yaw_offset * self.rotation_speed)
        pitch_rad = math.radians(-pitch_offset * self.rotation_speed)
        roll_rad = math.radians(roll_offset * self.rotation_speed)

        self.update_vectors()

        q_yaw = pyrr.quaternion.create_from_axis_rotation(self.up, yaw_rad)
        q_pitch = pyrr.quaternion.create_from_axis_rotation(self.right, pitch_rad)
        q_roll = pyrr.quaternion.create_from_axis_rotation(self.front, roll_rad)

        self.orientation = pyrr.quaternion.cross(q_roll, pyrr.quaternion.cross(q_pitch, pyrr.quaternion.cross(q_yaw, self.orientation)))
        self.orientation = pyrr.quaternion.normalize(self.orientation)



    def get_view_matrix(self):
        self.update_vectors()
        return pyrr.matrix44.create_look_at(
            eye=self.position,
            target=self.position + self.front,
            up=self.up,
            dtype=np.float32
        )
    
