import math
import numpy as np

class Sphere:
    def __init__(self, position, material):
        self.position = np.array(position, dtype=np.float32)
        self.material = material

def create_sphere(radius=1.0, sectors=40, stacks=40):
    vertices = []
    normals = []
    for i in range(stacks):
        theta1 = math.pi * i / stacks
        theta2 = math.pi * (i+1) / stacks
        for j in range(sectors):
            phi1 = 2 * math.pi * j / sectors
            phi2 = 2 * math.pi * (j+1) / sectors
            # Współrzędne 4 punktów siatki
            x1 = radius*math.sin(theta1)*math.cos(phi1)
            y1 = radius*math.cos(theta1)
            z1 = radius*math.sin(theta1)*math.sin(phi1)
            x2 = radius*math.sin(theta1)*math.cos(phi2)
            y2 = radius*math.cos(theta1)
            z2 = radius*math.sin(theta1)*math.sin(phi2)
            x3 = radius*math.sin(theta2)*math.cos(phi1)
            y3 = radius*math.cos(theta2)
            z3 = radius*math.sin(theta2)*math.sin(phi1)
            x4 = radius*math.sin(theta2)*math.cos(phi2)
            y4 = radius*math.cos(theta2)
            z4 = radius*math.sin(theta2)*math.sin(phi2)
            # Trójkąt 1
            vertices += [x1,y1,z1, x3,y3,z3, x4,y4,z4]
            normals  += [x1,y1,z1, x3,y3,z3, x4,y4,z4]
            # Trójkąt 2
            vertices += [x1,y1,z1, x4,y4,z4, x2,y2,z2]
            normals  += [x1,y1,z1, x4,y4,z4, x2,y2,z2]
    vertices = np.array(vertices, dtype=np.float32)
    normals = np.array(normals, dtype=np.float32)
    # Normalizacja normalnych
    for i in range(0, len(normals), 3):
        length = np.linalg.norm(normals[i:i+3])
        normals[i:i+3] /= length
    return vertices, normals