from PIL import Image, ImageDraw



points = []
faces = []

with open('model_1.obj', 'r') as f:
    for line in f:
        parts = line.strip().split()
        if not parts:
            continue

        if parts[0] == 'v' and len(parts) >= 4:
            points.append([float(parts[1]), float(parts[2]), float(parts[3])])
        elif parts[0] == 'f':
            face_vertices = []
            for vertex_data in parts[1:]:
                vertex_parts = vertex_data.split('/')
                vertex_index = int(vertex_parts[0]) - 1
                face_vertices.append(vertex_index)
            if len(face_vertices) >= 3:
                faces.append(face_vertices)

# Настройка цветов и проекции
FILL_COLOR = (255, 255, 255)
OUTLINE_COLOR = (200, 200, 200)

if points:
    x_coords = [p[0] for p in points]
    y_coords = [p[1] for p in points]
    min_x, max_x = min(x_coords), max(x_coords) # левый и правы1 x
    min_y, max_y = min(y_coords), max(y_coords) # нижний и верхний y
    model_width = max_x - min_x# ширина модели
    model_height = max_y - min_y# высота модели
    scale = min(1600 / model_width, 1600 / model_height) * 0.9# масштаб
    center_x = (min_x + max_x) / 2# центр модели по x
    center_y = (min_y + max_y) / 2# центр модели по y
    offset_x = 1000 - center_x * scale
    offset_y = 1000 - center_y * scale
else:
    scale = 5000
    offset_x = 1000
    offset_y = 1000

# Создание изображения
image = Image.new('RGB', (2000, 2000), color='black')
draw = ImageDraw.Draw(image)

def project_3d_to_2d(x, y, z):
    screen_x = int(x * scale + offset_x)
    screen_y = int(2000 - (y * scale + offset_y))
    return screen_x, screen_y

# Отрисовка полигонов
for face in faces:
    screen_points = []
    for vertex_index in face:
        if 0 <= vertex_index < len(points):
            x, y, z = points[vertex_index]
            screen_x, screen_y = project_3d_to_2d(x, y, z)
            screen_points.append((screen_x, screen_y))

    if len(screen_points) >= 3:
        draw.polygon(screen_points, fill=FILL_COLOR)

        for i in range(len(screen_points)):
            start = screen_points[i]

            if i == len(screen_points) - 1:  # Если это последняя вершина
                end = screen_points[0]  # Соединяем с первой вершиной
            else:
                end = screen_points[i + 1]  # Иначе со следующей вершиной

            draw.line([start, end], fill=OUTLINE_COLOR, width=1)

# Сохранение результата
image.save('model.png')
image.show()