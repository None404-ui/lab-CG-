from PIL import Image, ImageDraw



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



# Цвета
LINE_COLOR = (255, 255, 255)  # Белый цвет для рёбер

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

# Алгоритм Брезенхема
def draw_line_bresenham(draw, x1, y1, x2, y2, color):

    # Округляем координаты до ближайшего целого
    x1, y1 = int(round(x1)), int(round(y1))
    x2, y2 = int(round(x2)), int(round(y2))

    # Разница координат
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)

    # Направление движения
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1

    # Параметр принятия решения(отклонение от идеальной прямой)
    err = dx - dy

    while True:
        # Рисуем текущую точку
        draw.point((x1, y1), fill=color)

        # Если достигли конечной точки, выходим
        if x1 == x2 and y1 == y2:
            break

        # Вычисляем параметр принятия решения
        e2 = 2 * err

        # Корректируем движение по X или Y
        if e2 > -dy:
            err -= dy
            x1 += sx

        if e2 < dx:
            err += dx
            y1 += sy

# Преобразование 3D в 2D
def project_point(x, y, z):

    screen_x = x * scale + offset_x
    screen_y = 2000 - (y * scale + offset_y)  # Инвертируем Y для правильной ориентации
    return screen_x, screen_y

# Создание изображения
print("Создание изображения...")

image = Image.new('RGB', (2000, 2000), color='black')
draw = ImageDraw.Draw(image)

# Отрисовка ребер всех полигонов
print("Отрисовка рёбер...")

# Перебираем все полигоны
for face in faces:
    # Получаем экранные координаты всех вершин полигона
    screen_points = []
    for vertex_index in face:
        if 0 <= vertex_index < len(points):
            x, y, z = points[vertex_index]
            screen_x, screen_y = project_point(x, y, z)# Преобразование вершин из 3d в 2d
            screen_points.append((screen_x, screen_y))

    # Отрисовываем рёбра полигона (соединяем все вершины)
    if len(screen_points) >= 3:
        for i in range(len(screen_points)):
            # Соединяем текущую вершину со следующей
            start_point = screen_points[i]
            end_point = screen_points[(i + 1) % len(screen_points)]  # Замыкаем полигон

            # Используем алгоритм Брезенхема для отрисовки линии
            draw_line_bresenham(draw, start_point[0], start_point[1],
                              end_point[0], end_point[1], LINE_COLOR)

# Сохранение модели
print("Сохранение изображения...")
image.save('model_edges_bresenham.png')
image.show()
