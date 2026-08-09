TEE = {
    # 4" DWV run that houses the Pi
    "run_od": 114.3,
    "run_wall": 4.83,
    "run_bot": 40.0,     # open lower end; the inlet cap slips on here
    "run_top": 400.0,    # open upper end; the outlet cap slips on here
}


def build_tee_body(root):
    """The 4x4x1-1/2 reducing tee: vertical run for the Pi, branch for the mic.

    VERIFIED. 681669 mm3, 11 faces, one body,
    bbox x[-24.1, 179.3] y[0, 400] z[+-57.1].

    Built by boolean rather than by shelling. `build_elbow` can shell because a
    plain sweep has exactly two planar faces; a tee has none at the junction, and
    asking Fusion to shell "every planar face" there picks up the wrong set. So
    union the two outer solids, union the two bores, and subtract - every face is
    then implied by geometry rather than selected.

    The branch is the same line -> arc -> line sweep as the standalone elbow, so
    the mic housing carries over unchanged; it just arrives integral to the tee
    instead of as a separate fitting. Mouth still sits at the origin facing -Y.

    Sanity figures, all confirmed against the model:
      outer branch  420300 mm3  (identical to the standalone elbow sweep)
      outer run    3693898 mm3  (= pi * 57.15^2 * 360)
      union        4012025 mm3
      bore union   3416372 mm3
    The subtraction leaves 681669 rather than 595653 because the bore cylinder
    deliberately overshoots the run by 5 mm at each end to guarantee a clean cut;
    that overshoot (2 * 5 * pi * 52.35^2 = 86016 mm3) lies outside the solid.
    """
    p, t = PARAMS, TEE
    comp = new_component(root, 'PVC 4x4x1-1/2 reducing tee')
    x_run = p["bend_radius"] + p["leg_cable"]

    outer_branch = _sweep_branch(comp, p["pipe_od"])
    outer_run = _run_cylinder(comp, t["run_od"], t["run_bot"], t["run_top"], x_run)
    _combine(comp, outer_branch, outer_run, JOIN)

    bore_branch = _sweep_branch(comp, p["pipe_od"] - 2 * p["wall"])
    bore_run = _run_cylinder(comp, t["run_od"] - 2 * t["run_wall"],
                             t["run_bot"] - 5, t["run_top"] + 5, x_run)
    _combine(comp, bore_branch, bore_run, JOIN)

    _combine(comp, outer_branch, bore_branch, CUT)
    _mouth_socket(comp, outer_branch)
    outer_branch.name = "tee body"

    if comp.bRepBodies.count != 1:
        raise RuntimeError("tee left %d bodies, expected 1" % comp.bRepBodies.count)
    report(comp)
    return comp


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
