import pygame
import numpy as np
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, CLIP_RECT

class Renderer:
    def __init__(self, screen, camera, prisms):
        self.screen = screen
        self.camera = camera
        self.prisms = prisms

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
            return screen_vertices, abs(rotated[:,2])
    
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
    
    def scanline_polygon_fill(self, screen, polygon, zbuffer, color=(255, 255, 255)):
        points = polygon["points"]
        n = len(points)
        if n < 3:
            return

        min_y = max(int(min(p[1] for p in points)), 0)
        max_y = min(int(max(p[1] for p in points)), SCREEN_HEIGHT - 1)

        for y in range(min_y, max_y + 1):
            xz_intersections = []

            for i in range(n):
                j = (i + 1) % n
                x0, y0, z0 = points[i]
                x1, y1, z1 = points[j]

                if y0 == y1 and int(y0) == y:
                    x_start = int(min(x0, x1))
                    x_end = int(max(x0, x1))
                    z_start = z0 if x0 < x1 else z1
                    z_end = z1 if x0 < x1 else z0
                    for x in range(x_start, x_end + 1):
                        t = (x - x_start) / (x_end - x_start + 1e-6)
                        z = z_start + t * (z_end - z_start)
                        if 0 <= x < SCREEN_WIDTH and z < zbuffer[y][x]:
                            zbuffer[y][x] = z
                            screen.set_at((x, y), color)
                    continue

                if y < min(y0, y1) or y >= max(y0, y1):
                    continue

                t = (y - y0) / (y1 - y0 + 1e-6)
                x = x0 + t * (x1 - x0)
                z = z0 + t * (z1 - z0)
                xz_intersections.append((x, z))

            if len(xz_intersections) >= 2:
                xz_intersections.sort()
                for i in range(0, len(xz_intersections), 2):
                    if i + 1 >= len(xz_intersections):
                        break
                    x0, z0 = xz_intersections[i]
                    x1, z1 = xz_intersections[i + 1]
                    x_start = int(x0)
                    x_end = int(x1)
                    for x in range(x_start, x_end + 1):
                        if x1 == x0:
                            z = z0
                        else:
                            t = (x - x0) / (x1 - x0 + 1e-6)
                            z = z0 + t * (z1 - z0)
                        if 0 <= x < SCREEN_WIDTH and z < zbuffer[y][x]:
                            zbuffer[y][x] = z
                            screen.set_at((x, y), color)

    def scanline_render(self, screen, polygons):
        zbuffer = [[float('inf') for _ in range(SCREEN_WIDTH)] for _ in range(SCREEN_HEIGHT)]
        sorted_polygons = sorted(polygons, key=lambda poly: max(p[1] for p in poly["points"]))

        for poly in sorted_polygons:
            self.scanline_polygon_fill(screen, poly, zbuffer, color=poly["color"])


    def render(self):
        self.screen.fill((0, 0, 0))
        polygons = []
        for prism in self.prisms:
            transformed = prism.transformed_vertices()
            screen_verts, z = self.apply_transformations(transformed)
            if screen_verts is None:
                continue
            screen_pts = [(int((v[0] + 1) * 0.5 * SCREEN_WIDTH),
                        int((1 - (v[1] + 1) * 0.5) * SCREEN_HEIGHT))
                        for v in screen_verts if not np.isnan(v).any()]
            pts = np.column_stack((screen_pts, z))
            polygons.append((pts, prism.color))

        polygons = prism.extract_faces(polygons)
        self.scanline_render(self.screen, polygons)
        pygame.display.flip()