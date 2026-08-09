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

## Mounting the capsule

A microphone needs an opening, so a sealed waterproof enclosure is the wrong tool — it
muffles high frequencies and adds box resonance, exactly where song lives. What you want
is a **hood**: open at the bottom, sheds rain, passes sound.

- **A 1½" PVC 90° elbow** is the standard cheap answer. Capsule recessed inside the
  horizontal leg, opening facing down.
- **Never point the capsule up.** Down or horizontal only.
- **Under an eave or soffit**, 6–8 ft up, set back from the drip line so icicles don't
  form on it and so roof-shed snow doesn't bury it.
- **Cover the mouth** with something acoustically transparent and hydrophobic — nylon
  stocking works, expanded-PTFE membrane is better. Keeps out rain, spiders, and
  box elder bugs.
- **Never seal the capsule in a bag or airtight box.** It traps condensation and
  muffles the sound. Breathable and water-shedding beats sealed, every time.
- **Drip loop** in the cable below the entry point. Slope the wall pass-through downward
  toward the outside and seal it at the outer face.

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

Not recommended, but if there's no way to get a cable indoors:

- IP65/66 polycarbonate enclosure **with a pressure-equalization vent**. Without the
  vent, a "waterproof" box fills with condensation from the inside.
- Sun shield or radiation shield. A sealed enclosure in July sun runs 15–20 °C above
  ambient and a Pi 4 will throttle or die. **Summer solar gain kills these, not winter.**
- Cold-starting a Pi below -20 °C is out of spec, and the SD card is the usual first
  casualty. Run it on PoE and never let it power-cycle in January.
- GFCI outlet, outdoor-rated cable, and a grounded surge arrestor on any ethernet run
  that leaves the building. A long outdoor cable is a lightning antenna.
