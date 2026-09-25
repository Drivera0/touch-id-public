"""gen_frame_html.py -- rebuild frame-3d.html with the CURRENT mesh embedded.
The old file carried the 57.4 mm frame; a stale viewer is worse than none."""
import base64, os, json
import gen_frame as F

stl = open("flash_frame.stl", "rb").read()
b64 = base64.b64encode(stl).decode()
facts = {
    "frame": "57.80 x 68.80 x 22.00 mm",
    "recess": f"{F.REC_W} x {F.REC_H} x {F.REC_D} deep",
    "opening": f"{F.OPEN_W} x {F.OPEN_H}",
    "seat bar": f"top z = {F.SEAT_Z:.2f}, {F.BAR_W} mm wide",
    "pin protrusion": f"{F.PIN_PROUD} mm (PIN_L = {F.PIN_L}, "
                      f"{'measured' if F.PIN_L_OK else 'NOT measured'})",
    "dowel length": f"{(F.H-F.REC_D)+F.CAR_T-F.SEAT_Z+F.DOWEL_PROUD:.1f} mm",
    "volume": f"{F.base.val().Volume()/1000:.1f} cm3",
}
rows = "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in facts.items())

html = """<!doctype html><meta charset=utf-8>
<title>TouchID flash frame v1</title>
<style>
:root{--bg:#f6f7f9;--fg:#1c1f23;--pan:#fff;--line:#d8dce1;--accent:#2f6f4f}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){
--bg:#14171a;--fg:#e8eaed;--pan:#1e2226;--line:#333a41;--accent:#6fcf97}}
:root[data-theme=dark]{--bg:#14171a;--fg:#e8eaed;--pan:#1e2226;--line:#333a41;--accent:#6fcf97}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:15px/1.5 ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
header{padding:16px}h1{margin:0 0 2px;font-size:19px}
p.sub{margin:0;color:#8b949e;font-size:13px}
#wrap{display:flex;flex-wrap:wrap;gap:16px;padding:0 16px 24px}
#view{flex:1 1 420px;min-width:300px;height:68vh;min-height:360px;
background:var(--pan);border:1px solid var(--line);border-radius:10px}
aside{flex:0 1 300px;min-width:260px}
table{width:100%;border-collapse:collapse;background:var(--pan);
border:1px solid var(--line);border-radius:10px;overflow:hidden}
th,td{padding:8px 10px;text-align:left;font-size:13px;border-bottom:1px solid var(--line)}
th{color:#8b949e;font-weight:500;width:45%}tr:last-child th,tr:last-child td{border-bottom:0}
.note{margin-top:12px;padding:10px 12px;border-left:3px solid var(--accent);
background:var(--pan);border-radius:0 8px 8px 0;font-size:13px}
</style>
<header><h1>TouchID flash frame v1</h1>
<p class=sub>drag to rotate &middot; scroll to zoom &middot; right-drag to pan</p></header>
<div id=wrap><div id=view></div><aside><table>__ROWS__</table>
<div class=note>Generated from <code>flash_frame.stl</code> at build time, so this
view can never show a frame the files do not describe.</div></aside></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/examples/js/controls/OrbitControls.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/examples/js/loaders/STLLoader.js"></script>
<script>
const B64="__B64__";
const bin=atob(B64),buf=new Uint8Array(bin.length);
for(let i=0;i<bin.length;i++)buf[i]=bin.charCodeAt(i);
const el=document.getElementById('view');
const dark=matchMedia('(prefers-color-scheme:dark)').matches;
const sc=new THREE.Scene();sc.background=new THREE.Color(dark?0x1e2226:0xffffff);
const cam=new THREE.PerspectiveCamera(42,el.clientWidth/el.clientHeight,0.1,2000);
const rd=new THREE.WebGLRenderer({antialias:true});
rd.setPixelRatio(devicePixelRatio);rd.setSize(el.clientWidth,el.clientHeight);
el.appendChild(rd.domElement);
sc.add(new THREE.HemisphereLight(0xffffff,0x404050,0.9));
const d1=new THREE.DirectionalLight(0xffffff,0.7);d1.position.set(1,-1.4,1.6);sc.add(d1);
const d2=new THREE.DirectionalLight(0xffffff,0.35);d2.position.set(-1.2,0.8,-0.6);sc.add(d2);
const geo=new THREE.STLLoader().parse(buf.buffer);
geo.computeVertexNormals();geo.computeBoundingBox();
const bb=geo.boundingBox,c=bb.getCenter(new THREE.Vector3()),s=bb.getSize(new THREE.Vector3());
geo.translate(-c.x,-c.y,-c.z);
const mesh=new THREE.Mesh(geo,new THREE.MeshPhongMaterial(
  {color:dark?0xc9cdd2:0xbfc5cb,specular:0x222222,shininess:14,flatShading:false}));
sc.add(mesh);
const edges=new THREE.LineSegments(new THREE.EdgesGeometry(geo,28),
  new THREE.LineBasicMaterial({color:dark?0x55606a:0x8a949e}));
sc.add(edges);
const r=Math.max(s.x,s.y,s.z);
cam.position.set(r*1.1,-r*1.3,r*1.0);cam.up.set(0,0,1);
const ct=new THREE.OrbitControls(cam,rd.domElement);ct.target.set(0,0,0);ct.update();
addEventListener('resize',()=>{rd.setSize(el.clientWidth,el.clientHeight);
  cam.aspect=el.clientWidth/el.clientHeight;cam.updateProjectionMatrix();});
(function loop(){requestAnimationFrame(loop);ct.update();rd.render(sc,cam);})();
</script>"""
html = html.replace("__ROWS__", rows).replace("__B64__", b64)
open("frame-3d.html", "w", encoding="utf-8").write(html)
print(f"wrote frame-3d.html ({len(html)/1024:.0f} KB)")
