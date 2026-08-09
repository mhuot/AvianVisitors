# Where the exported PNGs land. Point this at your clone.
OUTPUT_DIR = os.path.expanduser("~/AvianVisitors/docs/img")
IMAGE_W, IMAGE_H = 2000, 1500

# Component name fragment -> appearance name, checked against the installed
# Fusion Appearance Library. There is no "PVC" appearance, so DWV white is
# stood in for by glossy white plastic.
PALETTE = [
    ("PVC", "Plastic - Glossy (White)"),
    ("capsule holder", "Plastic - Matte (Gray)"),
    ("vent carrier", "Plastic - Matte (Gray)"),
    ("retainer", "Plastic - Matte (Gray)"),
    ("lav capsule", "Aluminum - Polished"),
    ("windjammer", "Fabric (Grey)"),
    ("cable", "Rubber - Soft"),
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
    if not os.path.isdir(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    written = []

    # The windjammer is the alternative to the vent carrier and shares its
    # space, so it stays hidden in every documentation image.
    set_visible(design, ["windjammer"])
    written.append(shot(app, "mic-housing-assembly.png",
                        eye=(300, 120, 300), target=(45, 70, 0)))

    # Side elevation and the view up the mouth both need the PVC translucent.
    # Without it the elbow is an opaque tube and the interior renders as a black
    # hole: the recess, the holder and the vent port are all inside it.
    set_opacity(design, "PVC", 0.30)
    written.append(shot(app, "mic-housing-side.png",
                        eye=(20, 70, 420), target=(20, 62, 0)))

    # Straight up the mouth axis. This one needs a hand-framed orthographic
    # camera - a fit would recentre on the whole elbow and look up the bend
    # instead - so up is +Z here, the view direction being +Y.
    written.append(shot(app, "mic-housing-mouth.png",
                        eye=(0, -160, 0), target=(0, 30, 0), up=(0, 0, 1),
                        extents=60.0))
    set_opacity(design, "PVC", 1.0)

    # Detail on the capsule and vent carrier. Hiding the elbow and the retainer
    # clears the sight line; the holder stays because it is what traps the two
    # of them together.
    set_visible(design, ["windjammer", "PVC", "retainer"])
    written.append(shot(app, "mic-housing-detail.png",
                        eye=(60, 22, 70), target=(0, 36, 0), extents=22.0))
    set_visible(design, ["windjammer"])
    return written
