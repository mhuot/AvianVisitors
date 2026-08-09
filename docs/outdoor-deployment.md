# Outdoor deployment (cold climates)

Notes for running the mic outside year-round somewhere with real weather — written
for Minnesota (-30 °F winters, 95 °F/75 °F-dewpoint summers, ~50" snow, freeze/thaw
cycles), but the reasoning holds anywhere north of the Mason-Dixon.

**There are two builds here, and the cable length decides which one you get.**

The USB lavalier in the BOM puts the sound card in the USB plug and the capsule on about
6 ft of thin cable, and that 6 ft is the whole decision:

- **Indoor Pi.** If there's a spot inside within reach — a shelf at the window, the sash
  above it — put the Pi there and pass only the capsule through the wall. The one thing
  outdoors is a sealed electret, which handles -30 °F fine with a slight sensitivity drop.
  Everything that actually fails outdoors (SD card, WiFi radio, power supply, e-ink panel)
  stays in conditioned space. This is the easier build and you should take it if you can.
- **Outdoor station.** If there isn't — a pole in the yard, a detached garage, a far
  corner — the Pi has to live at the mic, and the whole thing goes in a
  [reducing tee](#the-outdoor-station). That brings PoE, a grounded surge arrestor and
  sun shading with it. Those stop being optional extras and become part of the design.

Don't try to split the difference by extending the mic instead of moving the Pi: active
USB extensions past ~5 m on a line-level mic pick up noise.

**The mic housing is identical either way** — the elbow, the membrane, the holder, the
vent carrier. Only the body it hangs off changes. Everything up to
[the e-ink frame](#the-e-ink-frame-stays-inside) applies to both builds; the tee section
covers what the outdoor station adds.

---

## Parts

Common to both builds. The outdoor station adds [a few more](#the-outdoor-station).

| Qty | Part | Approx | Notes |
|-----|------|--------|-------|
| 1 | 1½" PVC DWV 90° street elbow | ~$3 | Any hardware store. The mic housing. |
| 1 | Furry windjammer for lav capsule | ~$20 | Røde MiniFur-Lav or Bubblebee Windbubble. Matters more than the housing. |
| 4 | GORE GAW112 acoustic vent | $10/set | [GroupGets][groupgets], sold as AudioMoth spares. |
| 1 | 12" x 12" sheet, 12-mesh T-304 stainless | ~$12 | Covers all three screened points. **Not** galvanised hardware cloth. |
| 1 | ePTFE membrane | ~$10 | Mouth closure, outboard of the mesh. |
| 1 | Conduit strap or hose clamp | ~$2 | Soffit mount. |
| — | Exterior latex primer + light paint | ~$0 | PVC chalks under UV; light colour cuts solar gain. |

Optional printed parts in ASA — see [printed parts](#printed-parts).

## Mounting the capsule

A microphone needs an opening, so a sealed waterproof enclosure is the wrong tool — it
muffles high frequencies and adds box resonance, exactly where song lives. What you want
is a **hood**: open at the bottom, sheds rain, passes sound.

![Section through the mic housing: a 1½" PVC DWV 90° elbow with the mouth facing down,
a lavalier capsule recessed about 32 mm up inside behind a GORE acoustic vent on a
printed carrier, a printed spoked holder above it, an ePTFE membrane on a mesh backing
clamped by a retainer at the mouth, and a printed drip lip outside.](img/mic-housing-section.svg)

The same assembly as modelled, with the pipe hidden — capsule, holder and vent carrier
in the order they stack up the mouth:

![Fusion render of the mic housing internals: an aluminium-coloured lavalier capsule
seated in a yellow printed vent carrier, with the yellow spoked capsule holder around
it.](img/tee-mic-detail.png)

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
- **Never cap the mouth with a rigid disc**, whatever ports you drill in it. A membrane
  is fine; a cap is not. See [why a rigid cap fails](#why-a-rigid-cap-fails).
- **Drip loop** in the cable below the entry point. Slope the wall pass-through downward
  toward the outside and seal it at the outer face.

### Waterproofing the capsule itself

Protect the capsule with an acoustic vent — an ePTFE membrane that passes sound while
blocking liquid water. This one goes **directly on the capsule port**. It is a different
part from the mouth membrane below, and the two are complementary: this is the barrier
with a published specification, sitting closest to the thing that matters.

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

### Sourcing the stainless mesh

A terminology trap first: **"12 mesh" means 12 openings per inch**, while "12×12" in a
listing may instead mean a 12-inch square sheet. Listings often say both. You want a
12-inch sheet of roughly 12-mesh material.

One **12" × 12" sheet of 12-mesh T-304**, ~0.023" wire, ~1.5 mm openings, covers every
place mesh appears in this build and leaves spares:

| Where | Piece | Why this mesh |
|-------|-------|---------------|
| Mic mouth, behind the membrane | ⌀41 mm disc | Fine enough to stop the membrane bulging, ~60% open so it costs almost nothing acoustically |
| Under the mushroom cap | ⌀89 mm disc | Stops wasps and mice at the vent |
| Inside the drain cap | ⌀89 mm disc | Same, and coarse enough to keep draining |

Sources, in order of fuss: [Amazon][meshamzn] or [eBay][meshebay] for a ~$10-15 sheet;
[McMaster-Carr][meshmcm] if you want the alloy documented; [TWP Inc][meshtwp], who will
laser-cut it to size; [OnlineMetals][meshom] for custom cuts.

**Do not use hardware cloth from a big-box store.** It is galvanised, not stainless. It is
the obvious thing to grab, and it will rust and streak down your white PVC within a couple
of winters - and rust-jacking eventually tears the membrane it is supposed to support. Most
big-box "insect screen" is aluminium or fibreglass. If the label does not say 304 or 316,
it is neither.

304 is fine under an eave. Choose 316 only near the coast or a heavily salted road.

Three practical notes:

- Cut with tin snips and **deburr**. The cut ends are sharp enough to perforate the ePTFE
  membrane they sit against.
- **Never clamp stainless against aluminium** in a wet joint - that is a galvanic cell and
  the aluminium loses. Stainless hose clamps are correct.
- At the mouth the mesh goes **inboard** of the membrane: membrane outside shedding water,
  mesh behind taking the load.

The mesh is **not in the Fusion model** - at this scale it would render as a solid disc and
mislead more than it informs, so it appears in the line drawings only. If you are working
from the renders when you assemble, that is the piece that is missing.

[meshamzn]: https://www.amazon.com/Quality-Stainless-Steel-Mesh-Screen/dp/B07RC5YQZ8
[meshebay]: https://www.ebay.com/itm/293071536728
[meshmcm]: https://www.mcmaster.com/products/304-stainless-steel-wire-cloth/
[meshtwp]: https://www.twpinc.com/12-mesh-t304-stainless-023-wire-dia
[meshom]: https://www.onlinemetals.com/en/buy/stainless-steel/12x12-mesh-0-023-wire-diameter-stainless-steel-woven-wire-mesh-304/pid/mp-00002031

### Why a rigid cap fails

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

The small die-cut vents belong on the capsule, where the volume behind them is a fraction
of a cubic millimetre and resonance stays ultrasonic. That is how phones do it. Note the
distinction from the mouth membrane: what makes a resonator is the *area ratio* between
cavity and neck, so a barrier spanning the whole aperture is harmless where the same
material behind a 2.4 mm port in a rigid plate would not be.

### Printed parts

Printing is worth it, for holders rather than covers:

- **Vent carrier** — a boss with a single 2-3 mm through-hole. The vent seals to its flat
  outer face, the capsule presses against the back. This gives a domed lav grille the
  flat sealing surface it otherwise lacks, with negligible trapped volume.
- **Capsule holder** that press-fits the 1½" ID and centres the mic. Build it as spokes
  or webbing, ≥80% open — never a solid disc.
- **Retainer ring** that press-fits the bore and clamps the membrane and its mesh
  backing, trapping the membrane's turned-up edge against the bore wall.
- **Drip lip** extending the mouth 10-15 mm against wind-driven rain.

**Heat-set inserts for the Pi.** The sled's standoffs are bored for
[CNC Kitchen M3 x 3 short inserts][inserts] rather than tapped or self-tapped, so the
board can come off as many times as servicing needs without chewing out the plastic.
Their datasheet gives 4.6 mm body, 3.0 mm long, 4.0 mm recommended hole, 4.0 mm minimum
blind depth, 1.6 mm minimum wall. From that:

- **4.0 mm hole.** Model it at 4.0 even though it will measure nearer 3.8 off the bed -
  the nozzle over-extrudes on tight curves, and that shortfall is exactly what the
  insert grips.
- **9 mm boss**, not the 6 mm a bare standoff would be. The 1.6 mm wall minimum puts the
  floor at 7.2 mm measured from the hole, or 7.8 mm measured from the 4.6 mm body; 6 mm
  leaves about 0.7 mm and splits as the insert goes in.
- **4 mm blind bore**, the datasheet minimum, into 7 mm of standoff-plus-spine - a 3 mm
  floor underneath. Nothing breaks through the back of the plate.

The build checks the wall rule and the floor rather than trusting them, so narrowing the
boss or shortening the standoff fails loudly instead of producing a part that splits on
assembly. Swapping insert size is one parameter (`insert_len`); everything else follows.

[inserts]: https://cnckitchen.store/products/heat-set-insert-m3-x-3-short-version-100-pieces

![Fusion render of the printed Pi sled from its mounting face with the board removed:
four raised bosses each bored 4 mm for a heat-set insert, set among the six lightening
holes in the spine.](img/tee-sled-inserts.png)

That is the face the inserts go into — every other view has the board covering them.

Print in **ASA**. PLA's glass transition is ~60 °C and a dark part in July sun will pass
it, quite apart from having no UV life; PETG is an acceptable second with some yellowing.
Run 4+ perimeters — layer lines are capillary paths for water.

**Decouple the capsule.** A rigid printed holder conducts structure-borne noise straight
from the tube into the mic, so rain strikes and wind buffeting arrive as thumps. Seat the
capsule in a short length of silicone tubing inside the holder.

[groupgets]: https://groupgets.com/products/set-of-four-splashproof-acoustic-vents-for-the-audiomoth-usb-microphone-case
[gaw334]: https://groupgets-files.s3.amazonaws.com/AudioMoth/GORE-Acoustic-Vent-GAW334-Datasheet-en.pdf

The four printed parts, isolated:

![Fusion render of the mic's printed parts in yellow: the spoked capsule holder above,
the retainer ring and drip lip below.](img/tee-printed-mic.png)

![Fusion render of the printed Pi sled: two rings joined by a spine plate with six
lightening holes, the green Pi board mounted on standoffs.](img/tee-printed-sled.png)

Printed parts render **yellow** in these images. The line drawings use green for
"printed", but green beside a green PCB reads as the same material, so the renders
diverge deliberately.

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

## The outdoor station

When the Pi has to live at the mic, put it in its **own** body, not in the mic's.

![Section through a 3x3x1½ inch PVC reducing tee. The vertical 3 inch run holds a Pi on
a printed sled, vented at the top for warm air out and at the bottom for cool air in and
condensate drainage. The 1½ inch branch turns down through a 90 degree elbow carrying the
mic exactly as before, so the Pi never shares the mic
bore.](img/mic-housing-tee-variant.svg)

As modelled — 300 mm tall overall, 3.5" across:

![Fusion render of the assembled reducing tee: a white PVC 3 inch vertical run with a
mushroom vent cap on top standing off on three posts, a drilled cap at the bottom with the
PoE cable looping away below it, and the 1.5 inch branch turning down with the printed
drip lip at its mouth.](img/tee-assembly.png)

![The same view with the PVC at 25% opacity, showing the yellow printed Pi sled and its
green board in the vertical run, the cable dropping to the branch, the mic parts at the
mouth, and the inlet plenum inside the bottom cap.](img/tee-cutaway.png)

![Close view of the Pi bay: the printed sled's two ribs press-fitting the bore, the
lightened spine, and the Pi board standing off it.](img/tee-pi-bay.png)

A **3×3×1½" reducing tee** gives one assembly with two acoustic domains. The Pi gets its
own body, and the mic bore stays clean. Sharing a single tube between the two is the
tempting version and the wrong one: the Pi becomes a large reflector directly above the
capsule, and it is rigidly coupled to the same plastic the capsule is mounted in.

Both caps are purchased, not printed:

**This is two fittings, not one.** Nobody sells a tee whose branch curves down — what you
want is a reducing *sanitary* tee plus a street elbow glued into its branch. Searching for
a "reducing tee" in DWV is why it doesn't turn up; the word that matters is **sanitary**.

| Qty | Part | Approx | Notes |
|-----|------|--------|-------|
| 1 | 3×3×1½" PVC DWV reducing **sanitary** tee | ~$12 | [Charlotte PVC 00401][santee] — also at [Lowe's][santeelowes]. |
| 1 | 1½" PVC DWV **street** 90° elbow | ~$3 | Street, not regular: its spigot end glues straight into the tee's branch hub, with no pipe nipple between. |
| 1 | 3" PVC DWV pipe, ~600 mm | ~$10 | Cut into the run above and below the tee. |
| 1 | Oatey mushroom vent cap, 3" | ~$10 | Top. Sheds rain, passes air. Check it ships with a screen. |
| 1 | 3" PVC cap, drilled + screened | ~$5 | Bottom. **Never leave it solid** — see below. |
| 4 | CNC Kitchen M3 x 3 short heat-set inserts | ~$1 | Pi mounting in the printed sled. |
| — | Stainless hose clamps | ~$3 | Hold the screens at both cap ends. |

If the reducing sanitary tee is backordered — it sometimes is — buy a plain **3×3×3 DWV
sanitary tee** and a **3" × 1½" reducer bushing** ([Charlotte PVC 00107][bushing]) instead.
Both are stocked everywhere, and the assembled dimensions come out the same.

In the renders the tee and elbow are drawn as one continuous body, because the model sweeps
the branch in a single pass. The **step partway along the branch is the joint**: everything
outboard of it is the street elbow, everything inboard is the tee.

[santee]: https://www.homedepot.com/p/Charlotte-Pipe-3-in-x-3-in-x-1-1-2-in-DWV-PVC-Sanitary-Tee-Reducing-PVC004011200HD/203396203
[santeelowes]: https://www.lowes.com/pd/Charlotte-Pipe-3-in-x-3-in-x-1-1-2-in-dia-PVC-Schedule-40-Hub-Sanitary-Tee-Fitting/3132825
[bushing]: https://www.lowes.com/pd/Charlotte-Pipe-3-in-x-1-1-2-in-dia-PVC-Schedule-40-Spigot-Flush-Bushing-Fitting/3357818

Don't substitute an NDS drain grate at the bottom. Those fit **sewer-and-drain** pipe at
about 4.215" OD; Schedule 40 / DWV is 4.500", so it will not fit.

### The bottom cap must not be solid

Drainage, not airflow, is the reason. The tube is vented at the top, so humid air gets in;
at night the PVC drops below dew point and that moisture condenses and runs down. A solid
cap pools it at the lowest point, directly under the Pi, with nowhere to go.

Airflow matters less than it first appears. The tube's lateral area is about 0.13 m², and
combined natural convection plus radiation is roughly 9 W/m²K, so 5 W of Pi dissipation
gives only `5 / (0.13 × 9) ≈ 4 K` of rise — even with no ventilation at all. Mid-summer sun
on **white** PVC adds perhaps another 4 W, for ~8 K total. Painting it dark raises
absorptivity from ~0.3 to ~0.9 and makes solar the dominant term. Leave it white; that one
choice matters more than any amount of venting. (Order-of-magnitude estimates, but not
close enough to the limit for the error bars to matter.)

### No fan

It is the worst thing you could add to an acoustic station. A small fan puts broadband
noise across 200 Hz – 8 kHz — the whole song band — plus tonal blade-pass components,
which are exactly the artifact that generates false positives in a CNN reading
spectrograms. Worse, bolted to the same assembly it is *rigidly coupled* to the mic
housing, so the two-domain split does nothing to protect you: that split stops the Pi
reflecting sound, not vibrating the capsule. And it runs continuously, so it contaminates
every recording.

You don't need one. If a build ever does run hot, the levers in order are: shade it or
keep it white; use a **Pi Zero 2 W (~1.5 W) rather than a Pi 4 (~5 W)**, which cuts the
load by two-thirds; then undervolt or cap the clock.

Whichever body you choose:

- IP65/66 polycarbonate enclosure **with a pressure-equalization vent**. Without the
  vent, a "waterproof" box fills with condensation from the inside.
- Sun shield or radiation shield. A sealed enclosure in July sun runs 15–20 °C above
  ambient and a Pi 4 will throttle or die. **Summer solar gain kills these, not winter.**
- Cold-starting a Pi below -20 °C is out of spec, and the SD card is the usual first
  casualty. Run it on PoE and never let it power-cycle in January.
- GFCI outlet, outdoor-rated cable, and a grounded surge arrestor on any ethernet run
  that leaves the building. A long outdoor cable is a lightning antenna.
