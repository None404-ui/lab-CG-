from PIL import Image
import numpy as np
import  math
h=int(input("Введите количество строк: "))
w=int(input("Введите количество столбцов: "))
matrix=np.full((h,w,3),100 ,dtype=np.uint8)

def x_loop_line(image, x0, y0, x1, y1, color):
    xchange = False
    if (abs(x0 - x1) < abs(y0 - y1)):
        x0, y0 = y0, x0
        x1, y1 = y1, x1
        xchange = True

    if (x0 > x1):
        x0, x1 = x1, x0
        y0, y1 = y1, y0

    y = y0
    dy = 2*abs(y1 - y0)
    derror = 0
    y_update = 1 if y1 > y0 else -1

    for x in range (x0, x1):
        if (xchange):
            image[x, y] = color
        else:
            image[y, x] = color
        derror += dy
        if (derror > (x1-x0)):
            derror -= 2*(x1-x0)
            y += y_update




print(matrix)

x0,y0=100,100
for i in range(13):
    a=(2*3.14*i)/13
    x1= int(100+95*math.cos(a))
    y1= int(100+95*math.sin(a))
    x_loop_line(matrix,x0,y0,x1,y1,255)
matrix_image=Image.fromarray(matrix, 'RGB')
matrix_image.save('model.png')
