def run(_context: str):
    app = adsk.core.Application.get()
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    doc.name = "AvianVisitors mic housing"
    design = adsk.fusion.Design.cast(app.activeProduct)
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    root = design.rootComponent

    build_elbow(root)
    build_capsule_holder(root)
    build_vent_carrier(root)
    build_retainer_and_lip(root)
    build_capsule(root)
    build_windjammer(root)
    build_cable(root)

    paint_all(app, design)
    for path in render_all(app, design):
        print("  ->", path)
    print("DONE")
