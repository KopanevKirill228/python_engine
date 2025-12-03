"""
parameters.py — КОНФИГУРАЦИЯ 3D Graphics Engine
Здесь находятся ВСЕ настраиваемые параметры
"""

# ═══════════════════════════════════════════════════════════════════════════════
# ЭКРАН И ГРАФИКА
# ═══════════════════════════════════════════════════════════════════════════════

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 960
FPS = 60

# ═══════════════════════════════════════════════════════════════════════════════
# КАМЕРА И ПРОЕКЦИЯ
# ═══════════════════════════════════════════════════════════════════════════════

CAMERA_FOV = 60.0  # Поле зрения в градусах
CAMERA_Z = 8  # Расстояние камеры до объекта
ROTATION_SPEED = 1.0  # Скорость автоворота (не используется с мышью)

# ═══════════════════════════════════════════════════════════════════════════════
# ОСВЕЩЕНИЕ
# ═══════════════════════════════════════════════════════════════════════════════

LIGHT_DIRECTION = (1.0, 0.0, 0.0)  # Направление света
AMBIENT_INTENSITY = 0.1  # Интенсивность окружающего света (0.0-1.0)


# РЕЖИМЫ РЕНДЕРИНГА (включено/выключено)


ENABLE_BACKFACE_CULLING = True  # Отсечение невидимых граней
ENABLE_DEPTH_SORTING = True  # Z-буфферизация (сортировка по глубине)
ENABLE_WIREFRAME = False  # Каркас (только рёбра)



DEBUG_MODE = False  # Выводить отладочную информацию
SHOW_FPS = True  # Показывать FPS на экране
SHOW_NORMALS = False  # Показывать нормали (линии)



COLOR_BACKGROUND = (40, 40, 50)  # Фон экрана (RGB)
COLOR_WIREFRAME = (30, 30, 30)  # Цвет каркаса (RGB)
COLOR_TEXT = (200, 200, 200)  # Цвет текста (RGB)



# 📐 РАЗМЕРЫ И КОЛИЧЕСТВО ГРАНЕЙ ФИГУР (ЛЕГКО РЕДАКТИРУЕТСЯ!)

class GeometryParams:
    """Параметры для генерации всех 3D фигур"""

    # КУБ
    CUBE_SIZE = 0.7

    # СФЕРА
    SPHERE_RADIUS = 1
    SPHERE_LATITUDE_SEGMENTS = 12
    SPHERE_LONGITUDE_SEGMENTS = 24


    # ТОР
    TORUS_MAJOR_RADIUS = 0.4
    TORUS_MINOR_RADIUS = 0.18
    TORUS_MAJOR_SEGMENTS = 24
    TORUS_MINOR_SEGMENTS = 12

    # ЛЕНТА МЁБИУСА
    MOBIUS_RADIUS = 0.4
    MOBIUS_WIDTH = 0.3
    MOBIUS_SEGMENTS = 48


    # ВОЛНИСТАЯ ПЛОСКОСТЬ
    WAVY_SCALE = 0.15
    WAVY_U_SEGMENTS = 24
    WAVY_V_SEGMENTS = 24

    # ГИПЕРБОЛОИД
    HYPERBOLOID_SCALE = 0.1
    HYPERBOLOID_U_SEGMENTS = 24
    HYPERBOLOID_V_SEGMENTS = 24


    # СЕДЛО
    SADDLE_SCALE = 0.15  # Размер
    SADDLE_U_SEGMENTS = 24
    SADDLE_V_SEGMENTS = 24

    #БУТЫЛКА КЛЕЙНА
    KLEIN_BOTTLE_U_SEGMENTS = 24
    KLEIN_BOTTLE_V_SEGMENTS = 24


# УПРАВЛЕНИЕ МЫШЬЮ


MOUSE_SENSITIVITY = 0.015


# VIEWPORT (ОКНО ПРОСМОТРА)


VIEWPORT_PANEL_WIDTH = 280  # Ширина левой панели управления
VIEWPORT_MARGIN = 20  # Отступ viewport от края экрана
VIEWPORT_MARGIN_FROM_PANEL = 20  # Отступ viewport от панели

