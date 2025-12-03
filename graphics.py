import math

import math
import pygame
from Math3D import Math3D
from math_utils import LambertLighting, bresenham_line, compute_face_normal, is_face_visible
from parameters import (
    ENABLE_BACKFACE_CULLING, ENABLE_DEPTH_SORTING, ENABLE_WIREFRAME,
    CAMERA_FOV, CAMERA_Z, LIGHT_DIRECTION, AMBIENT_INTENSITY
)


class Renderer:
    """Рендерер 3D графики с Z-Buffer алгоритмом (без сортировки)"""

    def __init__(self, width, height, fov=CAMERA_FOV, camera_z=CAMERA_Z):

        self.width = width
        self.height = height
        self.camera_z = camera_z
        self._fov = fov

        self.screen = pygame.display.get_surface()
        self.lighting = LambertLighting(light_direction=LIGHT_DIRECTION,
                                        ambient_intensity=AMBIENT_INTENSITY)

        # Z-Buffer: для каждого пикселя храним ближайшую глубину
        self.z_buffer = [[float('inf')] * width for _ in range(height)]

        self._update_projection_matrix()

    def _update_projection_matrix(self):
        """Пересчитать матрицу проекции на основе текущего FOV"""
        fov_rad = math.radians(self._fov)
        aspect = self.width / self.height
        self.projection_matrix = Math3D.perspective_projection(fov_rad, aspect, 0.1, 100)

    @property
    def fov(self):
        return self._fov

    @fov.setter
    def fov(self, value):
        if self._fov != value:
            self._fov = value
            self._update_projection_matrix()

    def project_vertex(self, vertex_world):
        """
        Спроецировать 3D вершину в 2D координаты экрана
        Возвращает (x_screen, y_screen, z_ndc)
        """
        # ШАГ 1: Трансформируем в camera space
        vertex_shifted = [
            vertex_world[0],
            vertex_world[1],
            vertex_world[2] - self.camera_z
        ]

        # ШАГ 2: 4D координаты (вручную, просто добавляем w=1.0)
        v_4d = [vertex_shifted[0], vertex_shifted[1], vertex_shifted[2], 1.0]

        # ШАГ 3: Projection матрица (через Math3D)
        projected = Math3D.matrix_vector_multiply(self.projection_matrix, v_4d)

        # ШАГ 4: W-деление
        w = projected[3]
        if w < 0.001:
            return None

        x_ndc = projected[0] / w
        y_ndc = projected[1] / w
        z_ndc = projected[2] / w

        # Проверяем near/far plane
        if z_ndc < -1.0 or z_ndc > 1.0:
            return None

        # ШАГ 5: NDC → Screen space
        x_screen = (x_ndc + 1.0) * self.width / 2.0
        y_screen = (1.0 - y_ndc) * self.height / 2.0

        return (x_screen, y_screen, z_ndc)

    def _copy_mesh(self, mesh):
        """Скопировать меш"""
        new_mesh = type(mesh).__new__(type(mesh))

        new_mesh.vertices = [list(v) for v in mesh.vertices]
        new_mesh.faces = [list(f) for f in mesh.faces]
        new_mesh.face_normals = [list(n) for n in mesh.face_normals]

        return new_mesh

    def _transform_vertex(self, vertex, transform_matrix):
        """Применить матрицу трансформации к вершине (через Math3D)"""
        v_4d = [vertex[0], vertex[1], vertex[2], 1.0]
        result = Math3D.matrix_vector_multiply(transform_matrix, v_4d)
        return [result[0], result[1], result[2]]

    def _recalculate_normals(self, mesh):
        """Пересчитать нормали после трансформации (используя math_utils)"""
        mesh.face_normals = []

        for face in mesh.faces:
            if len(face) < 3:
                continue

            # Берём первые 3 вершины
            v0 = mesh.vertices[face[0]]
            v1 = mesh.vertices[face[1]]
            v2 = mesh.vertices[face[2]]

            # Используем compute_face_normal из math_utils
            normal = compute_face_normal(v0, v1, v2)
            mesh.face_normals.append(normal)

    def render_mesh(self, mesh, transform_matrix, custom_ambient=None):
        """Основной метод рендеринга меша с Z-Buffer (БЕЗ сортировки)"""
        render_mesh = self._copy_mesh(mesh)

        # Трансформируем вершины
        for i in range(len(render_mesh.vertices)):
            render_mesh.vertices[i] = self._transform_vertex(
                render_mesh.vertices[i], transform_matrix
            )

        # Пересчитываем нормали
        self._recalculate_normals(render_mesh)

        triangles_to_render = []
        culled_count = 0
        projected_ok = 0
        projected_fail = 0
        clipped_count = 0

        # Позиция камеры в world space
        camera_pos = [0.0, 0.0, self.camera_z]

        for face_idx, face in enumerate(render_mesh.faces):
            if face_idx >= len(render_mesh.face_normals):
                continue

            face_normal = render_mesh.face_normals[face_idx]

            # Вычисляем центр грани через Math3D.vector_add и масштабирование
            v0 = render_mesh.vertices[face[0]]
            v1 = render_mesh.vertices[face[1]]
            v2 = render_mesh.vertices[face[2]]

            # Используем Math3D методы для суммы
            sum_v = Math3D.vector_add(v0, v1)
            sum_v = Math3D.vector_add(sum_v, v2)

            # Масштабируем на 1/3
            face_center = Math3D.vector_scale(sum_v, 1.0 / 3.0)

            # Back Face Culling (используем is_face_visible из math_utils)
            if ENABLE_BACKFACE_CULLING:
                if not is_face_visible(face_normal, face_center, camera_pos):
                    culled_count += 1
                    continue

            # Вычисляем освещение (используем LambertLighting из math_utils)
            brightness = self.lighting.calculate_lighting(face_normal)

            # Проецируем вершины
            projected_vertices = []
            skip_face = False

            for vertex_idx in face[:3]:
                v = render_mesh.vertices[vertex_idx]
                proj_v = self.project_vertex(v)

                if proj_v is None:
                    projected_fail += 1
                    skip_face = True
                    break

                projected_vertices.append(proj_v)
                projected_ok += 1

            if skip_face or len(projected_vertices) < 3:
                clipped_count += 1
                continue

            triangles_to_render.append({
                'vertices': projected_vertices,
                'brightness': brightness
            })

        # БЕЗ СОРТИРОВКИ
        # Рендеруем в произвольном порядке - Z-Buffer
        # Очистить Z-buffer перед рендерингом - O(width * height)
        for row in self.z_buffer:
            for i in range(len(row)):
                row[i] = float('inf')

        # Растеризовать БЕЗ предварительной сортировки - O(n)
        self._rasterize_triangles(triangles_to_render)

    def _compute_barycentric_z(self, x, y, p1, p2, p3, z1, z2, z3):
        """
        Вычислить интерполированную Z координату в точке (x, y)
        внутри треугольника p1-p2-p3 с Z значениями z1, z2, z3

        Используем барицентрические координаты:
        z_interpolated = u*z1 + v*z2 + w*z3
        где u + v + w = 1
        """

        # Вычисляем знаки для барицентрических координат
        # sign = (px - bx) * (ay - by) - (ax - bx) * (py - by)

        def sign(px, py, ax, ay, bx, by):
            """Вычислить знак для точки относительно ребра"""
            return (px - bx) * (ay - by) - (ax - bx) * (py - by)

        # Вычисляем площадь треугольника (удвоенную через cross product)
        d1 = sign(x, y, p1[0], p1[1], p2[0], p2[1])
        d2 = sign(x, y, p2[0], p2[1], p3[0], p3[1])
        d3 = sign(x, y, p3[0], p3[1], p1[0], p1[1])

        # Полная площадь треугольника (удвоенная)
        area_doubled = sign(p1[0], p1[1], p2[0], p2[1], p3[0], p3[1])

        # Защита от деления на ноль
        if abs(area_doubled) < 0.0001:
            return (z1 + z2 + z3) / 3.0

        # Барицентрические координаты (нормализованные)
        u = d1 / area_doubled  # относительный вес вершины 1
        v = d2 / area_doubled  # относительный вес вершины 2
        w = d3 / area_doubled  # относительный вес вершины 3

        # Интерполируем Z через барицентрические координаты
        z_interpolated = u * z1 + v * z2 + w * z3

        return z_interpolated

    def _fill_triangle_with_z_interpolation(self, screen_coords, color, z_coords):
        """
        Заполнить треугольник с интерполяцией Z значений

        screen_coords: список из 3 кортежей (x, y)
        color: (r, g, b)
        z_coords: список из 3 значений Z для каждой вершины
        """

        p1 = (int(screen_coords[0][0]), int(screen_coords[0][1]))
        p2 = (int(screen_coords[1][0]), int(screen_coords[1][1]))
        p3 = (int(screen_coords[2][0]), int(screen_coords[2][1]))

        z1, z2, z3 = z_coords[0], z_coords[1], z_coords[2]

        # Bounding box (оптимизированный поиск min/max)
        min_x = min(p1[0], p2[0], p3[0])
        max_x = max(p1[0], p2[0], p3[0])
        min_y = min(p1[1], p2[1], p3[1])
        max_y = max(p1[1], p2[1], p3[1])

        # Обрезка по границам экрана
        min_x = max(0, min_x)
        max_x = min(self.width - 1, max_x)
        min_y = max(0, min_y)
        max_y = min(self.height - 1, max_y)

        def sign(px, py, ax, ay, bx, by):
            """Вычислить знак для точки относительно ребра"""
            return (px - bx) * (ay - by) - (ax - bx) * (py - by)

        # Проходим по всем пикселям в bounding box
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                d1 = sign(x, y, p1[0], p1[1], p2[0], p2[1])
                d2 = sign(x, y, p2[0], p2[1], p3[0], p3[1])
                d3 = sign(x, y, p3[0], p3[1], p1[0], p1[1])

                has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
                has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)

                # Если точка внутри треугольника
                if not (has_neg and has_pos):
                    # ===== Z-BUFFER ПРОВЕРКА С ИНТЕРПОЛЯЦИЕЙ =====
                    interpolated_z = self._compute_barycentric_z(
                        x, y, p1, p2, p3, z1, z2, z3
                    )

                    # Пишем пиксель если он ближе всех предыдущих
                    if interpolated_z < self.z_buffer[y][x]:
                        self.z_buffer[y][x] = interpolated_z
                        self.screen.set_at((x, y), color)

    def _rasterize_triangles(self, triangles):
        """
        Растеризовать и отрисовать треугольники БЕЗ предварительной сортировки
        Z-Buffer автоматически обеспечит правильный порядок
        """

        for tri in triangles:
            vertices = tri['vertices']
            brightness = tri['brightness']

            # Вычисляем цвет на основе яркости
            r = min(255, int(brightness))
            g = min(255, int(brightness // 2))
            b = min(255, int(255 - brightness // 2))
            color = (r, g, b)

            if len(vertices) >= 3:
                screen_coords = [(v[0], v[1]) for v in vertices]
                z_coords = [v[2] for v in vertices]  # Извлекаем Z для интерполяции

                # Заливаем треугольник с Z-интерполяцией
                self._fill_triangle_with_z_interpolation(screen_coords, color, z_coords)

                # Рисуем контур через Брезенхэм если нужен wireframe
                if ENABLE_WIREFRAME:
                    wireframe_color = (30, 30, 30)
                    # Используем bresenham_line из math_utils
                    for i in range(3):
                        p1 = screen_coords[i]
                        p2 = screen_coords[(i + 1) % 3]
                        # bresenham_line - из math_utils
                        line_points = bresenham_line(
                            int(p1[0]), int(p1[1]),
                            int(p2[0]), int(p2[1])
                        )
                        for point in line_points:
                            if 0 <= point[0] < self.width and 0 <= point[1] < self.height:
                                self.screen.set_at(point, wireframe_color)


class DebugRenderer(Renderer):
    """Рендерер с отладочной информацией"""
    pass