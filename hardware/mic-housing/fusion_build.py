"""Shared parameters and helpers for the mic housing build.

VERIFIED. Every length below is millimetres. The Fusion API works in
CENTIMETRES, so every dimension goes through mm() exactly once. Sketch
coordinates are built with pt(), extrude distances with vi(); neither is
ever fed a raw API value.

Facts established by probing this Fusion build (2704.1.36), not assumed:
  * xZConstructionPlane has normal (0, 1, 0). A positive extrude distance
    from an XZ sketch therefore travels +Y.
  * XZ sketch space maps (sx, sy) -> model (sx, 0, -sy).
  * yZConstructionPlane has normal (1, 0, 0); positive extrude travels +X.
"""

import math
import os

import adsk.core
import adsk.fusion

PARAMS = {
    # 1-1/2" PVC DWV, real dimensions
    "pipe_od": 48.26,
    "wall": 3.68,
    "socket_id": 48.80,    # hub bore, a slip fit over pipe OD
    "socket_depth": 25.40,
    "hub_shoulder": 3.0,   # material left past the socket for the pipe to butt
    "bend_radius": 57.15,  # centreline radius of the 90
    "leg_mouth": 75.0,     # straight run from the bend to the mouth
    "leg_cable": 65.0,     # straight run from the bend to the cable exit
    # Lavalier capsule stand-in. Measure yours and change these two.
    "capsule_dia": 6.0,
    "capsule_len": 15.0,
    "capsule_recess": 32.0,  # how far the capsule face sits up inside the mouth
    # Printed parts
    "holder_thick": 6.0,
    "holder_clear": 0.35,   # press-fit clearance against the bore
    "holder_rim": 3.0,      # radial width of the press-fit ring
    "hub_wall": 1.5,        # wall around the capsule in the holder hub
    "holder_capsule_clear": 0.1,
    "spoke_count": 3,
    "spoke_width": 3.0,     # 3.0 keeps the aperture just over 80% open
    "vent_carrier_od": 10.0,
    "vent_carrier_thick": 3.0,
    "vent_port_dia": 2.4,   # matches GORE GAW3342.45.0
    "vent_recess_depth": 2.0,
    "retainer_thick": 4.0,   # depth the plug ring reaches up the mouth socket
    "retainer_rim": 3.0,
    "lip_od": 62.16,        # 3 mm proud of the 56.16 hub OD all round
    "lip_thick": 3.0,       # the brim across the mouth face
    "skirt_wall": 2.0,
    "drip_lip": 12.0,       # total drop of brim + skirt below the mouth
    "cable_dia": 3.2,
    "cable_tail": 25.0,     # how far the cable runs past the cable hub
    # Windjammer envelope. This is the ALTERNATIVE to the vent carrier - a fur
    # muff over the bare capsule - so it is built but hidden by default.
    "jammer_rx": 11.0,
    "jammer_ry": 14.0,
}

NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
CUT = adsk.fusion.FeatureOperations.CutFeatureOperation


def mm(value):
    """Millimetres to the centimetres the Fusion API expects."""
    return value * 0.1


def pt(x=0.0, y=0.0, z=0.0):
    return adsk.core.Point3D.create(mm(x), mm(y), mm(z))


def vi(value_mm):
    return adsk.core.ValueInput.createByReal(mm(value_mm))


def bbox(body):
    """Bounding box back in millimetres, for sanity-printing."""
    lo, hi = body.boundingBox.minPoint, body.boundingBox.maxPoint
    return ([round(v * 10, 2) for v in lo.asArray()],
            [round(v * 10, 2) for v in hi.asArray()])


def report(comp):
    print("  %s: %d body(s)" % (comp.name, comp.bRepBodies.count))
    for b in comp.bRepBodies:
        print("    %-16s vol %9.1f mm3  bbox %s" % (
            b.name, b.physicalProperties.volume * 1000, bbox(b)))


def new_component(root, name):
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    occ.component.name = name
    return occ.component


def ring_profile(sketch, outer_dia, inner_dia, cx=0.0, cy=0.0):
    """Two concentric circles; return the annulus between them.

    Picked by LOOP COUNT, not by area. The annulus is the only profile with
    two profileLoops; the inner disc has one. Choosing "smallest area" as the
    original draft did happens to work when the ring is thick, but silently
    returns the inner disc as soon as the hole is small - which is exactly the
    case for the vent carrier's 2.4 mm port.
    """
    centre = adsk.core.Point3D.create(mm(cx), mm(cy), 0)
    circles = sketch.sketchCurves.sketchCircles
    circles.addByCenterRadius(centre, mm(outer_dia / 2.0))
    circles.addByCenterRadius(centre, mm(inner_dia / 2.0))
    rings = [p for p in sketch.profiles if p.profileLoops.count == 2]
    if len(rings) != 1:
        raise RuntimeError("sketch %r: expected 1 annulus, found %d of %d" % (
            sketch.name, len(rings), sketch.profiles.count))
    return rings[0]


def circle_profile(sketch, dia, cx=0.0, cy=0.0):
    centre = adsk.core.Point3D.create(mm(cx), mm(cy), 0)
    sketch.sketchCurves.sketchCircles.addByCenterRadius(centre, mm(dia / 2.0))
    return sketch.profiles.item(0)


def offset_plane(comp, base_plane, distance):
    planes = comp.constructionPlanes
    pin = planes.createInput()
    pin.setByOffset(base_plane, vi(distance))
    return planes.add(pin)


def extrude(comp, profile, distance, operation=NEW):
    """Single-sided extrude. Sign of `distance` follows the sketch plane's
    normal, so on an XZ sketch positive is +Y."""
    ex = comp.features.extrudeFeatures
    ei = ex.createInput(profile, operation)
    ei.setDistanceExtent(False, vi(distance))
    return ex.add(ei)


def mouth_plane(comp, y):
    """A sketch plane square to the mouth axis, `y` mm up inside the mouth.
    Its +extrude direction is +Y, i.e. further up the hood."""
    plane = offset_plane(comp, comp.xZConstructionPlane, y)
    plane.name = "mouth y=%g" % y
    return plane


# --------------------------------------------------------------- 01_elbow.py


def build_elbow(root):
    """The 1-1/2" PVC DWV 90 itself.

    VERIFIED: sweeps, shells and counterbores cleanly; renders as a recognisable
    DWV elbow with a hub at each end.

    Sweep the full OD solid along the centreline and shell it, rather than
    cutting a second swept body. The sweep has exactly two planar faces - the
    two cut ends - which makes them trivial to find and hand to the shell. That
    count is asserted below; if a future bend_radius change ever makes the sweep
    self-intersect, the assert fires instead of the shell silently misbehaving.
    """
    p = PARAMS
    comp = new_component(root, 'PVC 1-1/2in DWV 90 elbow')
    bore = p["pipe_od"] - 2 * p["wall"]
    hub_od = p["socket_id"] + 2 * p["wall"]
    r, lm, lc = p["bend_radius"], p["leg_mouth"], p["leg_cable"]

    # Centreline in the XY plane: down the mouth leg, round the bend, out the
    # cable leg. Mouth end sits at the origin so the mouth opening faces -Y.
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = "elbow centreline"
    lines, arcs = sk.sketchCurves.sketchLines, sk.sketchCurves.sketchArcs
    first = lines.addByTwoPoints(pt(0, 0, 0), pt(0, lm, 0))
    arc = arcs.addByCenterStartSweep(pt(r, lm, 0), first.endSketchPoint,
                                     -math.pi / 2.0)
    # addByCenterStartSweep does not guarantee which of the arc's two sketch
    # points is the free end, so pick the one furthest from the knee rather
    # than trusting endSketchPoint.
    knee = pt(0, lm, 0)
    a0, a1 = arc.startSketchPoint, arc.endSketchPoint
    far = a0 if a0.geometry.distanceTo(knee) > a1.geometry.distanceTo(knee) else a1
    lines.addByTwoPoints(far, pt(r + lc, lm + r, 0))

    path = comp.features.createPath(first, True)
    if path.count != 3:
        raise RuntimeError("centreline chained %d segments, expected 3 "
                           "(line, arc, line)" % path.count)

    # Section on XZ at the origin: its normal is +Y, which is exactly the
    # path's starting direction, so no axis-mapping guesswork.
    psk = comp.sketches.add(comp.xZConstructionPlane)
    psk.name = "elbow section"
    circle_profile(psk, p["pipe_od"])
    sweeps = comp.features.sweepFeatures
    body = sweeps.add(sweeps.createInput(
        psk.profiles.item(0), path, NEW)).bodies.item(0)
    body.name = "PVC elbow"

    planar = [f for f in body.faces if isinstance(f.geometry, adsk.core.Plane)]
    if len(planar) != 2:
        raise RuntimeError("sweep has %d planar faces, expected exactly 2"
                           % len(planar))
    ends = adsk.core.ObjectCollection.create()
    for face in planar:
        ends.add(face)
    shells = comp.features.shellFeatures
    shi = shells.createInput(ends, False)
    shi.insideThickness = vi(p["wall"])
    shells.add(shi)

    # Both ends of a DWV fitting are hubs. Build each as a boss ring joined on,
    # then a counterbore cut back into it; that leaves the shoulder the pipe
    # butts against without any face-selection.
    hs = comp.sketches.add(comp.xZConstructionPlane)
    hs.name = "mouth hub boss"
    extrude(comp, ring_profile(hs, hub_od, bore),
            p["socket_depth"] + p["hub_shoulder"], JOIN)
    cs = comp.sketches.add(comp.xZConstructionPlane)
    cs.name = "mouth counterbore"
    extrude(comp, circle_profile(cs, p["socket_id"]), p["socket_depth"], CUT)

    x_end = r + lc
    cp = offset_plane(comp, comp.yZConstructionPlane, x_end)
    cp.name = "cable end"
    hs2 = comp.sketches.add(cp)
    hs2.name = "cable hub boss"
    # Work out where the cable-leg axis lands in this sketch's own 2D space
    # instead of assuming how YZ maps to it.
    local = hs2.modelToSketchSpace(pt(x_end, lm + r, 0))
    cx, cy = local.x * 10.0, local.y * 10.0
    extrude(comp, ring_profile(hs2, hub_od, bore, cx, cy),
            -(p["socket_depth"] + p["hub_shoulder"]), JOIN)
    cs2 = comp.sketches.add(cp)
    cs2.name = "cable counterbore"
    extrude(comp, circle_profile(cs2, p["socket_id"], cx, cy),
            -p["socket_depth"], CUT)

    report(comp)
    return comp


# -------------------------------------------------------------- 02_holder.py


def build_capsule_holder(root):
    """Ring that press-fits the bore, a central hub gripping the capsule, and
    spokes between the two.

    VERIFIED: builds as a single joined body; visually confirmed sitting up
    inside the mouth with three clean spokes and an open aperture.

    The spokes are drawn analytically at 360/n degrees rather than made with a
    circular pattern feature. A pattern would need a separate body to pattern
    and then a combine to weld it back, and the pattern axis has to be the
    component's Y axis; three rectangles in one sketch is fewer moving parts
    and extrudes straight into the ring and hub with a single JOIN.
    """
    p = PARAMS
    comp = new_component(root, "Printed - capsule holder")
    bore = p["pipe_od"] - 2 * p["wall"]
    ring_od = bore - p["holder_clear"]
    ring_id = ring_od - 2 * p["holder_rim"]
    hub_id = p["capsule_dia"] + p["holder_capsule_clear"]
    hub_od = hub_id + 2 * p["hub_wall"]
    thick = p["holder_thick"]

    plane = mouth_plane(comp, p["capsule_recess"])

    sk = comp.sketches.add(plane)
    sk.name = "holder ring"
    body = extrude(comp, ring_profile(sk, ring_od, ring_id),
                   thick, NEW).bodies.item(0)
    body.name = "capsule holder"

    hsk = comp.sketches.add(plane)
    hsk.name = "holder hub"
    extrude(comp, ring_profile(hsk, hub_od, hub_id), thick, JOIN)

    ssk = comp.sketches.add(plane)
    ssk.name = "holder spokes"
    lines = ssk.sketchCurves.sketchLines
    r_in = hub_od / 2.0 - 1.0    # overlap the hub so the JOIN welds
    r_out = ring_id / 2.0 + 1.0  # overlap the ring likewise
    half = p["spoke_width"] / 2.0
    for i in range(int(p["spoke_count"])):
        a = 2.0 * math.pi * i / p["spoke_count"]
        ux, uy = math.cos(a), math.sin(a)
        vx, vy = -math.sin(a), math.cos(a)
        corners = [(r_in * ux - half * vx, r_in * uy - half * vy),
                   (r_out * ux - half * vx, r_out * uy - half * vy),
                   (r_out * ux + half * vx, r_out * uy + half * vy),
                   (r_in * ux + half * vx, r_in * uy + half * vy)]
        for j in range(4):
            x0, y0 = corners[j]
            x1, y1 = corners[(j + 1) % 4]
            lines.addByTwoPoints(pt(x0, y0, 0), pt(x1, y1, 0))
    if ssk.profiles.count != int(p["spoke_count"]):
        raise RuntimeError("spoke sketch made %d profiles, expected %d"
                           % (ssk.profiles.count, p["spoke_count"]))
    profiles = adsk.core.ObjectCollection.create()
    for prof in ssk.profiles:
        profiles.add(prof)
    extrude(comp, profiles, thick, JOIN)

    quarter_pi = math.pi / 4.0
    aperture = quarter_pi * ring_id ** 2
    blocked = (quarter_pi * hub_od ** 2
               + p["spoke_count"] * p["spoke_width"]
               * (ring_id - hub_od) / 2.0)
    print("  holder aperture %.0f mm2, %.1f%% open"
          % (aperture, 100.0 * (aperture - blocked) / aperture))
    report(comp)
    return comp


# -------------------------------------------------------- 03_vent_carrier.py


def build_vent_carrier(root):
    """The part that makes a GORE vent usable on a domed lav grille: a flat
    outer face for the adhesive, a 2.4 mm port, and a recess the capsule nose
    seats into so almost no air volume is trapped behind the membrane.

    VERIFIED: volume matches the closed-form expectation to 0.01 mm3, and the
    three planar faces land where they should - y=29 (adhesive face, 74.0 mm2,
    pierced only by the port), y=30 (recess floor), y=32 (rim against the
    capsule).

    The recess must be cut from the CAPSULE side. Cutting it from the sketch at
    the disc's base - as the original draft did - opens it on the adhesive face
    instead, which both loses the seat and leaves the membrane spanning a 6.4 mm
    hole. So the recess is cut downwards from a plane at the top face.
    """
    p = PARAMS
    comp = new_component(root, "Printed - vent carrier")
    thick = p["vent_carrier_thick"]
    y_top = p["capsule_recess"]          # face the capsule presses against
    y_bot = y_top - thick                # flat face the vent adheres to

    base = mouth_plane(comp, y_bot)
    sk = comp.sketches.add(base)
    sk.name = "vent carrier disc"
    body = extrude(comp, circle_profile(sk, p["vent_carrier_od"]),
                   thick, NEW).bodies.item(0)
    body.name = "vent carrier"

    psk = comp.sketches.add(base)
    psk.name = "vent port"
    extrude(comp, circle_profile(psk, p["vent_port_dia"]), thick, CUT)

    top = mouth_plane(comp, y_top)
    rsk = comp.sketches.add(top)
    rsk.name = "capsule recess"
    extrude(comp, circle_profile(rsk, p["capsule_dia"] + 0.4),
            -p["vent_recess_depth"], CUT)

    report(comp)
    return comp


# ------------------------------------------------------------ 04_retainer.py


def build_retainer_and_lip(root):
    """One printed part doing two jobs at the mouth: a plug ring that press-fits
    the mouth socket and traps the bug mesh behind it, and a brim plus skirt
    that stand proud of the hub to throw wind-driven rain clear of the opening.

    VERIFIED: joins into a single body, bbox y[-12, 4] x,z[+-31.08]; visually
    confirmed standing proud of the 56.16 mm hub with the skirt hanging below
    the mouth.

    Note it fits the SOCKET (48.80), not the 40.90 pipe bore - the mouth end of
    a DWV fitting is counterbored for the first 25.4 mm, so a part sized to the
    bore would simply fall out. The capsule holder, which sits at y=32, is above
    the counterbore and does fit the bore.
    """
    p = PARAMS
    comp = new_component(root, "Printed - retainer and drip lip")
    plug_od = p["socket_id"] - p["holder_clear"]
    plug_id = plug_od - 2 * p["retainer_rim"]

    mouth = mouth_plane(comp, 0.0)
    sk = comp.sketches.add(mouth)
    sk.name = "retainer plug"
    body = extrude(comp, ring_profile(sk, plug_od, plug_id),
                   p["retainer_thick"], NEW).bodies.item(0)
    body.name = "retainer and drip lip"

    bsk = comp.sketches.add(mouth)
    bsk.name = "drip brim"
    extrude(comp, ring_profile(bsk, p["lip_od"], plug_id),
            -p["lip_thick"], JOIN)

    ssk = comp.sketches.add(mouth_plane(comp, -p["lip_thick"]))
    ssk.name = "drip skirt"
    extrude(comp, ring_profile(ssk, p["lip_od"],
                               p["lip_od"] - 2 * p["skirt_wall"]),
            -(p["drip_lip"] - p["lip_thick"]), JOIN)

    if comp.bRepBodies.count != 1:
        raise RuntimeError("retainer made %d bodies, expected 1 joined body"
                           % comp.bRepBodies.count)
    report(comp)
    return comp


# ----------------------------------------------------------- 05_reference.py


def capsule_y0():
    """The capsule's nose plane. It sits vent_recess_depth BELOW the datum so
    the nose actually seats in the vent carrier's recess rather than merely
    touching its rim."""
    return PARAMS["capsule_recess"] - PARAMS["vent_recess_depth"]


def build_capsule(root):
    """VERIFIED: 424.1 mm3, exactly pi/4 * 6^2 * 15, spanning y 30..45."""
    p = PARAMS
    comp = new_component(root, "Reference - lav capsule")
    sk = comp.sketches.add(mouth_plane(comp, capsule_y0()))
    sk.name = "capsule section"
    body = extrude(comp, circle_profile(sk, p["capsule_dia"]),
                   p["capsule_len"], NEW).bodies.item(0)
    body.name = "lav capsule"
    report(comp)
    return comp


def build_windjammer(root):
    """Fur is not worth modelling; a soft ellipsoid at the right envelope is
    enough to check it clears the bore. 22 mm across against a 40.90 mm bore,
    so it does.

    VERIFIED: 7095.8 mm3 against the 4/3*pi*rx^2*ry ideal of 7092.5.

    A real ellipsoid, not the three-point arc the draft used - a 3-point arc is
    circular, so revolving it gives a lens 22 x 28 rather than an ellipsoid.
    Here a full sketch ellipse is split by a line on the axis, giving two half
    profiles, and the one on +X is revolved.

    This body deliberately occupies the same space as the capsule holder and
    vent carrier: a windjammer and a membrane vent are alternative treatments
    of the same capsule, never fitted together. It is hidden by default.
    """
    p = PARAMS
    comp = new_component(root, "Reference - windjammer")
    rx, ry = p["jammer_rx"], p["jammer_ry"]
    cy = capsule_y0() + p["capsule_len"] / 2.0

    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = "windjammer half section"
    sk.sketchCurves.sketchEllipses.add(
        pt(0, cy, 0), pt(0, cy + ry, 0), pt(rx, cy, 0))
    sk.sketchCurves.sketchLines.addByTwoPoints(
        pt(0, cy - ry, 0), pt(0, cy + ry, 0))
    half = None
    for prof in sk.profiles:
        if prof.areaProperties().centroid.x > 0:
            half = prof
    if half is None:
        raise RuntimeError("no +X half profile in the windjammer sketch")

    revolves = comp.features.revolveFeatures
    ri = revolves.createInput(half, comp.yConstructionAxis, NEW)
    ri.setAngleExtent(False, adsk.core.ValueInput.createByString("360 deg"))
    body = revolves.add(ri).bodies.item(0)
    body.name = "windjammer"
    report(comp)
    return comp


def build_cable(root):
    """Swept along the same centreline geometry the elbow uses, starting at the
    top of the capsule and running out past the cable hub.

    VERIFIED: 3 path segments, bbox x[-1.6, 147.15] y[45, 133.75].

    The section is sketched on a plane at the path's start rather than at the
    origin and moved afterwards, which is what the draft did; a swept body is
    much easier to reason about when its profile actually sits on its path.
    """
    p = PARAMS
    comp = new_component(root, "Reference - cable")
    y0 = capsule_y0() + p["capsule_len"]
    r, lm, lc = p["bend_radius"], p["leg_mouth"], p["leg_cable"]

    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = "cable centreline"
    lines, arcs = sk.sketchCurves.sketchLines, sk.sketchCurves.sketchArcs
    first = lines.addByTwoPoints(pt(0, y0, 0), pt(0, lm, 0))
    arc = arcs.addByCenterStartSweep(pt(r, lm, 0), first.endSketchPoint,
                                     -math.pi / 2.0)
    knee = pt(0, lm, 0)
    a0, a1 = arc.startSketchPoint, arc.endSketchPoint
    far = a0 if a0.geometry.distanceTo(knee) > a1.geometry.distanceTo(knee) else a1
    lines.addByTwoPoints(far, pt(r + lc + p["cable_tail"], lm + r, 0))

    path = comp.features.createPath(first, True)
    if path.count != 3:
        raise RuntimeError("cable centreline chained %d segments, expected 3"
                           % path.count)

    psk = comp.sketches.add(mouth_plane(comp, y0))
    psk.name = "cable section"
    sweeps = comp.features.sweepFeatures
    body = sweeps.add(sweeps.createInput(
        circle_profile(psk, p["cable_dia"]), path, NEW)).bodies.item(0)
    body.name = "cable"
    report(comp)
    return comp


# -------------------------------------------------------------- 98_render.py


# Where the exported PNGs land. Point this at your clone.
OUTPUT_DIR = os.path.expanduser("~/AvianVisitors/docs/img")
IMAGE_W, IMAGE_H = 2000, 1500

# Component name fragment -> appearance name, checked against the installed
# Fusion Appearance Library. There is no "PVC" appearance, so DWV white is
# stood in for by glossy white plastic.
PALETTE = [
    ("PVC", "Plastic - Glossy (White)"),
    ("capsule holder", "Plastic - Matte (Gray)"),
    ("vent carrier", "Plastic - Matte (Gray)"),
    ("retainer", "Plastic - Matte (Gray)"),
    ("lav capsule", "Aluminum - Polished"),
    ("windjammer", "Fabric (Grey)"),
    ("cable", "Rubber - Soft"),
]


def _by_name(collection, name):
    """Appearances.itemByName raises "invalid name" rather than returning None
    when there is no match, so every lookup has to be guarded."""
    try:
        return collection.itemByName(name)
    except Exception:
        return None


def paint_all(app, design):
    """Best effort. A missing appearance should never kill the build."""
    root = design.rootComponent
    cache = {}
    for fragment, wanted in PALETTE:
        applied = cache.get(wanted)
        if applied is None:
            applied = _by_name(design.appearances, wanted)
        if applied is None:
            for lib in app.materialLibraries:
                found = _by_name(lib.appearances, wanted)
                if found:
                    applied = design.appearances.addByCopy(found, wanted)
                    break
        if applied is None:
            print("  no appearance named %r, leaving default" % wanted)
            continue
        cache[wanted] = applied
        for occ in root.occurrences:
            if fragment.lower() in occ.component.name.lower():
                for body in occ.component.bRepBodies:
                    body.appearance = applied


def set_visible(design, hidden_fragments):
    """Show every component except those whose name contains one of the
    fragments. Returns the names left visible."""
    root = design.rootComponent
    frags = [f.lower() for f in hidden_fragments]
    shown = []
    for occ in root.occurrences:
        want = not any(f in occ.component.name.lower() for f in frags)
        if occ.isLightBulbOn != want:
            occ.isLightBulbOn = want
        if want:
            shown.append(occ.component.name)
    return shown


def set_opacity(design, fragment, opacity):
    """Make a component see-through so the parts inside it read. Best effort:
    opacity is not settable on every Fusion release."""
    root = design.rootComponent
    for occ in root.occurrences:
        if fragment.lower() in occ.component.name.lower():
            try:
                occ.component.opacity = opacity
            except Exception as exc:
                print("  opacity %r failed: %s" % (fragment, exc))


def _apply(vp, cam):
    vp.camera = cam
    vp.refresh()
    adsk.doEvents()


def shot(app, filename, eye, target, up=(0.0, 1.0, 0.0), extents=None):
    """Write one PNG.

    `extents` is None for a perspective view framed by isFitView, which frames
    whatever is currently VISIBLE - hiding parts is therefore the way to zoom
    in. Give `extents` in mm to switch to an orthographic camera framed by hand,
    which is the only way to aim at a point the fit would not have chosen (the
    straight-up-the-mouth view, for one).
    """
    vp = app.activeViewport
    vp.visualStyle = adsk.core.VisualStyles.ShadedWithVisibleEdgesOnlyVisualStyle

    def build(camera_type, fit):
        cam = vp.camera
        cam.cameraType = camera_type
        cam.eye = adsk.core.Point3D.create(mm(eye[0]), mm(eye[1]), mm(eye[2]))
        cam.target = adsk.core.Point3D.create(
            mm(target[0]), mm(target[1]), mm(target[2]))
        cam.upVector = adsk.core.Vector3D.create(up[0], up[1], up[2])
        cam.isFitView = fit
        return cam

    if extents is None:
        cam = build(adsk.core.CameraTypes.PerspectiveCameraType, True)
        try:
            _apply(vp, cam)
        except Exception:
            # The camera is still carrying viewExtents from an earlier
            # orthographic shot, and Fusion refuses to make that perspective.
            # Bounce through an orthographic fit to clear it, then retry.
            _apply(vp, build(adsk.core.CameraTypes.OrthographicCameraType, True))
            _apply(vp, build(adsk.core.CameraTypes.PerspectiveCameraType, True))
    else:
        # viewExtents only sticks on a camera that is ALREADY orthographic.
        # Setting cameraType and viewExtents in one assignment silently keeps
        # the old extents - which looks like a wildly mis-zoomed render rather
        # than an error - so commit the projection change first, then reread
        # the camera and frame it.
        _apply(vp, build(adsk.core.CameraTypes.OrthographicCameraType, False))
        cam = vp.camera
        cam.isFitView = False
        cam.viewExtents = mm(extents)
        _apply(vp, cam)
        got = vp.camera.viewExtents
        if abs(got - mm(extents)) > 0.01 * mm(extents):
            raise RuntimeError("viewExtents did not take for %s: asked %.3f, "
                               "got %.3f" % (filename, mm(extents), got))

    path = os.path.join(OUTPUT_DIR, filename)
    if not vp.saveAsImageFile(path, IMAGE_W, IMAGE_H):
        raise RuntimeError("saveAsImageFile failed for " + path)
    print("  wrote %s" % filename)
    return path


def render_all(app, design):
    if not os.path.isdir(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    written = []

    # The windjammer is the alternative to the vent carrier and shares its
    # space, so it stays hidden in every documentation image.
    set_visible(design, ["windjammer"])
    written.append(shot(app, "mic-housing-assembly.png",
                        eye=(300, 120, 300), target=(45, 70, 0)))

    # Side elevation and the view up the mouth both need the PVC translucent.
    # Without it the elbow is an opaque tube and the interior renders as a black
    # hole: the recess, the holder and the vent port are all inside it.
    set_opacity(design, "PVC", 0.30)
    written.append(shot(app, "mic-housing-side.png",
                        eye=(20, 70, 420), target=(20, 62, 0)))

    # Straight up the mouth axis. This one needs a hand-framed orthographic
    # camera - a fit would recentre on the whole elbow and look up the bend
    # instead - so up is +Z here, the view direction being +Y.
    written.append(shot(app, "mic-housing-mouth.png",
                        eye=(0, -160, 0), target=(0, 30, 0), up=(0, 0, 1),
                        extents=60.0))
    set_opacity(design, "PVC", 1.0)

    # Detail on the capsule and vent carrier. Hiding the elbow and the retainer
    # clears the sight line; the holder stays because it is what traps the two
    # of them together.
    set_visible(design, ["windjammer", "PVC", "retainer"])
    written.append(shot(app, "mic-housing-detail.png",
                        eye=(60, 22, 70), target=(0, 36, 0), extents=22.0))
    set_visible(design, ["windjammer"])
    return written


# ----------------------------------------------------------------- 99_run.py


def run(_context: str):
    app = adsk.core.Application.get()
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    doc.name = "AvianVisitors mic housing"
    design = adsk.fusion.Design.cast(app.activeProduct)
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    root = design.rootComponent

    build_elbow(root)
    build_capsule_holder(root)
    build_vent_carrier(root)
    build_retainer_and_lip(root)
    build_capsule(root)
    build_windjammer(root)
    build_cable(root)

    paint_all(app, design)
    for path in render_all(app, design):
        print("  ->", path)
    print("DONE")
