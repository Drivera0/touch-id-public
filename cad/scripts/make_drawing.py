# Generates touchid_module_drawing.svg (v4) and the blank fill-in version.
# Run: python make_drawing.py
import re, os
S = 12  # px per mm
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "drawings")

def build(BLANK):
    def mm(v): return v * S
    def bl(s):  # blank decimals in fill-in version
        return re.sub(r'[+−-]?\d+\.\d+', '_____', s) if BLANK else s
    def line(x1,y1,x2,y2,cls="dim"): return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" class="{cls}"/>'
    def txt(x,y,s,anchor="middle",size=13,rot=None,cls=""):
        r=f' transform="rotate({rot} {x:.1f} {y:.1f})"' if rot else ''
        c=f' class="{cls}"' if cls else ''
        return f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" font-size="{size}"{r}{c}>{bl(s)}</text>'
    def rrect(cx,cy,w,h,r,cls="body"):
        return f'<rect x="{cx-w/2:.1f}" y="{cy-h/2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r:.1f}" class="{cls}"/>'
    def dim_h(x1,x2,y,label):
        return [line(x1,y-6,x1,y+6),line(x2,y-6,x2,y+6),line(x1,y,x2,y),txt((x1+x2)/2,y-8,label)]
    def dim_v(x,y1,y2,label):
        return [line(x-6,y1,x+6,y1),line(x-6,y2,x+6,y2),line(x,y1,x,y2),txt(x-8,(y1+y2)/2,label,rot=-90)]

    W,H = 1560, 1680
    P = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Helvetica,Arial">',
    '<style>.body{fill:#e8edf5;stroke:#223;stroke-width:2}.pcb{fill:#f7f7ee;stroke:#556;stroke-width:1.6}'
    '.hidden{stroke:#889;stroke-width:1;stroke-dasharray:5 4;fill:none}.dim{stroke:#c0392b;stroke-width:1}'
    '.padu{fill:#d4a017;stroke:#8a6a00;stroke-width:1}.padn{fill:#e8e8e8;stroke:#999;stroke-width:1}'
    '.hatch{fill:url(#h);stroke:#223;stroke-width:1.5}text{fill:#c0392b}.t2{fill:#223}.lead{stroke:#c0392b;stroke-width:0.8}</style>',
    '<defs><pattern id="h" width="6" height="6" patternTransform="rotate(45)" patternUnits="userSpaceOnUse"><line x1="0" y1="0" x2="0" y2="6" stroke="#667" stroke-width="1"/></pattern></defs>',
    f'<rect width="{W}" height="{H}" fill="white"/>']
    title = ("TouchID Module — BLANK measurement drawing (write values on the lines)" if BLANK
             else "TouchID Module — dimensioned drawing v6 (final design — caliper pass 2, rear shelf, outside-seated sensor)")
    P.append(txt(W/2,34,title,"middle",22))
    P.append(txt(W/2,56,"units: mm — lip tier: 2.90 plastic + 1.2 PCB = 4.10 (19.66 sq); top tier 18.52 sq x 4.26; assembled total 8.36","middle",14))

    lw, bw, lh, th, bh = 19.66, 18.52, 2.90, 4.26, 7.16   # plastic only; PCB adds 1.2 below
    cr = 2.0                 # corner radius (est)
    arm_w = 5.12; tip_diag = 30.14; tip_to_hole = 2.40
    ear_diag = tip_diag - lw*0.70710678 - tip_to_hole   # = 13.84 hole centre from module centre
    u = 0.70710678

    # ================= TOP VIEW (ear bottom-left) =================
    cx, cy = 330, 360
    P.append(txt(cx,cy-mm(15),"TOP VIEW (flush face)","middle",16))
    ex, ey = -ear_diag*u, ear_diag*u   # screen: left, DOWN -> use +y screen down
    exs, eys = cx+mm(ex), cy+mm(-ey)+2*mm(ey)  # ear bottom-left => screen (+down)
    exs, eys = cx-mm(ear_diag*u), cy+mm(ear_diag*u)
    # arm: parallel-sided strip along the 30.4 diagonal, half-circle end at
    # the tip; NO screw hole drawn (user adds it)
    tipd = ear_diag + arm_w/2          # 16.46 from center
    ind  = 9.0                         # inner end, buried inside the body
    acx, acy = cx-mm((tipd+ind)/2*u), cy+mm((tipd+ind)/2*u)
    alen = tipd - ind
    P.append(f'<g transform="rotate(-45 {acx:.1f} {acy:.1f})"><rect x="{acx-mm(alen/2):.1f}" y="{acy-mm(arm_w/2):.1f}" width="{mm(alen):.1f}" height="{mm(arm_w):.1f}" rx="{mm(arm_w/2):.1f}" class="body"/>'
             f'{line(acx-mm(alen/2+1.4),acy-mm(arm_w/2),acx-mm(alen/2+1.4),acy+mm(arm_w/2))}'
             f'{line(acx-mm(alen/2+1.9),acy-mm(arm_w/2),acx-mm(alen/2+0.9),acy-mm(arm_w/2))}'
             f'{line(acx-mm(alen/2+1.9),acy+mm(arm_w/2),acx-mm(alen/2+0.9),acy+mm(arm_w/2))}'
             f'{txt(acx-mm(alen/2+2.4),acy+4,"5.18","end",12)}</g>')
    P.append(rrect(cx,cy,mm(lw),mm(lw),mm(cr)))                      # lip (visible border)
    P.append(rrect(cx,cy,mm(bw),mm(bw),mm(cr)))                      # top square
    P.append(f'<circle cx="{cx}" cy="{cy}" r="{mm(6.2):.1f}" class="body"/>')
    P.append(f'<circle cx="{cx}" cy="{cy}" r="{mm(7.1):.1f}" class="hidden"/>')
    P += dim_h(cx-mm(bw/2),cx+mm(bw/2),cy+mm(lw/2)+30,"18.52")
    P += dim_h(cx-mm(lw/2),cx+mm(lw/2),cy+mm(lw/2)+62,"19.66")
    P += dim_v(cx+mm(lw/2)+34,cy-mm(bw/2),cy+mm(bw/2),"18.52")
    P.append(txt(cx+mm(2),cy-mm(7.6),"O13.5 window / O15.7 bezel seat","start",12))
    P.append(txt(exs-mm(1.0),eys+mm(5.6),"arm 5.12 wide, 2.94 thick — screw not drawn (add your own)","start",12))
    # tip-to-far-corner diagonal
    fx, fy = cx+mm(lw/2*u*1.41421*0.0)+mm(lw/2)*0+ (cx+mm( (lw/2-cr*0.29)*1 )), 0
    tipx, tipy = cx-mm((ear_diag+arm_w/2)*u), cy+mm((ear_diag+arm_w/2)*u)
    farx, fary = cx+mm(lw/2*1)*u*1.41421, cy-mm(lw/2)*u*1.41421
    farx, fary = cx+mm(9.86*u*1.41421), cy-mm(9.86*u*1.41421)
    P.append(line(tipx,tipy,farx,fary,"dim"))
    lbx,lby = tipx+(farx-tipx)*0.22, tipy+(fary-tipy)*0.22
    P.append(txt(lbx-8,lby-8,"30.14 tip-to-corner","end",12,rot=-45))

    # ================= SECTION A-A =================
    sx0, sy0 = 380, 900
    P.append(txt(sx0,sy0-mm(15),"SECTION A-A (through sensor axis)","middle",16))
    def Q(x,z): return (sx0+mm(x), sy0-mm(z))
    top_t, slip, wd2, bd2, wall = 1.6, 0.8, 6.2, 7.1, 1.4
    lw2, bw2 = lw/2, bw/2
    lprof=[(-lw2,0),(-lw2,lh),(-bw2,lh),(-bw2,bh),(-wd2,bh),(-wd2,bh-slip),(-bd2,bh-slip),(-bd2,bh-top_t),(-bw2+wall,bh-top_t),(-bw2+wall,lh),(-lw2+wall,lh),(-lw2+wall,0)]
    rprof=[(x*-1,z) for (x,z) in lprof]
    for prof in (lprof,rprof):
        pth=" ".join(f"{Q(x,z)[0]:.1f},{Q(x,z)[1]:.1f}" for x,z in prof)
        P.append(f'<polygon points="{pth}" class="hatch"/>')
    pcb=" ".join(f"{Q(x,z)[0]:.1f},{Q(x,z)[1]:.1f}" for x,z in [(-lw2,0),(lw2,0),(lw2,-1.2),(-lw2,-1.2)])
    P.append(f'<polygon points="{pcb}" class="hidden"/>')
    P.append(txt(Q(lw2+1,-1)[0],Q(lw2+1,-0.9)[1],"PCB 1.2 — the module's flush bottom (arm bottom = housing back, 1.2 above it)","start",12))
    P.append(line(*Q(-lw2-5,bh),*Q(lw2+5,bh),"hidden"))
    P.append(txt(Q(lw2+5,bh)[0]+4,Q(lw2+5,bh)[1]+4,"flush with metal enclosure","start",12))
    P += dim_v(Q(-lw2-3,0)[0]-14,Q(0,bh)[1],Q(0,-1.2)[1],"8.36 incl PCB")
    P += dim_v(Q(-lw2-3,0)[0]-58,Q(0,lh)[1],Q(0,-1.2)[1],"4.10 lip+PCB")
    P += dim_v(Q(lw2+3,0)[0]+44,Q(0,bh)[1],Q(0,lh)[1],"4.26 top tier")
    P += dim_h(Q(-wd2,0)[0],Q(wd2,0)[0],Q(0,-2.6)[1]+18,"O13.5 window")
    P += dim_h(Q(-bd2,0)[0],Q(bd2,0)[0],Q(0,-2.6)[1]+46,"O15.7 c'bore x 1.0 deep")
    P.append(txt(*Q(0,bh+1.8),"sensor drops in from OUTSIDE, lands on the shoulder - cannot be pushed in","middle",12))

    # ---- ARM DETAIL (side, at the corner) ----
    dx0, dy0 = sx0 - 90, sy0 + 300
    P.append(txt(dx0+mm(1),dy0-mm(14),"ARM DETAIL (side)","middle",14))
    def D(x,z): return (dx0+mm(x), dy0-mm(z))
    step = (19.72-18.64)/2   # 0.54 lip overhang per side
    # lip tier profile (corner region)
    P.append(f'<polygon points="{D(0,0)[0]:.1f},{D(0,0)[1]:.1f} {D(9,0)[0]:.1f},{D(9,0)[1]:.1f} {D(9,lh)[0]:.1f},{D(9,lh)[1]:.1f} {D(0,lh)[0]:.1f},{D(0,lh)[1]:.1f}" class="body"/>')
    # top tier (set in by the lip step)
    P.append(f'<polygon points="{D(step,lh)[0]:.1f},{D(step,lh)[1]:.1f} {D(9,lh)[0]:.1f},{D(9,lh)[1]:.1f} {D(9,bh)[0]:.1f},{D(9,bh)[1]:.1f} {D(step,bh)[0]:.1f},{D(step,bh)[1]:.1f}" class="body"/>')
    # arm flush with the back plane, 3.0 tall (top ends 1.20 below the lip step)
    P.append(f'<rect x="{D(-5.5,3.0)[0]:.1f}" y="{D(-5.5,3.0)[1]:.1f}" width="{mm(5.5):.1f}" height="{mm(3.0):.1f}" rx="{mm(0.8):.1f}" class="body"/>')
    P += dim_v(D(-6.6,0)[0],D(0,3.0)[1],D(0,0)[1],"2.90")
    # PCB below the housing back — the module's real bottom
    P.append(f'<rect x="{D(-5.5,0)[0]:.1f}" y="{D(-5.5,0)[1]:.1f}" width="{mm(15):.1f}" height="{mm(1.2):.1f}" class="hidden" stroke-dasharray="5 4"/>')
    P += dim_v(D(-9.6,0)[0],D(0,0)[1],D(0,-1.2)[1],"1.20 PCB")
    P.append(line(*D(-6.2,lh),*D(9,lh),"hidden"))
    P.append(txt(*D(9.5,lh-0.3),"lip step (top of plastic lip, z=2.90) - arm flush with the FULL lip","start",11))
    P.append(txt(*D(9.5,1.2),"PCB (dashed) forms the module bottom below the arm","start",11))
    P.append(txt(*D(9.5,0.4),"module back (PCB side)","start",11))

    # ====== BACK ASSEMBLY VIEW (pad side: housing + arm + PCB + pins) ======
    gx, gy = 1080, 830
    P.append(txt(gx,gy-mm(16.5),"BACK VIEW — housing + PCB screwed on (pad side, as installed viewed from below)","middle",16))
    def R(x,y): return (gx+mm(x), gy-mm(y))   # +y up
    # arm sticking out bottom-right (behind PCB, part of housing)
    axs, ays = R(ear_diag*u, -ear_diag*u)
    tipd = ear_diag + arm_w/2; ind = 9.0; alen = tipd - ind
    bcx, bcy = R((tipd+ind)/2*u, -(tipd+ind)/2*u)
    P.append(f'<g transform="rotate(45 {bcx:.1f} {bcy:.1f})"><rect x="{bcx-mm(alen/2):.1f}" y="{bcy-mm(arm_w/2):.1f}" width="{mm(alen):.1f}" height="{mm(arm_w):.1f}" rx="{mm(arm_w/2):.1f}" class="body"/></g>')
    P.append(rrect(gx,gy,mm(lw),mm(lw),mm(cr)))                    # housing back edge
    P.append(rrect(gx,gy,mm(19.0),mm(19.0),mm(cr),"pcb"))          # PCB on top
    P.append(txt(axs+mm(1.0),ays+mm(3.6),"arm flush with back (screw not drawn), tip at 30.14 diag","start",11))
    # All 10 pads with REAL pin names (pad side = mirror of the slot view,
    # so columns swap within each block; rows: top = rear). Gold = used.
    pads = [("J4-2",4.33,7.84,False),("J4-1",6.87,7.84,False),
            ("J4-4",4.33,5.30,False),("J4-3",6.87,5.30,False),
            ("J4-6",4.33,2.76,False),("J4-5",6.87,2.76,True),
            ("J11-2",-6.67,8.07,True),("J11-1",-4.13,8.07,True),
            ("J11-4",-6.67,5.53,False),("J11-3",-4.13,5.53,True)]
    for name,rxx,ry,used in pads:
        px,py=R(rxx,ry)
        P.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{mm(1.1):.1f}" class="{"padu" if used else "padn"}"/>')
        P.append(txt(px,py+mm(1.9),name,"middle",8.5,cls="t2"))
    P.append(txt(*R(3.0,11.9),"J4 mate (2.50 pitch)","start",12))
    P.append(txt(*R(-9.0,11.9),"J11 mate","end",12))
    legend = ["GOLD = USED (pin test 2026-08-18):",
              "  J11-1/2/3 : VBAT in, 3.47-3.68 V — tie together",
              "  J4-5 : GND (continuity confirmed)",
              "GRAY = leave unconnected:",
              "  J4-1/3/4 : 3.3 V pulled-up encoder lines",
              "  J4-2, J4-6 : idle low",
              "  J11-4 : floating ~0.33 V"]
    for i,s in enumerate(legend):
        P.append(txt(*R(11.4,8.4-1.5*i),s,"start",11))
    # M2 PCB screws + posts
    for (sxp,syp) in [(-8.3,0.0),(8.3,0.0)]:
        px,py=R(sxp,syp)
        P.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{mm(1.1):.1f}" class="body"/>')
        P.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{mm(0.35):.1f}" class="hidden"/>')
    P.append(txt(*R(-11.2,-1.6),"M2 screw (2 mm thread,","end",11))
    P.append(txt(*R(-11.2,-2.9),"holds PCB to housing)","end",11))
    P.append(line(*R(-10.9,-1.9),*R(-9.2,-0.5),"lead"))
    # PROPOSED alignment posts (through PCB holes): full circle below,
    # half circle against the top wall, centered between J11 and J4 groups

    P.append(txt(*R(0,10.6),"Ø2.15 PCB holes over the OFFSET half posts (+1.0,+8.5) / (−7.5,−8.5) — board only fits one way","middle",10))
    P.append(txt(gx,gy+mm(15.5),"Pin roles CONFIRMED by pin test 2026-08-18 — still pending: sleep sweep + load test on J11 (see Pin Test Results)","middle",12.5))

    # ====== BACK VIEW — HOUSING ONLY (PCB removed, what's underneath) ======
    hx, hy = 1080, 1400
    P.append(txt(hx,hy-mm(16.5),"BACK VIEW — housing only (PCB removed)","middle",16))
    def RH(x,y): return (hx+mm(x), hy-mm(y))
    # arm (recessed 1.2 behind the back plane but visible)
    hax, hay = RH(ear_diag*u, -ear_diag*u)
    tipd2 = ear_diag + arm_w/2; ind2 = 9.0; alen2 = tipd2 - ind2
    hbx, hby = RH((tipd2+ind2)/2*u, -(tipd2+ind2)/2*u)
    P.append(f'<g transform="rotate(45 {hbx:.1f} {hby:.1f})"><rect x="{hbx-mm(alen2/2):.1f}" y="{hby-mm(arm_w/2):.1f}" width="{mm(alen2):.1f}" height="{mm(arm_w):.1f}" rx="{mm(arm_w/2):.1f}" class="body"/></g>')
    # housing back rim (PCB seating face) + open cavity
    P.append(f'<defs><clipPath id="houclip"><rect x="{hx-mm(lw)/2:.1f}" y="{hy-mm(lw)/2:.1f}" width="{mm(lw):.1f}" height="{mm(lw):.1f}" rx="{mm(cr):.1f}"/></clipPath></defs>')
    P.append(rrect(hx,hy,mm(lw),mm(lw),mm(cr)))
    cav = 16.8
    P.append(rrect(hx,hy,mm(cav),mm(cav),mm(1.0),"pcb"))       # cavity opening (z0..4.20)
    P.append(rrect(hx,hy,mm(15.7),mm(15.7),mm(1.0),"hidden"))  # upper cavity (z4.20..6.84)
    P.append(f'<circle cx="{hx}" cy="{hy}" r="{mm(7.1):.1f}" class="hidden"/>')   # sensor c'bore
    P.append(f'<circle cx="{hx}" cy="{hy}" r="{mm(6.2):.1f}" class="hidden"/>')   # window (deepest)
    # screw bosses (Ø4.6, clipped so they stay inside the outline) + pilots
    P.append('<g clip-path="url(#houclip)">')
    for (sxp,syp) in [(-8.3,0.0),(8.3,0.0)]:
        px,py = RH(sxp,syp)
        P.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{mm(2.3):.1f}" class="body"/>')
        P.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{mm(0.85):.1f}" class="hidden"/>')
    P.append('</g>')
    # ---- labels (everything) ----
    P.append(txt(*RH(0,12.2),"19.66 sq outer edge (lip tier, rounded R2.0)","middle",11))
    P.append(line(*RH(4.5,11.4),*RH(6.5,9.6),"lead"))
    P.append(txt(*RH(-11.4,6.6),"wall 1.4","end",11))
    P.append(line(*RH(-11.1,6.3),*RH(-9.0,5.6),"lead"))
    P.append(txt(*RH(-11.4,4.5),"screw boss Ø4.6,","end",11))
    P.append(txt(*RH(-11.4,3.2),"M2 pilot Ø1.7 × 5.0 deep","end",11))
    P.append(txt(*RH(-11.4,1.9),"at (−8.3, 0) — inner flat for ESP32","end",10))
    P.append(line(*RH(-11.1,3.9),*RH(-9.6,0.8),"lead"))
    P.append(txt(*RH(11.4,7.0),"cavity 16.86 sq x 2.90 deep","start",11))
    P.append(txt(*RH(11.4,5.7),"(fits ESP32-C3-MINI-1, 16.6 long)","start",10))
    P.append(txt(*RH(11.4,4.0),"upper cavity 15.72 sq,","start",11))
    P.append(txt(*RH(11.4,2.7),"z 2.90 -> 5.56 (dashed)","start",10))
    P.append(txt(*RH(11.4,0.6),"sensor c'bore O15.7 from top (dashed)","start",11))
    P.append(txt(*RH(11.4,-0.7),"window O13.5 through (dashed)","start",10))
    P.append(txt(*RH(11.4,-2.8),"second boss at (+8.3, 0)","start",11))
    P.append(line(*RH(11.1,-2.5),*RH(9.4,-1.0),"lead"))
    P.append(txt(*RH(-11.4,-4.2),"flat rim = PCB seating","end",11))
    P.append(txt(*RH(-11.4,-5.5),"face (back plane, z=0)","end",11))
    P.append(line(*RH(-11.1,-4.6),*RH(-8.9,-3.0),"lead"))
    P.append(txt(*RH(11.4,-6.4),"arm: 5.12 wide, 2.94 thick,","start",11))
    P.append(txt(*RH(11.4,-7.7),"flush with this back plane,","start",10))
    P.append(txt(*RH(11.4,-9.0),"tip at 30.14 diagonal","start",10))
    P.append(line(*RH(11.1,-6.8),*RH(10.4,-9.4),"lead"))
    # PROPOSED posts in the housing view too

    P.append(txt(*RH(0,-12.4),"NO alignment posts - the two M2 screws at (+-8.3, 0) locate the PCB","middle",11))


    # notes
    nx, ny = 900, 120
    notes = (["HOW TO FILL IN","- Every _____ is a value to measure with calipers.",
      "- BACK VIEW frame: pad side (underside), arm bottom-right,","   origin at board center, +x right, +y up.",
      "- Also record: pad pitch, pad dia, arm hole dia, arm thickness,","   corner radius, PCB thickness, boss height in slot."] if BLANK else
     ["NOTES  (all dims caliper-measured 2026-08-20 unless noted)",
      "1. Lip 19.66 sq x 4.10 incl. the 1.2 PCB -> plastic lip 2.90.",
      "    Housing alone 7.16 tall; assembled with PCB 8.36.",
      "2. Top tier 18.52 sq, corners R2.0. Walls 1.4 -> cavity 16.86 sq.",
      "3. Top plate 2.0 thick: O15.7 counterbore 1.0 deep from the TOP face,",
      "    O13.5 window through -> 1.1 wide x 1.0 thick shoulder. The sensor",
      "    is fitted from OUTSIDE and bears DOWN on that shoulder, so finger",
      "    pressure cannot push it into the enclosure. Max bezel here is O16.",
      "4. Rear shelf 11.0 x 1.18 out x 1.36 thick, top at z=2.62, hollow under,",
      "    gusset each end - slides under the metal case as a pivot.",
      "5. Arm 5.12 wide x 2.94 thick; tip->opposite corner 30.14; hole O2.0",
      "    at 13.84 from centre, csk O4.4. Screw down here last.",
      "6. PCB 19.60 x 17.60 x 1.20, FLUSH WITH THE FRONT - the 2.06 shortfall",
      "    is all at the rear, under the shelf. Screws at (+-8.30, 0).",
      "7. Pogo pads measured + fabbed: pitch 2.50, pad O2.20."])
    for i,s in enumerate(notes):
        P.append(f'<text x="{nx}" y="{ny+i*22}" font-size="{15 if i==0 else 13}" class="t2">{s}</text>')


    # ---------------- side labels + measurement callouts ----------------
    # ear sits bottom-left in the TOP VIEW; FRONT = the edge the retention
    # tab slides under (opposite the screw corner).
    def sides(ox, oy, half, tag=""):
        S_=[]
        S_.append(txt(ox, oy-half-16, "REAR", "middle", 13, cls="t2"))
        S_.append(txt(ox, oy+half+26, "FRONT" + tag, "middle", 13, cls="t2"))
        S_.append(txt(ox-half-30, oy+4, "LEFT", "middle", 13, cls="t2"))
        S_.append(txt(ox+half+30, oy+4, "RIGHT", "middle", 13, cls="t2"))
        return S_
    P += sides(cx, cy, mm(lw/2))
    P += sides(gx, gy, mm(lw/2))
    P += sides(hx, hy, mm(lw/2))



    # ---- rear retention shelf (11 wide, projects 1.18, 1.36 thick shelf) ----
    tab_w, tab_out = 11.0, 1.18
    for (ox, oy, flip) in ((cx, cy, -1), (hx, hy, -1)):
        yb = oy + flip*mm(lw/2)
        P.append(f'<rect x="{ox-mm(tab_w/2):.1f}" y="{yb-mm(tab_out):.1f}" '
                 f'width="{mm(tab_w):.1f}" height="{mm(tab_out):.1f}" class="body"/>')
    P += dim_h(cx-mm(tab_w/2), cx+mm(tab_w/2), cy-mm(lw/2)-mm(3.4), "11.0 shelf")
    P.append(txt(cx+mm(7.0), cy-mm(lw/2)-mm(1.6),
                 "REAR SHELF: 11.0 wide x 1.18 out x 1.36 thick, top at z=2.62,",
                 "start", 11))
    P.append(txt(cx+mm(7.0), cy-mm(lw/2)-mm(0.5),
                 "open underneath, triangular gusset each end - slides under the case",
                 "start", 11))

    P.append('</svg>')
    name = "touchid_module_drawing_blank.svg" if BLANK else "touchid_module_drawing.svg"
    open(os.path.join(OUT,name),"w").write("\n".join(P))
    print("wrote",name)

build(False)
build(True)
