#!/usr/bin/env python3
"""k2post.py DUMP.bin - post-mortem walker for a WildBits (NitrOS-9 L2) 512K RAM dump.
System addresses are translated through the system DAT image (slot -> 8K physical block)."""
import sys
d = open(sys.argv[1], "rb").read()
# ---- offsets (lwasm, Level 2 + wildbits.d, 2026-09-02)
D_BlkMap=0x40; D_ModDir=0x44; D_PrcDBT=0x48; D_SysPrc=0x4A; D_SysDAT=0x4C; D_SysMem=0x4E; D_Proc=0x50
D_AProcQ=0x52; D_WProcQ=0x54; D_SProcQ=0x56; D_Tasks=0x20; D_TskIPt=0xA1; D_Task1N=0x3D; D_TINIT=0x91; D_SSTskN=0xA4
D_Slice=0x2F; D_TSlice=0x30; D_DbgMem=0x0A; D_SWPage=0x03; D_PthDBT=0x88
P_ID=0;P_PID=1;P_SID=2;P_CID=3;P_SP=4;P_Task=6;P_PagCnt=7;P_Prior=0xA;P_Age=0xB;P_State=0xC;P_Queue=0xD;P_IOQP=0xF;P_IOQN=0x10;P_PModul=0x11;P_Signal=0x19;P_DATImg=0x40
STATE={0x80:"Sys",0x40:"TimSlp",0x20:"TimOut",0x10:"ImgChg",0x08:"Susp",0x02:"Condem",0x01:"Dead"}
def b8(p): return d[p]
def b16(p): return (d[p]<<8)|d[p+1]
sysdat_ptr = b16(D_SysDAT)          # system address of the system DAT image (in page 0 block => physical == system)
sysimg = [b16(sysdat_ptr+2*i) for i in range(8)]
def blk(i):  # physical block for system slot i, or None if free
    return None if sysimg[i]==0x333E else sysimg[i]&0xFF
def phys(sa):
    bk = blk(sa>>13)
    return None if bk is None else (bk<<13)|(sa&0x1FFF)
def rd8(sa):  p=phys(sa); return None if p is None else d[p]
def rd16(sa): p=phys(sa); return None if p is None else (d[p]<<8)|d[p+1]
def st(s): return "|".join(n for m,n in STATE.items() if s&m) or "-"
def modname(sa):
    try:
        if rd16(sa)!=0x87CD: return "?"
        off=rd16(sa+4); s=""; p=sa+off
        for _ in range(16):
            c=rd8(p); s+=chr(c&0x7F); p+=1
            if c&0x80: break
        return s
    except Exception: return "?"
print("system DAT image:", " ".join(f"{i}:{'..' if blk(i) is None else f'{blk(i):02X}'}" for i in range(8)))
print(f"D.Proc={b16(D_Proc):04X} D.SysPrc={b16(D_SysPrc):04X} AProcQ={b16(D_AProcQ):04X} WProcQ={b16(D_WProcQ):04X} SProcQ={b16(D_SProcQ):04X} PrcDBT={b16(D_PrcDBT):04X} Slice={b8(D_Slice)} TSlice={b8(D_TSlice)} SSTskN={b8(D_SSTskN)} TINIT={b8(D_TINIT):02X} Task1N={b8(D_Task1N)} DbgMem/WZStat={b16(D_DbgMem):04X}")
def desc(sa, tag=""):
    p=phys(sa)
    if p is None: print(f"  {tag}{sa:04X}: UNMAPPED slot"); return
    print(f"  {tag}{sa:04X} (phys {p:05X}): ID={rd8(sa+P_ID):02X} PID={rd8(sa+P_PID):02X} SID={rd8(sa+P_SID):02X} CID={rd8(sa+P_CID):02X} SP={rd16(sa+P_SP):04X} Task={rd8(sa+P_Task)} Pri={rd8(sa+P_Prior)} Age={rd8(sa+P_Age)} State={rd8(sa+P_State):02X}({st(rd8(sa+P_State))}) Queue={rd16(sa+P_Queue):04X} Sig={rd8(sa+P_Signal)} PModul={rd16(sa+P_PModul):04X}:{modname(rd16(sa+P_PModul))} img={' '.join('..' if rd16(sa+P_DATImg+2*i)==0x333E else f'{rd16(sa+P_DATImg+2*i)&0xFF:02X}' for i in range(8))}")
def walk(name, head):
    print(f"{name} queue:")
    sa=b16(head); seen=set(); n=0
    while sa and sa not in seen and n<20:
        seen.add(sa); desc(sa); q=rd16(sa+P_Queue); sa=q if q is not None else 0; n+=1
    if not seen: print("  (empty)")
print("current:"); desc(b16(D_Proc))
walk("ACTIVE", D_AProcQ); walk("WAIT", D_WProcQ); walk("SLEEP", D_SProcQ)
print("PID table (D.PrcDBT):")
tbl=b16(D_PrcDBT)
for pid in range(1,64):
    hi=rd8(tbl+pid)
    if hi and hi!=0xFF: desc(hi<<8, tag=f"pid {pid:2d} -> ")
smap=b16(D_SysMem); m=[rd8(smap+i) for i in range(256)]
runs=[];s=None
for i in range(257):
    u = i<256 and m[i]
    if u and s is None: s=i
    if not u and s is not None: runs.append(f"{s:02X}-{i-1:02X}"); s=None
print("SMAP used runs:", " ".join(runs))
# system stacks: top 24 bytes above SP for every system-state descriptor (return addresses)
print("system-state stack tops (SP -> up):")
for pid in range(1,64):
    hi=rd8(tbl+pid)
    if not hi or hi==0xFF: continue
    sa=hi<<8; sp=rd16(sa+P_SP); s=rd8(sa+P_State)
    if s&0x80 and sp:
        words=[rd16(sp+2*i) for i in range(14)]
        print(f"  pid {pid:2d} SP={sp:04X}: "+" ".join("----" if w is None else f"{w:04X}" for w in words))
print("raw first 32 bytes of each descriptor:")
for pid in range(1,64):
    hi=rd8(tbl+pid)
    if hi and hi!=0xFF:
        p=phys(hi<<8); print(f"  pid {pid:2d} @{hi:02X}00:", d[p:p+32].hex() if p is not None else "unmapped")
bm=b16(D_BlkMap); print("BlkMap 00-1F:", "".join({0:'.',1:'U',2:'M',0x80:'N'}.get(rd8(bm+i),'?') for i in range(32)))
