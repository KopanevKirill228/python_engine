"""
obj_loader.py — Загрузчик файлов формата OBJ (ИСПРАВЛЕННАЯ ВЕРСИЯ)
Поддерживает базовый OBJ формат с вершинами, гранями и нормалями

ИСПРАВЛЕНИЯ:
1. Валидация индексов вершин
2. Поддержка отрицательных индексов OBJ
3. Проверка минимума вершин
4. Корректное вычисление vertex normals для экспорта
5. Исправление load_multiple() для нормалей
"""

import os
from geometry import Mesh
from math_utils import compute_face_normal


class OBJLoader:
    """
    Загрузчик OBJ файлов

    Поддерживаемые элементы:
    - v (vertex) — вершины в 3D пространстве
    - f (face) — грани (треугольники или многоугольники)
    - vn (vertex normal) — нормали вершин (вычисляются заново)
    - vt (texture coordinate) — текстурные координаты (игнорируются)
    - g (group) — группы (игнорируются)
    - o (object) — объекты (игнорируются)

    Поддерживает отрицательные индексы OBJ!
    Например: f -1 -2 -3 означает последние 3 загруженные вершины
    """

    @staticmethod
    def load(filepath, scale=1.0):
        """
        Загрузить OBJ файл

        Процесс:
        1. Открываем файл
        2. Парсим каждую строку
        3. Собираем вершины и грани
        4. ВАЛИДИРУЕМ индексы вершин
        5. Применяем масштабирование
        6. Вычисляем нормали
        """

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"OBJ файл не найден: {filepath}")

        # Списки для хранения данных
        vertices = []
        faces = []
        parsing_errors = 0

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    # Удаляем пробелы в начале и конце
                    line = line.strip()

                    # Пропускаем пустые строки и комментарии
                    if not line or line.startswith('#'):
                        continue

                    # Разбиваем строку на команду и аргументы
                    parts = line.split()
                    if not parts:
                        continue

                    command = parts[0]

                    # ===== ПАРСИНГ ВЕРШИН (VERTEX) =====
                    if command == 'v':
                        try:
                            # Формат: v x y z [w]
                            # w (homogeneous coordinate) опциональна, по умолчанию 1
                            x = float(parts[1]) * scale
                            y = float(parts[2]) * scale
                            z = float(parts[3]) * scale
                            vertices.append([x, y, z])

                        except (ValueError, IndexError) as e:
                            print(f"⚠️ Ошибка парсинга вершины на строке {line_num}: {e}")
                            parsing_errors += 1
                            continue

                    # ===== ПАРСИНГ ГРАНЕЙ (FACE) =====
                    elif command == 'f':
                        try:
                            # Формат: f v1 v2 v3 ... или f v1/vt1/vn1 v2/vt2/vn2 ...
                            # Нам нужны только индексы вершин
                            face_indices = []

                            for i in range(1, len(parts)):
                                # Парсим "v/vt/vn" или "v//vn" или "v/vt" или "v"
                                vertex_data = parts[i].split('/')
                                vertex_idx_raw = int(vertex_data[0])

                                # Отрицательные индексы считаются от конца загруженных вершин
                                if vertex_idx_raw < 0:
                                    # -1 = последняя вершина, -2 = предпоследняя и т.д.
                                    vertex_idx = len(vertices) + vertex_idx_raw
                                else:
                                    # Положительные индексы в OBJ 1-based
                                    vertex_idx = vertex_idx_raw - 1

                                if vertex_idx < 0 or vertex_idx >= len(vertices):
                                    raise ValueError(
                                        f"Индекс вершины {vertex_idx_raw} вне границ "
                                        f"(всего вершин: {len(vertices)})"
                                    )

                                face_indices.append(vertex_idx)


                            if len(face_indices) < 3:
                                print(f"⚠️ Грань на строке {line_num} содержит менее 3 вершин, пропускаем")
                                parsing_errors += 1
                                continue

                            # Если грань имеет больше 3 вершин, разбиваем её на треугольники
                            # Используем триангуляцию веером: v0, v1, v2; v0, v2, v3; v0, v3, v4; ...
                            for i in range(1, len(face_indices) - 1):
                                triangle = [
                                    face_indices[0],
                                    face_indices[i],
                                    face_indices[i + 1]
                                ]
                                faces.append(triangle)

                        except (ValueError, IndexError) as e:
                            print(f"⚠️ Ошибка парсинга грани на строке {line_num}: {e}")
                            parsing_errors += 1
                            continue

                    # Остальные команды игнорируем (vn, vt, g, o, и т.д.)

        except IOError as e:
            raise IOError(f"Ошибка при чтении файла {filepath}: {e}")

        # ИСПРАВЛЕНИЕ #4: Проверяем достаточность данных
        if len(vertices) == 0:
            raise ValueError(f"Загруженный OBJ файл не содержит вершин")

        if len(faces) == 0:
            raise ValueError(f"Загруженный OBJ файл не содержит граней")

        if parsing_errors > 0:
            print(f"⚠️ Всего ошибок при парсинге: {parsing_errors}")

        print(f"✓ Загружено: {len(vertices)} вершин, {len(faces)} граней")

        # Создаём меш
        mesh = Mesh(vertices, faces)

        # Вычисляем нормали
        mesh.compute_face_normals()

        return mesh

    @staticmethod
    def load_multiple(filepaths, scale=1.0):
        """
        Загрузить несколько OBJ файлов в один меш

        Args:
            filepaths: список путей к файлам или одна строка
            scale: коэффициент масштабирования

        Returns:
            объект Mesh с объединёнными данными
        """

        # Если передана одна строка, преобразуем в список
        if isinstance(filepaths, str):
            filepaths = [filepaths]

        # Создаём пустой меш
        combined_mesh = Mesh()

        # Загружаем каждый файл и добавляем его данные
        for filepath in filepaths:
            try:
                mesh = OBJLoader.load(filepath, scale)

                # Запомним смещение индексов вершин
                vertex_offset = len(combined_mesh.vertices)

                # Добавляем вершины
                combined_mesh.vertices.extend(mesh.vertices)

                # Добавляем грани с коррекцией индексов
                for face in mesh.faces:
                    adjusted_face = [idx + vertex_offset for idx in face]
                    combined_mesh.faces.append(adjusted_face)

                # ИСПРАВЛЕНИЕ #5: Добавляем нормали с учётом смещения
                # (хотя они будут пересчитаны после объединения)
                for normal in mesh.face_normals:
                    combined_mesh.face_normals.append(normal)

            except (FileNotFoundError, IOError, ValueError) as e:
                print(f"❌ Ошибка загрузки {filepath}: {e}")
                continue

        # ИСПРАВЛЕНИЕ #5b: Пересчитываем нормали объединённого меша
        # (важно!) вместо использования старых нормалей
        combined_mesh.face_normals = []  # Очищаем старые
        combined_mesh.compute_face_normals()

        return combined_mesh


class OBJExporter:
    """
    Экспортер меша в OBJ формат

    ИСПРАВЛЕНИЕ: Теперь корректно экспортирует vertex normals
    (усреднённые нормали вершин), а не грани
    """

    @staticmethod
    def _compute_vertex_normals(mesh):
        """
        Вычислить нормали вершин как усреднение нормалей граней

        Процесс:
        1. Для каждой вершины инициализируем нормаль (0, 0, 0)
        2. Для каждой грани добавляем её нормаль всем её вершинам
        3. Нормализуем каждую вершинную нормаль

        Args:
            mesh: объект Mesh

        Returns:
            список вершинных нормалей (parallel к mesh.vertices)
        """

        # Инициализируем нормали вершин нулями
        vertex_normals = [[0.0, 0.0, 0.0] for _ in mesh.vertices]

        # Для каждой грани добавляем её нормаль всем вершинам грани
        for face_idx, face in enumerate(mesh.faces):
            if face_idx < len(mesh.face_normals):
                face_normal = mesh.face_normals[face_idx]

                # Добавляем нормаль грани к нормалям её вершин
                for vertex_idx in face:
                    vertex_normals[vertex_idx][0] += face_normal[0]
                    vertex_normals[vertex_idx][1] += face_normal[1]
                    vertex_normals[vertex_idx][2] += face_normal[2]

        # Нормализуем каждую вершинную нормаль
        for i in range(len(vertex_normals)):
            normal = vertex_normals[i]

            # Вычисляем длину: sqrt(x² + y² + z²)
            length_sq = normal[0] ** 2 + normal[1] ** 2 + normal[2] ** 2

            if length_sq > 0:
                length = length_sq ** 0.5
                vertex_normals[i][0] /= length
                vertex_normals[i][1] /= length
                vertex_normals[i][2] /= length
            else:
                # Если нормаль нулевая, используем (0, 0, 1)
                vertex_normals[i] = [0.0, 0.0, 1.0]

        return vertex_normals

    @staticmethod
    def save(mesh, filepath, include_normals=True):
        """
        Сохранить меш в OBJ файл

        Процесс:
        1. Открываем файл для записи
        2. Записываем заголовок
        3. Записываем все вершины (v команды)
        4. Вычисляем и записываем нормали вершин (vn команды)
        5. Записываем все грани с ссылками на вершины и нормали (f команды)

        Args:
            mesh: объект Mesh
            filepath: путь для сохранения
            include_normals: включить ли нормали в файл
        """

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # Заголовок
                f.write("# OBJ File exported by Python 3D Graphics Engine\n")
                f.write(f"# Vertices: {len(mesh.vertices)}\n")
                f.write(f"# Faces: {len(mesh.faces)}\n\n")

                # Записываем вершины
                f.write("# Vertices\n")
                for i, vertex in enumerate(mesh.vertices):
                    x, y, z = vertex[0], vertex[1], vertex[2]
                    f.write(f"v {x:.6f} {y:.6f} {z:.6f}\n")

                f.write("\n")

                # ИСПРАВЛЕНИЕ #6: Вычисляем и записываем vertex normals
                vertex_normals = []
                if include_normals:
                    f.write("# Vertex Normals\n")
                    vertex_normals = OBJExporter._compute_vertex_normals(mesh)

                    for normal in vertex_normals:
                        nx, ny, nz = normal[0], normal[1], normal[2]
                        f.write(f"vn {nx:.6f} {ny:.6f} {nz:.6f}\n")

                    f.write("\n")

                # Записываем грани с индексами нормалей
                f.write("# Faces\n")
                for face_idx, face in enumerate(mesh.faces):
                    # OBJ использует 1-based индексы
                    face_1based = [str(idx + 1) for idx in face]

                    if include_normals and len(vertex_normals) > 0:
                        # Формат с нормалями: f v1//vn1 v2//vn2 v3//vn3
                        # (используем vertex normals, а не face normals)
                        face_str = " ".join([f"{v_idx}//{v_idx}" for v_idx in face_1based])
                    else:
                        # Формат без нормалей: f v1 v2 v3
                        face_str = " ".join(face_1based)

                    f.write(f"f {face_str}\n")

        except IOError as e:
            raise IOError(f"Ошибка при сохранении файла {filepath}: {e}")

        print(f"✓ Меш успешно сохранён в {filepath}")

    @staticmethod
    def save_multiple(meshes, filepath, include_normals=True):
        """
        Сохранить несколько мешей в один OBJ файл

        Args:
            meshes: список объектов Mesh
            filepath: путь для сохранения
            include_normals: включить ли нормали
        """

        # Объединяем все мешы
        combined_mesh = Mesh()

        for mesh in meshes:
            vertex_offset = len(combined_mesh.vertices)

            combined_mesh.vertices.extend(mesh.vertices)

            for face in mesh.faces:
                adjusted_face = [idx + vertex_offset for idx in face]
                combined_mesh.faces.append(adjusted_face)

            combined_mesh.face_normals.extend(mesh.face_normals)

        # Сохраняем объединённый меш
        OBJExporter.save(combined_mesh, filepath, include_normals)