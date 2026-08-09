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
