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
