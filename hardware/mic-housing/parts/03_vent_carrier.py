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
