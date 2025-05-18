import numpy as np

class Material:
    def __init__(self, ambient, diffuse, specular, shininess):
        self.ambient = ambient.astype(np.float32)
        self.diffuse = diffuse.astype(np.float32)
        self.specular = specular.astype(np.float32)
        self.shininess = shininess
