# Outdoor deployment (cold climates)

Notes for running the mic outside year-round somewhere with real weather — written
for Minnesota (-30 °F winters, 95 °F/75 °F-dewpoint summers, ~50" snow, freeze/thaw
cycles), but the reasoning holds anywhere north of the Mason-Dixon.

**The short version: only the mic capsule goes outside.** The Pi, the frame, and the
power supply stay indoors.

---

## Why the split

The USB lavalier in the BOM puts the sound card in the USB plug and the capsule on
~6 ft of thin cable. Take advantage of that: the Pi sits on a shelf at the window, the
capsule goes through the wall or sash, and the only thing exposed to weather is a sealed
electret capsule — which handles -30 °F fine, with a slight sensitivity drop.

Everything that actually fails outdoors (SD card, WiFi radio, power supply, e-ink panel)
stays in the conditioned space.

If 6 ft isn't enough, move the Pi rather than extending the mic. Active USB extensions
past ~5 m on a line-level mic pick up noise.

---

## Parts

| Qty | Part | Approx | Notes |
|-----|------|--------|-------|
| 1 | 1½" PVC DWV 90° street elbow | ~$3 | Any hardware store. The mic housing. |
| 1 | Furry windjammer for lav capsule | ~$20 | Røde MiniFur-Lav or Bubblebee Windbubble. Matters more than the housing. |
| 4 | GORE GAW112 acoustic vent | $10/set | [GroupGets][groupgets], sold as AudioMoth spares. |
| 1 | Stainless mesh + ePTFE membrane | ~$10 | Mouth closure; mesh backs the membrane. |
| 1 | Conduit strap or hose clamp | ~$2 | Soffit mount. |
| — | Exterior latex primer + light paint | ~$0 | PVC chalks under UV; light colour cuts solar gain. |

Optional printed parts in ASA — see [printed parts](#printed-parts).

## Mounting the capsule

A microphone needs an opening, so a sealed waterproof enclosure is the wrong tool — it
muffles high frequencies and adds box resonance, exactly where song lives. What you want
is a **hood**: open at the bottom, sheds rain, passes sound.

![Section through the mic housing: a 1½" PVC DWV 90° elbow with the mouth facing down,
a lavalier capsule recessed about 32 mm up inside behind a GORE acoustic vent on a
printed carrier, a printed spoked holder above it, bug mesh and retainer at the mouth,
and a printed drip lip outside.](img/mic-housing-section.svg)

- **A 1½" PVC 90° elbow** is the standard cheap answer. Capsule recessed inside the
  horizontal leg, opening facing down.
- **Never point the capsule up.** Down or horizontal only.
- **Under an eave or soffit**, 6–8 ft up, set back from the drip line so icicles don't
  form on it and so roof-shed snow doesn't bury it.
- **Close the mouth** with an ePTFE membrane outboard, backed by stainless mesh and
  clamped by the retainer ring. One part then does two jobs — nothing gets past a
  sub-micron pore size, and the whole bore stays dry, which protects the holder, the
  cable and the printed parts as well as the capsule. The mesh is what stops the
  membrane drumming under wind and rain load.
- **Never seal the capsule in a bag or airtight box.** It traps condensation and
  muffles the sound. Breathable and water-shedding beats sealed, every time.
- **Never cap the mouth.** See [why the tube stays open](#why-the-tube-stays-open).
- **Drip loop** in the cable below the entry point. Slope the wall pass-through downward
  toward the outside and seal it at the outer face.

### Waterproofing the capsule itself

Protect the capsule with an acoustic vent — an ePTFE membrane that passes sound while
blocking liquid water. It goes **directly on the capsule port**, never across the tube
mouth.

Cheapest retail source: [GroupGets sells four GORE GAW112 vents for $10][groupgets],
listed as spares for the AudioMoth USB Microphone Case. AudioMoth is a bioacoustic
recorder, so these are already proven for outdoor wildlife audio. Adhesive-backed, no
minimum order.

That part is Gore's dust-and-splash grade. If you want the immersion-rated ePTFE, ask
Gore or their distributor Sealing Devices for **GAW334** samples — IP67/IP68, 0.31 mm
thick, oleophobic:

| Inner Ø | Outer Ø | Part number   |
|---------|---------|---------------|
| 1.6 mm  | 3.2 mm  | GAW3341.63.2  |
| 2.0 mm  | 3.6 mm  | GAW3342.03.6  |
| 2.4 mm  | 5.0 mm  | GAW3342.45.0  |
| 3.0 mm  | 6.0 mm  | GAW3343.06.0  |

Under an eave, splash grade is plenty. IP68 is for phones dropped in toilets.

Two things worth knowing from the [GAW334 datasheet][gaw334]:

- Transmission loss is **under 2 dB at 1 kHz**, and the loss is concentrated at the low
  end — about 3 dB down at 100 Hz, converging to near zero by 10 kHz. The membrane is a
  gentle high-pass, so it attenuates wind rumble while passing song untouched. It works
  *with* the windjammer.
- The acrylic adhesive is rated **-40 to 85 °C**. A -35 °F night is -37 °C, so you are
  inside spec but not by much. Apply it on a warm day, press hard, and add a mechanical
  backup (a wrap of self-amalgamating tape) rather than trusting adhesive alone for
  five winters.

Note these vents are **tiny** — 1.6-3.0 mm inner diameter. They cover a microphone port,
not an opening. If your lav has a domed metal grille there is nowhere for the adhesive to
seal; see the printed vent carrier below.

### Membrane at the mouth as well

Closing the mouth with a membrane is not the same mistake as capping it. A rigid cap vents
~1300 mm² of bore through a few mm² of port, and that area ratio is what builds the
resonator described below. A membrane spans the full bore, so there is no neck at all — it
adds distributed flow resistance, which if anything damps the hood's own tube resonance.

![Enlarged section through the mouth: an ePTFE membrane across the full bore on the
outboard face, stainless mesh immediately inboard as backing, both clamped by a printed
retainer ring that press-fits into the bore, with the membrane turned up between retainer
and bore wall.](img/mic-housing-mouth-detail.svg)

Two honest caveats. The acoustic-grade Gore material only exists as small die-cut vents,
so spanning 40 mm means apparel-grade laminate with **no published acoustic data** — its
loss is higher than the quoted 2 dB and weighted toward the high frequencies that matter.
And a membrane can ice over in a glaze event or load up with pollen, which is the failure
mode that actually takes a station offline. Treat it as a service item, replaced each
spring, and keep the capsule vent as the one barrier with a known specification.

### Why the tube stays open

It is tempting to cap the elbow with a printed disc carrying a few acoustic vents. Don't.
That turns the tube into a Helmholtz resonator — an ~80 cm³ cavity venting through
millimetre-scale necks:

```
f = (c/2π)·√(A / (V·L_eff))
  = 54.6 · √(7.07e-6 / (8e-5 · 4.55e-3))  ≈  240 Hz
```

Resonance lands near 240 Hz and the response rolls off ~12 dB/octave above it. Song at
4 kHz is four octaves up — roughly 45-50 dB down. More ports don't rescue it either;
frequency scales with the square root of open area, so clearing the song band would take
about a thousand times more area than these vents can give.

The membrane belongs on the capsule, where the volume behind it is a fraction of a cubic
millimetre and resonance stays ultrasonic. That is how phones do it.

### Printed parts

Printing is worth it, for holders rather than covers:

- **Vent carrier** — a boss with a single 2-3 mm through-hole. The vent seals to its flat
  outer face, the capsule presses against the back. This gives a domed lav grille the
  flat sealing surface it otherwise lacks, with negligible trapped volume.
- **Capsule holder** that press-fits the 1½" ID and centres the mic. Build it as spokes
  or webbing, ≥80% open — never a solid disc.
- **Retainer ring** at the mouth to hold the bug mesh.
- **Drip lip** extending the mouth 10-15 mm against wind-driven rain.

Print in **ASA**. PLA's glass transition is ~60 °C and a dark part in July sun will pass
it, quite apart from having no UV life; PETG is an acceptable second with some yellowing.
Run 4+ perimeters — layer lines are capillary paths for water.

**Decouple the capsule.** A rigid printed holder conducts structure-borne noise straight
from the tube into the mic, so rain strikes and wind buffeting arrive as thumps. Seat the
capsule in a short length of silicone tubing inside the holder.

[groupgets]: https://groupgets.com/products/set-of-four-splashproof-acoustic-vents-for-the-audiomoth-usb-microphone-case
[gaw334]: https://groupgets-files.s3.amazonaws.com/AudioMoth/GORE-Acoustic-Vent-GAW334-Datasheet-en.pdf

### Enclosure materials, if you build one anyway

- ABS goes brittle in deep cold and chalks under UV. Use polycarbonate or ASA.
- Any sealed box needs a Gore-type pressure-equalization vent, or it breathes moist air
  in through every gap as it thermal-cycles and condenses on the inside.
- Skip clear lids. Solar gain in July, no benefit.

### Wind

Wind is the number one signal-quality problem in open country. Rumble is
low-frequency, it swamps the analysis window, and it shows up as a solid smear across
the spectrogram.

Foam alone is not enough. Use foam **plus** a furry "dead cat" windjammer.

---

## Siting

- Prevailing winds are NW in winter, S/SW in summer, so the **east or southeast side of
  the house** is sheltered for both.
- Keep it away from the AC condenser or heat pump. It runs all summer, masks everything,
  and generates false detections.
- Aim away from the road. Tire noise on wet pavement is broadband hiss across the
  whole band.
- Plan on pulling and cleaning the windscreen twice a year.

---

## Settings for an outdoor mic

An outdoor capsule sees far more noise than a window-mounted one. Tighten the filters
in the admin overlay:

- **Latitude / longitude** plus the species-occurrence filter (`sf_thresh`) is the
  single biggest false-positive reducer. It restricts candidates to what eBird says is
  actually present in your area that week — which matters enormously in a climate where
  the species list swings hard between January and May.
- **Confidence** around 0.7, and back **sensitivity** off a notch. Defaults tuned for an
  indoor window mic will hand you a lot of junk outside.

For the illustration pipeline, pass your own region instead of the README's `US-CA`:

```bash
python3 ~/BirdNET-Pi/avian/scripts/pregen.py --labels ~/BirdNET-Pi/model/labels.txt \
  --ebird-region US-MN --force
```

---

## The e-ink frame stays inside

Don't mount the Inky Impression outdoors. Colour e-ink (Spectra 6) is specified for
roughly 0–40 °C operating, with good colour only around 15–35 °C. Refreshing a colour
panel below freezing is slow, renders wrong colours, and risks permanent ghosting —
five months a year of unusable panel, on a $300 part. It's designed to hang on the wall
by the window anyway.

---

## If the Pi really must go outside

The USB lavalier's cable is only about 6 ft, so if there is no indoor spot within that
distance — a pole in the yard, a detached garage, a far corner — the Pi has to live at
the mic. In that case put it in its **own** body, not in the mic's.

![Section through a 4x4x1½ inch PVC reducing tee. The vertical 4 inch run holds a Pi on
a printed sled, vented at the top for warm air out and at the bottom for cool air in and
condensate drainage. The 1½ inch branch turns down through a 90 degree elbow carrying the
mic exactly as before, so the Pi never shares the mic
bore.](img/mic-housing-tee-variant.svg)

A **4×4×1½" reducing tee** gives one assembly with two acoustic domains. The Pi gets a
chimney instead of a dead-end pocket, and the mic bore stays clean. Sharing a single tube
between the two is the tempting version and the wrong one: the Pi becomes a large
reflector directly above the capsule, and the two thermal layouts fight — the mic wants
one opening at the bottom, the Pi wants cool air low and warm air out high.

Whichever body you choose:

- IP65/66 polycarbonate enclosure **with a pressure-equalization vent**. Without the
  vent, a "waterproof" box fills with condensation from the inside.
- Sun shield or radiation shield. A sealed enclosure in July sun runs 15–20 °C above
  ambient and a Pi 4 will throttle or die. **Summer solar gain kills these, not winter.**
- Cold-starting a Pi below -20 °C is out of spec, and the SD card is the usual first
  casualty. Run it on PoE and never let it power-cycle in January.
- GFCI outlet, outdoor-rated cable, and a grounded surge arrestor on any ethernet run
  that leaves the building. A long outdoor cable is a lightning antenna.
