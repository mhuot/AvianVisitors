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
