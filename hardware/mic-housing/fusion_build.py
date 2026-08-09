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


# ----------------------------------------------------------------- 06_tee.py


TEE = {
    # 3" DWV run that houses the Pi. Sized from the board, not by feel: a Pi
    # Zero 2 W on edge with a 5.5 mm standoff puts its far corner
    # sqrt(15^2 + 6.9^2) = 16.5 mm off the axis, so ~38 mm of bore would do.
    # 3" (79.76) leaves room for the sled, the cable and a PoE splitter.
    #
    # Not 2": the Oatey mushroom cap is sold for 3" or 4" but not 2", and at 2"
    # the sled's spine wings shrink to ~7 mm, too narrow to lighten.
    "run_od": 88.9,
    "run_wall": 4.57,
    "run_bot": 70.0,     # open lower end; the inlet cap slips on here
    "run_top": 300.0,    # open upper end; the outlet cap slips on here
    "run_axis_x": 122.15,
    # Where the tee's branch hub ends and the street elbow begins. Outboard of
    # this face is a separate fitting you buy separately.
    "hub_joint_x": 67.15,
}


def build_tee_body(root):
    """The 3x3x1-1/2 reducing tee: vertical run for the Pi, branch for the mic.

    VERIFIED. 373558 mm3, one body,
    bbox x[-28.08, 166.6] y[0, 300] z[+-44.45].

    The two bbox minima are the checks that matter: -28.08 is exactly the 56.16
    hub radius, and y=0 means the mouth survived the socket cut.

    Built by boolean rather than by shelling. `build_elbow` can shell because a
    plain sweep has exactly two planar faces; a tee has none at the junction, and
    asking Fusion to shell "every planar face" there picks up the wrong set. So
    union the two outer solids, union the two bores, and subtract - every face is
    then implied by geometry rather than selected.

    The branch is the same line -> arc -> line sweep as the standalone elbow, so
    the mic housing carries over unchanged; it just arrives integral to the tee
    instead of as a separate fitting. Mouth still sits at the origin facing -Y.

    The bore cylinder deliberately overshoots the run by 5 mm at each end so the
    cut never has to resolve coincident faces. That overshoot lies outside the
    solid, so the finished volume is larger than (outer union - bore union) by
    exactly 2 * 5 * pi/4 * run_id^2 - worth knowing before treating the
    difference as an error.
    """
    p, t = PARAMS, TEE
    comp = new_component(root, 'PVC 3x3x1-1/2 reducing tee')
    x_run = p["bend_radius"] + p["leg_cable"]

    outer_branch = _sweep_branch(comp, p["pipe_od"])
    outer_run = _run_cylinder(comp, t["run_od"], t["run_bot"], t["run_top"], x_run)
    _combine(comp, outer_branch, outer_run, JOIN)

    bore_branch = _sweep_branch(comp, p["pipe_od"] - 2 * p["wall"])
    bore_run = _run_cylinder(comp, t["run_od"] - 2 * t["run_wall"],
                             t["run_bot"] - 5, t["run_top"] + 5, x_run)
    _combine(comp, bore_branch, bore_run, JOIN)

    _combine(comp, outer_branch, bore_branch, CUT)
    _branch_hub(comp)
    _mouth_socket(comp, outer_branch)
    outer_branch.name = "tee body"

    if comp.bRepBodies.count != 1:
        raise RuntimeError("tee left %d bodies, expected 1" % comp.bRepBodies.count)
    report(comp)
    return comp


def _branch_hub(comp):
    """Swell the outboard part of the branch into a hub.

    THIS IS TWO FITTINGS, not one. No maker sells a tee whose branch curves 90
    degrees downward. What you buy is a reducing SANITARY tee plus a 1-1/2"
    street 90 whose spigot glues into the tee's branch hub. The model sweeps the
    branch as one continuous solid for simplicity, so without this swell the
    render invites you to shop for a part that does not exist.

    The hub's end face at `x0` is the joint: everything outboard of it is the
    street elbow, everything inboard is the tee.

    Revolved rather than extruded because the branch axis runs along X, and every
    verified plane convention here is for XZ sketches, whose extrudes travel +Y.
    A revolve about a sketch line needs only an XY sketch.
    """
    p, t = PARAMS, TEE
    branch_y = p["leg_mouth"] + p["bend_radius"]
    x0, x1 = t["hub_joint_x"], t["run_axis_x"] - 17.0
    y_lo = branch_y + p["pipe_od"] / 2.0
    y_hi = branch_y + (p["socket_id"] + 2 * p["wall"]) / 2.0

    sk = comp.sketches.add(comp.xYConstructionPlane)
    lines = sk.sketchCurves.sketchLines
    axis = lines.addByTwoPoints(pt(x0 - 12, branch_y, 0), pt(x1 + 12, branch_y, 0))
    corners = [pt(x0, y_lo, 0), pt(x1, y_lo, 0), pt(x1, y_hi, 0), pt(x0, y_hi, 0)]
    for i in range(4):
        lines.addByTwoPoints(corners[i], corners[(i + 1) % 4])

    profiles = [pr for pr in sk.profiles if pr.profileLoops.count == 1]
    if len(profiles) != 1:
        raise RuntimeError("branch hub sketch made %d profiles, expected 1"
                           % len(profiles))
    revolves = comp.features.revolveFeatures
    ri = revolves.createInput(profiles[0], axis, JOIN)
    ri.setAngleExtent(False, adsk.core.ValueInput.createByString("360 deg"))
    revolves.add(ri)


def _mouth_socket(comp, body):
    """Counterbore the branch mouth to `socket_id` for `socket_depth`.

    A real reducing tee's branch is a hub - you glue pipe into it - so this is
    what the fitting actually looks like. It also matters structurally here:
    `build_retainer_and_lip` is sized to the 48.80 socket, not the 40.90 bore,
    so without this the retainer has nothing to grip and falls straight out.
    """
    p = PARAMS
    hub_od = p["socket_id"] + 2 * p["wall"]
    hub_len = p["socket_depth"] + p["hub_shoulder"]
    bore = p["pipe_od"] - 2 * p["wall"]
    base = mouth_plane(comp, 0.0)

    # The socket is WIDER than the pipe it receives (48.80 vs 48.26), so it can
    # only be cut into a hub. Counterboring the bare swept branch just saws the
    # mouth off - the cutter is larger than the tube's outside diameter.
    extrude(comp, circle_profile(comp.sketches.add(base), hub_od), hub_len, JOIN)
    # The hub goes on as a solid slug, so reopen the through bore behind it...
    extrude(comp, circle_profile(comp.sketches.add(base), bore), hub_len, CUT)
    # ...then take the socket itself out of the first socket_depth.
    extrude(comp, circle_profile(comp.sketches.add(base), p["socket_id"]),
            p["socket_depth"], CUT)


def _sweep_branch(comp, dia):
    """Mic branch: mouth at the origin facing -Y, running +X to meet the run."""
    p = PARAMS
    r, lm, lc = p["bend_radius"], p["leg_mouth"], p["leg_cable"]
    sk = comp.sketches.add(comp.xYConstructionPlane)
    lines, arcs = sk.sketchCurves.sketchLines, sk.sketchCurves.sketchArcs
    first = lines.addByTwoPoints(pt(0, 0, 0), pt(0, lm, 0))
    arc = arcs.addByCenterStartSweep(pt(r, lm, 0), first.endSketchPoint,
                                     -math.pi / 2.0)
    knee = pt(0, lm, 0)
    a0, a1 = arc.startSketchPoint, arc.endSketchPoint
    far = a0 if a0.geometry.distanceTo(knee) > a1.geometry.distanceTo(knee) else a1
    lines.addByTwoPoints(far, pt(r + lc, lm + r, 0))

    path = comp.features.createPath(first, True)
    if path.count != 3:
        raise RuntimeError("branch chained %d segments, expected 3" % path.count)

    psk = comp.sketches.add(comp.xZConstructionPlane)
    circle_profile(psk, dia)
    sweeps = comp.features.sweepFeatures
    return sweeps.add(sweeps.createInput(
        psk.profiles.item(0), path, NEW)).bodies.item(0)


def _run_cylinder(comp, dia, y_lo, y_hi, x_at):
    """Vertical run. Extruded symmetric about XZ then translated, so the result
    never depends on which way the plane normal points."""
    length = y_hi - y_lo
    sk = comp.sketches.add(comp.xZConstructionPlane)
    circle_profile(sk, dia, cx=x_at)
    ex = comp.features.extrudeFeatures
    ei = ex.createInput(sk.profiles.item(0), NEW)
    ei.setSymmetricExtent(vi(length), True)
    body = ex.add(ei).bodies.item(0)

    col = adsk.core.ObjectCollection.create()
    col.add(body)
    m = adsk.core.Matrix3D.create()
    m.translation = adsk.core.Vector3D.create(0, mm(y_lo + length / 2.0), 0)
    comp.features.moveFeatures.add(
        comp.features.moveFeatures.createInput(col, m))
    return body


def _combine(comp, target, tool, operation):
    col = adsk.core.ObjectCollection.create()
    col.add(tool)
    ci = comp.features.combineFeatures.createInput(target, col)
    ci.operation = operation
    return comp.features.combineFeatures.add(ci)


# ------------------------------------------------------------- 07_pi_sled.py


SLED = {
    # Raspberry Pi Zero 2 W. It is the right board for this build: ~1.5 W against
    # a Pi 4's ~5 W, which is most of the reason no active cooling is needed.
    "pi_len": 65.0,
    "pi_wid": 30.0,
    "pi_thick": 1.4,
    "pi_hole_dx": 58.0,     # mounting hole pitch, long axis
    "pi_hole_dy": 23.0,     # mounting hole pitch, short axis
    # Printed sled
    "sled_bot": 175.0,      # y at the lower rib
    "sled_len": 92.0,
    "rib_thick": 5.0,
    "rib_rim": 6.0,
    "sled_clear": 0.4,      # press fit against the run bore
    "spine_thick": 3.0,
    "spine_half": 35.0,     # overlaps the ribs' inner radius so the JOIN welds
    "lighten_dia": 14.0,
    "lighten_x": 25.0,      # outboard of the 30 mm board and its standoffs
    "lighten_pitch": 30.0,
    # CNC Kitchen "Heat Set Insert M3 x 3, short version". Off their datasheet:
    # 4.6 body diameter, 3.0 long, 4.0 recommended hole, 4.0 minimum blind-hole
    # depth, 1.6 minimum wall.
    "insert_len": 3.0,
    "insert_od": 4.6,
    "insert_hole_dia": 4.0,
    "insert_min_depth": 4.0,  # datasheet minimum for a blind hole
    "insert_min_wall": 1.6,
    "insert_floor": 2.0,      # plastic left under the bore
    # Boss diameter is checked against the wall rule at build time rather than
    # trusted. 9.0 clears both readings of it: 4.0 + 2*1.6 = 7.2 from the hole,
    # 4.6 + 2*1.6 = 7.8 from the insert body.
    "standoff": 4.0,
    "standoff_dia": 9.0,
}


def _run_axis_x():
    return PARAMS["bend_radius"] + PARAMS["leg_cable"]


def _move(comp, body, dx=0.0, dy=0.0, dz=0.0):
    col = adsk.core.ObjectCollection.create()
    col.add(body)
    m = adsk.core.Matrix3D.create()
    m.translation = adsk.core.Vector3D.create(mm(dx), mm(dy), mm(dz))
    comp.features.moveFeatures.add(comp.features.moveFeatures.createInput(col, m))


def build_pi_sled(root):
    """Printed carrier that press-fits the 4in run and holds the Pi on edge.

    Two ribs centre it in the bore; a spine plate across the diameter carries the
    board. The board sits in a plane containing the run axis, so both faces see
    the full height of the tube and neither is pressed against a wall.

    The ribs are rings rather than discs for the same reason the capsule holder
    is: a disc across the bore would dam the convection path and, at the bottom,
    hold water.
    """
    p, s = PARAMS, SLED
    comp = new_component(root, "Printed - Pi sled")
    x_run = _run_axis_x()
    run_id = TEE["run_od"] - 2 * TEE["run_wall"]
    rib_od = run_id - s["sled_clear"]
    rib_id = rib_od - 2 * s["rib_rim"]
    y_lo, y_hi = s["sled_bot"], s["sled_bot"] + s["sled_len"]

    lower = comp.sketches.add(mouth_plane(comp, y_lo))
    body = extrude(comp, ring_profile(lower, rib_od, rib_id, cx=x_run),
                   s["rib_thick"], NEW).bodies.item(0)
    body.name = "Pi sled"

    upper = comp.sketches.add(mouth_plane(comp, y_hi - s["rib_thick"]))
    extrude(comp, ring_profile(upper, rib_od, rib_id, cx=x_run),
            s["rib_thick"], JOIN)

    # Spine: sketched on XY (normal +Z) and extruded symmetric, so it straddles
    # z=0 and no extrude direction has to be guessed.
    ssk = comp.sketches.add(comp.xYConstructionPlane)
    half = s["spine_half"]
    corners = [pt(x_run - half, y_lo, 0), pt(x_run + half, y_lo, 0),
               pt(x_run + half, y_hi, 0), pt(x_run - half, y_hi, 0)]
    lines = ssk.sketchCurves.sketchLines
    for i in range(4):
        lines.addByTwoPoints(corners[i], corners[(i + 1) % 4])
    ex = comp.features.extrudeFeatures
    ei = ex.createInput(ssk.profiles.item(0), JOIN)
    ei.setSymmetricExtent(vi(s["spine_thick"]), True)
    ex.add(ei)

    y_mid = (y_lo + y_hi) / 2.0

    # Lighten the wings. The spine is edge-on to the airflow so it blocks almost
    # nothing (70 x 3 mm of footprint against a 4996 mm2 bore), but solid it is
    # over half the sled's filament. The cutouts sit outboard of the board and
    # its standoffs, and let the two halves of the tube exchange air.
    lsk = comp.sketches.add(comp.xYConstructionPlane)
    for sx in (-1, 1):
        for row in (-1, 0, 1):
            lsk.sketchCurves.sketchCircles.addByCenterRadius(
                pt(x_run + sx * s["lighten_x"], y_mid + row * s["lighten_pitch"], 0),
                mm(s["lighten_dia"] / 2.0))
    holes = adsk.core.ObjectCollection.create()
    for prof in lsk.profiles:
        holes.add(prof)
    ei = ex.createInput(holes, CUT)
    ei.setSymmetricExtent(vi(s["spine_thick"] * 4), True)
    ex.add(ei)

    # Standoffs, on the +Z face only. The board hangs off one side; the other
    # side stays clear so air is not funnelled through a narrow slot. They are
    # tall enough that a blind insert hole still leaves a floor: standoff +
    # spine = 7 mm of material against a 4 mm bore.
    hsk = comp.sketches.add(comp.xYConstructionPlane)
    for sx in (-1, 1):
        for sy in (-1, 1):
            hsk.sketchCurves.sketchCircles.addByCenterRadius(
                pt(x_run + sx * s["pi_hole_dy"] / 2.0,
                   y_mid + sy * s["pi_hole_dx"] / 2.0, 0),
                mm(s["standoff_dia"] / 2.0))
    posts = adsk.core.ObjectCollection.create()
    for prof in hsk.profiles:
        posts.add(prof)
    ei = ex.createInput(posts, JOIN)
    ei.setDistanceExtent(False, vi(s["spine_thick"] / 2.0 + s["standoff"]))
    ex.add(ei)

    # Blind bores for the heat-set inserts, cut down from the standoff faces.
    wall = (s["standoff_dia"] - s["insert_od"]) / 2.0
    if wall < s["insert_min_wall"]:
        raise RuntimeError(
            "boss wall %.2f mm is under the %.2f mm minimum; widen standoff_dia"
            % (wall, s["insert_min_wall"]))
    hole_depth = max(s["insert_len"] + 1.0, s["insert_min_depth"])
    top_z = s["spine_thick"] / 2.0 + s["standoff"]
    depth_available = s["standoff"] + s["spine_thick"]
    if hole_depth + s["insert_floor"] > depth_available:
        raise RuntimeError(
            "insert bore %.1f + floor %.1f exceeds %.1f mm of material; raise "
            "standoff" % (hole_depth, s["insert_floor"], depth_available))

    top = offset_plane(comp, comp.xYConstructionPlane, top_z)
    bsk = comp.sketches.add(top)
    for sx in (-1, 1):
        for sy in (-1, 1):
            bsk.sketchCurves.sketchCircles.addByCenterRadius(
                pt(x_run + sx * s["pi_hole_dy"] / 2.0,
                   y_mid + sy * s["pi_hole_dx"] / 2.0, 0),
                mm(s["insert_hole_dia"] / 2.0))
    bores = adsk.core.ObjectCollection.create()
    for prof in bsk.profiles:
        bores.add(prof)
    ei = ex.createInput(bores, CUT)
    ei.setDistanceExtent(False, vi(-hole_depth))
    ex.add(ei)

    if comp.bRepBodies.count != 1:
        raise RuntimeError("sled left %d bodies, expected 1 welded body"
                           % comp.bRepBodies.count)
    report(comp)
    return comp


def build_pi_board(root):
    """Reference only - a Pi Zero 2 W stood in for by its board outline."""
    s = SLED
    comp = new_component(root, "Reference - Pi board")
    x_run = _run_axis_x()
    y_mid = s["sled_bot"] + s["sled_len"] / 2.0

    sk = comp.sketches.add(comp.xYConstructionPlane)
    hw, hl = s["pi_wid"] / 2.0, s["pi_len"] / 2.0
    corners = [pt(x_run - hw, y_mid - hl, 0), pt(x_run + hw, y_mid - hl, 0),
               pt(x_run + hw, y_mid + hl, 0), pt(x_run - hw, y_mid + hl, 0)]
    lines = sk.sketchCurves.sketchLines
    for i in range(4):
        lines.addByTwoPoints(corners[i], corners[(i + 1) % 4])
    ex = comp.features.extrudeFeatures
    ei = ex.createInput(sk.profiles.item(0), NEW)
    ei.setSymmetricExtent(vi(s["pi_thick"]), True)
    body = ex.add(ei).bodies.item(0)
    body.name = "Pi board"
    _move(comp, body, dz=s["spine_thick"] / 2.0 + s["standoff"]
          + s["pi_thick"] / 2.0)
    report(comp)
    return comp


def build_cable_riser(root):
    """The mic cable, continuing from where the branch sweep ends at the run
    axis up to the underside of the sled. Stops at the lower rib rather than
    passing through the spine."""
    p, s = PARAMS, SLED
    comp = new_component(root, "Reference - cable riser")
    x_run = _run_axis_x()
    y0 = p["leg_mouth"] + p["bend_radius"]

    sk = comp.sketches.add(mouth_plane(comp, y0))
    body = extrude(comp, circle_profile(sk, p["cable_dia"], cx=x_run),
                   s["sled_bot"] - y0, NEW).bodies.item(0)
    body.name = "cable riser"
    report(comp)
    return comp


# ---------------------------------------------------------------- 08_caps.py


CAPS = {
    # Both caps are PURCHASED, not printed. They are modelled anyway so the
    # assembly renders show the thing you actually hang on the wall, and so the
    # clearances above and below the run can be checked against real fittings.
    "skirt_id": 89.7,        # slips over the 88.9 run OD
    "skirt_od": 99.7,
    "skirt_len": 40.0,
    "skirt_drop": 25.0,      # how far the skirt reaches down over the pipe
    "crown_od": 112.0,
    "crown_thick": 6.0,
    "crown_gap": 18.0,       # the annular exit: this is what vents the tube
    "post_count": 3,
    "post_dia": 8.0,
    "post_r": 47.3,          # on the skirt's wall, midway across the rim
    "drain_base": 8.0,
    "drain_wall_len": 62.0,
    "drain_drop": 45.0,      # base sits this far below the pipe end
    "hole_dia": 8.0,
    "hole_count": 8,
    "hole_r": 28.0,
    "poe_dia": 6.0,
}


def build_vent_cap(root):
    """Oatey-style mushroom vent cap for the top of the run. PURCHASED.

    A skirt clamps over the pipe and a raised crown sits above it on three
    posts. Air leaves the pipe, rises inside the skirt and exits radially
    through the `crown_gap` annulus - which is why the crown has to stand off
    rather than sit down on the rim. Rain cannot fall straight in because the
    crown overhangs the whole opening.
    """
    p, c = PARAMS, CAPS
    comp = new_component(root, "PVC - mushroom vent cap (purchased)")
    x_run = PARAMS["bend_radius"] + PARAMS["leg_cable"]
    y_skirt = TEE["run_top"] - c["skirt_drop"]
    y_rim = y_skirt + c["skirt_len"]
    y_crown = y_rim + c["crown_gap"]

    sk = comp.sketches.add(mouth_plane(comp, y_skirt))
    body = extrude(comp, ring_profile(sk, c["skirt_od"], c["skirt_id"], cx=x_run),
                   c["skirt_len"], NEW).bodies.item(0)
    body.name = "mushroom vent cap"

    psk = comp.sketches.add(mouth_plane(comp, y_rim))
    for i in range(c["post_count"]):
        theta = 2.0 * math.pi * i / c["post_count"]
        psk.sketchCurves.sketchCircles.addByCenterRadius(
            pt(x_run + c["post_r"] * math.cos(theta),
               c["post_r"] * math.sin(theta), 0),
            mm(c["post_dia"] / 2.0))
    posts = adsk.core.ObjectCollection.create()
    for prof in psk.profiles:
        posts.add(prof)
    ex = comp.features.extrudeFeatures
    ei = ex.createInput(posts, JOIN)
    ei.setDistanceExtent(False, vi(c["crown_gap"]))
    ex.add(ei)

    csk = comp.sketches.add(mouth_plane(comp, y_crown))
    extrude(comp, circle_profile(csk, c["crown_od"], cx=x_run),
            c["crown_thick"], JOIN)

    if comp.bRepBodies.count != 1:
        raise RuntimeError("vent cap left %d bodies, expected 1"
                           % comp.bRepBodies.count)
    report(comp)
    return comp


def build_drain_cap(root):
    """Plain PVC cap for the bottom, drilled and screened. PURCHASED.

    Solid, this would pool overnight condensate directly under the Pi with
    nowhere to go - drainage is the reason it is drilled, not airflow. The
    centre hole passes the PoE cable through its gland.
    """
    p, c = PARAMS, CAPS
    comp = new_component(root, "PVC - drain cap (purchased)")
    x_run = PARAMS["bend_radius"] + PARAMS["leg_cable"]
    y_base = TEE["run_bot"] - c["drain_drop"]
    y_wall = y_base + c["drain_base"]

    bsk = comp.sketches.add(mouth_plane(comp, y_base))
    body = extrude(comp, circle_profile(bsk, c["skirt_od"], cx=x_run),
                   c["drain_base"], NEW).bodies.item(0)
    body.name = "drain cap"

    wsk = comp.sketches.add(mouth_plane(comp, y_wall))
    extrude(comp, ring_profile(wsk, c["skirt_od"], c["skirt_id"], cx=x_run),
            c["drain_wall_len"], JOIN)

    # Drain holes on a bolt circle, plus the centre pass-through for the cable.
    hsk = comp.sketches.add(mouth_plane(comp, y_base))
    for i in range(c["hole_count"]):
        theta = 2.0 * math.pi * i / c["hole_count"]
        hsk.sketchCurves.sketchCircles.addByCenterRadius(
            pt(x_run + c["hole_r"] * math.cos(theta),
               c["hole_r"] * math.sin(theta), 0),
            mm(c["hole_dia"] / 2.0))
    hsk.sketchCurves.sketchCircles.addByCenterRadius(
        pt(x_run, 0, 0), mm(c["poe_dia"] / 2.0 + 1.0))
    holes = adsk.core.ObjectCollection.create()
    for prof in hsk.profiles:
        holes.add(prof)
    ex = comp.features.extrudeFeatures
    ei = ex.createInput(holes, CUT)
    ei.setDistanceExtent(False, vi(c["drain_base"]))
    ex.add(ei)

    report(comp)
    return comp


def build_poe_cable(root):
    """PoE cable leaving the drain cap, with the drip loop outside.

    Swept the same way as the mic branch: a line -> arc -> line centreline in
    the XY plane, with the section taken on a plane at the path's start.
    """
    p, c = PARAMS, CAPS
    comp = new_component(root, "Reference - PoE cable")
    x_run = PARAMS["bend_radius"] + PARAMS["leg_cable"]
    y_start = TEE["run_bot"] - c["drain_drop"]
    y_knee = y_start - 55.0
    radius = 30.0

    sk = comp.sketches.add(comp.xYConstructionPlane)
    lines, arcs = sk.sketchCurves.sketchLines, sk.sketchCurves.sketchArcs
    first = lines.addByTwoPoints(pt(x_run, y_start, 0), pt(x_run, y_knee, 0))
    arc = arcs.addByCenterStartSweep(pt(x_run + radius, y_knee, 0),
                                     first.endSketchPoint, math.pi / 2.0)
    knee = pt(x_run, y_knee, 0)
    a0, a1 = arc.startSketchPoint, arc.endSketchPoint
    far = a0 if a0.geometry.distanceTo(knee) > a1.geometry.distanceTo(knee) else a1
    lines.addByTwoPoints(far, pt(x_run + radius + 95.0, y_knee - radius, 0))

    path = comp.features.createPath(first, True)
    if path.count != 3:
        raise RuntimeError("PoE centreline chained %d segments, expected 3"
                           % path.count)

    psk = comp.sketches.add(mouth_plane(comp, y_start))
    circle_profile(psk, c["poe_dia"], cx=x_run)
    sweeps = comp.features.sweepFeatures
    body = sweeps.add(sweeps.createInput(
        psk.profiles.item(0), path, NEW)).bodies.item(0)
    body.name = "PoE cable"
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
    # Verified present in the installed Fusion Appearance Library. Printed parts
    # are yellow rather than the green the SVG drawings use: green next to a
    # green PCB reads as the same material, and filament yellow is unambiguous.
    ("PVC", "Plastic - Glossy (White)"),
    ("capsule holder", "Plastic - Matte (Yellow)"),
    ("vent carrier", "Plastic - Matte (Yellow)"),
    ("retainer", "Plastic - Matte (Yellow)"),
    ("Pi sled", "Plastic - Matte (Yellow)"),
    ("Pi board", "Plastic - Glossy (Green)"),
    ("lav capsule", "Aluminum - Anodized Glossy (Grey)"),
    ("windjammer", "Fabric (Grey)"),
    ("cable", "Plastic - Matte (Black)"),
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
    """Seven images of the reducing-tee station.

    The tee is 400 mm tall against a 6 mm capsule, so no single framing carries
    both. Two overall views establish the assembly, two show the interiors, and
    two isolate the printed parts.

    Fragments passed to set_visible are matched as substrings, so they have to be
    chosen with care: "capsule" alone would also hide the capsule holder.
    """
    if not os.path.isdir(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    written = []
    x_run = PARAMS["bend_radius"] + PARAMS["leg_cable"]

    # The windjammer is the alternative to the vent carrier and occupies the
    # same space, so it stays hidden in every documentation image.
    set_visible(design, ["windjammer"])

    written.append(shot(app, "tee-assembly.png",
                        eye=(560, 330, 500), target=(66, 150, 0)))

    # Same camera, PVC dropped to a quarter. Everything that matters is inside
    # the pipe; opaque, the image is just two tubes.
    set_opacity(design, "PVC", 0.25)
    written.append(shot(app, "tee-cutaway.png",
                        eye=(560, 330, 500), target=(66, 150, 0)))

    # The Pi bay. Three-quarter rather than square-on: dead ahead renders the
    # board and spine as flat rectangles with no depth cue at all.
    written.append(shot(app, "tee-pi-bay.png",
                        eye=(x_run + 215, 300, 210), target=(x_run, 221, 0),
                        extents=100.0))
    set_opacity(design, "PVC", 1.0)

    # Mic internals. Hiding the tee and the retainer clears the sight line; the
    # holder stays because it is what traps the capsule and carrier together.
    set_visible(design, ["windjammer", "PVC", "retainer"])
    written.append(shot(app, "tee-mic-detail.png",
                        eye=(60, 22, 70), target=(0, 36, 0), extents=22.0))

    # Printed parts on their own - what you actually send to the slicer.
    set_visible(design, ["PVC", "lav capsule", "windjammer", "cable",
                         "vent carrier", "retainer", "capsule holder"])
    written.append(shot(app, "tee-printed-sled.png",
                        eye=(x_run + 190, 300, 205), target=(x_run, 221, 0)))

    # The sled with the board taken off, from the mounting face. Every other
    # sled view has the board covering the four insert bosses, which are the
    # features you actually need to see before assembly.
    set_visible(design, ["PVC", "lav capsule", "windjammer", "cable",
                         "vent carrier", "retainer", "capsule holder",
                         "Pi board"])
    written.append(shot(app, "tee-sled-inserts.png",
                        eye=(x_run + 70, 278, 195), target=(x_run, 221, 0),
                        extents=105.0))

    set_visible(design, ["PVC", "lav capsule", "windjammer", "cable", "Pi "])
    written.append(shot(app, "tee-printed-mic.png",
                        eye=(80, 66, 88), target=(0, 14, 0), extents=86.0))

    set_visible(design, ["windjammer"])
    return written


# ----------------------------------------------------------------- 99_run.py


DOC_NAME = "AvianVisitors reducing-tee station"
PART_NUMBER = "2026-08-09-15-43-34-211"


def _clear(root):
    """Empty the root component so a rebuild lands in the existing document as a
    new version, rather than spawning a fresh Untitled every run."""
    while root.occurrences.count > 0:
        root.occurrences.item(0).deleteMe()
    while root.bRepBodies.count > 0:
        root.bRepBodies.item(0).deleteMe()
    while root.sketches.count > 0:
        root.sketches.item(0).deleteMe()


def run(_context: str):
    app = adsk.core.Application.get()
    doc = app.activeDocument

    # Refuse to build into the wrong file. This script saves at the end, and an
    # unguarded save would either overwrite whatever happens to be open or
    # litter the hub with Untitled documents.
    if doc is None or DOC_NAME not in doc.name:
        raise RuntimeError(
            "active document is %r, expected %r. Open that document first."
            % (doc.name if doc else None, DOC_NAME))

    design = adsk.fusion.Design.cast(app.activeProduct)
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    root = design.rootComponent
    _clear(root)

    # The tee supersedes build_elbow: the branch is the same geometry, it just
    # arrives integral to the fitting. build_elbow is kept in the tree for the
    # indoor-Pi variant but is not part of this assembly.
    build_tee_body(root)

    build_capsule_holder(root)
    build_vent_carrier(root)
    build_retainer_and_lip(root)
    build_capsule(root)
    build_windjammer(root)
    build_cable(root)

    build_pi_sled(root)
    build_pi_board(root)
    build_cable_riser(root)

    # Purchased, but modelled so the assembly renders show the real thing.
    build_vent_cap(root)
    build_drain_cap(root)
    build_poe_cable(root)

    # root.name is bound to the document name and raises if assigned.
    root.partNumber = PART_NUMBER
    print("part number: %s" % root.partNumber)

    paint_all(app, design)
    for path in render_all(app, design):
        print("  ->", path)

    if doc.save("Automated rebuild from parts/*.py"):
        print("SAVED new version of %r" % doc.name)
    else:
        print("SAVE REPORTED FAILURE for %r" % doc.name)
    print("DONE")
