import bpy,numpy as np,os,json
OUT=os.path.dirname(os.path.abspath(__file__))
exec(open(OUT+'/round3_comparison.py').read().split('comparison_paths=[]')[0])
D=OUT+'/renders/game'
glyphs['G']=['01111','10000','10000','10111','10001','10001','01111']
boards=[];rows=[]
for name in ['front-quarter','side','rear','rear-quarter']:
    a=read(D+'/before-'+name+'.png');b=read(D+'/after-'+name+'.png')
    h0,w0=a.shape[:2];hh=round(h0*1000/w0)
    a=read(D+'/before-'+name+'.png',1000,hh);b=read(D+'/after-'+name+'.png',1000,hh)
    h,w=a.shape[:2];c=np.zeros((h+46,w*2+12,4),np.float32);c[:,:,:3]=.018;c[:,:,3]=1
    c[46:,:w]=a;c[46:,w+12:]=b
    label(c,'ROUND 4',20,13);label(c,'GAME',w+32,13)
    path=D+'/compare-'+name+'.png';save(path,c);boards.append(path)
    rows.append(read(path,1400,round(c.shape[0]*1400/c.shape[1])))
overview=np.concatenate(rows,axis=0);save(D+'/comparison-overview.png',overview)
json.dump({'before_left_after_right':True,'comparisons':boards},open(D+'/comparisons.json','w'),indent=2)
print('COMPARISONS COMPLETE',flush=True)
