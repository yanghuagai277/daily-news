from PIL import Image, ImageDraw
import os

os.makedirs("icons", exist_ok=True)
SIZE = 512
BG = (31, 111, 235)


def make(path, maskable=False):
    img = Image.new("RGB", (SIZE, SIZE), BG)
    d = ImageDraw.Draw(img)
    cx = cy = SIZE // 2
    if maskable:
        r = int(SIZE * 0.42)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255))
        r2 = int(SIZE * 0.27)
        d.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], fill=BG)
    else:
        r = int(SIZE * 0.30)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255))
        r2 = int(SIZE * 0.18)
        d.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], fill=BG)
    img.save(path)
    print("wrote", path)


make("icons/icon-512.png", maskable=False)
make("icons/icon-192.png", maskable=False)
make("icons/maskable-512.png", maskable=True)
Image.open("icons/icon-512.png").resize((180, 180)).save("icons/apple-touch-icon.png")
print("done")
