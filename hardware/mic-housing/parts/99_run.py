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
