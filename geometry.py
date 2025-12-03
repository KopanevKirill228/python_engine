import math
from Math3D import Math3D
from math_utils import compute_face_normal


class Mesh:
    """
    Базовый класс для 3D меша

    Хранит:
    - vertices: список вершин [x, y, z]
    - faces: список граней (индексы вершин)
    - face_normals: нормали граней (вычисляются автоматически)
    """

    def __init__(self, vertices=None, faces=None):
        """
        Инициализация меша

        vertices: список вершин [x, y, z] или None
        faces: список граней (индексы вершин) или None
        """
        self.vertices = vertices if vertices is not None else []
        self.faces = faces if faces is not None else []
        self.face_normals = []

        # Вычисляем нормали, если есть вершины
        if len(self.vertices) > 0:
            self.compute_face_normals()

    def add_vertex(self, x, y, z):
        """
        Добавить вершину в меш

        x, y, z: координаты вершины
        """
        self.vertices.append([x, y, z])

    def add_face(self, *vertex_indices):
        """
        Добавить грань в меш

        *vertex_indices: индексы вершин (обычно 3 для треугольника)
        Пример: add_face(0, 1, 2)
        """
        self.faces.append(list(vertex_indices))

    def compute_face_normals(self):
        """
        Вычислить нормали для всех граней

        Для каждой грани (треугольник):
        1. Берём первые 3 вершины
        2. Вычисляем два ребра: edge1 = v1 - v0, edge2 = v2 - v0
        3. Вычисляем нормаль: normal = edge1 × edge2
        4. Нормализуем результат
        """
        self.face_normals = []

        for face in self.faces:
            # Пропускаем грани с менее чем 3 вершинами
            if len(face) < 3:
                continue

            # Получаем индексы первых трёх вершин (треугольник)
            v0_idx = face[0]
            v1_idx = face[1]
            v2_idx = face[2]

            # Получаем координаты вершин
            v0 = self.vertices[v0_idx]
            v1 = self.vertices[v1_idx]
            v2 = self.vertices[v2_idx]

            # Вычисляем нормаль (используя math_utils)
            normal = compute_face_normal(v0, v1, v2)
            self.face_normals.append(normal)

    def transform(self, transformation_matrix):
        """
        Применить матрицу трансформации ко всем вершинам

        Процесс:
        1. Конвертируем вершину в однородные координаты [x, y, z, 1]
        2. Применяем матрицу: transformed = matrix × vertex
        3. Нормализуем если w != 1
        4. Берём первые 3 компоненты результата
        5. Пересчитываем нормали

        """
        new_vertices = []

        for vertex in self.vertices:
            # Конвертируем в однородные координаты
            v_4d = [vertex[0], vertex[1], vertex[2], 1.0]

            # Применяем трансформацию (явное матричное умножение)
            transformed = Math3D.matrix_vector_multiply(transformation_matrix, v_4d)

            # W-нормализация
            w = transformed[3]
            if abs(w) > 1e-6:
                transformed = [transformed[i] / w for i in range(3)]
            else:
                transformed = transformed[:3]

            new_vertices.append(transformed)

        self.vertices = new_vertices
        self.compute_face_normals()


class Cube(Mesh):


    def __init__(self, size=1.0):
        """Инициализация куба"""
        super().__init__()

        s = size

        # Добавляем 8 вершин куба
        self.add_vertex(-s, -s, -s)  # 0: left-bottom-back
        self.add_vertex(+s, -s, -s)  # 1: right-bottom-back
        self.add_vertex(+s, +s, -s)  # 2: right-top-back
        self.add_vertex(-s, +s, -s)  # 3: left-top-back
        self.add_vertex(-s, -s, +s)  # 4: left-bottom-front
        self.add_vertex(+s, -s, +s)  # 5: right-bottom-front
        self.add_vertex(+s, +s, +s)  # 6: right-top-front
        self.add_vertex(-s, +s, +s)  # 7: left-top-front


        # Смотрим с внешней стороны куба, идём CCW (против часовой стрелки)

        # ВЕРХНЯЯ ГРАНЬ (y = +s, смотрим сверху)
        self.add_face(7, 6, 2)
        self.add_face(7, 2, 3)

        # НИЖНЯЯ ГРАНЬ (y = -s, смотрим снизу)
        self.add_face(0, 1, 5)
        self.add_face(0, 5, 4)

        # ПЕРЕДНЯЯ ГРАНЬ (z = +s, смотрим спереди)
        self.add_face(4, 5, 6)
        self.add_face(4, 6, 7)

        # ЗАДНЯЯ ГРАНЬ (z = -s, смотрим сзади)
        self.add_face(1, 0, 3)
        self.add_face(1, 3, 2)

        # ЛЕВАЯ ГРАНЬ (x = -s, смотрим слева)
        self.add_face(0, 4, 7)
        self.add_face(0, 7, 3)

        # ПРАВАЯ ГРАНЬ (x = +s, смотрим справа)
        self.add_face(5, 1, 2)
        self.add_face(5, 2, 6)

        # После всех add_face()

        # Вычисляем нормали
        self.compute_face_normals()




class Sphere(Mesh):
    """
    Сфера (UV Sphere)

    Генерируется параметрически:
    x = r * sin(θ) * cos(φ)
    y = r * sin(θ) * sin(φ)
    z = r * cos(θ)

    где:
    θ (theta) — угол от северного полюса (0 до π)
    φ (phi) — азимутальный угол (0 до 2π)

    Параметры:
    - radius: радиус сферы
    - latitude_segments: количество сегментов по широте (разбиение по θ)
    - longitude_segments: количество сегментов по долготе (разбиение по φ)
    """

    def __init__(self, radius=1.0, latitude_segments=16, longitude_segments=32):
        """
        Инициализация сферы

        radius: радиус сферы
        latitude_segments: количество горизонтальных сегментов (минимум 3)
        longitude_segments: количество вертикальных сегментов (минимум 4)
        """
        super().__init__()

        # Гарантируем минимальное разбиение
        lat_segs = max(3, latitude_segments)
        lon_segs = max(4, longitude_segments)

        self.generate_uv_sphere(radius, lat_segs, lon_segs)

    def generate_uv_sphere(self, radius, lat_segments, lon_segments):
        """
        Генерировать сферу через параметрическое разбиение

        Процесс:
        1. Создаём сетку вершин по формулам:
           x = r * sin(θ) * cos(φ)
           y = r * sin(θ) * sin(φ)
           z = r * cos(θ)
        2. Соединяем вершины в четырёхугольники
        3. Разбиваем четырёхугольники на два треугольника


        radius: радиус сферы
        lat_segments: разбиение по широте (θ: 0 к π)
        lon_segments: разбиение по долготе (φ: 0 к 2π)
        """

        # Создаём сетку вершин
        vertices_grid = []

        for i in range(lat_segments + 1):
            # θ (theta) — угол от 0 (северный полюс) к π (южный полюс)
            theta = (math.pi * i) / lat_segments
            sin_theta = math.sin(theta)
            cos_theta = math.cos(theta)

            lat_row = []

            for j in range(lon_segments):
                # φ (phi) — азимутальный угол от 0 к 2π
                phi = (2 * math.pi * j) / lon_segments
                sin_phi = math.sin(phi)
                cos_phi = math.cos(phi)

                # Параметрические уравнения сферы
                x = radius * sin_theta * cos_phi
                y = radius * sin_theta * sin_phi
                z = radius * cos_theta

                # Добавляем вершину и запоминаем индекс
                vertex_idx = len(self.vertices)
                self.add_vertex(x, y, z)
                lat_row.append(vertex_idx)

            vertices_grid.append(lat_row)


        for i in range(lat_segments):
            for j in range(lon_segments):
                # Индексы четырёх вершин четырёхугольника
                # ПРАВИЛЬНЫЙ порядок: меняем a и b, d и c
                a = vertices_grid[i][j]
                b = vertices_grid[i + 1][j]  # ← ПОМЕНЯТЬ!
                c = vertices_grid[i + 1][(j + 1) % lon_segments]
                d = vertices_grid[i][(j + 1) % lon_segments]  # ← ПОМЕНЯТЬ!

                # Разбиваем четырёхугольник на два треугольника
                # Оба теперь имеют правильную ориентацию CCW!
                self.add_face(a, b, c)
                self.add_face(a, c, d)

        # Вычисляем нормали
        self.compute_face_normals()


class Torus(Mesh):
    """
    Тор (Torus of Revolution)

    Генерируется параметрически:
    x = (R + r * cos(v)) * cos(u)
    y = (R + r * cos(v)) * sin(u)
    z = r * sin(v)

    где:
    u (0 к 2π) — угол вокруг основной оси (revolve angle)
    v (0 к 2π) — угол вокруг трубки (tube angle)
    R — основной радиус (расстояние от центра до центра трубки)
    r — радиус трубки

    Параметры:
    - major_radius (R): основной радиус тора
    - minor_radius (r): радиус трубки
    - major_segments: разбиение по u (вокруг основной оси)
    - minor_segments: разбиение по v (вокруг трубки)
    """

    def __init__(self, major_radius=2.0, minor_radius=0.8,
                 major_segments=32, minor_segments=16):
        """
        Инициализация тора

        major_radius: основной радиус R
        minor_radius: радиус трубки r
        major_segments: разбиение по азимуту (минимум 8)
        minor_segments: разбиение по углу трубки (минимум 4)
        """
        super().__init__()

        # Гарантируем минимальное разбиение
        maj_segs = max(8, major_segments)
        min_segs = max(4, minor_segments)

        self.generate_torus(major_radius, minor_radius, maj_segs, min_segs)

    def generate_torus(self, R, r, major_segs, minor_segs):
        """
        Генерировать тор через параметрическое разбиение

        Процесс:
        1. Создаём сетку вершин по формулам выше
        2. Для каждой точки вычисляем координаты
        3. Соединяем в четырёхугольники (с периодичностью по u и v)
        4. Разбиваем на треугольники


        R: основной радиус
        r: радиус трубки
        major_segs: разбиение по u
        minor_segs: разбиение по v
        """

        # Создаём сетку вершин
        vertices_grid = []

        for i in range(major_segs):
            # u — угол вокруг основной оси (0 к 2π)
            u = (2 * math.pi * i) / major_segs
            cos_u = math.cos(u)
            sin_u = math.sin(u)

            u_row = []

            for j in range(minor_segs):
                # v — угол вокруг трубки (0 к 2π)
                v = (2 * math.pi * j) / minor_segs
                cos_v = math.cos(v)
                sin_v = math.sin(v)

                # Параметрические уравнения тора
                dist_from_axis = R + r * cos_v

                x = dist_from_axis * cos_u
                y = dist_from_axis * sin_u
                z = r * sin_v

                # Добавляем вершину
                vertex_idx = len(self.vertices)
                self.add_vertex(x, y, z)
                u_row.append(vertex_idx)

            vertices_grid.append(u_row)


        for i in range(major_segs):
            for j in range(minor_segs):
                # Индексы четырёх вершин четырёхугольника
                # ПРАВИЛЬНО: НЕ меняем порядок!
                a = vertices_grid[i][j]
                b = vertices_grid[(i + 1) % major_segs][j]
                c = vertices_grid[(i + 1) % major_segs][(j + 1) % minor_segs]
                d = vertices_grid[i][(j + 1) % minor_segs]

                # Разбиваем четырёхугольник на два треугольника
                # ОБА треугольника имеют одинаковую ориентацию (CCW)!
                self.add_face(a, b, c)
                self.add_face(a, c, d)

        # Вычисляем нормали
        self.compute_face_normals()


class MobiusStrip(Mesh):
    """
    Лента Мёбиуса (Mobius Strip)

    Генерируется параметрически:
    x = (R + t * cos(u/2)) * cos(u)
    y = t * sin(u/2)
    z = (R + t * cos(u/2)) * sin(u)

    где:
    u (0 к 2π) — угол вдоль полосы
    t (-w/2 к w/2) — расстояние от центральной линии
    R — основной радиус
    w — ширина полосы

    Интересное свойство: это одностороння поверхность!
    (нельзя различить «внутри» и «снаружи»)
    """

    def __init__(self, radius=2.0, width=1.0, segments=64):
        """
        Инициализация ленты Мёбиуса

        radius: основной радиус R
        width: ширина полосы w
        segments: количество сегментов по длине (минимум 16)
        """
        super().__init__()

        # Гарантируем минимальное разбиение
        segs = max(16, segments)

        self.generate_mobius(radius, width, segs)

    def generate_mobius(self, R, w, segments):
        """
        Генерировать ленту Мёбиуса

        Ключевое свойство: u идёт от 0 к 4π (не 2π!)
        Это даёт полный оборот ленты на 180° относительно центра.

        R: основной радиус
        w: ширина полосы
        segments: разбиение по длине
        """

        # Параметр width_segments фиксирован (только 2 точки по ширине)
        # Это даёт одну "сторону" полосы
        width_segments = 2

        # Создаём сетку вершин
        vertices_grid = []

        for i in range(segments):
            # u — угол вдоль полосы (0 к 4π для полного оборота!)
            u = (4 * math.pi * i) / segments
            cos_u_half = math.cos(u / 2)
            sin_u_half = math.sin(u / 2)
            cos_u = math.cos(u)
            sin_u = math.sin(u)

            u_row = []

            for j in range(width_segments):
                # t — расстояние от центральной линии (-w/2 к w/2)
                t = (w / 2) * (2 * j / (width_segments - 1) - 1)

                # Параметрические уравнения ленты Мёбиуса
                dist_from_axis = R + t * cos_u_half

                x = dist_from_axis * cos_u
                y = t * sin_u_half
                z = dist_from_axis * sin_u

                # Добавляем вершину
                vertex_idx = len(self.vertices)
                self.add_vertex(x, y, z)
                u_row.append(vertex_idx)

            vertices_grid.append(u_row)


        for i in range(segments):
            for j in range(width_segments - 1):

                a = vertices_grid[i][j]
                b = vertices_grid[(i + 1) % segments][j]
                c = vertices_grid[(i + 1) % segments][j + 1]
                d = vertices_grid[i][j + 1]


                self.add_face(a, b, c)
                self.add_face(a, c, d)

        # Вычисляем нормали
        self.compute_face_normals()


class ParametricSurface(Mesh):
    """
    Параметрическая поверхность (произвольная)

    Позволяет генерировать любую поверхность, заданную двумя параметрами u и v:
    x = f(u, v)
    y = g(u, v)
    z = h(u, v)
    """

    def __init__(self, func, u_range=(0, 2 * math.pi), v_range=(0, 2 * math.pi),
                 u_segments=32, v_segments=32):
        """
        Инициализация параметрической поверхности

        func: функция(u, v) → (x, y, z)
        u_range: диапазон параметра u (u_min, u_max)
        v_range: диапазон параметра v (v_min, v_max)
        u_segments: разбиение по u
        v_segments: разбиение по v
        """
        super().__init__()

        self.generate_parametric(func, u_range, v_range, u_segments, v_segments)

    def generate_parametric(self, func, u_range, v_range, u_segs, v_segs):
        """
        Генерировать параметрическую поверхность
        Процесс:
        1. Разбиваем диапазон u на u_segs сегментов
        2. Разбиваем диапазон v на v_segs сегментов
        3. Для каждой пары (u, v) вычисляем (x, y, z) через func
        4. Соединяем вершины в четырёхугольники
        5. Разбиваем на треугольники
           ⭐ ПРАВИЛЬНЫЙ порядок разбиения!
        """

        u_min, u_max = u_range
        v_min, v_max = v_range

        # Создаём сетку вершин
        vertices_grid = []

        for i in range(u_segs):
            # Интерполируем u в его диапазоне
            u = u_min + (u_max - u_min) * i / (u_segs - 1)

            u_row = []

            for j in range(v_segs):
                # Интерполируем v в его диапазоне
                v = v_min + (v_max - v_min) * j / (v_segs - 1)

                # Вычисляем координаты через функцию
                x, y, z = func(u, v)

                # Добавляем вершину
                vertex_idx = len(self.vertices)
                self.add_vertex(x, y, z)
                u_row.append(vertex_idx)

            vertices_grid.append(u_row)


        for i in range(u_segs - 1):
            for j in range(v_segs - 1):

                a = vertices_grid[i][j]
                b = vertices_grid[i + 1][j]
                c = vertices_grid[i + 1][j + 1]
                d = vertices_grid[i][j + 1]

                self.add_face(a, b, c)
                self.add_face(a, c, d)

        # Вычисляем нормали
        self.compute_face_normals()


# ===== ПРИМЕРЫ ПАРАМЕТРИЧЕСКИХ ПОВЕРХНОСТЕЙ =====

def create_wavy_plane(u, v):
    """
    Волнистая плоскость
    z = sin(x) * cos(y)
    """
    x = u
    y = v
    z = math.sin(u) * math.cos(v)
    return (x, y, z)


def create_hyperboloid(u, v):
    """
    Гиперболоид вращения
    x = u * cos(v)
    y = u * sin(v)
    z = u²
    """
    x = u * math.cos(v)
    y = u * math.sin(v)
    z = u * u
    return (x, y, z)


def create_saddle(u, v):
    """
    Гиперболический параболоид (седло)
    z = x² - y²
    """
    x = u
    y = v
    z = u * u - v * v
    return (x, y, z)


def create_klein_bottle_approximation(u, v):
    """
    Приближение бутылки Клейна
    (точное параметрическое уравнение очень сложное)
    """
    r = 4 * (1 - math.cos(u) / 2)
    x = r * math.cos(u) * math.cos(v)
    y = r * math.sin(u)
    z = r * math.cos(u) * math.sin(v) + 4 * math.sin(u)
    return (x * 0.3, y * 0.3, z * 0.3)


# ===== ГЕНЕРАТОР ГЕОМЕТРИИ (фасад) =====

class GeometryGenerator:
    """
    Фасад для создания различных 3D фигур
    Все методы статические для удобства использования
    """

    @staticmethod
    def cube(size=1.0):
        """Создать куб"""
        return Cube(size)

    @staticmethod
    def sphere(radius=1.0, latitude_segments=16, longitude_segments=32):
        """Создать сферу"""
        return Sphere(radius, latitude_segments, longitude_segments)

    @staticmethod
    def torus(major_radius=2.0, minor_radius=0.8,
              major_segments=32, minor_segments=16):
        """Создать тор"""
        return Torus(major_radius, minor_radius, major_segments, minor_segments)

    @staticmethod
    def mobius_strip(radius=2.0, width=1.0, segments=64):
        """Создать ленту Мёбиуса"""
        return MobiusStrip(radius, width, segments)

    @staticmethod
    def wavy_plane(scale=1.0, u_segments=32, v_segments=32):
        """Создать волнистую плоскость"""

        def scaled_wavy_plane(u, v):
            x, y, z = create_wavy_plane(u * scale, v * scale)
            return (x, y, z * 0.5)

        return ParametricSurface(
            scaled_wavy_plane,
            u_range=(-math.pi, math.pi),
            v_range=(-math.pi, math.pi),
            u_segments=u_segments,
            v_segments=v_segments
        )

    @staticmethod
    def hyperboloid(scale=1.0, u_segments=32, v_segments=32):
        """Создать гиперболоид вращения"""

        def scaled_hyperboloid(u, v):
            x, y, z = create_hyperboloid(u * scale, v)
            return (x, y, z * 0.5)

        return ParametricSurface(
            scaled_hyperboloid,
            u_range=(0.5, 2.5),
            v_range=(0, 2 * math.pi),
            u_segments=u_segments,
            v_segments=v_segments
        )

    @staticmethod
    def saddle(scale=1.0, u_segments=32, v_segments=32):
        """Создать седло (гиперболический параболоид)"""

        def scaled_saddle(u, v):
            x, y, z = create_saddle(u * scale, v * scale)
            return (x, y, z)

        return ParametricSurface(
            scaled_saddle,
            u_range=(-math.pi, math.pi),
            v_range=(-math.pi, math.pi),
            u_segments=u_segments,
            v_segments=v_segments
        )

    @staticmethod
    def klein_bottle(u_segments=32, v_segments=32):
        """Создать приближение бутылки Клейна"""
        return ParametricSurface(
            create_klein_bottle_approximation,
            u_range=(0, 2 * math.pi),
            v_range=(0, 2 * math.pi),
            u_segments=u_segments,
            v_segments=v_segments
        )