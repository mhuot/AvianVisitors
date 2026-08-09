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
