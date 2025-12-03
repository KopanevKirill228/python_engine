import pygame
import math
import sys
import tkinter as tk
from tkinter import filedialog

from graphics import Renderer, DebugRenderer
from geometry import GeometryGenerator, Mesh
from obj_loader import OBJLoader
from Math3D import Math3D
from parameters import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    CAMERA_FOV, CAMERA_Z,
    LIGHT_DIRECTION, AMBIENT_INTENSITY,
    ENABLE_BACKFACE_CULLING, ENABLE_DEPTH_SORTING,
    ENABLE_WIREFRAME, ROTATION_SPEED,
    COLOR_BACKGROUND, COLOR_TEXT,
    DEBUG_MODE, SHOW_FPS, SHOW_NORMALS,
    MOUSE_SENSITIVITY,
    VIEWPORT_PANEL_WIDTH, VIEWPORT_MARGIN, VIEWPORT_MARGIN_FROM_PANEL,
    GeometryParams
)


class Slider:
    """Ползунок для управления параметром"""

    def __init__(self, x, y, width, height, min_val, max_val, initial_val, label, color=(100, 150, 200)):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.label = label
        self.color = color
        self.rect = pygame.Rect(x, y, width, height)
        self.slider_rect = pygame.Rect(x, y + height + 5, width, 10)
        self.knob_radius = 8
        self.is_dragging = False
        self._update_knob_position()

    def _update_knob_position(self):
        """Обновить позицию ручки ползунка"""
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        self.knob_x = self.slider_rect.x + ratio * self.slider_rect.width

    def _value_from_position(self, mouse_x):
        """Получить значение из позиции мыши"""
        ratio = (mouse_x - self.slider_rect.x) / self.slider_rect.width
        ratio = max(0, min(1, ratio))
        return self.min_val + ratio * (self.max_val - self.min_val)

    def update(self, mouse_pos, mouse_pressed):
        """Обновить состояние ползунка"""
        knob_rect = pygame.Rect(self.knob_x - self.knob_radius,
                                self.slider_rect.y - self.knob_radius,
                                self.knob_radius * 2, self.knob_radius * 2)

        if mouse_pressed[0] and knob_rect.collidepoint(mouse_pos):
            self.is_dragging = True
        elif not mouse_pressed[0]:
            self.is_dragging = False

        if self.is_dragging:
            self.value = self._value_from_position(mouse_pos[0])
            self._update_knob_position()

    def draw(self, screen, font):
        """Отрисовать ползунок"""
        # Подпись
        label_text = font.render(f"{self.label}: {self.value:.1f}°", True, (200, 200, 200))
        screen.blit(label_text, (self.x, self.y - 25))

        # Полоса ползунка
        pygame.draw.rect(screen, (100, 100, 100), self.slider_rect)
        pygame.draw.rect(screen, COLOR_TEXT, self.slider_rect, 1)

        # Ручка ползунка
        pygame.draw.circle(screen, self.color, (int(self.knob_x), int(self.slider_rect.centery)),
                           self.knob_radius)
        pygame.draw.circle(screen, COLOR_TEXT, (int(self.knob_x), int(self.slider_rect.centery)),
                           self.knob_radius, 2)


class Button:
    """Кнопка управления"""

    def __init__(self, x, y, width, height, text, color=(100, 150, 200),
                 hover_color=(120, 170, 220), pressed_color=(80, 130, 180)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.pressed_color = pressed_color
        self.current_color = color
        self.is_hovered = False
        self.is_pressed = False

    def draw(self, screen, font):
        """Отрисовать кнопку"""
        pygame.draw.rect(screen, self.current_color, self.rect)
        pygame.draw.rect(screen, COLOR_TEXT, self.rect, 2)

        text_surface = font.render(self.text, True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def update(self, mouse_pos, mouse_pressed):
        """Обновить состояние кнопки"""
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        self.is_pressed = self.is_hovered and mouse_pressed

        if self.is_pressed:
            self.current_color = self.pressed_color
        elif self.is_hovered:
            self.current_color = self.hover_color
        else:
            self.current_color = self.color

    def is_clicked(self):
        """Проверить был ли клик по кнопке"""
        return self.is_hovered and not self.is_pressed


class Checkbox:
    """Чекбокс"""

    def __init__(self, x, y, size, label, initial_state=False, color=(100, 150, 200)):
        self.rect = pygame.Rect(x, y, size, size)
        self.label = label
        self.checked = initial_state
        self.color = color
        self.is_hovered = False

    def draw(self, screen, font):
        """Отрисовать чекбокс"""
        pygame.draw.rect(screen, COLOR_TEXT, self.rect, 2)
        if self.checked:
            pygame.draw.rect(screen, self.color, self.rect)

        text_surface = font.render(self.label, True, COLOR_TEXT)
        screen.blit(text_surface, (self.rect.right + 10, self.rect.centery - text_surface.get_height() // 2))

    def update(self, mouse_pos):
        """Обновить состояние"""
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self):
        """Проверить клик"""
        return self.is_hovered

    def toggle(self):
        """Переключить состояние"""
        self.checked = not self.checked


class ControlPanel:
    """Левая панель управления с кнопками и информацией"""

    def __init__(self, width=280, screen_width=SCREEN_WIDTH, screen_height=SCREEN_HEIGHT):
        self.width = width
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.rect = pygame.Rect(0, 0, width, screen_height)

        y_pos = 15

        # Заголовок
        self.title_y = y_pos
        y_pos += 50

        # ===== НОВОЕ: ПОЛЗУНОК FOV =====
        self.fov_slider = Slider(15, y_pos, width - 30, 20,
                                 min_val=10.0, max_val=120.0, initial_val=60.0,
                                 label="FOV", color=(100, 200, 150))
        y_pos += 70

        # Кнопки переключения объектов
        button_width = width - 30
        self.prev_button = Button(15, y_pos, button_width, 35, "← Предыдущий")
        y_pos += 45
        self.next_button = Button(15, y_pos, button_width, 35, "Следующий →")
        y_pos += 45

        # ===== НОВАЯ КНОПКА: ЗАГРУЗИТЬ OBJ =====
        self.load_obj_button = Button(15, y_pos, button_width, 35, "📂 Загрузить OBJ")
        y_pos += 45

        # Информация об объекте
        self.info_y = y_pos
        y_pos += 100

        # Чекбоксы
        self.backface_checkbox = Checkbox(15, y_pos, 12, "Back Face", ENABLE_BACKFACE_CULLING)
        y_pos += 25
        self.depthsort_checkbox = Checkbox(15, y_pos, 12, "Z-Sort", ENABLE_DEPTH_SORTING)
        y_pos += 25
        self.wireframe_checkbox = Checkbox(15, y_pos, 12, "Wireframe", ENABLE_WIREFRAME)
        y_pos += 50

        # Кнопки управления
        self.pause_button = Button(15, y_pos, button_width, 35, "⏸ Пауза")
        y_pos += 45
        self.reset_button = Button(15, y_pos, button_width, 35, "⟲ Сброс")
        y_pos += 55

        # Кнопка выхода
        self.exit_button = Button(15, screen_height - 50, button_width, 35, "✕ Выход")

        # Справка
        self.help_text_y = screen_height - 85

    def update(self, mouse_pos, mouse_buttons):
        """Обновить состояние всех элементов"""
        self.fov_slider.update(mouse_pos, mouse_buttons)
        self.prev_button.update(mouse_pos, mouse_buttons[0])
        self.next_button.update(mouse_pos, mouse_buttons[0])
        self.load_obj_button.update(mouse_pos, mouse_buttons[0])
        self.pause_button.update(mouse_pos, mouse_buttons[0])
        self.reset_button.update(mouse_pos, mouse_buttons[0])
        self.exit_button.update(mouse_pos, mouse_buttons[0])

        self.backface_checkbox.update(mouse_pos)
        self.depthsort_checkbox.update(mouse_pos)
        self.wireframe_checkbox.update(mouse_pos)

    def draw(self, screen, font, object_info, paused):
        """Отрисовать панель управления"""
        # Фон панели
        pygame.draw.rect(screen, (30, 30, 40), self.rect)
        pygame.draw.line(screen, COLOR_TEXT, (self.width, 0), (self.width, self.screen_height), 3)

        # Заголовок
        title = font.render("УПРАВЛЕНИЕ", True, COLOR_TEXT)
        screen.blit(title, (self.width // 2 - title.get_width() // 2, self.title_y))

        # ===== ОТРИСОВКА ПОЛЗУНКА FOV =====
        self.fov_slider.draw(screen, pygame.font.Font(None, 18))

        # Кнопки переключения
        self.prev_button.draw(screen, font)
        self.next_button.draw(screen, font)
        self.load_obj_button.draw(screen, font)

        # Информация об объекте
        small_font = pygame.font.Font(None, 16)
        info_text = [
            f"Объект: {object_info['name']}",
            f"{object_info['index']}/{object_info['total']}",
            "",
            f"Вершин: {object_info['vertices']}",
            f"Граней: {object_info['faces']}",
        ]

        for i, line in enumerate(info_text):
            text_surface = small_font.render(line, True, COLOR_TEXT)
            screen.blit(text_surface, (15, self.info_y + i * 16))

        # Чекбоксы
        self.backface_checkbox.draw(screen, small_font)
        self.depthsort_checkbox.draw(screen, small_font)
        self.wireframe_checkbox.draw(screen, small_font)

        # Кнопки управления
        self.pause_button.draw(screen, font)
        self.reset_button.draw(screen, font)

        # Статус паузы
        if paused:
            pause_text = small_font.render("ПАУЗА", True, (255, 100, 100))
            screen.blit(pause_text, (15, self.pause_button.rect.bottom + 5))

        # Кнопка выхода
        self.exit_button.draw(screen, font)

        # Справка
        help_lines = [
            "🖱️ Мышка: вращение",
            "⌨️ A/D: объекты",
            "Пробел: пауза",
        ]
        for i, line in enumerate(help_lines):
            text = small_font.render(line, True, (150, 150, 150))
            screen.blit(text, (15, self.help_text_y + i * 15))


class ViewportRenderer:
    """Рендерер с окном просмотра (viewport)"""

    def __init__(self, renderer, x, y, width, height):
        self.renderer = renderer
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x, y, width, height)

    def render_mesh_in_viewport(self, mesh, transform_matrix):
        """Отрисовать меш в окно просмотра"""
        original_screen = self.renderer.screen

        temp_surface = pygame.Surface((self.width, self.height))
        temp_surface.fill((50, 50, 60))

        self.renderer.screen = temp_surface
        self.renderer.render_mesh(mesh, transform_matrix)
        self.renderer.screen = original_screen

        original_screen.blit(temp_surface, (self.x, self.y))
        pygame.draw.rect(original_screen, COLOR_TEXT, self.rect, 3)


class Application:
    """
    Главное приложение 3D Graphics Engine
    С полной поддержкой мышиного управления и объемной визуализацией
    """

    def __init__(self):
        """Инициализация приложения"""
        pygame.init()

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("3D Graphics Engine — Interactive 3D Viewer")

        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 22)

        self.renderer = DebugRenderer(SCREEN_WIDTH, SCREEN_HEIGHT)

        # ===== РАЗМЕРЫ VIEWPORT (из parameters.py) =====
        panel_width = VIEWPORT_PANEL_WIDTH
        viewport_width = SCREEN_WIDTH - panel_width - VIEWPORT_MARGIN_FROM_PANEL * 2
        viewport_height = SCREEN_HEIGHT - VIEWPORT_MARGIN * 2

        # Создаём viewport рендерер
        self.viewport = ViewportRenderer(
            self.renderer,
            panel_width + VIEWPORT_MARGIN_FROM_PANEL,
            VIEWPORT_MARGIN,
            viewport_width,
            viewport_height
        )

        # Создаём панель управления
        self.panel = ControlPanel(panel_width, SCREEN_WIDTH, SCREEN_HEIGHT)

        # Параметры сцены
        self.running = True
        self.paused = False
        self.current_object_index = 0

        # ===== МЫШИНОЕ ВРАЩЕНИЕ (из parameters.py) =====
        self.angle_x = 0.0
        self.angle_y = 0.0
        self.mouse_drag = False
        self.mouse_prev = None
        self.mouse_sensitivity = MOUSE_SENSITIVITY

        # ===== НОВОЕ: ПЕРЕМЕННАЯ МАСШТАБА ДЛЯ FOV =====
        self.fov_scale = 1.0

        # Время для автоанимации
        self.time = 0

        # Список объектов
        self.objects = []
        self.object_names = []

        # ===== OBJ ФАЙЛ =====
        self.loaded_obj_mesh = None
        self.loaded_obj_name = "OBJ Файл"

        self._init_geometry()

    def _init_geometry(self):
        """Инициализировать все объекты геометрии (из parameters.py)"""

        # Куб
        cube = GeometryGenerator.cube(size=GeometryParams.CUBE_SIZE)
        self.objects.append(cube)
        self.object_names.append("Куб")

        # Сфера
        sphere = GeometryGenerator.sphere(
            radius=GeometryParams.SPHERE_RADIUS,
            latitude_segments=GeometryParams.SPHERE_LATITUDE_SEGMENTS,
            longitude_segments=GeometryParams.SPHERE_LONGITUDE_SEGMENTS
        )
        self.objects.append(sphere)
        self.object_names.append("Сфера")

        # Тор
        torus = GeometryGenerator.torus(
            major_radius=GeometryParams.TORUS_MAJOR_RADIUS,
            minor_radius=GeometryParams.TORUS_MINOR_RADIUS,
            major_segments=GeometryParams.TORUS_MAJOR_SEGMENTS,
            minor_segments=GeometryParams.TORUS_MINOR_SEGMENTS
        )
        self.objects.append(torus)
        self.object_names.append("Тор")

        # Лента Мёбиуса
        mobius = GeometryGenerator.mobius_strip(
            radius=GeometryParams.MOBIUS_RADIUS,
            width=GeometryParams.MOBIUS_WIDTH,
            segments=GeometryParams.MOBIUS_SEGMENTS
        )
        self.objects.append(mobius)
        self.object_names.append("Лента Мёбиуса")

        # Волнистая плоскость
        wavy = GeometryGenerator.wavy_plane(
            scale=GeometryParams.WAVY_SCALE,
            u_segments=GeometryParams.WAVY_U_SEGMENTS,
            v_segments=GeometryParams.WAVY_V_SEGMENTS
        )
        self.objects.append(wavy)
        self.object_names.append("Волнистая плоскость")

        # Гиперболоид
        hyperboloid = GeometryGenerator.hyperboloid(
            scale=GeometryParams.HYPERBOLOID_SCALE,
            u_segments=GeometryParams.HYPERBOLOID_U_SEGMENTS,
            v_segments=GeometryParams.HYPERBOLOID_V_SEGMENTS
        )
        self.objects.append(hyperboloid)
        self.object_names.append("Гиперболоид")

        # Седло
        saddle = GeometryGenerator.saddle(
            scale=GeometryParams.SADDLE_SCALE,
            u_segments=GeometryParams.SADDLE_U_SEGMENTS,
            v_segments=GeometryParams.SADDLE_V_SEGMENTS
        )
        self.objects.append(saddle)
        self.object_names.append("Седло")

        # Бутылка Клейна
        klein = GeometryGenerator.klein_bottle(
            u_segments=GeometryParams.KLEIN_BOTTLE_U_SEGMENTS,
            v_segments=GeometryParams.KLEIN_BOTTLE_V_SEGMENTS
        )
        self.objects.append(klein)
        self.object_names.append("Бутылка Клейна")

    def _load_obj_file(self):
        """Загрузить OBJ файл через диалог"""
        # Создаём корневое окно Tkinter (скрытое)
        root = tk.Tk()
        root.withdraw()

        # Открываем диалог выбора файла
        file_path = filedialog.askopenfilename(
            title="Выберите OBJ файл",
            filetypes=[("OBJ файлы", "*.obj"), ("Все файлы", "*.*")]
        )

        root.destroy()

        if not file_path:
            print("❌ Файл не выбран")
            return

        try:
            # Загружаем OBJ файл
            mesh = OBJLoader.load(file_path, scale=1.0)

            # Нормализуем меш (центрируем и масштабируем)
            self._normalize_mesh(mesh)

            self.loaded_obj_mesh = mesh

            # Извлекаем имя файла
            import os
            self.loaded_obj_name = os.path.splitext(os.path.basename(file_path))[0]

            print(f"✅ OBJ загружен: {self.loaded_obj_name}")
            print(f"   Вершин: {len(mesh.vertices)}, Граней: {len(mesh.faces)}")

        except Exception as e:
            print(f"❌ Ошибка при загрузке OBJ: {e}")
            import traceback
            traceback.print_exc()

    def _normalize_mesh(self, mesh):
        """Нормализовать меш (центрировать и масштабировать)"""
        if len(mesh.vertices) == 0:
            return

        # Найти граничный ящик
        vertices = mesh.vertices
        min_x = min(v[0] for v in vertices)
        max_x = max(v[0] for v in vertices)
        min_y = min(v[1] for v in vertices)
        max_y = max(v[1] for v in vertices)
        min_z = min(v[2] for v in vertices)
        max_z = max(v[2] for v in vertices)

        # Центр
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        center_z = (min_z + max_z) / 2

        # Размер
        size_x = max_x - min_x
        size_y = max_y - min_y
        size_z = max_z - min_z
        max_size = max(size_x, size_y, size_z)

        # Нормализуем вершины
        for v in mesh.vertices:
            v[0] = (v[0] - center_x) / max_size * 2 if max_size > 0 else v[0]
            v[1] = (v[1] - center_y) / max_size * 2 if max_size > 0 else v[1]
            v[2] = (v[2] - center_z) / max_size * 2 if max_size > 0 else v[2]

    def _handle_input(self):
        """Обработить ввод пользователя"""

        mouse_pos = pygame.mouse.get_pos()
        mouse_buttons = pygame.mouse.get_pressed()

        self.panel.update(mouse_pos, mouse_buttons)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # ===== МЫШИНОЕ ВРАЩЕНИЕ =====
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # Проверяем, нажали ли в области viewport
                    if self.viewport.rect.collidepoint(event.pos):
                        self.mouse_drag = True
                        self.mouse_prev = event.pos

                    # Клики на кнопки панели
                    if self.panel.prev_button.is_clicked():
                        self.current_object_index = (self.current_object_index - 1) % len(self.objects)
                        self.loaded_obj_mesh = None
                        print(f"Объект: {self.object_names[self.current_object_index]}")

                    elif self.panel.next_button.is_clicked():
                        self.current_object_index = (self.current_object_index + 1) % len(self.objects)
                        self.loaded_obj_mesh = None
                        print(f"Объект: {self.object_names[self.current_object_index]}")

                    # ===== НОВАЯ ОБРАБОТКА: ЗАГРУЗИТЬ OBJ =====
                    elif self.panel.load_obj_button.is_clicked():
                        self._load_obj_file()

                    elif self.panel.pause_button.is_clicked():
                        self.paused = not self.paused
                        status = "Пауза" if self.paused else "Воспроизведение"
                        print(f"Статус: {status}")

                    elif self.panel.reset_button.is_clicked():
                        self.time = 0
                        self.angle_x = 0.0
                        self.angle_y = 0.0
                        print("Сброс: позиция восстановлена")

                    elif self.panel.exit_button.is_clicked():
                        self.running = False

                    elif self.panel.backface_checkbox.is_clicked():
                        self.panel.backface_checkbox.toggle()

                    elif self.panel.depthsort_checkbox.is_clicked():
                        self.panel.depthsort_checkbox.toggle()

                    elif self.panel.wireframe_checkbox.is_clicked():
                        self.panel.wireframe_checkbox.toggle()

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.mouse_drag = False
                    self.mouse_prev = None

            elif event.type == pygame.MOUSEMOTION and self.mouse_drag:
                mx, my = event.pos
                px, py = self.mouse_prev
                dx = mx - px
                dy = my - py

                # Обновляем углы вращения
                self.angle_x += dy * self.mouse_sensitivity
                self.angle_y += dx * self.mouse_sensitivity

                self.mouse_prev = event.pos

            # ===== КЛАВИАТУРА =====
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    self.current_object_index = (self.current_object_index + 1) % len(self.objects)
                    self.loaded_obj_mesh = None
                    print(f"Объект: {self.object_names[self.current_object_index]}")

                elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    self.current_object_index = (self.current_object_index - 1) % len(self.objects)
                    self.loaded_obj_mesh = None
                    print(f"Объект: {self.object_names[self.current_object_index]}")

                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                    status = "Пауза" if self.paused else "Воспроизведение"
                    print(f"Статус: {status}")

                elif event.key == pygame.K_r:
                    self.time = 0
                    self.angle_x = 0.0
                    self.angle_y = 0.0
                    print("Сброс: позиция восстановлена")

                elif event.key == pygame.K_h:
                    self._print_help()

    def _print_help(self):
        """Вывести справку управления"""
        print("\n" + "=" * 70)
        print(" 3D GRAPHICS ENGINE — УПРАВЛЕНИЕ")
        print("=" * 70)
        print("🖱️  МЫШКА:")
        print("   • Зажмите и перемещайте мышь в viewport для вращения объекта")
        print("   • Кнопки на панели слева для управления")
        print("\n⌨️  КЛАВИАТУРА:")
        print("   • A/D или Стрелки ← → — переключение объектов")
        print("   • Пробел — пауза/возобновление")
        print("   • R — сброс позиции")
        print("   • H — справка")
        print("   • ESC — выход")
        print("\n📂 OBJ ФАЙЛЫ:")
        print("   • Нажмите кнопку '📂 Загрузить OBJ' для выбора файла")
        print("   • Загруженный OBJ будет отображаться на экране")
        print("\n🎚️ FOV ПОЛЗУНОК:")
        print("   • Перемещайте ползунок вверху панели для изменения размера")
        print("   • Диапазон: 10° - 120°")
        print("   • Размер обновляется сразу при перемещении")
        print("\n💡 ВСЕ ПАРАМЕТРЫ в файле parameters.py:")
        print("   • Размеры фигур (CUBE_SIZE, SPHERE_RADIUS и т.д.)")
        print("   • Количество граней (SPHERE_LATITUDE_SEGMENTS и т.д.)")
        print("   • Чувствительность мыши (MOUSE_SENSITIVITY)")
        print("=" * 70 + "\n")

    def _update(self, dt):
        """Обновить состояние сцены"""

        if not self.paused:
            self.time += dt


        # Математика перспективной проекции:
        # Чем больше FOV, тем дальше объект кажется, тем меньше размер
        # Чем меньше FOV, тем ближе объект кажется, тем больше размер
        #
        # Формула: scale = tan(default_fov / 2) / tan(current_fov / 2)
        # Это обратная зависимость FOV к видимому размеру

        default_fov_rad = math.radians(60.0)  # 60° по умолчанию
        current_fov_rad = math.radians(self.panel.fov_slider.value)

        # Вычисляем масштаб через тангенсы углов половины FOV
        # tan(fov/2) пропорционален размеру проекции объекта
        tan_default = math.tan(default_fov_rad / 2.0)
        tan_current = math.tan(current_fov_rad / 2.0)

        # Масштаб = как изменился размер проекции
        self.fov_scale = tan_default / tan_current

    def _render(self):
        """Отрисовать сцену"""

        self.screen.fill(COLOR_BACKGROUND)

        # ===== ВЫБОР МЕША: OBJ или текущий объект =====
        if self.loaded_obj_mesh is not None:
            current_mesh = self.loaded_obj_mesh
            object_name = self.loaded_obj_name
        else:
            current_mesh = self.objects[self.current_object_index]
            object_name = self.object_names[self.current_object_index]

        # ===== МАТРИЦА ТРАНСФОРМАЦИИ =====
        # Используем углы вращения от мыши
        rot_x = Math3D.rotation_matrix_x(self.angle_x)
        rot_y = Math3D.rotation_matrix_y(self.angle_y)
        rot_z = Math3D.rotation_matrix_z(0)

        # Объединяем матрицы вращения
        transform = Math3D.matrix_multiply(rot_x, rot_y)
        transform = Math3D.matrix_multiply(transform, rot_z)

        # ===== НОВОЕ: ДОБАВЛЯЕМ МАСШТАБИРОВАНИЕ ИЗ FOV =====
        # Матрица масштабирования
        scale_matrix = [
            [self.fov_scale, 0, 0, 0],
            [0, self.fov_scale, 0, 0],
            [0, 0, self.fov_scale, 0],
            [0, 0, 0, 1]
        ]

        # Применяем масштабирование к трансформации
        transform = Math3D.matrix_multiply(transform, scale_matrix)

        # Рендерим меш в viewport
        self.viewport.render_mesh_in_viewport(current_mesh, transform)

        # Информация об объекте
        object_info = {
            'name': object_name,
            'index': self.current_object_index + 1 if self.loaded_obj_mesh is None else 0,
            'total': len(self.objects),
            'vertices': len(current_mesh.vertices),
            'faces': len(current_mesh.faces)
        }

        # Отрисовываем панель управления
        self.panel.draw(self.screen, self.font, object_info, self.paused)

        # Статистика FPS
        fps = self.clock.get_fps()
        small_font = pygame.font.Font(None, 16)
        fps_text = small_font.render(f"FPS: {fps:.1f}", True, COLOR_TEXT)
        self.screen.blit(fps_text, (SCREEN_WIDTH - 90, 10))

        # Информация о положении мышки
        if self.mouse_drag:
            drag_text = small_font.render("ВРАЩЕНИЕ...", True, (0, 200, 100))
            self.screen.blit(drag_text, (SCREEN_WIDTH - 140, 28))

        # ===== НОВОЕ: ПОКАЗЫВАЕМ ТЕКУЩЕЕ ЗНАЧЕНИЕ FOV И МАСШТАБА =====
        fov_info = small_font.render(f"FOV Scale: {self.fov_scale:.2f}x", True, (100, 200, 150))
        self.screen.blit(fov_info, (SCREEN_WIDTH - 160, 46))

        pygame.display.flip()

    def run(self):
        """Главной цикл приложения"""

        while self.running:
            self._handle_input()

            dt = self.clock.tick(FPS) / 1000.0
            self._update(dt)

            self._render()

        pygame.quit()
        print("✅ Приложение завершено.")
        sys.exit(0)


def main():
    """Главная функция"""

    try:
        app = Application()
        app.run()

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()