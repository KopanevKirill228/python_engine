
import math
class Math3D:
    """Класс со всеми операциями векторной и матричной математики"""

    @staticmethod
    def vector_norm(v):
        #Вычислить длину вектора
        sum_sq = v[0] ** 2 + v[1] ** 2 + v[2] ** 2
        return math.sqrt(sum_sq)

    @staticmethod
    def vector_normalize(v):
        """
        Нормализовать вектор (привести к единичной длине)"""
        norm = Math3D.vector_norm(v)
        if norm < 1e-6:
            # Если вектор нулевой, возвращаем дефолтный вектор
            return [0, 0, 1]
        return [v[0] / norm, v[1] / norm, v[2] / norm]

    @staticmethod
    def vector_dot(a, b):
        """
        Скалярное произведение двух векторов
        Математика: a·b = a.x*b.x + a.y*b.y + a.z*b.z
        """
        return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]

    @staticmethod
    def vector_cross(a, b):
        """
        Векторное произведение (кросс-произведение)
        Математика:
        a × b = [
            a.y*b.z - a.z*b.y,
            a.z*b.x - a.x*b.z,
            a.x*b.y - a.y*b.x
        ]
        Результат: вектор, перпендикулярный обоим входным векторам
        """
        return [
            a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]
        ]

    @staticmethod
    def vector_subtract(a, b):
        """
        Вычитание векторов a - b
        Математика: (a - b) = [a.x - b.x, a.y - b.y, a.z - b.z]
        """
        return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]

    @staticmethod
    def vector_add(a, b):
        """
        Сложение векторов
        Математика: (a + b) = [a.x + b.x, a.y + b.y, a.z + b.z]
        """
        return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]

    @staticmethod
    def vector_scale(v, scalar):
        """
        Умножить вектор на скаляр
        Математика: s*v = [s*v.x, s*v.y, s*v.z]
        """
        return [v[0] * scalar, v[1] * scalar, v[2] * scalar]

    # ОПЕРАЦИИ С МАТРИЦАМИ (4x4)

    @staticmethod
    def identity_matrix():
        """
        Создать единичную матрицу 4x4

        Математика:
        [1 0 0 0]
        [0 1 0 0]
        [0 0 1 0]
        [0 0 0 1]
        """
        return [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ]

    @staticmethod
    def zeros_matrix(rows, cols):
        """
        Создать нулевую матрицу размером rows x cols
        """
        return [[0.0 for _ in range(cols)] for _ in range(rows)]

    @staticmethod
    def matrix_multiply(A, B):
        """
        Умножить две матрицы A × B

        Математика: C[i][j] = Σ(A[i][k] * B[k][j]) для всех k

        A: матрица размером (m x n)
        B: матрица размером (n x p)
        Возвращает: матрица размером (m x p)
        """
        rows_A = len(A)
        cols_A = len(A[0]) if A else 0
        rows_B = len(B)
        cols_B = len(B[0]) if B else 0

        if cols_A != rows_B:
            raise ValueError(f"Несовместимые размеры матриц: {cols_A} != {rows_B}")

        result = Math3D.zeros_matrix(rows_A, cols_B)

        for i in range(rows_A):
            for j in range(cols_B):
                for k in range(cols_A):
                    result[i][j] += A[i][k] * B[k][j]

        return result

    @staticmethod
    def matrix_vector_multiply(mat, vec):
        """
        Умножить матрицу 4x4 на вектор 4x1

        Математика: result[i] = Σ(mat[i][j] * vec[j]) для всех j
        """
        result = [0.0, 0.0, 0.0, 0.0]

        for i in range(4):
            for j in range(4):
                result[i] += mat[i][j] * vec[j]

        return result

    @staticmethod
    def matrix_transpose(mat):
        """
        Транспонировать матрицу (строки становятся столбцами)
        """
        rows = len(mat)
        cols = len(mat[0]) if mat else 0

        result = Math3D.zeros_matrix(cols, rows)

        for i in range(rows):
            for j in range(cols):
                result[j][i] = mat[i][j]

        return result

    # МАТРИЦЫ ТРАНСФОРМАЦИИ

    @staticmethod
    def translation_matrix(tx, ty, tz):
        """
        Матрица трансляции (сдвига)

        Математика:
        [1  0  0 tx]
        [0  1  0 ty]
        [0  0  1 tz]
        [0  0  0  1]

        Сдвигает точку на вектор (tx, ty, tz)

        tx, ty, tz: смещение по осям
        """
        mat = Math3D.identity_matrix()
        mat[0][3] = tx
        mat[1][3] = ty
        mat[2][3] = tz
        return mat

    @staticmethod
    def rotation_matrix_x(angle):
        """
        Матрица вращения вокруг оси X

        Математика:
        [1    0         0      0]
        [0  cos(θ)  -sin(θ)   0]
        [0  sin(θ)   cos(θ)   0]
        [0    0         0      1]

        angle: угол вращения в радианах
        Возвращает: матрица вращения 4x4
        """
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        return [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, cos_a, -sin_a, 0.0],
            [0.0, sin_a, cos_a, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ]

    @staticmethod
    def rotation_matrix_y(angle):
        """
        Матрица вращения вокруг оси Y

        Математика:
        [ cos(θ)   0  sin(θ)  0]
        [   0      1    0     0]
        [-sin(θ)   0  cos(θ)  0]
        [   0      0    0     1]

        angle: угол вращения в радианах
        Возвращает: матрица вращения 4x4
        """
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        return [
            [cos_a, 0.0, sin_a, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [-sin_a, 0.0, cos_a, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ]

    @staticmethod
    def rotation_matrix_z(angle):
        """
        Матрица вращения вокруг оси Z

        Математика:
        [cos(θ)  -sin(θ)  0  0]
        [sin(θ)   cos(θ)  0  0]
        [  0        0     1  0]
        [  0        0     0  1]

        angle: угол вращения в радианах
        Возвращает: матрица вращения 4x4
        """
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        return [
            [cos_a, -sin_a, 0.0, 0.0],
            [sin_a, cos_a, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ]

    @staticmethod
    def scale_matrix(sx, sy, sz):
        """
        Матрица масштабирования

        Математика:
        [sx  0   0  0]
        [0  sy   0  0]
        [0   0  sz  0]
        [0   0   0  1]

        sx, sy, sz: масштабирование по осям
        Возвращает: матрица масштабирования 4x4
        """
        mat = Math3D.identity_matrix()
        mat[0][0] = sx
        mat[1][1] = sy
        mat[2][2] = sz
        return mat

    @staticmethod
    def perspective_projection(fov, aspect, near, far):
        """
        Матрица перспективной проекции (для 3D→2D преобразования)

        f = 1 / tan(fov / 2)

        [f/aspect    0         0                      0     ]
        [   0        f         0                      0     ]
        [   0        0    (far+near)/(near-far)  2*far*near/(near-far)]
        [   0        0        -1                      1     ]

        fov: поле зрения в радианах
        aspect: отношение ширины к высоте (width / height)
        near: расстояние до ближней плоскости отсечения
        far: расстояние до дальней плоскости отсечения
        Возвращает: матрица проекции 4x4
        """
        f = 1.0 / math.tan(fov / 2.0)

        mat = Math3D.zeros_matrix(4, 4)

        mat[0][0] = f / aspect
        mat[1][1] = f
        mat[2][2] = (far + near) / (near - far)
        mat[2][3] = (2 * far * near) / (near - far)
        mat[3][2] = -1.0
        mat[3][3] = 1.0

        return mat

    # ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ

    @staticmethod
    def vector_angle(a, b):
        """
        Вычислить угол между двумя векторами
        """
        dot = Math3D.vector_dot(a, b)
        norm_a = Math3D.vector_norm(a)
        norm_b = Math3D.vector_norm(b)

        if norm_a < 1e-6 or norm_b < 1e-6:
            return 0.0

        cos_angle = dot / (norm_a * norm_b)
        # Clamп для избежания ошибок из-за floating point
        cos_angle = max(-1.0, min(1.0, cos_angle))

        return math.acos(cos_angle)

    @staticmethod
    def vector_distance(a, b):
        """
        Вычислить расстояние между двумя точками
        """
        diff = Math3D.vector_subtract(b, a)
        return Math3D.vector_norm(diff)

    @staticmethod
    def lerp(a, b, t):
        """
        Линейная интерполяция между двумя векторами

        Математика: result = a + t * (b - a) = (1-t)*a + t*b
        где t ∈ [0, 1]

        a, b: векторы [x, y, z]
        t: параметр интерполяции [0, 1]
        """
        if t < 0:
            t = 0
        elif t > 1:
            t = 1

        return [
            a[0] + t * (b[0] - a[0]),
            a[1] + t * (b[1] - a[1]),
            a[2] + t * (b[2] - a[2])
        ]