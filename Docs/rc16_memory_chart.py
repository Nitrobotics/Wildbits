from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'wildbits-rc16-memory-map.pdf'
# Reference PNG has no physical resolution metadata. At 96 dpi this page
# reproduces its exact 1940 x 1920 pixel dimensions and aspect ratio.
W,H = 1455,1440
for name,file in [('Body','arial.ttf'),('Bold','arialbd.ttf'),('Mono','consola.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(Path('C:/Windows/Fonts')/file)))
c=canvas.Canvas(str(OUT),pagesize=(W,H))
c.setTitle('WildBits rc16 - K2 and Jr2 memory layout')
c.setAuthor('WildBits')
BG='#101B29'; INK='#EAF1FA'; MUTED='#B9C9DB'
RAM='#174F4B'; FLASH='#624130'; IO='#293F67'; GAP='#35404F'
c.setFillColor(HexColor(BG));c.rect(0,0,W,H,fill=1,stroke=0)
def text(x,y,s,size=12,font='Body',color=INK):
    c.setFillColor(HexColor(color));c.setFont(font,size);c.drawString(x,H-y,s)
def rect(x,y,w,h,col):
    c.setFillColor(HexColor(col));c.rect(x,H-y-h,w,h,fill=1,stroke=0)
def section(y,num,title,subtitle):
    rect(32,y,1391,35,'#22354A');text(44,y+24,num,15,'Bold','#70DFCA');text(80,y+24,title,17,'Bold')
    text(44,y+55,subtitle,11.5,color=MUTED)
def table(x,y,widths,headers,rows,rh=29):
    full=sum(widths);rect(x,y,full,29,'#314860')
    xx=x
    for w,h in zip(widths,headers):text(xx+9,y+20,h,10.5,'Bold');xx+=w
    y+=29
    for vals,col in rows:
        rect(x,y,full,rh,col);xx=x
        for i,(w,v) in enumerate(zip(widths,vals)):
            text(xx+9,y+rh/2+4,v,11.3,'Mono' if i==0 else 'Body')
            xx+=w
        c.setStrokeColor(HexColor('#536171'));c.setLineWidth(.35);c.line(x,H-y-rh,x+full,H-y-rh)
        y+=rh
    return y

text(34,38,'WILDBITS / HARDWARE ADDRESS REFERENCE',12,'Bold','#70DFCA')
text(34,83,'Core rc16 memory layout',35,'Bold')
text(35,111,'Foenix F256 K2 + Jr2  |  Current RTL and NitrOS-9 max-RAM kernel  |  14 September 2026',13,color=MUTED)
for x,w,big,small,col in [(34,447,'1,792 KB','CPU RAM pool with FLASHDIS = 1',RAM),(497,447,'224 x 8 KB','MMU blocks available to the max-RAM kernel',IO),(960,461,'2,048 KB','Physical SRAM capacity: 1M x 16 bits',FLASH)]:
    rect(x,131,w,76,col);text(x+16,163,big,24,'Bold');text(x+16,190,small,12)

section(226,'01','The 256-entry MMU block space','Byte ranges below are block x $2000 through block x $2000 + $1FFF. Device selections are not SRAM accesses.')
rows=[
(['$00-$3F','$000000-$07FFFF','512 KB','SRAM','SRAM / 64 blocks'],RAM),
(['$40-$7F','$080000-$0FFFFF','512 KB','Flash select','SRAM / 64 blocks'],FLASH),
(['$80-$9F','$100000-$13FFFF','256 KB','Cartridge / expansion select','SRAM / 32 blocks'],FLASH),
(['$A0-$BF','$140000-$17FFFF','256 KB','SRAM','SRAM / 32 blocks'],RAM),
(['$C0-$C7','$180000-$18FFFF','64 KB','Sectored device space','Device space / NotRAM'],IO),
(['$C8-$CF','$190000-$19FFFF','64 KB','No RAM selection','NotRAM'],GAP),
(['$D0-$EF','$1A0000-$1DFFFF','256 KB','SRAM','SRAM / 32 blocks'],RAM),
(['$F0-$FF','$1E0000-$1FFFFF','128 KB','No RAM selection','NotRAM'],GAP),
]
table(34,293,[135,275,120,385,472],['MMU BLOCKS','BYTE ADDRESS RANGE','SPAN','RESET: FLASHDIS = 0','MAX-RAM: FLASHDIS = 1'],rows,30)
text(44,582,'The kernel excludes $C0-$CF and $F0-$FF. The 1,792 KB total is the RAM pool before OS, screen and application allocations.',12,color=MUTED)

section(601,'02','Address translation and the rc16 control bit','The CPU selects a block through an MMU slot. VICKY and DMA use SRAM byte addresses directly.')
rect(34,669,685,126,'#183C46');rect(735,669,686,126,'#283650')
text(49,693,'CPU -> MMU -> SRAM',15,'Bold','#70DFCA')
text(49,718,'byte address = (block x $2000) + 13-bit offset',13,'Mono')
text(49,742,'Example: $D0:$0000 -> $1A0000 -> word pins $D0000',12,'Mono')
text(49,767,'Block $D0 ends at $1A1FFF; the whole $D0-$EF range ends at $1DFFFF.',11.5)
text(750,693,'MMU_IO_CTRL: CPU $FFA1',15,'Bold','#9ABEFF')
text(750,718,'Bit 2: FLASHDIS. Reset = 0; set to 1 for RAM in $40-$9F.',12)
text(750,742,'Read bit 7 = 1 identifies support. Preserve the other control bits.',12)
text(750,767,'Bits 0 / 1 enable fixed internal RAM at $FD00 / vectors at $FFF0.',11.5)
text(44,817,'SRAM pins carry a WORD address: byte address >> 1; the low byte-address bit selects a byte lane. No +$30 or address folding.',12,'Bold')

section(836,'03','Device pages and fixed CPU windows','These are peripheral views, not extra RAM. Mapping a device page into a CPU slot selects its page-relative offsets.')
table(34,903,[124,245,316],['MMU PAGE','PAGE OFFSETS','CONTENTS'],[
(['$C0','$0000-$0FFF','Gamma tables / mouse image'],IO),
(['$C0','$1000-$12FF','Bitmap, tile and misc controls'],IO),
(['$C0','$1300-$16FF','128 sprite attribute records'],IO),
(['$C0','$1700-$177F','Text foreground/background LUTs'],IO),
(['$C1','$0000-$0FFF','Two font banks'],IO),
(['$C1','$1000-$1FFF','Four graphics palette LUTs'],IO),
(['$C2 / $C3','Page-relative offsets','Text characters / text attributes'],IO),
(['$C4','Sound register offsets','SID / PSG register space'],IO),
],28)
table(735,903,[195,491],['CPU ADDRESS','FIXED WINDOW / CONTROL'],[
(['$FD00-$FDFF','256-byte internal RAM when $FFA1 bit 0 = 1'],IO),
(['$FE00-$FEFF','System, IRQ, timers, serial, mouse, DMA, math'],IO),
(['$FF00-$FF5F','SD, splash SPI, WizFi, MIDI, W6100, VS1053'],IO),
(['$FF90','DIP-switch input'],IO),
(['$FFA0','Active LUT bits 1:0; edit LUT bits 5:4'],IO),
(['$FFA1 / $FFA8-$FFAF','I/O control / eight MMU slot registers'],IO),
(['$FFC0-$FFCF','Video master, layers, border and bitmap mode'],IO),
(['$FFF0-$FFFF','16-byte vector RAM when $FFA1 bit 1 = 1'],IO),
],28)
text(44,1176,'Selected device resources are shown above; gaps in those tables are not a promise of usable storage or a connected peripheral.',11,color=MUTED)

rect(34,1199,1387,122,'#22354A')
text(49,1225,'HOW TO READ THIS MAP',14,'Bold','#70DFCA')
text(49,1250,'RAM mode: the rc16 max-RAM kernel detects $FFA1 bit 7 and sets FLASHDIS. A core alone does not enlarge the kernel block pool.',12)
text(49,1274,'Video / DMA: physical SRAM addressing bypasses the CPU LUT and FLASHDIS. The CPU device-space holes do not remove SRAM capacity.',12)
text(49,1298,'Fixed windows override the selected CPU slot. rc16 inhibits SRAM writes at $FFA0-$FFAF so MMU register writes cannot leak into RAM.',12)

text(34,1349,'SOURCE BASIS',10,'Bold','#70DFCA')
text(34,1370,'TyVKy2K2x1_MMU_Register.v  |  TyVKy2K2turbo_MMU_FNX6809.v  |  defs/wildbits.d  |  wb/max_ram_upgrade: krnp2.asm',10.5,color=MUTED)
text(34,1392,'Original chart artwork and wording. Reference image used only for the colorful tabular format and page proportions.',10.5,color=MUTED)
text(34,1417,'1940 x 1920 reference pixels at 96 dpi  /  vector PDF  /  all addresses hexadecimal ($)',10,color=MUTED)
c.showPage();c.save()
print(OUT)
