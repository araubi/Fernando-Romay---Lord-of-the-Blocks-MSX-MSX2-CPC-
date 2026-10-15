import sys
from PIL import Image
fs=[int(x) for x in sys.argv[2].split(',')]
ims=[Image.open('/tmp/claude-0/cpc_%d.png'%f) for f in fs]
W=Image.new('RGB',(1280,200*((len(ims)+1)//2)))
for i,im in enumerate(ims): W.paste(im,((i%2)*640,(i//2)*200))
W.save(sys.argv[1])
