from pathlib import Path
from html import escape
import re
import textwrap
from lxml import html
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, CondPageBreak, Table, TableStyle, Preformatted
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader
import pypdfium2 as pdfium

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output'/'pdf'
OUT.mkdir(parents=True,exist_ok=True)
TMP=ROOT/'tmp'/'pdfs'
TMP.mkdir(parents=True,exist_ok=True)
for name,file in [('Arial','arial.ttf'),('Arial-Bold','arialbd.ttf'),('Arial-Italic','ariali.ttf'),('Arial-BoldItalic','arialbi.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(Path('C:/Windows/Fonts')/file)))
pdfmetrics.registerFontFamily('Arial',normal='Arial',bold='Arial-Bold',italic='Arial-Italic',boldItalic='Arial-BoldItalic')
GREEN=colors.HexColor('#254d3b')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='Text',fontName='Arial',fontSize=9.5,leading=14,spaceAfter=8,textColor=colors.HexColor('#24352e')))
styles.add(ParagraphStyle(name='TitleDoc',fontName='Arial-Bold',fontSize=32,leading=39,textColor=GREEN,spaceAfter=24))
styles.add(ParagraphStyle(name='Chapter',fontName='Arial-Bold',fontSize=21,leading=26,textColor=GREEN,spaceAfter=20))
styles.add(ParagraphStyle(name='Sub',fontName='Arial-Bold',fontSize=12,leading=16,textColor=GREEN,spaceBefore=15,spaceAfter=8,keepWithNext=True))
styles.add(ParagraphStyle(name='Cell',parent=styles['Text'],fontSize=8,leading=11,spaceAfter=0,splitLongWords=True))
styles.add(ParagraphStyle(name='CellHead',parent=styles['Cell'],fontName='Arial-Bold'))
styles.add(ParagraphStyle(name='CodeDoc',fontName='Courier',fontSize=7.5,leading=10.5,spaceBefore=6,spaceAfter=10))
styles.add(ParagraphStyle(name='Source',parent=styles['Text'],fontSize=8,leading=11,textColor=colors.HexColor('#657268')))

tree=html.parse(str(ROOT/'documentation'/'backend'/'index.html'))
story=[]
def clean(s):
    return s.replace('\u2011','-').replace('\u2013','-').replace('\u2014','-').replace('\u00a0',' ')
def text(el): return clean(''.join(el.itertext()).strip())
def inline(el):
    result=escape(clean(el.text or ''))
    for child in el:
        content=inline(child)
        if child.tag in ('strong','b'): content='<b>'+content+'</b>'
        elif child.tag in ('em','i'): content='<i>'+content+'</i>'
        elif child.tag=='br': content='<br/>'
        elif child.tag=='code': content='<font name="Courier" size="8">'+content+'</font>'
        result+=content+escape(clean(child.tail or ''))
    return result
def para(value,style='Text'): return Paragraph(value,styles[style])

def emit(el):
    tag=el.tag
    cls=el.get('class','')
    if tag in ('script','style','input','output','button') or cls in ('eyebrow','symbols') or 'simulator' in cls: return
    if tag=='h2': return
    if tag in ('h3','summary'):
        story.append(para(inline(el),'Sub')); return
    if tag=='p':
        value=inline(el)
        if 'bouton' in text(el).lower() and ('PDF' in text(el) or 'Imprimer' in text(el)): return
        if 'documentation fonctionne hors ligne' in text(el):
            value='Ce PDF constitue un instantané de l’analyse et du code. La clé secrète Django est masquée. Aucune donnée personnelle, aucun jeton de robot et aucun contenu de session de la base ne sont reproduits.'
        story.append(para(value));return
    if tag=='a':
        if story and isinstance(story[-1],Paragraph): story[-1].keepWithNext=True
        story.append(para(escape(text(el)),'Source')); return
    if tag in ('ol','ul'):
        for i,li in enumerate(el,1): story.append(para(('<b>'+str(i)+'.</b> ' if tag=='ol' else '- ')+inline(li)))
        return
    if tag=='pre':
        raw=text(el)
        if 'source-code' in cls:
            raw='\n'.join((text(span.find('i')).rjust(4)+'  '+clean(span.find('i').tail or '').rstrip()) for span in el.xpath('./code/span'))
        raw=raw.replace('→','->').replace('──','--').replace('│','|').replace('├','+').replace('└','+').replace('┘','+').replace('─','-').replace('≤','<=')
        lines=[]
        for line in raw.splitlines():
            lines.extend(textwrap.wrap(line,width=103,replace_whitespace=False,drop_whitespace=False,subsequent_indent='      ') or [''])
        story.append(Preformatted('\n'.join(lines),styles['CodeDoc']));return
    if tag=='table':
        rows=[]
        for tr in el.xpath('./thead/tr | ./tbody/tr | ./tr'):
            rows.append([para(inline(td),'CellHead' if td.tag=='th' else 'Cell') for td in tr])
        if not rows:return
        n=len(rows[0]); widths={2:[155,340],3:[105,180,210],4:[160,65,105,165]}.get(n,[495/n]*n)
        t=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e9eee4')),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#d4dccd')),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
        story.extend([t,Spacer(1,12)]);return
    if cls=='flow':
        values=[text(x).replace('\n',' ') for x in el if x.tag=='span']
        story.append(para(' → '.join(escape(v) for v in values)));return
    if cls=='callout':story.append(para(inline(el)));return
    for child in el:emit(child)

class Doc(SimpleDocTemplate):
    def afterFlowable(self,f):
        if isinstance(f,Paragraph) and f.style.name=='Chapter':
            label=f.getPlainText(); key='chapter-'+str(self.page)
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(label,key,0)
            self.notify('TOCEntry',(0,label,self.page,key))

def page(canvas,doc):
    canvas.saveState()
    w,h=doc.pagesize
    if doc.page>1:
        canvas.setFont('Arial',8);canvas.setFillColor(GREEN)
        canvas.drawString(50,h-30,'ROBOAGRI-KIN  /  ANALYSE DU BACKEND')
        canvas.setStrokeColor(colors.HexColor('#d4dccd'));canvas.line(50,42,w-50,42)
        canvas.setFont('Arial',8);canvas.drawString(50,28,'Analyse du code local - 18 novembre 2026')
        canvas.drawRightString(w-50,28,str(doc.page))
    canvas.restoreState()

story.extend([Spacer(1,95),para('ROBOAGRI-KIN','Sub'),para('Comprendre<br/>le backend','TitleDoc'),para('Architecture, base de données, API et règles métier','Sub'),Spacer(1,22),para('Document de référence pour l’équipe'),para('Analyse de l’implémentation locale du 18 novembre 2026'),Spacer(1,30),para('<b>12 modèles métier · 5 domaines · 3 parcours détaillés</b>'),para('Une explication du fonctionnement réel, des fonctions encore incomplètes et des contrôles effectués, suivie du dictionnaire des données et du code source numéroté.'),Spacer(1,35),para('Périmètre : backend Django RoboAgri-Kin et ses interactions avec le frontend. Aucun essai sur robot physique. Les données de la base ne sont pas reproduites.','Source'),PageBreak(),para('Sommaire','TitleDoc')])
toc=TableOfContents()
toc.levelStyles=[ParagraphStyle(name='TOC',fontName='Arial',fontSize=10,leading=15,spaceBefore=7,textColor=GREEN)]
story.extend([toc,PageBreak()])
for i,section in enumerate(tree.xpath('//section[@data-chapter]'),1):
    if i>1:story.extend([CondPageBreak(170),Spacer(1,25)])
    title=text(section.find('h2'))
    story.append(para(f'{i:02d}. {escape(title)}','Chapter'))
    for child in section:emit(child)

target=OUT/'RoboAgri-Kin_Explication_Backend.pdf'
doc=Doc(str(target),pagesize=(595.28,841.89),leftMargin=50,rightMargin=50,topMargin=55,bottomMargin=58,title='RoboAgri-Kin - Explication du backend',author='Documentation technique RoboAgri-Kin')
doc.multiBuild(story,onFirstPage=page,onLaterPages=page)
reader=PdfReader(str(target))
extracted='\n'.join(p.extract_text() or '' for p in reader.pages)
assert '33 tests' in extracted
assert 'django-insecure-' not in extracted
assert len(reader.pages)>15
pdf=pdfium.PdfDocument(str(target))
sample=[0,1,2,5,10,len(pdf)//2,len(pdf)-2]
from PIL import Image,ImageOps,ImageDraw
thumbs=[]
for index in sample:
    im=pdf[index].render(scale=1.2).to_pil().convert('RGB')
    im.save(TMP/f'page-{index+1}.png')
    im.thumbnail((360,510))
    tile=Image.new('RGB',(380,545),'#dfe4de');tile.paste(im,((380-im.width)//2,20))
    ImageDraw.Draw(tile).text((12,525),f'Page {index+1}',fill='black');thumbs.append(tile)
sheet=Image.new('RGB',(380*4,545*2),'#dfe4de')
for i,t in enumerate(thumbs):sheet.paste(t,((i%4)*380,(i//4)*545))
sheet.save(TMP/'controle.pdf.png')
print(str(target))
print('Pages:',len(reader.pages),'Bytes:',target.stat().st_size,'Extracted characters:',len(extracted))
