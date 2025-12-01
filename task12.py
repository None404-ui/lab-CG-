import numpy as np
from PIL import Image
import random
import math

# Импорт функции отрисовки треугольника
from task8 import draw_triangle
# Импорт функции вычисления нормали
from task11 import triangle_normal

points = []
faces = []

with open('model_1.obj', 'r') as f:
    for line in f:
        parts = line.strip().split()
        if not parts:
            continue

        if parts[0] == 'v' and len(parts) >= 4:
            # Сохраняем координаты вершин как числа с плавающей точкой
            x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
            points.append([x, y, z])

        elif parts[0] == 'f':
            # Создаем список индексов вершин для полигона
            face_vertices = []
            for vertex_data in parts[1:]:
                vertex_parts = vertex_data.split('/')
                vertex_index = int(vertex_parts[0]) - 1  # -1 потому что в OBJ нумерация с 1
                face_vertices.append(vertex_index)

            if len(face_vertices) >= 3:
                faces.append(face_vertices)

print(f"Загружено: {len(points)} вершин, {len(faces)} полигонов")

# Границы модели для масштабирования
if points:
    x_coords = [p[0] for p in points]
    y_coords = [p[1] for p in points]
    min_x, max_x = min(x_coords), max(x_coords)
    min_y, max_y = min(y_coords), max(y_coords)

    model_width = max_x - min_x
    model_height = max_y - min_y

    # Масштабируем модель
    scale = min(1600 / model_width, 1600 / model_height) * 0.9

    # Центрируем модель на изображении
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    offset_x = 1000 - center_x * scale
    offset_y = 1000 - center_y * scale
else:
    scale = 5000
    offset_x = 1000
    offset_y = 1000

# Преобразование 3D в 2D
def project_point(x, y, z):
    screen_x = x * scale + offset_x
    screen_y = 2000 - (y * scale + offset_y)  # Инвертируем Y для правильной ориентации
    return screen_x, screen_y

# Направление света
light_direction = [0, 0, 1]  # l̄ = [0, 0, 1]

# Создание изображения с помощью numpy
print("Создание изображения...")
image = np.zeros((2000, 2000, 3), dtype=np.uint8)  # RGB изображение

# Отрисовка всех полигонов модели с отсечением нелицевых граней
print("Отрисовка полигонов с отсечением нелицевых граней...")

for i, face in enumerate(faces):
    if len(face) < 3:
        continue

    # Получаем исходные 3D координаты вершин треугольника
    if 0 <= face[0] < len(points) and 0 <= face[1] < len(points) and 0 <= face[2] < len(points):
        x0, y0, z0 = points[face[0]]
        x1, y1, z1 = points[face[1]]
        x2, y2, z2 = points[face[2]]

        # Вычисляем нормаль треугольника
        n_x, n_y, n_z = triangle_normal(x0, y0, z0, x1, y1, z1, x2, y2, z2)

        # Вычисляем косинус угла падения света
        dot_product = n_x * light_direction[0] + n_y * light_direction[1] + n_z * light_direction[2]
        norm_n = math.sqrt(n_x * n_x + n_y * n_y + n_z * n_z)
        norm_l = math.sqrt(light_direction[0] * light_direction[0] + 
                          light_direction[1] * light_direction[1] + 
                          light_direction[2] * light_direction[2])
        
        if norm_n > 0 and norm_l > 0:
            cosine = dot_product / (norm_n * norm_l)
        else:
            cosine = 0

        # Отрисовываем только полигоны с cos < 0
        if cosine < 0:
            # Получаем экранные координаты всех вершин полигона
            screen_points = []
            for vertex_index in face:
                if 0 <= vertex_index < len(points):
                    x, y, z = points[vertex_index]
                    screen_x, screen_y = project_point(x, y, z)
                    screen_points.append((screen_x, screen_y))

            # Если полигон имеет больше 3 вершин, разбиваем на треугольники
            # Используем простой подход: берём первые 3 вершины для каждого треугольника
            if len(screen_points) >= 3:
                # Генерируем случайный цвет для каждого треугольника
                color = [random.randint(0, 255) for _ in range(3)]  # RGB

                # Отрисовываем треугольник с помощью нашей функции
                x0_screen, y0_screen = screen_points[0]
                x1_screen, y1_screen = screen_points[1]
                x2_screen, y2_screen = screen_points[2]

                draw_triangle(x0_screen, y0_screen, x1_screen, y1_screen, x2_screen, y2_screen, 2000, 2000, image, color)

        if i % 100 == 0:  # Показываем прогресс каждые 100 полигонов
            print(f"Обработано {i+1}/{len(faces)} полигонов")

print("Все полигоны обработаны")

# Сохранение модели
pil_image = Image.fromarray(image)
pil_image.save('model.png')
print("Изображение сохранено как 'model.png'")

pil_image.show()
print("Готово!")






