from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.platypus import Table,TableStyle,Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor,black
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

out=Path('E:/cygwin64/home/taylo/Wildbits/Docs')
pdfmetrics.registerFont(TTFont('Arial','C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('ArialBold','C:/Windows/Fonts/arialbd.ttf'))
style=ParagraphStyle('body',fontName='Arial',fontSize=9.5,leading=12,textColor=black)
def P(s): return Paragraph(s,style)
p=out/'wildbits-rc16-endian-plan.pdf'
c=canvas.Canvas(str(p),pagesize=(612,792))
c.setTitle('WildBits rc16 - Big-endian correction plan')
c.setFillColor(HexColor('#bdeff5')); c.rect(0,690,612,102,fill=1,stroke=0)
c.setFillColor(black);c.setFont('ArialBold',21);c.drawString(30,757,'WildBits rc16 | Byte-order review')
c.setFont('Arial',11);c.drawString(30,735,'Existing RTL layout and planned 6809 big-endian corrections')
c.setFont('ArialBold',11);c.drawString(30,711,'NOT FIXED IN RC16  /  PLANNED - NO RTL CHANGES MADE')
rows=[['Register / scope','Existing rc16 mapping','Planned mapping','wildbits.d label impact'],
['WM8776 command<br/>K2 + Jr2<br/><br/>16-bit write','FE70 = bits 7:0<br/>FE71 = bits 15:8<br/>FE72 = start transfer','FE70 = bits 15:8<br/>FE71 = bits 7:0<br/>Keep FE72 trigger.','CODECCmdLo/Hi match current RTL.<br/><br/>Swap their offsets with the RTL; current Lo=0, Hi=1.'],
['Optical keyboard count<br/>K2 optical scanner<br/><br/>12-bit read','FE12 = bits 7:0<br/>FE13 = bits 11:8<br/>(upper nibble zero)','FE12 = bits 11:8<br/>FE13 = bits 7:0','OKB.CntLo/Hi match current RTL.<br/><br/>Swap offsets 2 and 3. Update byte-load order in readers.'],
['VICKY version / subversion<br/>K2 + Jr2<br/><br/>16-bit reads','FFDC = version low<br/>FFDD = version high<br/>FFDE = subversion low<br/>FFDF = subversion high','FFDC = version high<br/>FFDD = version low<br/>FFDE = subversion high<br/>FFDF = subversion low','VKY_VERSION_LO/HI and VKY_SUBVER_LO/HI match RTL.<br/><br/>Swap $1C/$1D and $1E/$1F offsets.'],
['Master control<br/>K2 + Jr2<br/><br/>Two control bytes','FFC0 = control 0<br/>(enable flags, named L)<br/>FFC1 = control 1<br/>(mode flags, named H)','Proposed H at FFC0;<br/>L at FFC1.<br/><br/>Move the complete control-byte functions.','MASTER_CTRL_REG_L/H match existing byte locations.<br/><br/>L/H imply a word, but RTL treats them as separate controls.'],
['Layer control<br/>K2 + Jr2<br/><br/>16-bit control output','FFC2 = low byte<br/>FFC3 = high byte<br/><br/>RTL output = {reg[3], reg[2]}','FFC2 = high byte<br/>FFC3 = low byte','VKY_LAYER_CTRL_L/H match current RTL.<br/><br/>Swap offsets 2 and 3 and preserve layer-field meaning.']]
data=[[P(x) for x in row] for row in rows]
t=Table(data,colWidths=[112,139,139,162],rowHeights=[32,94,94,98,104,88])
t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8),('GRID',(0,0),(-1,-1),.5,black),('BACKGROUND',(0,0),(-1,0),HexColor('#ffcd57')),('BACKGROUND',(0,1),(-1,1),HexColor('#ffd3cd')),('BACKGROUND',(0,2),(-1,2),HexColor('#fff1a6')),('BACKGROUND',(0,3),(-1,3),HexColor('#c6f2f5')),('BACKGROUND',(0,4),(-1,4),HexColor('#e8e8e8')),('BACKGROUND',(0,5),(-1,5),HexColor('#fff1a6'))]))
w,h=t.wrap(552,650);t.drawOn(c,30,678-h)
note=P('<b>Label conflicts:</b> No current value-to-RTL mismatch was found in these groups. Their low-first layout conflicts with the desired 6809 word order. Changing only wildbits.d would misdescribe rc16. Most pairs use sequential rmb declarations: moving lines changes offsets. Update RTL, definitions and callers together.')
note.wrap(552,80);note.drawOn(c,30,91)
c.setFont('Arial',8);c.drawString(30,67,'RTL: CODEC_Interface8.v:61-64; OpticalKeyboardScanner.v:195-196;')
c.drawString(30,56,'TinyVickyControl_Registers.v:83-86,155-158,171,233-250. Definitions: wildbits.d.')
c.drawString(30,40,'Source review: 2026-09-14 | Addresses are CPU addresses in hex | Planned release not assigned')
c.save()

print(p)
