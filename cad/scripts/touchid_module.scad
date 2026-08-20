// TouchID module housing — parametric OpenSCAD (v3, caliper-measured)
// Mirrors touchid_module.py. Two-tier body:
//   tier 1 (back, z 0..lip_h):     19.72 sq lip — PCB mounts on its back
//   tier 2 (top, z lip_h..body_h): 18.64 sq — top face flush with enclosure
// Z=0 = BACK (PCB/pogo side). Housing top view = mirror-x of pad-side view.
// MEASURED: 18.64 x 18.64 x 8.44; lip 19.72 x 4.20; ear diagonal 30.4.

FIT = 0.14;
body_w = 18.64 - FIT;  body_l = 18.64 - FIT;   // top tier
lip_w  = 19.72 - 0.12; lip_l  = 19.72 - 0.12;  // back lip tier
pcb_t_ref = 1.2;
lip_h  = 4.20 - pcb_t_ref;   // 3.0 plastic lip (measured 4.20 included PCB edge)
body_h = 8.44 - pcb_t_ref;  // 7.24 housing; assembled with PCB = 8.44
corner_ch = 1.8;  top_t = 1.6;  wall_t = 1.4;

sensor_window_d = 12.4;  // SET TO YOUR SENSOR
sensor_body_d   = 14.2;
sensor_lip_t    = 0.8;

// MEASURED arm: 5.18 wide, 3.0 thick; tip-to-opposite-corner diagonal 30.4
arm_w = 5.18;
ear_r = arm_w / 2;                  // rounded tip radius 2.59
ear_diag = 16.46 - ear_r;           // hole center from module center = 13.87
ear_t = 3.0;
ear_hole_d = 2.3; ear_csk_d = 4.4;
ear_sx = -1; ear_sy = -1;

pcb_screw_pilot_d = 1.7; pcb_screw_depth = 5.0;
pcb_screw_pos = [[8.3, 0], [-8.3, 0]];  // relocated for ESP32 clearance
boss_flat_x = 6.75;                     // inner flat on bosses
post_d = 2.0; post_h = 2.0;
post_pos = [];  // no posts

$fn = 64;
u = 0.70710678;
ex = ear_sx * ear_diag * u;
ey = ear_sy * ear_diag * u;
ear_offset = ear_diag - (lip_w/2) * 1.41421;

module oct2d(w, l) {
    polygon([
        [-w/2+corner_ch, -l/2], [ w/2-corner_ch, -l/2],
        [ w/2, -l/2+corner_ch], [ w/2,  l/2-corner_ch],
        [ w/2-corner_ch,  l/2], [-w/2+corner_ch,  l/2],
        [-w/2, l/2-corner_ch], [-w/2, -l/2+corner_ch]]);
}

difference() {
    union() {
        linear_extrude(lip_h) oct2d(lip_w, lip_l);                     // lip tier
        translate([0,0,lip_h]) linear_extrude(body_h-lip_h) oct2d(body_w, body_l); // top tier
        // arm: top face at the lip step (z = lip_h), 3.0 deep
        translate([ex, ey, 0]) cylinder(h = ear_t, d = 2*ear_r);
        translate([ear_sx*(12.2+ear_diag)/2*u, ear_sy*(12.2+ear_diag)/2*u, 0])
            rotate([0, 0, (ear_sx*ear_sy > 0) ? 45 : -45]) translate([0,0,ear_t/2])
            cube([ear_diag - 12.2, 2*ear_r, ear_t], center = true);    // short bridge
        for (p = pcb_screw_pos)                                        // screw bosses
            intersection() {
                translate([p[0], p[1], 0]) cylinder(h = pcb_screw_depth + 0.5, d = 4.6);
                linear_extrude(body_h) oct2d(lip_w, lip_l);
                // inner flat so the ESP32 module clears
                translate([sign(p[0])*(boss_flat_x + 15), p[1], pcb_screw_depth/2])
                    cube([30, 30, pcb_screw_depth + 2], center = true);
            }
        for (p = post_pos)                                             // alignment post
            translate([p[0], p[1], -post_h]) cylinder(h = post_h, d = post_d);
    }
    // stepped interior cavity: bigger in the lip tier (fits ESP32-C3-MINI-1)
    translate([0, 0, -0.01])
        cube([lip_w - 2*wall_t, lip_l - 2*wall_t, 2*lip_h], center = true);
    translate([-(body_w - 2*wall_t)/2, -(body_l - 2*wall_t)/2, lip_h - 0.01])
        cube([body_w - 2*wall_t, body_l - 2*wall_t, body_h - top_t - lip_h + 0.02]);
    // sensor window + counterbore leaving retaining lip
    translate([0, 0, -1]) cylinder(h = body_h + 2, d = sensor_window_d);
    translate([0, 0, body_h - top_t - 0.01])
        cylinder(h = top_t - sensor_lip_t + 0.01, d = sensor_body_d);
    // ear screw hole + 90deg countersink (opens at arm top face, z = lip_h)
    translate([ex, ey, -1]) cylinder(h = ear_t + 2, d = ear_hole_d);
    translate([ex, ey, ear_t - (ear_csk_d - ear_hole_d)/2])
        cylinder(h = (ear_csk_d - ear_hole_d)/2 + 0.01, d1 = ear_hole_d, d2 = ear_csk_d);
    // screwdriver/head relief above the arm
    translate([ex, ey, ear_t - 0.01]) cylinder(h = body_h - ear_t + 0.02, d = ear_csk_d + 0.6);
    // PCB screw pilot holes
    for (p = pcb_screw_pos)
        translate([p[0], p[1], -0.01]) cylinder(h = pcb_screw_depth, d = pcb_screw_pilot_d);
}
