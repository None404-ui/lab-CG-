f = open('model_1.obj')
points = []
arr = []
for a in f:
    a_spl = a.split()
    if (a_spl[0] == 'v'):
        print(a)
        points.append([float(a_spl[1]),
                         float(a_spl[2]),
                         float(a_spl[3])])

