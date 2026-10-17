import bpy,os,numpy as np
OUT='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-free'
# Reuse only the image read/save and bitmap-label helpers, not previous output.
exec(open(OUT+'/round3_comparison.py').read().split('comparison_paths=[]')[0])
D=OUT+'/renders/round4'
glyphs['2']=['01110','10001','00001','00010','00100','01000','11111']
comparison_paths=[]
def board(a,b,path,left,right):
    h,w=a.shape[:2];im=np.ones((h+46,w*2+18,4),np.float32)*.022;im[:,:,3]=1
    im[46:,:w]=a;im[46:,w+18:]=b
    label(im,left,18,12);label(im,right,w+36,12)
    save(path,im);comparison_paths.append(path)
a=read(REF+'/13-rear-diffuser.png',1280,720);b=read(D+'/01-match-rear-13.png',1280,720)
board(a,b,D+'/comparison-13-full-rear-reference-left.png','REFERENCE 13','ROUND 4 - MATCHED REAR')
board(a[465:695,315:965],b[465:695,315:965],D+'/comparison-13-diffuser-reference-left.png','REFERENCE 13 - DIFFUSER','ROUND 4 - DIFFUSER')
a=read(REF+'/12-rear-quarter-wing-4k.png',2048,1152);b=read(D+'/02-match-rear-quarter-12.png',2048,1152)
board(a[420:1140,600:1640],b[420:1140,600:1640],D+'/comparison-12-rear-quarter-reference-left.png','REFERENCE 12','ROUND 4 - REAR')
