from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
P=Path(__file__).resolve().parent
for n,f in [('Arial','arial.ttf'),('Bold','arialbd.ttf'),('Mono','consola.ttf')]:
 pdfmetrics.registerFont(TTFont(n,str(Path('C:/Windows/Fonts')/f)))
W,H=1455,1440
c=canvas.Canvas(str(P/'wildbits-rc16-memory-map-large-type.pdf'),pagesize=(W*2,H*2))
c.scale(2,2)
c.setTitle('WildBits rc16 memory layout - address grid')
rows=[]
colors={'ram':'FFF0A6','io':'FFD0CA','mmu':'AEEBF2','video':'D0F4F7','sound':'FFDFD8','gap':'E5E5E5','vector':'FFF5BF','flash':'B8EDF3'}
def row(block,offset,start,end,what,mode,kind='io'):
 rows.append(([block,offset,start,end,what,mode],kind))
def band(s): rows.append((s,'band'))
band('CPU LOGICAL ADDRESS SPACE - fixed windows override the selected MMU slot')
row('Slot 0-7','$0000-$1FFF','$0000','$FFFF','Eight CPU slots, 8 KB each; each slot selects one MMU block','Four LUTs','ram')
row('Fixed','$1D00-$1DFF','$FD00','$FDFF','Internal 256-byte RAM window','FFA1 bit 0 = 1','mmu')
for a,b,s in [(0xFE00,0xFE0F,'System controls'),(0xFE10,0xFE1F,'K2 keyboard interface'),(0xFE20,0xFE2F,'Interrupt controller'),(0xFE30,0xFE3F,'Timer registers'),(0xFE40,0xFE4F,'Real-time clock'),(0xFE50,0xFE5F,'PS/2 keyboard and mouse'),(0xFE60,0xFE6F,'Serial UART / DriveWire'),(0xFE70,0xFE7F,'Codec control'),(0xFE80,0xFE8F,'IEC interface'),(0xFE90,0xFE9F,'External SD interface'),(0xFEA0,0xFEAF,'Mouse cursor controls'),(0xFEB0,0xFEBF,'VIA 0'),(0xFEC0,0xFEDF,'DMA registers'),(0xFEE0,0xFEFF,'Integer math registers'),(0xFF00,0xFF0F,'Internal SD interface'),(0xFF10,0xFF1F,'Splash flash SPI'),(0xFF20,0xFF2F,'WizFi interface'),(0xFF30,0xFF3F,'MIDI UART'),(0xFF40,0xFF4F,'W6100 Ethernet - K2'),(0xFF50,0xFF5F,'VS1053 sound interface'),(0xFF60,0xFF6F,'I2C control - K2'),(0xFF70,0xFF7F,'LCD interface - K2'),(0xFF80,0xFF8F,'NES / SNES controls'),(0xFF90,0xFF9F,'DIP-switch registers')]:
 row('Fixed',f'${a&8191:04X}-${b&8191:04X}',f'${a:04X}',f'${b:04X}',s,'CPU fixed decode')
row('Fixed','$1FA0','$FFA0','$FFA0','MMU: active LUT bits 1:0; edit LUT bits 5:4','MMU control','mmu')
row('Fixed','$1FA1','$FFA1','$FFA1','FLASHDIS bit 2; support read bit 7; RAM enables bits 1:0','Reset bits 6:0 = 0','mmu')
row('Fixed','$1FA8-$1FAF','$FFA8','$FFAF','Eight block-number registers for the selected edit LUT','MMU slot table','mmu')
row('Fixed','$1FB0-$1FBF','$FFB0','$FFBF','VIA 1 - K2','CPU fixed decode')
row('Fixed','$1FC0-$1FDF','$FFC0','$FFDF','Video controls; HIRES4 / CLUT-group register at $FFCB','CPU fixed decode','video')
row('Fixed','$1FE0-$1FEF','$FFE0','$FFEF','Floating-point math registers','CPU fixed decode')
row('Fixed','$1FF0-$1FFF','$FFF0','$FFFF','Internal vector RAM; reset vector at $FFFE-$FFFF','FFA1 bit 1 = 1','vector')
band('MMU BLOCK MAP - byte address = block x $2000 + offset; K2 and Jr2 rc16')
for block,lo,hi,size,mode,kind in [('$00-$3F',0,0x7FFFF,'512 KB SRAM','Always RAM','ram'),('$40-$7F',0x80000,0xFFFFF,'512 KB: flash select or SRAM','FLASHDIS 0 / 1','flash'),('$80-$9F',0x100000,0x13FFFF,'256 KB: cartridge select or SRAM','FLASHDIS 0 / 1','flash'),('$A0-$BF',0x140000,0x17FFFF,'256 KB SRAM','Always RAM','ram'),('$C0-$C7',0x180000,0x18FFFF,'64 KB sectored device address space','NotRAM','video'),('$C8-$CF',0x190000,0x19FFFF,'64 KB without CPU RAM selection','NotRAM','gap'),('$D0-$EF',0x1A0000,0x1DFFFF,'256 KB SRAM','Always RAM','ram'),('$F0-$FF',0x1E0000,0x1FFFFF,'128 KB without CPU RAM selection','NotRAM','gap')]:
 row(block,'$0000-$1FFF',f'${lo:06X}',f'${hi:06X}',size,mode,kind)
band('SECTORED DEVICE DETAIL - address columns below are page x $2000 + offset, not SRAM pin addresses')
for block,lo,hi,what,kind in [(0xC0,0,0x3FF,'Blue gamma table','video'),(0xC0,0x400,0x7FF,'Green gamma table','video'),(0xC0,0x800,0xBFF,'Red gamma table','video'),(0xC0,0xC00,0xFFF,'Mouse cursor image','video'),(0xC0,0x1000,0x10FF,'Bitmap registers','video'),(0xC0,0x1100,0x11FF,'Tile registers','video'),(0xC0,0x1200,0x12FF,'Miscellaneous video registers','video'),(0xC0,0x1300,0x16FF,'128 sprite attribute records, 8 bytes each','video'),(0xC0,0x1700,0x173F,'Text foreground palette / readback','video'),(0xC0,0x1740,0x177F,'Text background palette / readback','video'),(0xC1,0,0x7FF,'Font bank 0','video'),(0xC1,0x800,0xFFF,'Font bank 1','video'),(0xC1,0x1000,0x13FF,'Graphics palette 0','video'),(0xC1,0x1400,0x17FF,'Graphics palette 1','video'),(0xC1,0x1800,0x1BFF,'Graphics palette 2','video'),(0xC1,0x1C00,0x1FFF,'Graphics palette 3','video'),(0xC2,0,0x12BF,'Text character RAM - 4,800 bytes','video'),(0xC3,0,0x12BF,'Text attribute RAM - 4,800 bytes','video'),(0xC4,0,0x1F,'Left SID register window','sound'),(0xC4,0x80,0x9F,'Mono SID register window','sound'),(0xC4,0x100,0x11F,'Right SID register window','sound'),(0xC4,0x180,0x183,'OPL3 FM synthesis - writes only; no status / IRQ','sound'),(0xC4,0x200,0x217,'Left / mono / right PSG windows','sound')]:
 row(f'${block:02X}',f'${lo:04X}-${hi:04X}',f'${block*8192+lo:06X}',f'${block*8192+hi:06X}',what,f'Mapped page ${block:02X}',kind)
# Double the actual type size and reflow within the original chart width.
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import ParagraphStyle
from xml.sax.saxutils import escape
widths=[49,70,54,54,222,103]
data=[]; commands=[]
def add(vals,bg,header=False,span=False):
 idx=len(data); items=[]
 for i,s in enumerate(vals):
  style=ParagraphStyle('cell',fontName='Bold' if header else ('Mono' if i<4 and not span else 'Arial'),fontSize=7.5,leading=8.2,textColor=HexColor('#000000'))
  items.append(Paragraph(escape(s),style))
 if span: items += ['']*5; commands.append(('SPAN',(0,idx),(-1,idx)))
 data.append(items);commands.append(('BACKGROUND',(0,idx),(-1,idx),HexColor('#'+bg)))
add(['WILDBITS rc16 | K2 + Jr2 | MEMORY ADDRESS GRID | 14 September 2026'],'E0E0E0',True,True)
add(['FLASHDIS = 1: 1,792 KB RAM (224 blocks) | Physical SRAM: 2,048 KB / 1M x 16 | FLASHDIS resets to 0'],'FFF0A6',True,True)
add(['MMU block / view','Offset in 8 KB slot','Address from','Address through','RESOURCE / FUNCTION','SELECTION / MODE'],'FFF5BF',True)
section_styles=[]
section_no=0
for vals,kind in rows:
 if kind=='band':
  section_no+=1
  idx=len(data)
  if section_no>1:
   add([''],'FFFFFF',span=True)
   section_styles += [('TOPPADDING',(0,idx),(-1,idx),2),('BOTTOMPADDING',(0,idx),(-1,idx),2)]
   idx=len(data)
  title=['1. CPU LOGICAL ADDRESS SPACE - fixed CPU windows', '2. MMU BLOCK MAP - block x $2000 + offset', '3. SECTORED DEVICE DETAIL - device addresses, not SRAM pins'][section_no-1]
  add([title],['FFACA1','FFE16A','7FDCE8'][section_no-1],True,True)
  data[idx][0]=Paragraph(escape(title),ParagraphStyle('section',fontName='Bold',fontSize=9,leading=10,textColor=HexColor('#000000')))
  section_styles += [('LINEABOVE',(0,idx),(-1,idx),1.5,HexColor('#000000')),('LINEBELOW',(0,idx),(-1,idx),1.5,HexColor('#000000'))]
 else:add(vals,colors[kind])
for s in ['RAM byte address = (MMU block x $2000) + offset. SRAM word pins = byte address >> 1; bit 0 selects the byte lane.',
'$D0 alone spans $1A0000-$1A1FFF. The entire $D0-$EF group spans $1A0000-$1DFFFF. No translation fold.',
'Max-RAM kernel sets FLASHDIS after detecting support; free RAM depends on allocations. VICKY / DMA bypass the CPU MMU.',
'Register rows show decode windows, not a guarantee that every byte is implemented. Unlisted device offsets are not general RAM.',
'Sources: rc16 MMU RTL; K2/Jr2 I/O device RTL; wildbits.d; wb/max_ram_upgrade krnp2.asm.']:
 add([s],'E6E6E6',span=True)
t=Table(data,colWidths=widths)
t.setStyle(TableStyle(commands+[('GRID',(0,0),(-1,-1),.8,HexColor('#333333')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),2),('RIGHTPADDING',(0,0),(-1,-1),2),('TOPPADDING',(0,0),(-1,-1),0.48),('BOTTOMPADDING',(0,0),(-1,-1),0.48)]))
t.setStyle(TableStyle(section_styles))
tw,th=t.wrap(552,100000)
c=canvas.Canvas(str(P/'wildbits-rc16-memory-map-letter.pdf'),pagesize=(612,792))
c.setTitle('WildBits rc16 memory grid - large black type')
assert th <= 768, f'Table too tall: {th}'
t.drawOn(c,30,792-12-th);c.showPage();c.save()
print('Page size:',1455,th+14)