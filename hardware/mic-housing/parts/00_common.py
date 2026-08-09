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
