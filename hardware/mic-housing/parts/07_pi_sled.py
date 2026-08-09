SLED = {
    # Raspberry Pi Zero 2 W. It is the right board for this build: ~1.5 W against
    # a Pi 4's ~5 W, which is most of the reason no active cooling is needed.
    "pi_len": 65.0,
    "pi_wid": 30.0,
    "pi_thick": 1.4,
    "pi_hole_dx": 58.0,     # mounting hole pitch, long axis
    "pi_hole_dy": 23.0,     # mounting hole pitch, short axis
    # Printed sled
    "sled_bot": 200.0,      # y at the lower rib
    "sled_len": 100.0,
    "rib_thick": 5.0,
    "rib_rim": 8.0,
    "sled_clear": 0.4,      # press fit against the run bore
    "spine_thick": 3.0,
    "spine_half": 46.0,     # overlaps the ribs' inner radius so the JOIN welds
    "lighten_dia": 26.0,
    "lighten_x": 30.5,      # outboard of the 30 mm board and its standoffs
    "lighten_pitch": 34.0,
    "standoff": 4.0,
    "standoff_dia": 6.0,
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
    # nothing (92 x 3 mm of footprint against an 8601 mm2 bore), but solid it is
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
    # side stays clear so air is not funnelled through a 4 mm slot.
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
