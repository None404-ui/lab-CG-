from PIL import Image
import numpy as np

h=int(input("Введите количество строк: "))
w=int(input("Введите количество столбцов: "))
matrix=np.full((h,w,3),0 ,dtype=np.uint8)
for y in range(h):
   for x in range(w):
       value=(x+y)%155
       matrix[y, x] =[value,value,value]



print(matrix)
matrix_image=Image.fromarray(matrix, 'RGB')
matrix_image.save('model.png')
