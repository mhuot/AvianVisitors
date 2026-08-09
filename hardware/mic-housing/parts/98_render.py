# Where the exported PNGs land. Point this at your clone.
OUTPUT_DIR = os.path.expanduser("~/AvianVisitors/docs/img")
IMAGE_W, IMAGE_H = 2000, 1500

# Component name fragment -> appearance name, checked against the installed
# Fusion Appearance Library. There is no "PVC" appearance, so DWV white is
# stood in for by glossy white plastic.
PALETTE = [
    # Verified present in the installed Fusion Appearance Library. Printed parts
    # are yellow rather than the green the SVG drawings use: green next to a
    # green PCB reads as the same material, and filament yellow is unambiguous.
    ("PVC", "Plastic - Glossy (White)"),
    ("capsule holder", "Plastic - Matte (Yellow)"),
    ("vent carrier", "Plastic - Matte (Yellow)"),
    ("retainer", "Plastic - Matte (Yellow)"),
    ("Pi sled", "Plastic - Matte (Yellow)"),
    ("Pi board", "Plastic - Glossy (Green)"),
    ("lav capsule", "Aluminum - Anodized Glossy (Grey)"),
    ("windjammer", "Fabric (Grey)"),
    ("cable", "Plastic - Matte (Black)"),
]


def _by_name(collection, name):
    """Appearances.itemByName raises "invalid name" rather than returning None
    when there is no match, so every lookup has to be guarded."""
    try:
        return collection.itemByName(name)
    except Exception:
        return None


def paint_all(app, design):
    """Best effort. A missing appearance should never kill the build."""
    root = design.rootComponent
    cache = {}
    for fragment, wanted in PALETTE:
        applied = cache.get(wanted)
        if applied is None:
            applied = _by_name(design.appearances, wanted)
        if applied is None:
            for lib in app.materialLibraries:
                found = _by_name(lib.appearances, wanted)
                if found:
                    applied = design.appearances.addByCopy(found, wanted)
                    break
        if applied is None:
            print("  no appearance named %r, leaving default" % wanted)
            continue
        cache[wanted] = applied
        for occ in root.occurrences:
            if fragment.lower() in occ.component.name.lower():
                for body in occ.component.bRepBodies:
                    body.appearance = applied


def set_visible(design, hidden_fragments):
    """Show every component except those whose name contains one of the
    fragments. Returns the names left visible."""
    root = design.rootComponent
    frags = [f.lower() for f in hidden_fragments]
    shown = []
    for occ in root.occurrences:
        want = not any(f in occ.component.name.lower() for f in frags)
        if occ.isLightBulbOn != want:
            occ.isLightBulbOn = want
        if want:
            shown.append(occ.component.name)
    return shown


def set_opacity(design, fragment, opacity):
    """Make a component see-through so the parts inside it read. Best effort:
    opacity is not settable on every Fusion release."""
    root = design.rootComponent
    for occ in root.occurrences:
        if fragment.lower() in occ.component.name.lower():
            try:
                occ.component.opacity = opacity
            except Exception as exc:
                print("  opacity %r failed: %s" % (fragment, exc))


def _apply(vp, cam):
    vp.camera = cam
    vp.refresh()
    adsk.doEvents()


def shot(app, filename, eye, target, up=(0.0, 1.0, 0.0), extents=None):
    """Write one PNG.

    `extents` is None for a perspective view framed by isFitView, which frames
    whatever is currently VISIBLE - hiding parts is therefore the way to zoom
    in. Give `extents` in mm to switch to an orthographic camera framed by hand,
    which is the only way to aim at a point the fit would not have chosen (the
    straight-up-the-mouth view, for one).
    """
    vp = app.activeViewport
    vp.visualStyle = adsk.core.VisualStyles.ShadedWithVisibleEdgesOnlyVisualStyle

    def build(camera_type, fit):
        cam = vp.camera
        cam.cameraType = camera_type
        cam.eye = adsk.core.Point3D.create(mm(eye[0]), mm(eye[1]), mm(eye[2]))
        cam.target = adsk.core.Point3D.create(
            mm(target[0]), mm(target[1]), mm(target[2]))
        cam.upVector = adsk.core.Vector3D.create(up[0], up[1], up[2])
        cam.isFitView = fit
        return cam

    if extents is None:
        cam = build(adsk.core.CameraTypes.PerspectiveCameraType, True)
        try:
            _apply(vp, cam)
        except Exception:
            # The camera is still carrying viewExtents from an earlier
            # orthographic shot, and Fusion refuses to make that perspective.
            # Bounce through an orthographic fit to clear it, then retry.
            _apply(vp, build(adsk.core.CameraTypes.OrthographicCameraType, True))
            _apply(vp, build(adsk.core.CameraTypes.PerspectiveCameraType, True))
    else:
        # viewExtents only sticks on a camera that is ALREADY orthographic.
        # Setting cameraType and viewExtents in one assignment silently keeps
        # the old extents - which looks like a wildly mis-zoomed render rather
        # than an error - so commit the projection change first, then reread
        # the camera and frame it.
        _apply(vp, build(adsk.core.CameraTypes.OrthographicCameraType, False))
        cam = vp.camera
        cam.isFitView = False
        cam.viewExtents = mm(extents)
        _apply(vp, cam)
        got = vp.camera.viewExtents
        if abs(got - mm(extents)) > 0.01 * mm(extents):
            raise RuntimeError("viewExtents did not take for %s: asked %.3f, "
                               "got %.3f" % (filename, mm(extents), got))

    path = os.path.join(OUTPUT_DIR, filename)
    if not vp.saveAsImageFile(path, IMAGE_W, IMAGE_H):
        raise RuntimeError("saveAsImageFile failed for " + path)
    print("  wrote %s" % filename)
    return path


def render_all(app, design):
    """Six images of the reducing-tee station.

    The tee is 400 mm tall against a 6 mm capsule, so no single framing carries
    both. Two overall views establish the assembly, two show the interiors, and
    two isolate the printed parts.

    Fragments passed to set_visible are matched as substrings, so they have to be
    chosen with care: "capsule" alone would also hide the capsule holder.
    """
    if not os.path.isdir(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    written = []
    x_run = PARAMS["bend_radius"] + PARAMS["leg_cable"]

    # The windjammer is the alternative to the vent carrier and occupies the
    # same space, so it stays hidden in every documentation image.
    set_visible(design, ["windjammer"])

    written.append(shot(app, "tee-assembly.png",
                        eye=(700, 430, 620), target=(77, 200, 0)))

    # Same camera, PVC dropped to a quarter. Everything that matters is inside
    # the pipe; opaque, the image is just two tubes.
    set_opacity(design, "PVC", 0.25)
    written.append(shot(app, "tee-cutaway.png",
                        eye=(700, 430, 620), target=(77, 200, 0)))

    # The Pi bay. Three-quarter rather than square-on: dead ahead renders the
    # board and spine as flat rectangles with no depth cue at all.
    written.append(shot(app, "tee-pi-bay.png",
                        eye=(x_run + 270, 345, 265), target=(x_run, 250, 0),
                        extents=120.0))
    set_opacity(design, "PVC", 1.0)

    # Mic internals. Hiding the tee and the retainer clears the sight line; the
    # holder stays because it is what traps the capsule and carrier together.
    set_visible(design, ["windjammer", "PVC", "retainer"])
    written.append(shot(app, "tee-mic-detail.png",
                        eye=(60, 22, 70), target=(0, 36, 0), extents=22.0))

    # Printed parts on their own - what you actually send to the slicer.
    set_visible(design, ["PVC", "lav capsule", "windjammer", "cable",
                         "vent carrier", "retainer", "capsule holder"])
    written.append(shot(app, "tee-printed-sled.png",
                        eye=(x_run + 240, 350, 260), target=(x_run, 250, 0)))

    set_visible(design, ["PVC", "lav capsule", "windjammer", "cable", "Pi "])
    written.append(shot(app, "tee-printed-mic.png",
                        eye=(80, 66, 88), target=(0, 14, 0), extents=86.0))

    set_visible(design, ["windjammer"])
    return written
