import numpy as np
import json
from constants import SCREEN_WIDTH, SCREEN_HEIGHT

class Prism:
    def __init__(self, size, position, color = (255, 255, 255)):
        self.vertices = self.create_rectangular_prism(*size)
        self.position = np.array(position)
        self.color = color
        self.edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),
            (4, 5), (5, 6), (6, 7), (7, 4),
            (0, 4), (1, 5), (2, 6), (3, 7)
        ]

    def get_edge_points(self, edge):
        return self.vertices[edge[0], :3], self.vertices[edge[1], :3]

    @staticmethod
    def load_prisms_from_file(path):
        with open(path, 'r') as f:
            data = json.load(f)

        prisms = []
        for item in data:
            size = item.get("size", [1, 1, 1])
            position = item.get("position", [0, 0, 0])
            color = item.get("color", (255, 255, 255))
            prisms.append(Prism(size, position, color))
        return prisms
    
    @staticmethod
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
    
    @staticmethod
    def extract_faces(shapes):
        face_indices = [
            (0, 3, 2, 1),
            (4, 5, 6, 7),
            (0, 1, 5, 4),
            (2, 3, 7, 6),
            (0, 4, 7, 3),
            (1, 2, 6, 5), 
        ]
        polygons = []
        for pts, color in shapes: 
            
            for face in face_indices:
                polygon = {
                    "points": [pts[i] for i in face],
                    "color": color
                }
                polygons.append(polygon)

        return polygons


    def transformed_vertices(self):
        transformed = self.vertices.copy()
        transformed[:, :3] += self.position
        return transformed