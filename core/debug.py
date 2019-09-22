# stuff for debugging color finding routines
import numpy as np
from PIL import Image

# draw point array
def draw_pa(img, pa, color=np.array([255,0,0],dtype="uint8")):
    data = np.array(img)
    for p in pa.points:
        data[p[0],p[1]] = color
    return Image.fromarray(data)
