def run(_context: str):
    app = adsk.core.Application.get()
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    doc.name = "AvianVisitors reducing-tee station"
    design = adsk.fusion.Design.cast(app.activeProduct)
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    root = design.rootComponent

    # The tee supersedes build_elbow: the branch is the same geometry, it just
    # arrives integral to the fitting. build_elbow is kept in the tree for the
    # mic-only variant but is not part of this assembly.
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

    paint_all(app, design)
    for path in render_all(app, design):
        print("  ->", path)
    print("DONE")
