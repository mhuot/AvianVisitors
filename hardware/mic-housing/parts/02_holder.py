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
