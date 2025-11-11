from PIL import Image, ImageDraw
import numpy as np

def barycentric_coordinates(x, y, x0, y0, x1, y1, x2, y2):
    lambda0 = ((x - x2) * (y1 - y2) - (x1 - x2) * (y - y2)) / ((x0 - x2) * (y1 - y2) - (x1 - x2) * (y0 - y2))
    lambda1 = ((x0 - x2) * (y - y2) - (x - x2) * (y0 - y2)) / ((x0 - x2) * (y1 - y2) - (x1 - x2) * (y0 - y2))
    lambda2 = 1.0 - lambda0 - lambda1
    return lambda0, lambda1, lambda2


def draw_triangle(x0, y0, x1, y1, x2, y2, image_width, image_height, image, color):

    xmin = int(min(x0, x1, x2))
    xmax = int(max(x0, x1, x2)) + 1
    ymin = int(min(y0, y1, y2))
    ymax = int(max(y0, y1, y2)) + 1

    if xmin < 0:
        xmin = 0
    if xmax > image_width:
        xmax = image_width
    if ymin < 0:
        ymin = 0
    if ymax > image_height:
        ymax = image_height


    for y in range(ymin, ymax):
        for x in range(xmin, xmax):
            lambda0, lambda1, lambda2 = barycentric_coordinates(x, y, x0, y0, x1, y1, x2, y2)
            if lambda0 >= 0 and lambda1 >= 0 and lambda2 >= 0:
                image[y, x] = color
image = np.zeros((2000, 2000, 3), dtype=np.uint8)
draw_triangle(-20.0, 80.0, 80.0, 80.0, 30.0, 180.0, 2000,2000,image,[255,0,0])
draw_triangle(200.0, 800.0, 80.0, 80.0, 30.0, 180.0, 2000,2000,image,[0,255,0])
draw_triangle(1000.0, 800.0, 1150.0, 220.0, 1100.0, 180.0, 2000,2000,image,[0,0,255])
pil_image = Image.fromarray(image)
pil_image.save('triangle_tests.png')


