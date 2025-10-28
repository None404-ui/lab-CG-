from PIL import Image, ImageDraw

f = open('model_1.obj')
points = []
for a in f:
    a_spl = a.split()
    if a_spl[0] == 'v':
        points.append([float(a_spl[1]), float(a_spl[2]), float(a_spl[3])])

img = Image.new('RGB', (2000, 2000), color='black')
draw = ImageDraw.Draw(img)

for point in points:
    x, y, z = point

    screen_x = int(5000 * x + 1000)
    screen_y = int(-5000 * y + 1000)

    if 0 <= screen_x < 2000 and 0 <= screen_y < 2000:
        draw.rectangle([screen_x - 1, screen_y - 1, screen_x + 1, screen_y + 1], fill='white')

img.save('model_points_pil.png')
img.show()