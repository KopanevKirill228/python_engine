
import math
from Math3D import Math3D


def bresenham_line(x0, y0, x1, y1):
    """
    Алгоритм Брезенхема для рисования линии

    Алгоритм инкрементальный, использует целые числа и вычитание ошибки.
    Сложность: O(max(dx, dy))

    Математика:
    1. Вычисляем dx = |x1 - x0|, dy = |y1 - y0|
    2. Инициализируем ошибку: err = dx - dy
    3. На каждом шаге:
       - Рисуем точку (x, y)
       - Вычисляем ошибку: e2 = 2 * err
       - Если e2 > -dy, сдвигаем x на sx, вычитаем dy из ошибки
       - Если e2 < dx, сдвигаем y на sy, добавляем dx к ошибке

    x0, y0: начальная точка
    x1, y1: конечная точка
    Возвращает: список точек (x, y) вдоль линии
    """
    points = []

    # Вычисляем дельта координат
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)

    # Определяем направление движения
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1

    # Инициализируем ошибку
    err = dx - dy

    # Текущая позиция
    x, y = x0, y0

    while True:
        # Добавляем текущую точку
        points.append((int(x), int(y)))

        # Проверяем, достигли ли конца
        if x == x1 and y == y1:
            break

        # Вычисляем удвоенную ошибку
        e2 = 2 * err

        # Движение по X
        if e2 > -dy:
            err -= dy
            x += sx

        # Движение по Y
        if e2 < dx:
            err += dx
            y += sy

    return points


class LambertLighting:
    """
    Модель освещения Ламберта (диффузное освещение)

    Формула:
    I = ambient + (1 - ambient) * max(0, normal · light_direction) чтоб пересвета не было хах

    Где:
    - ambient: фоновое освещение [0, 1]
    - normal: нормаль поверхности
    - light_direction: направление источника света
    """

    def __init__(self, light_direction=None, ambient_intensity=0.3):
        """
        Инициализация источника света

        light_direction: вектор направления света [x, y, z]
        ambient_intensity: фоновая интенсивность [0, 1]
        """
        if light_direction is None:
            light_direction = [0, 0, 1]

        # Нормализуем направление света
        self.light_direction = Math3D.vector_normalize(light_direction)

        # Фоновое освещение
        self.ambient = max(0.0, min(1.0, ambient_intensity))

    def calculate_lighting(self, surface_normal, max_brightness=255):
        """
        Вычислить интенсивность света для грани

        Процесс:
        1. Нормализуем нормаль поверхности
        2. Вычисляем скалярное произведение: normal · light_direction
        3. Берём максимум с 0 (свет только спереди)
        4. Вычисляем итоговую яркость: ambient + diffuse * (1 - ambient)
        5. Преобразуем в диапазон [0, 255]

        surface_normal: нормаль грани [x, y, z]
        max_brightness: максимальная яркость в RGB (обычно 255)
        Возвращает: интенсивность [0, max_brightness]
        """
        # Нормализуем нормаль
        normal = Math3D.vector_normalize(surface_normal)

        # Вычисляем косинус угла между нормалью и светом
        # Скалярное произведение двух нормализованных векторов = cos(угол)
        cos_angle = Math3D.vector_dot(normal, self.light_direction)

        # Диффузная компонента (только если свет спереди: cos_angle > 0)
        diffuse = max(0.0, cos_angle)

        # Общая интенсивность = фон + диффузная часть
        # Если diffuse = 0 (свет сзади), интенсивность = ambient
        # Если diffuse = 1 (свет спереди), интенсивность = 1.0
        total_intensity = self.ambient + diffuse * (1.0 - self.ambient)

        # Clamп в [0, 1]
        total_intensity = max(0.0, min(1.0, total_intensity))

        # Преобразуем в диапазон [0, max_brightness]
        result = int(total_intensity * max_brightness)

        # Гарантируем диапазон [0, 255]
        return max(0, min(255, result))


def compute_face_normal(v0, v1, v2):
    """
    Вычислить нормаль грани по трём вершинам

    Процесс:
    1. Вычисляем два ребра грани:
       edge1 = v1 - v0
       edge2 = v2 - v0
    2. Вычисляем нормаль как кросс-произведение:
       normal = edge1 × edge2
    3. Нормализуем результат

    Порядок вершин (CCW/CW) определяет направление нормали!

    v0, v1, v2: вершины грани (списки или кортежи [x, y, z])
    Возвращает: нормализованный вектор нормали [x, y, z]
    """
    # Вычисляем два ребра
    edge1 = Math3D.vector_subtract(v1, v0)
    edge2 = Math3D.vector_subtract(v2, v0)

    # Кросс-произведение даёт нормаль
    normal = Math3D.vector_cross(edge1, edge2)

    # Нормализуем результат
    return Math3D.vector_normalize(normal)


def is_face_visible(face_normal, face_center, camera_position):
    """
    Проверить, видима ли грань (backface culling)

    Математика:
    1. Вычисляем вектор от центра грани к камере
    2. Нормализуем его
    3. Проверяем: если скалярное произведение > 0,
       нормаль смотрит в сторону камеры → грань видима

    Параметры:
    - face_normal: нормаль грани [x, y, z] (предполагается нормализованной)
    - face_center: центр грани [x, y, z]
    - camera_position: позиция камеры [x, y, z]

    Возвращает: True если грань видима, False если скрыта
    """
    # Вычисляем направление от грани к камере
    to_camera = Math3D.vector_subtract(camera_position, face_center)

    # ✅ НОРМАЛИЗУЕМ вектор
    to_camera = Math3D.vector_normalize(to_camera)

    # Скалярное произведение
    dot_product = Math3D.vector_dot(face_normal, to_camera)

    # Грань видима если нормаль смотрит в сторону камеры
    # Используем небольшой эпсилон для надежности
    return dot_product > -1e-6


def compute_triangle_center(v0, v1, v2):
    """
    Вычислить центр (барицентр) треугольника

    Математика: center = (v0 + v1 + v2) / 3

    v0, v1, v2: вершины треугольника [x, y, z]
    Возвращает: центр треугольника [x, y, z]
    """
    center = [0.0, 0.0, 0.0]

    for i in range(3):
        center[i] = (v0[i] + v1[i] + v2[i]) / 3.0

    return center


def point_in_triangle_2d(p, v0, v1, v2):
    """
    Проверить, находится ли точка внутри треугольника (2D)

    Используется алгоритм барицентрических координат

    p, v0, v1, v2: точки [x, y]
    Возвращает: True если точка внутри, False если снаружи
    """

    def sign(p1, p2, p3):
        return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])

    d1 = sign(p, v0, v1)
    d2 = sign(p, v1, v2)
    d3 = sign(p, v2, v0)

    has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
    has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)

    return not (has_neg and has_pos)



def barycentric_interpolation(v0, v1, v2, p):
    """
    Вычислить барицентрические координаты точки p относительно треугольника v0-v1-v2

    Возвращает кортеж (w0, w1, w2) такой что:
    p = w0*v0 + w1*v1 + w2*v2
    w0 + w1 + w2 = 1.0

    v0, v1, v2: вершины треугольника [x, y, z]
    p: интерполируемая точка [x, y, z]
    Возвращает: кортеж (w0, w1, w2) — веса для интерполяции
    """
    # Вычисляем два ребра
    edge0 = Math3D.vector_subtract(v1, v0)
    edge1 = Math3D.vector_subtract(v2, v0)
    edge2 = Math3D.vector_subtract(p, v0)

    # Скалярные произведения
    dot00 = Math3D.vector_dot(edge0, edge0)
    dot01 = Math3D.vector_dot(edge0, edge1)
    dot02 = Math3D.vector_dot(edge0, edge2)
    dot11 = Math3D.vector_dot(edge1, edge1)
    dot12 = Math3D.vector_dot(edge1, edge2)

    # Вычисляем барицентрические координаты
    inv_denom = 1.0 / (dot00 * dot11 - dot01 * dot01)
    w1 = (dot11 * dot02 - dot01 * dot12) * inv_denom
    w2 = (dot00 * dot12 - dot01 * dot02) * inv_denom
    w0 = 1.0 - w1 - w2

    return (w0, w1, w2)


def rasterize_triangle_barycentric(triangle_points, color, surface):
    """
    Растеризовать треугольник методом барицентрических координат

    Ручная математика:
    1. Вычислить площадь основного треугольника (через cross product)
    2. Для каждого пикселя в bounding box:
       - Вычислить площади подтреугольников (через sign функцию)
       - Вычислить барицентрические координаты λ1, λ2, λ3
       - Если все λi >= 0, пиксель внутри → закрасить
    """

    if len(triangle_points) < 3:
        return

    p1 = (int(triangle_points[0][0]), int(triangle_points[0][1]))
    p2 = (int(triangle_points[1][0]), int(triangle_points[1][1]))
    p3 = (int(triangle_points[2][0]), int(triangle_points[2][1]))

    # ===== ШАГ 1: Bounding Box (ручная вычисление min/max) =====
    min_x = min(p1[0], p2[0], p3[0])
    max_x = max(p1[0], p2[0], p3[0])
    min_y = min(p1[1], p2[1], p3[1])
    max_y = max(p1[1], p2[1], p3[1])

    # Обрезка по границам экрана (ручная проверка)
    min_x = max(0, min_x)
    max_x = min(surface.get_width() - 1, max_x)
    min_y = max(0, min_y)
    max_y = min(surface.get_height() - 1, max_y)

    # ===== ШАГ 2: Вычислить знак для барицентрических координат =====
    def sign(px, py, ax, ay, bx, by):
        """
        Вычислить знак точки (px, py) относительно ребра (ax, ay) -> (bx, by)
        Используя cross product (вектор):

        v1 = (bx - ax, by - ay)  [вектор ребра]
        v2 = (px - ax, py - ay)  [вектор от начала ребра к точке]

        cross = v1.x * v2.y - v1.y * v2.x

        Это эквивалентно:
        (px - bx) * (ay - by) - (ax - bx) * (py - by)
        """
        return (px - bx) * (ay - by) - (ax - bx) * (py - by)

    # ===== ШАГ 3: Предвычислить ориентацию треугольника =====
    # Проверяем, ориентирован ли треугольник по часовой или против часовой
    orientation = sign(p1[0], p1[1], p2[0], p2[1], p3[0], p3[1])

    # ===== ШАГ 4: Проход по всем пикселям в bounding box =====
    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            # Вычислить знаки для трёх рёбер
            d1 = sign(x, y, p1[0], p1[1], p2[0], p2[1])
            d2 = sign(x, y, p2[0], p2[1], p3[0], p3[1])
            d3 = sign(x, y, p3[0], p3[1], p1[0], p1[1])

            # Проверить, находится ли точка внутри треугольника
            # Для этого все знаки должны быть одного знака
            if orientation > 0:
                # Треугольник ориентирован против часовой
                if d1 >= 0 and d2 >= 0 and d3 >= 0:
                    surface.set_at((x, y), color)
            else:
                # Треугольник ориентирован по часовой
                if d1 <= 0 and d2 <= 0 and d3 <= 0:
                    surface.set_at((x, y), color)