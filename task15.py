import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

# Константы размеров изображения
IMAGE_WIDTH = 2000
IMAGE_HEIGHT = 2000

# Пути к файлам
MODEL_PATH = Path('model_1.obj')
OUTPUT_PATH = Path('model.png')

# Углы поворота вокруг осей X, Y, Z (в градусах)
ALPHA_DEG = 15.0   # вращение вокруг оси X
BETA_DEG = 35.0    # вращение вокруг оси Y
GAMMA_DEG = -10.0  # вращение вокруг оси Z

# Вектор сдвига: половина ширины и высоты изображения для центрирования модели
TRANSLATION_VECTOR = np.array(
    [IMAGE_WIDTH / 2.0, IMAGE_HEIGHT / 2.0, 0.0],
    dtype=np.float32
)


def load_model(path: Path):
    # Загрузка модели из OBJ файла
    points = []
    faces = []

    # Чтение файла построчно
    with path.open('r', encoding='utf-8') as obj_file:
        for line in obj_file:
            parts = line.strip().split()

            # Обработка вершин (строка начинается с 'v')
            if parts[0] == 'v':
                x, y, z = map(float, parts[1:4])
                points.append([x, y, z])
            # Обработка граней (строка начинается с 'f')
            elif parts[0] == 'f':
                face_vertices = [int(vertex_data.split('/')[0]) - 1 
                                for vertex_data in parts[1:]]
                faces.append(face_vertices)

    return np.array(points, dtype=np.float32), faces


def rotation_matrix(alpha_deg: float, beta_deg: float, gamma_deg: float) -> np.ndarray:
    # Построение матрицы поворота R = R_x * R_y * R_z
    # Преобразование углов из градусов в радианы
    alpha = math.radians(alpha_deg)
    beta = math.radians(beta_deg)
    gamma = math.radians(gamma_deg)

    # Матрица поворота вокруг оси X
    rx = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, math.cos(alpha), math.sin(alpha)],
            [0.0, -math.sin(alpha), math.cos(alpha)],
        ],
        dtype=np.float32,
    )

    # Матрица поворота вокруг оси Y
    ry = np.array(
        [
            [math.cos(beta), 0.0, math.sin(beta)],
            [0.0, 1.0, 0.0],
            [-math.sin(beta), 0.0, math.cos(beta)],
        ],
        dtype=np.float32,
    )

    # Матрица поворота вокруг оси Z
    rz = np.array(
        [
            [math.cos(gamma), math.sin(gamma), 0.0],
            [-math.sin(gamma), math.cos(gamma), 0.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float32,
    )

    # Композиция поворотов: сначала Z, потом Y, потом X
    return rx @ ry @ rz


def prepare_vertices(points: np.ndarray, rot_matrix: np.ndarray) -> np.ndarray:
    # Преобразование вершин: центрирование, масштабирование, поворот и сдвиг
    
    # Находим границы модели для центрирования
    min_vals = points.min(axis=0)
    max_vals = points.max(axis=0)
    center = (min_vals + max_vals) / 2.0
    centered = points - center

    # Вычисляем масштаб для размещения модели на изображении
    extent = max((max_vals - min_vals).max(), 1e-5)
    scale = 0.45 * min(IMAGE_WIDTH, IMAGE_HEIGHT) / extent
    scaled = centered * scale

    # Применяем матрицу поворота: X' = R * X
    rotated = (rot_matrix @ scaled.T).T
    # Применяем вектор сдвига: X' = X' + t
    transformed = rotated + TRANSLATION_VECTOR

    # Преобразуем 3D координаты в экранные 2D координаты
    screen_points = np.empty((rotated.shape[0], 2), dtype=np.int32)
    # Координата X: округляем и ограничиваем границами изображения
    screen_points[:, 0] = np.clip(np.rint(transformed[:, 0]), 0, IMAGE_WIDTH - 1)
    # Координата Y: инвертируем ось Y для соответствия системе координат изображения
    screen_points[:, 1] = np.clip(
        np.rint(IMAGE_HEIGHT - transformed[:, 1]),
        0,
        IMAGE_HEIGHT - 1,
    )

    return screen_points


def render_model(vertices_2d: np.ndarray, faces: list[list[int]]) -> Image.Image:
    # Отрисовка модели на изображении
    image = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), color='black')
    draw = ImageDraw.Draw(image)

    # Цвета для заливки и контура полигонов
    fill_color = (235, 235, 235)
    outline_color = (120, 120, 120)

    # Отрисовка каждого полигона
    for face in faces:
        # Получаем экранные координаты вершин полигона
        polygon = [tuple(vertices_2d[vertex_index]) for vertex_index in face]
        # Рисуем полигон с заливкой и контуром
        draw.polygon(polygon, fill=fill_color, outline=outline_color)

    return image


def main():
    # Загрузка модели из OBJ файла
    points, faces = load_model(MODEL_PATH)
    print(f'Загружено: {len(points)} вершин, {len(faces)} полигонов')

    # Построение матрицы поворота
    rot = rotation_matrix(ALPHA_DEG, BETA_DEG, GAMMA_DEG)
    # Преобразование вершин: центрирование, масштабирование, поворот и сдвиг
    screen_vertices = prepare_vertices(points, rot)

    # Отрисовка модели на изображении
    image = render_model(screen_vertices, faces)
    # Сохранение результата
    image.save(OUTPUT_PATH)
    print(f'Изображение сохранено как {OUTPUT_PATH}')

    # Показ изображения
    image.show()



if __name__ == '__main__':
    main()

