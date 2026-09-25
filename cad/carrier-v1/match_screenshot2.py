"""match_screenshot2.py -- same sampling as match_screenshot.py, drawn properly.
Screen = (-x, -y), i.e. the part rotated 180 deg about Z, which is how Dan's
CAD viewer is showing it.  Colours chosen to match his screenshot."""
import numpy as np, struct
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
from matplotlib.colors import ListedColormap
import gen_carrier as G

def load(p):
    b=open(p,"rb").read(); n=struct.unpack("<I",b[80:84])[0]
    a=np.frombuffer(b,dtype=np.uint8,count=n*50,offset=84).reshape(n,50)
    return a[:,12:48].copy().view("<f4").reshape(n,3,3).astype(np.float64)

T=load("flash_frame.stl"); A,B,C=T[:,0,:],T[:,1,:],T[:,2,:]
E1,E2=B-A,C-A; V=T.reshape(-1,3); lo,hi=V.min(0),V.max(0)
D=np.array([0.0137,0.0071,1.0]); D/=np.linalg.norm(D)
P=np.cross(D,E2); det=np.einsum('ij,ij->i',E1,P)
ok=np.abs(det)>1e-12; inv=np.where(ok,1.0/np.where(ok,det,1),0.0)
def inside(pts,chunk=256):
    pts=np.asarray(pts,float); out=np.zeros(len(pts),bool)
    for s in range(0,len(pts),chunk):
        p=pts[s:s+chunk][:,None,:]; Tv=p-A[None]
        u=np.einsum('knj,nj->kn',Tv,P)*inv; Q=np.cross(Tv,E1[None])
        v=(Q@D)*inv; t=np.einsum('nj,knj->kn',E2,Q)*inv
        out[s:s+chunk]=((ok&(u>=0)&(u<=1)&(v>=0)&(u+v<=1)&(t>1e-9)).sum(1)%2)==1
    return out

STEP=0.28
xs=np.arange(lo[0]+0.01,hi[0],STEP)+0.013
ys=np.arange(lo[1]+0.01,hi[1],STEP)+0.007
X,Y=np.meshgrid(xs,ys); flat=np.column_stack([X.ravel(),Y.ravel()])
print(f"sampling {len(flat)} columns ...")
deck=inside(np.column_stack([flat,np.full(len(flat),18.5)])).reshape(X.shape)
bar =inside(np.column_stack([flat,np.full(len(flat), 6.0)])).reshape(X.shape)
img=np.where(deck,2,np.where(bar,1,0))
img=img[::-1,::-1]                       # <-- the 180 deg rotation
print("done")

cmap=ListedColormap(["#23272b","#c2c2c2","#9a9a9a"])   # void / bar seen through / deck
fig,ax=plt.subplots(figsize=(7.0,8.3)); fig.patch.set_facecolor("#23272b")
ax.set_facecolor("#23272b")
ax.imshow(img,origin="lower",cmap=cmap,vmin=0,vmax=2,
          extent=[-hi[0],-lo[0],-hi[1],-lo[1]],interpolation="nearest")
ax.add_patch(Rectangle((-hi[0],-hi[1]),hi[0]-lo[0],hi[1]-lo[1],
                       fill=False,ec="#555",lw=1.2))

def s(x,y):  # board-local -> frame -> screen
    return (-(x-7.5), -(y-9.0))
for px in (-8.,-6.,-4.,-2.,0.):
    ax.add_patch(Circle(s(px,3.0),.85,fc="#ffcc33",ec="#4a3800",lw=1.0,zorder=5))
for (px,py) in G.MH_DUT:
    ax.add_patch(Circle(s(px,py),.9,fc="#5ec8ff",ec="#023",lw=1.0,zorder=5))

ax.annotate("",xy=(0,-33.6),xytext=(0,-27.0),
            arrowprops=dict(arrowstyle="-|>",lw=2.4,color="#ff5555"),zorder=6)
ax.text(0,-26.2,"ARROW / SPACEBAR WALL",ha="center",va="bottom",
        fontsize=8.5,color="#ff8888",weight="bold")
ax.text(0,31.5,"power-in (J1) end",ha="center",va="top",fontsize=8.5,color="#aaa")
ax.text(-27.5,14.0,"gold = the 5 pogo pins\nblue = the 2 dowels\nboth land inside the window",
        ha="left",va="center",fontsize=8.5,color="#eee")

ax.set_xlim(-31,31); ax.set_ylim(-37,37)
ax.set_aspect("equal"); ax.axis("off")
ax.set_title("flash_frame.stl, sampled from the file JLC printed,\n"
             "drawn in the same orientation as your screenshot",
             fontsize=10,color="#eee")
fig.tight_layout(); fig.savefig("match-screenshot2.png",dpi=185,facecolor="#23272b")
print("wrote match-screenshot2.png")
