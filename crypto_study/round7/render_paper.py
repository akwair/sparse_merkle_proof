from pathlib import Path
import pypdfium2 as pdfium
from PIL import Image,ImageOps,ImageDraw
from pypdf import PdfReader
import json
ROOT=Path(__file__).resolve().parent
P=ROOT/'manuscript/main.pdf';OUT=ROOT/'pdf_qa';OUT.mkdir(exist_ok=True)
doc=pdfium.PdfDocument(P);images=[]
for i in range(len(doc)):
 im=doc[i].render(scale=1.5).to_pil().convert('RGB');im.save(OUT/f'page_{i+1:02}.png');images.append(im)
for start in range(0,len(images),4):
 thumbs=[]
 for i,im in enumerate(images[start:start+4],start+1):
  th=im.copy();th.thumbnail((600,850));tile=Image.new('RGB',(620,885),'#e5e7eb');tile.paste(th,((620-th.width)//2,25));ImageDraw.Draw(tile).text((10,7),f'Page {i}',fill='black');thumbs.append(tile)
 sheet=Image.new('RGB',(1240,1770),'white')
 for j,t in enumerate(thumbs):sheet.paste(t,((j%2)*620,(j//2)*885))
 sheet.save(OUT/f'sheet_{start//4+1}.png')
r=PdfReader(P);texts=[p.extract_text() for p in r.pages]
(OUT/'text.txt').write_text('\n\n'.join(texts),encoding='utf-8')
(OUT/'checks.json').write_text(json.dumps({'pages':len(r.pages),'page_characters':[len(t) for t in texts],'replacement_characters':sum(t.count('\ufffd') for t in texts),'unresolved_marker':any('??' in t for t in texts)},indent=2))
print('Rendered',len(doc),'pages.')
