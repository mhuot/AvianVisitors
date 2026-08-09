# Mic housing Fusion build - progress

**State: reducing-tee assembly complete.** Ten bodies build, six documentation
PNGs are written, and every part below was checked against a render before being
committed to disk.

Both caps are **purchased, not printed** - an Oatey mushroom vent cap on top and
a drilled, screened PVC cap below - so they are deliberately not modelled. The
printed parts are the capsule holder, vent carrier, retainer/drip lip and Pi
sled.

`fusion_build.py` is the deliverable. It is `parts/*.py` concatenated in name
order, separated by two blank lines and a `# ---- <filename>` banner:

```sh
python3 - <<'EOF'
import glob, os
parts = sorted(glob.glob("parts/*.py"))
out = []
for i, f in enumerate(parts):
    if i:
        out.append("# " + "-" * (74 - len(os.path.basename(f))) + " " +
                   os.path.basename(f))
    out.append(open(f).read().rstrip("\n"))
open("fusion_build.py", "w").write("\n\n\n".join(out) + "\n")
EOF
```

`00_common.py` supplies the module docstring, imports, `PARAMS` and the
helpers; `NN_*.py` each supply one `build_*` function; `98_render.py` supplies
appearances and rendering; `99_run.py` supplies `run()`. **Edit the part files,
not the assembled script.** Run it through the Fusion MCP with
`featureType: "script"`; it creates its own fresh design document each time, so
it is safe to re-run. It does not save the document.

## Design decision

The build is the **3x3x1-1/2 reducing tee**, not the standalone elbow: Pi in the
vertical 3" run, mic in the 1-1/2" branch. Sized from the board rather than
by feel: a Pi Zero 2 W on edge with a 5.5 mm standoff needs only ~38 mm of
bore, so 4" was overkill. Not 2" either - the Oatey cap is sold for 3" or 4"
but not 2", and at 2" the sled's spine wings are too narrow to lighten. `01_elbow.py` is kept because the
mic-housing geometry is identical either way, but `06_tee.py` is what the
assembly uses - the branch arrives integral to the tee rather than as a separate
fitting. Parts 2-5 are unaffected; they live in the branch bore regardless.

## Verified parts

| Part | File | Evidence |
|---|---|---|
| PVC 3x3x1-1/2 reducing tee | `06_tee.py` | 373558 mm3, one body, bbox x[-28.08, 166.6] y[0, 300] z[+-44.45]. The x and y minima are the checks that matter: -28.08 is exactly the 56.16 hub radius, and y=0 means the mouth survived the socket cut. |
| Pi sled | `07_pi_sled.py` | One welded body, 29901 mm3, bbox x[82.47, 161.83] y[175, 267] z[+-39.68]. Two ribs at 79.36 press-fit the 79.76 bore; six 16 mm lightening cutouts. |
| Pi board | `07_pi_sled.py` | Reference. 2730 mm3 = 65 x 30 x 1.4 exactly, standing off the spine at z 5.5..6.9. |
| Cable riser | `07_pi_sled.py` | Reference. Runs the branch cable from where the sweep ends at the run axis (y=132.15) up to the lower rib (y=200). |
| PVC 1-1/2" DWV 90 elbow | `01_elbow.py` | 126949 mm3, bbox x[-28.08, 122.15] y[0, 160.23] z[+-28.08]. Renders as a DWV 90 with a hub at each end, mouth facing -Y, cable leg +X. |
| Capsule holder | `02_holder.py` | One joined body, 3029 mm3, y 32..38, aperture 80.8% open. Ring, three spokes and hub all read in the mouth render. |
| Vent carrier | `03_vent_carrier.py` | 166.76 mm3 against a closed-form 166.76. Faces at y=29 (adhesive, 74.02 mm2, pierced only by the 2.4 port), y=30 (recess floor), y=32 (rim). |
| Retainer + drip lip | `04_retainer.py` | One joined body, 9974 mm3, bbox y[-12, 4] r 31.08. Stands 3 mm proud of the 56.16 hub with the skirt hanging below the mouth. |
| Reference bodies | `05_reference.py` | Capsule 424.1 mm3 = pi/4*6^2*15 exactly. Windjammer 7095.8 vs the 7092.5 ideal ellipsoid. Cable: 3 path segments, bbox x[-1.6, 147.15]. |

### Assembly stack on the mouth axis

```
y = -12 .. 0    drip skirt and brim
y =   0 .. 4    retainer plug, press-fit in the 48.80 mouth socket
y =  29 .. 32   vent carrier (adhesive face down at y=29)
y =  30 .. 45   lav capsule, nose seated 2 mm into the carrier recess
y =  32 .. 38   capsule holder, press-fit in the 40.90 bore
y =  45 ..      cable, out along the centreline
```

## Deviations from the draft, and why

* **`ring_profile` picked the wrong profile.** The draft chose the annulus by
  smallest area. That happens to work for the hub (ring 1163 mm2 vs inner disc
  1314 mm2) but inverts as soon as the hole is small - which is exactly the
  vent carrier's 2.4 mm port. Now selected by `profileLoops.count == 2`.
* **The vent carrier's recess was cut from the wrong face.** Extruding the cut
  from the disc's base plane opens the recess on the adhesive face, losing the
  capsule seat and leaving the membrane spanning a 6.4 mm hole. It is now cut
  downwards from a plane at the top face, and the capsule was moved down by
  `vent_recess_depth` so its nose actually enters the seat.
* **`arcs.addByCenterStartSweep` does not reliably return the free end** as
  `endSketchPoint`. Both centrelines now pick the arc point furthest from the
  knee. `createPath(first_line, True)` then chains all 3 segments.
* **The windjammer was not an ellipsoid.** A three-point arc is circular, so
  the draft's revolve gave a 22 x 28 lens. It is now a real sketch ellipse
  split by a line on the axis, with the +X half revolved.
* **The cable profile was sketched at the origin and moved afterwards.** It is
  now sketched on a plane at the path's start.
* **The retainer was sized to the 40.90 bore.** The mouth end of a DWV fitting
  is counterbored to 48.80 for the first 25.4 mm, so a part sized to the bore
  falls straight out. It now fits the socket. The holder, at y=32, is above the
  counterbore and does correctly fit the bore.
* **Spokes are drawn analytically, not patterned.** A circular pattern needs a
  separate body to pattern and a combine to weld it back; three rectangles in
  one sketch extrude straight into the ring and hub with a single JOIN.
* **`explode()` was dropped**, as the brief allowed. `occurrence.transform2` is
  not usable in parametric mode and the four required images do not need it.
* **`ui.messageBox` was removed** - it blocks on a human clicking OK.
* **Holder proportions changed** to hit the openness target: `spoke_width`
  4.5 -> 3.0, `holder_rim` 4.0 -> 3.0. See the caveat below.

## Caveats

* **"80% open" is measured across the holder's own aperture** (inside the press
  -fit ring), where it is 80.8%. Measured against the full 40.90 mm pipe bore
  it is 58%, and 80% of the bore is not reachable at any spoke width: a ring
  with even a 1.5 mm rim already blocks 14% of the bore on its own, before the
  hub or any spokes. The printed number in the build output is the aperture
  figure.
* **The windjammer is hidden in all six renders.** It is the alternative to
  the vent carrier - a fur muff over the bare capsule - so it deliberately
  occupies the same space as the carrier and holder hub and makes a nonsense
  of any image containing both. It builds correctly and clears the bore
  (22 mm across a 40.90 mm bore).
* **The tee is rendered at 25% opacity in the cutaway and Pi-bay images.** There
  is no section view in the model; without it the interior is an unlit cavity.

## Fusion API facts established by probing (do not re-derive)

Fusion 2704.1.36.

* API lengths are CENTIMETRES; everything goes through `mm()` exactly once.
* `xZConstructionPlane` normal is `(0, 1, 0)`, so a **positive** extrude
  distance from an XZ sketch travels **+Y**. XZ sketch `(sx, sy)` maps to model
  `(sx, 0, -sy)`. Offset planes built from it keep both conventions.
* `yZConstructionPlane` normal is `(1, 0, 0)`; positive extrude travels +X.
* The elbow sweep has exactly **2 planar faces**, so shelling by "every planar
  face" is safe. The code asserts the count rather than assuming it.
* `Appearances.itemByName` **raises** `RuntimeError: invalid name` when there is
  no match rather than returning None. Every lookup must be guarded.
* There is **no "PVC" appearance** in the installed libraries.
* `Camera.viewExtents` only sticks on a camera that is **already** orthographic.
  Setting `cameraType` and `viewExtents` in the same assignment silently keeps
  the old extents - which renders as a wildly mis-zoomed image rather than an
  error. `shot()` commits the projection change first, then re-reads the camera
  and frames it, then verifies the extents took.
* Conversely, setting `cameraType` to perspective on a camera carrying explicit
  extents raises `Camera type must be orthographic for extents`. `shot()`
  bounces through an orthographic fit to clear it.
* `Viewport.saveAsImageFile(path, 2000, 1500)` re-renders off-screen at the
  requested size with anti-aliasing and an opaque background; it does not
  letterbox to the on-screen viewport's aspect ratio.
* Screenshots taken through the MCP `screenshot` query with a `direction`
  argument come back unfitted and stale-looking. Set the camera from inside a
  script instead.
* **A socket can only be cut into a hub.** `socket_id` (48.80) is larger than
  `pipe_od` (48.26), so counterboring a bare swept branch does not make a socket
  - it saws the mouth clean off, which shows up as the body's y minimum jumping
  from 0 to `socket_depth`. Join a `socket_id + 2*wall` hub first, reopen the
  through bore behind it, then cut the socket.
* Shelling does not generalise from the elbow to the tee. A plain sweep has
  exactly two planar faces so "shell every planar face" is safe; a tee junction
  has none and the rule picks up the wrong set. Union the outer solids, union
  the bores, subtract.
* Give a cutting body a few mm of overshoot past its target. The leftover is
  easy to account for (overshoot x section area) and it avoids coincident-face
  boolean failures. The tee's 86016 mm3 discrepancy is exactly that.
* Appearance names confirmed present: `Plastic - Glossy (White|Black|Green|
  Yellow|Blue|Red)`, `Plastic - Matte (same set + Gray)`, `Plastic - Translucent
  Matte (White|Gray|Green|Red|Blue)`, `Aluminum - Anodized Glossy (Grey|Blue|
  Red)`, `Paint - Enamel Glossy (...)`. There is still no "PVC".
* `set_visible` matches fragments as **substrings**, so they need care:
  `"capsule"` also hides the capsule *holder*. Use `"lav capsule"`.

## Output

`~/AvianVisitors/docs/img/`, all 2000x1500:

* `tee-assembly.png` - iso, opaque.
* `tee-cutaway.png` - same camera, PVC at 25% opacity.
* `tee-pi-bay.png` - the Pi bay, three-quarter. Square-on renders the board and
  spine as flat rectangles with no depth cue, so the camera is deliberately off
  axis.
* `tee-mic-detail.png` - capsule, holder and vent carrier, tee hidden.
* `tee-printed-sled.png` - the sled and board alone.
* `tee-printed-mic.png` - the mic's printed parts alone.

Printed parts render yellow rather than the green the SVG drawings use for
"printed": green beside a green PCB reads as the same material.

The older `mic-housing-*.png` renders are from the elbow-only build and are now
stale.
