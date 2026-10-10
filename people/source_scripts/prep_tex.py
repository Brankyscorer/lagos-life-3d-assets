# Resize Rocketbox TGA textures to 512 (jpg colour/normal, png opacity with alpha) -> /workspace/rb/tex/<avatar>/512
import sys, os, glob
from PIL import Image
for av in sys.argv[1:]:
    src=f'/workspace/rb/av/{av}/Textures'; dst=f'/workspace/rb/tex/{av}/512'; os.makedirs(dst,exist_ok=True)
    for f in glob.glob(f'{src}/*.tga'):
        n=os.path.basename(f)[:-4]
        if 'specular' in n: continue
        im=Image.open(f)
        if 'opacity' in n:
            im.convert('RGBA').resize((512,512),Image.LANCZOS).save(f'{dst}/{n}.png',optimize=True)
        else:
            im.convert('RGB').resize((512,512),Image.LANCZOS).save(f'{dst}/{n}.jpg',quality=88,optimize=True)
    print(av, sorted(os.listdir(dst)))
