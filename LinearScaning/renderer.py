import pygame
import numpy as np
from constants import SCREEN_WIDTH, SCREEN_HEIGHT
from collections import defaultdict

class Renderer:
    def __init__(self, screen, camera, prisms):
        self.screen = screen
        self.camera = camera
        self.prisms = prisms

    def rotate_to_camera(self, vertices):
        rotated = self.camera.rotation.apply(vertices[:, :3])
        rotated = np.hstack((rotated, vertices[:, 3:]))

        return rotated


    def apply_transformations(self, vertices):
            projection = self.camera.get_projection_matrix()
            projected = vertices @ projection.T

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


    def scanline_polygon_fill(self, img_buffer, polygon, zbuffer):
        points = polygon["points"]
        color = polygon["color"]
        n = len(points)
        if n < 3:
            return

        min_y = max(int(min(p[1] for p in points)), 0)
        max_y = min(int(max(p[1] for p in points)), SCREEN_HEIGHT - 1)

        for y in range(min_y, max_y + 1):
            xz_intersections = []
            z_row = zbuffer[y]
            img_row = img_buffer[y]

            for i in range(n):
                j = (i + 1) % n
                x0, y0, z0 = points[i]
                x1, y1, z1 = points[j]
                if y0 == y1 and int(y0) == y:
                    x_start = int(min(x0, x1))
                    x_end = int(max(x0, x1))

                    if x_end < 0 or x_start >= SCREEN_WIDTH:
                        continue 

                    x_start = max(x_start, 0)
                    x_end = min(x_end, SCREEN_WIDTH - 1)

                    if x1 != x0:
                        dz = (z1 - z0) / (x1 - x0 + 1e-6)
                    else:
                        dz = 0

                    z = z0 + (x_start - x0) * dz

                    for x in range(x_start, x_end + 1):
                        if z < z_row[x]:
                            z_row[x] = z
                            img_row[x] = color
                        z += dz
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

                    ix0 = max(int(x0), 0)
                    ix1 = min(int(x1), SCREEN_WIDTH - 1)

                    if x1 != x0:
                        dz = (z1 - z0) / (x1 - x0 + 1e-6)
                    else:
                        dz = 0

                    z = z0 + (ix0 - x0) * dz

                    for x in range(ix0, ix1 + 1):
                        if z < z_row[x]:
                            z_row[x] = z
                            img_row[x] = color
                        z += dz

    def scanline_render(self, polygons):
        zbuffer = np.full((SCREEN_HEIGHT, SCREEN_WIDTH), np.inf, dtype=np.float32)
        img_buffer = np.zeros((SCREEN_HEIGHT, SCREEN_WIDTH, 3), dtype=np.uint8)

        for poly in sorted(polygons, key=lambda poly: max(p[1] for p in poly["points"])):
            self.scanline_polygon_fill(img_buffer, poly, zbuffer)

        pygame.surfarray.blit_array(self.screen, np.transpose(img_buffer, (1, 0, 2)))
        pygame.display.flip()

    
    def render(self):
        polygons = []
        for prism in self.prisms:
            transformed = prism.transformed_vertices()
            faces = prism.extract_faces([(transformed, prism.color)])

            for face in faces:
                verts = np.array(face["points"])
                if len(verts) < 3:
                    continue
                verts = self.rotate_to_camera(verts)
                z = abs(verts[:,2])
                normal = np.cross(verts[1][:3] - verts[0][:3], verts[2][:3] - verts[0][:3])
                if np.dot(normal, verts[0][:3]) > 0:
                    continue
                            
                screen_verts = self.apply_transformations(verts)
                if screen_verts is None or np.isnan(screen_verts).all():
                    continue

                valid_mask = ~np.isnan(screen_verts).any(axis=1)
                screen_pts = [(int((v[0] + 1) * 0.5 * SCREEN_WIDTH),
                            int((1 - (v[1] + 1) * 0.5) * SCREEN_HEIGHT))
                            for v in screen_verts[valid_mask]]
                z = z[valid_mask]
                if len(screen_pts) == len(z) and len(z) >= 3:
                    pts = np.column_stack((screen_pts, z))
                    polygons.append({
                        "points": pts,
                        "color": face["color"]
                    })
        self.scanline_render(polygons)