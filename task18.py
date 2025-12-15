import numpy as np
from PIL import Image

from task7 import barycentric_coordinates
from task11 import triangle_normal

# Загрузка модели из файла.
points = []  # список всех вершин (x, y, z)
faces = []  # список полигонов (индексы вершин)
texture_coords = []  # список координат текстур (u, v)
face_texture_indices = []  # список индексов текстур для каждого полигона

with open('model_1.obj', 'r') as f:
    for line in f:
        parts = line.strip().split()

        # Строка вершины: "v x y z"
        if parts[0] == 'v':
            x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
            points.append([x, y, z])

        # Строка координат текстуры: "vt u v"
        elif parts[0] == 'vt':
            u = float(parts[1])
            v = float(parts[2])
            texture_coords.append([u, v])

        elif parts[0] == 'f':
            face_vertices = []
            face_tex_indices = []
            for vertex_data in parts[1:]:
                vertex_parts = vertex_data.split('/')
                vertex_index = int(vertex_parts[0]) - 1
                face_vertices.append(vertex_index)
                tex_index = int(vertex_parts[1]) - 1
                face_tex_indices.append(tex_index)
            faces.append(face_vertices)
            face_texture_indices.append(face_tex_indices)

print(f"Загружено: {len(points)} вершин, {len(faces)} полигонов, {len(texture_coords)} координат текстур")

# Направление света
light_direction = np.array([0.0, 0.0, 1.0])  # свет светит вдоль оси Z
light_norm = np.linalg.norm(light_direction)

# Вычисление нормалей для каждой вершины
# Нормаль вершины = сумма нормалей всех полигонов, которые используют эту вершину
vertex_normals = np.zeros((len(points), 3), dtype=np.float64)

for face in faces:
    # Берём координаты трёх вершин треугольника
    x0, y0, z0 = points[face[0]]
    x1, y1, z1 = points[face[1]]
    x2, y2, z2 = points[face[2]]

    # Вычисляем нормаль этого треугольника
    n_x, n_y, n_z = triangle_normal(x0, y0, z0, x1, y1, z1, x2, y2, z2)
    face_normal = np.array([n_x, n_y, n_z])

    # Добавляем эту нормаль ко всем вершинам треугольника
    for vertex_index in face:
        vertex_normals[vertex_index] += face_normal

# Вычисление освещения для каждой вершины
vertex_intensity = np.zeros(len(points), dtype=np.float64)

for i in range(len(points)):
    n = vertex_normals[i]
    n_norm = np.linalg.norm(n)  # длина вектора нормали

    if n_norm > 0 and light_norm > 0:
        # Косинус угла между нормалью и светом
        dot_product = np.dot(n, light_direction)
        vertex_intensity[i] = dot_product / (n_norm * light_norm)

# Загрузка изображения текстуры в память
texture_image = Image.open('bunny-atlas.jpg')
texture_array = np.array(texture_image)
texture_width, texture_height = texture_image.size
WT = texture_width  # ширина текстуры
HT = texture_height  # высота текстуры

# Подготовка к отрисовке: масштаб и центрирование
# Находим границы модели
x_coords = [p[0] for p in points]
y_coords = [p[1] for p in points]
min_x, max_x = min(x_coords), max(x_coords)
min_y, max_y = min(y_coords), max(y_coords)

# Размеры модели
model_width = max_x - min_x
model_height = max_y - min_y

# Масштаб чтобы модель поместилась на изображение
scale = min(1600 / model_width, 1600 / model_height) * 0.9

# Сдвиг чтобы модель была в центре изображения
center_x = (min_x + max_x) / 2
center_y = (min_y + max_y) / 2
offset_x = 1000 - center_x * scale
offset_y = 1000 - center_y * scale


def project_point(x, y, z):
    # Переводит 3D координаты в 2D координаты на экране
    screen_x = x * scale + offset_x
    # Минус потому что в изображении Y растёт вниз, а в модели вверх
    screen_y = 2000 - (y * scale + offset_y)
    return screen_x, screen_y


# Создание изображения и z-буфера
image = np.zeros((2000, 2000, 3), dtype=np.uint8)  # чёрное изображение
z_buffer = np.full((2000, 2000), float('inf'), dtype=np.float32)  # буфер глубины


def draw_triangle_textured(z0, z1, z2,
                           x0_screen, y0_screen, x1_screen, y1_screen, x2_screen, y2_screen,
                           u0t, v0t, u1t, v1t, u2t, v2t,
                           I0, I1, I2,
                           image_width, image_height, image, z_buffer, texture_array, WT, HT):
    # Находим прямоугольник вокруг треугольника
    xmin = max(0, int(min(x0_screen, x1_screen, x2_screen)))
    xmax = min(image_width, int(max(x0_screen, x1_screen, x2_screen)) + 1)
    ymin = max(0, int(min(y0_screen, y1_screen, y2_screen)))
    ymax = min(image_height, int(max(y0_screen, y1_screen, y2_screen)) + 1)

    # Перебираем все пиксели в этом прямоугольнике
    for y in range(ymin, ymax):
        for x in range(xmin, xmax):
            # Вычисляем барицентрические координаты
            lambda0, lambda1, lambda2 = barycentric_coordinates(
                x, y, x0_screen, y0_screen, x1_screen, y1_screen, x2_screen, y2_screen
            )

            # Если все веса положительные - точка внутри треугольника
            if lambda0 > 0 and lambda1 > 0 and lambda2 > 0:
                # Вычисляем глубину точки
                z_point = lambda0 * z0 + lambda1 * z1 + lambda2 * z2

                # Рисуем только если эта точка ближе чем то что уже нарисовано
                if z_point < z_buffer[y, x]:
                    # Вычисляем координаты текстуры используя барицентрическую интерполяцию
                    u_texture = WT * (lambda0 * u0t + lambda1 * u1t + lambda2 * u2t)
                    v_interp = lambda0 * v0t + lambda1 * v1t + lambda2 * v2t
                    v_texture = HT * (1 - v_interp)  # Инвертируем v координату

                    # Округляем координаты
                    u_texture = int(round(u_texture))
                    v_texture = int(round(v_texture))

                    # Проверяем границы текстуры
                    u_texture = max(0, min(WT - 1, u_texture))
                    v_texture = max(0, min(HT - 1, v_texture))

                    # Получаем цвет из текстуры
                    texture_color = texture_array[v_texture, u_texture]

                    # Интерполируем интенсивность освещения
                    intensity = lambda0 * I0 + lambda1 * I1 + lambda2 * I2
                    brightness = -225 * intensity
                    # Ограничиваем яркость от 0 до 255 (как в задании 17)
                    brightness = max(0, min(255, int(brightness)))
                    brightness_factor = brightness / 255.0
                    # Применяем затенение к текстуре
                    shaded_color = texture_color * brightness_factor
                    # Ограничиваем значения от 0 до 255
                    shaded_color = np.clip(shaded_color, 0, 255).astype(np.uint8)

                    # Рисуем пиксель цветом из текстуры с затенением
                    image[y, x] = shaded_color

                    # Запоминаем глубину этой точки
                    z_buffer[y, x] = z_point


# Отрисовка всех полигонов
for face_idx, face in enumerate(faces):
    # Берём координаты вершин
    x0, y0, z0 = points[face[0]]
    x1, y1, z1 = points[face[1]]
    x2, y2, z2 = points[face[2]]

    # Переводим вершины в экранные координаты
    x0_screen, y0_screen = project_point(x0, y0, z0)
    x1_screen, y1_screen = project_point(x1, y1, z1)
    x2_screen, y2_screen = project_point(x2, y2, z2)

    tex_indices = face_texture_indices[face_idx]
    u0t, v0t = texture_coords[tex_indices[0]]
    u1t, v1t = texture_coords[tex_indices[1]]
    u2t, v2t = texture_coords[tex_indices[2]]

    # Берём яркость каждой вершины
    I0 = vertex_intensity[face[0]]
    I1 = vertex_intensity[face[1]]
    I2 = vertex_intensity[face[2]]

    draw_triangle_textured(
        z0, z1, z2,
        x0_screen, y0_screen, x1_screen, y1_screen, x2_screen, y2_screen,
        u0t, v0t, u1t, v1t, u2t, v2t,
        I0, I1, I2,
        2000, 2000, image, z_buffer, texture_array, WT, HT
    )

# Сохранение результата
pil_image = Image.fromarray(image)
pil_image.save('model.png')
print("Изображение сохранено как 'model.png'")
pil_image.show()

