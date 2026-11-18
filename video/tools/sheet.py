# Une imagenes en una hoja de contacto: python3 tools/sheet.py carpeta salida.png [columnas]
import sys, glob, re
from PIL import Image
d, outp = sys.argv[1], sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 4
def key(f):
    m = re.search(r'(E\d+)_(\d+)\.png$', f)
    return (m.group(1), int(m.group(2))) if m else (f, 0)
fs = sorted([f for f in glob.glob(d + '/E*_*.png')], key=key)
ims = [Image.open(f) for f in fs]
w, h = ims[0].size
out = Image.new('RGB', (w * cols, h * ((len(ims) + cols - 1) // cols)), 'white')
for i, im in enumerate(ims):
    out.paste(im, ((i % cols) * w, (i // cols) * h))
out.save(outp)
print(len(ims), 'imagenes')
