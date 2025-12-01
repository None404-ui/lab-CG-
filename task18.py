import numpy as np
from PIL import Image
from pathlib import Path
from task7 import barycentric_coordinates
from task11 import triangle_normal

IMAGE_WIDTH = 2000
IMAGE_HEIGHT = 2000
MODEL_PATH = Path('model_1.obj')
OUTPUT_PATH = Path('model.png')

LIGHT_DIRECTION = np.array([0.0, 0.0, 1.0], dtype=np.float32)


def load_model_with_uv(path: Path) -> Tuple[np.ndarray, np.ndarray, List[List[int]], List[List[Optional[int]]]]:
    vertices: list[list[float]] = []
    tex_coords: list[list[float]] = []
    faces: list[list[int]] = []
    face_tex_indices: list[list[Optional[int]]] = []

    with path.open('r', encoding='utf-8') as obj_file:
        for line in obj_file:
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue

            parts = stripped.split()
            prefix = parts[0]

            if prefix == 'v':
                vertices.append(list(map(float, parts[1:4])))
            elif prefix == 'vt':
                tex_coords.append(list(map(float, parts[1:3])))
            elif prefix == 'f':
                v_indices: list[int] = []
                vt_indices: list[Optional[int]] = []
                for vertex_data in parts[1:]:
                    indices = vertex_data.split('/')
                    v_indices.append(int(indices[0]) - 1)
                    if len(indices) > 1 and indices[1]:
                        vt_indices.append(int(indices[1]) - 1)
                    else:
                        vt_indices.append(None)

                if len(v_indices) == 3:
                    faces.append(v_indices)
                    face_tex_indices.append(vt_indices)
                else:
                    # Простейшая фан-триангуляция, если встретятся полигоны > 3 вершин
                    for i in range(1, len(v_indices) - 1):
                        faces.append([v_indices[0], v_indices[i], v_indices[i + 1]])
                        face_tex_indices.append([vt_indices[0], vt_indices[i], vt_indices[i + 1]])

    return (
        np.array(vertices, dtype=np.float32),
        np.array(tex_coords, dtype=np.float32) if tex_coords else np.zeros((0, 2), dtype=np.float32),
        faces,
        face_tex_indices,
    )


def compute_projection_params(points: np.ndarray) -> Tuple[float, float, float]:
    x_coords = points[:, 0]
    y_coords = points[:, 1]

    min_x, max_x = x_coords.min(), x_coords.max()
    min_y, max_y = y_coords.min(), y_coords.max()

    width = max(max_x - min_x, 1e-6)
    height = max(max_y - min_y, 1e-6)

    scale = 0.9 * min(IMAGE_WIDTH / width, IMAGE_HEIGHT / height)
    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0

    offset_x = IMAGE_WIDTH / 2.0 - center_x * scale
    offset_y = IMAGE_HEIGHT / 2.0 - center_y * scale
    return scale, offset_x, offset_y


def project_point(point: Sequence[float], scale: float, offset_x: float, offset_y: float) -> Tuple[float, float]:
    screen_x = point[0] * scale + offset_x
    screen_y = IMAGE_HEIGHT - (point[1] * scale + offset_y)
    return screen_x, screen_y


def compute_vertex_normals(points: np.ndarray, faces: Sequence[Sequence[int]]) -> np.ndarray:
    normals = np.zeros_like(points, dtype=np.float32)
    for face in faces:
        idx0, idx1, idx2 = face
        x0, y0, z0 = points[idx0]
        x1, y1, z1 = points[idx1]
        x2, y2, z2 = points[idx2]
        normal = np.array(triangle_normal(x0, y0, z0, x1, y1, z1, x2, y2, z2), dtype=np.float32)
        normals[face] += normal

    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    np.divide(
        normals,
        np.where(lengths == 0.0, 1.0, lengths),
        out=normals,
    )
    return normals


def draw_triangle_textured(
    projected: Sequence[Tuple[float, float]],
    depths: Sequence[float],
    tex_coords: Sequence[Tuple[float, float]],
    intensities: Sequence[float],
    image: np.ndarray,
    z_buffer: np.ndarray,
    texture: np.ndarray,
) -> None:
    (x0, y0), (x1, y1), (x2, y2) = projected
    z0, z1, z2 = depths
    uv0, uv1, uv2 = tex_coords
    i0, i1, i2 = intensities

    xmin = max(0, int(np.floor(min(x0, x1, x2))))
    xmax = min(IMAGE_WIDTH - 1, int(np.ceil(max(x0, x1, x2))))
    ymin = max(0, int(np.floor(min(y0, y1, y2))))
    ymax = min(IMAGE_HEIGHT - 1, int(np.ceil(max(y0, y1, y2))))

    tex_h, tex_w = texture.shape[:2]

    for y in range(ymin, ymax + 1):
        for x in range(xmin, xmax + 1):
            lambdas = barycentric_coordinates(
                x + 0.5,
                y + 0.5,
                x0,
                y0,
                x1,
                y1,
                x2,
                y2,
            )
            if any(np.isnan(l) for l in lambdas):
                continue

            l0, l1, l2 = lambdas
            if l0 < -1e-5 or l1 < -1e-5 or l2 < -1e-5:
                continue

            depth = l0 * z0 + l1 * z1 + l2 * z2
            if depth >= z_buffer[y, x]:
                continue

            u = np.clip(l0 * uv0[0] + l1 * uv1[0] + l2 * uv2[0], 0.0, 1.0)
            v = np.clip(l0 * uv0[1] + l1 * uv1[1] + l2 * uv2[1], 0.0, 1.0)

            tex_x = int(np.clip(round(u * (tex_w - 1)), 0, tex_w - 1))
            # OBJ координата V отсчитывается снизу, поэтому отражаем по вертикали
            tex_y = int(np.clip(round((1.0 - v) * (tex_h - 1)), 0, tex_h - 1))

            color = texture[tex_y, tex_x].astype(np.float32)
            intensity = np.clip(l0 * i0 + l1 * i1 + l2 * i2, 0.0, 1.0)
            shaded = np.clip(color * (0.2 + 0.8 * intensity), 0, 255)

            image[y, x] = shaded.astype(np.uint8)
            z_buffer[y, x] = depth


def main() -> None:
    points, tex_coords, faces, tex_faces = load_model_with_uv(MODEL_PATH)
    print(f'Загружено: {len(points)} вершин, {len(faces)} треугольников')

    if tex_coords.size == 0:
        raise RuntimeError('В модели отсутствуют текстурные координаты (строки vt)')

    texture_image = Image.open(TEXTURE_PATH).convert('RGB')
    texture = np.array(texture_image, dtype=np.uint8)
    print(f'Текстура: {texture.shape[1]}x{texture.shape[0]} пикселей')

    scale, offset_x, offset_y = compute_projection_params(points)
    vertex_normals = compute_vertex_normals(points, faces)
    light_dir = LIGHT_DIRECTION / np.linalg.norm(LIGHT_DIRECTION)
    vertex_intensity = np.clip(vertex_normals @ light_dir, 0.0, 1.0)

    canvas = np.zeros((IMAGE_HEIGHT, IMAGE_WIDTH, 3), dtype=np.uint8)
    z_buffer = np.full((IMAGE_HEIGHT, IMAGE_WIDTH), np.inf, dtype=np.float32)

    for face, uv_indices in zip(faces, tex_faces):
        if None in uv_indices:
            continue

        world_vertices = points[face]
        projected = [
            project_point(world_vertices[i], scale, offset_x, offset_y)
            for i in range(3)
        ]
        depths = world_vertices[:, 2]
        uv_coords = tex_coords[uv_indices]
        intensities = vertex_intensity[face]

        draw_triangle_textured(
            projected,
            depths,
            uv_coords,
            intensities,
            canvas,
            z_buffer,
            texture,
        )

    result_image = Image.fromarray(canvas)
    result_image.save(OUTPUT_PATH)
    print(f'Изображение сохранено как {OUTPUT_PATH}')
    result_image.show()


if __name__ == '__main__':
    main()


