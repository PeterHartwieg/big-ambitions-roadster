# Task: solve the real car's proportions from the reveal photos

You are driving a running Blender 5.2 instance through the `blender` MCP server. Work on your own until the task is finished; nobody will answer questions during the run. This task measures; it does not model the car.

## Why

Seven passes have modelled a two-seat electric hypercar for a Big Ambitions mod against eight reveal photos, inside a fixed size spec: 4.58 m long, 2.00 m wide, 1.15 m high, wheelbase 2.95 m, 0.72 m tyres, hubs at (±0.84, ±1.475, 0.36). Those numbers were a guess from two photos. Pass 7 (`{REPO}/art/roadster-v7/report.txt`, `projection-diagnostics.json`) found that the side camera only fits that spec at about 15° elevation, which pushes the far front fender and tyre into the side outline. A camera that fits the photo's front lines up the near crown but moves the canopy away from it. The likely cause is wrong proportions in the spec, not wrong geometry. Find the real ones.

## Reference

`{REPO}/art/reference/` (also attached): `01-front.jpg` (straight front, studio), `02-rear.jpg` (straight rear, studio, slightly above), `03-rear-wing.jpg` and `04-doors.jpg` (rear three-quarter on stage), `05-hero.jpg` (near side view, driving), `06`, `07`, `08` (flight shots and an underside composite). Pass 3 to 7 cameras and overlays are in `{REPO}/art/roadster-v4/` to `roadster-v7/` (`.blend` files and `renders/`).

## What to do

1. Treat these as unknowns: overall length, width across the body, roof height, wheelbase, front and rear overhang, front and rear track, tyre diameter, wheel width, hub height, ground clearance, nose-tip height, tail-top height, windscreen-base position, and the height of the body top over the front wheel. Fix the scale with one assumption: a tyre diameter of 0.72 m. Also report every result as a ratio to the wheelbase, so the scale can change later.
2. Mark landmarks in the photos by pixel: wheel ellipses (both visible wheels, rim and tyre edges), tyre ground contacts, nose tip, tail, roof top, windscreen base and top, door seam, and the light bars. Do it in `05` first, then `01`, `02`, `03`, `04`.
3. Solve each photo's camera (position, rotation, focal length) together with the unknowns, so that one set of proportions explains all five photos at once. Fitting each photo's camera on its own was the earlier passes' mistake. A simple parametric car in Blender (boxes and cylinders at the unknown sizes) and a least-squares fit in Python are enough. numpy and mathutils are available inside Blender.
4. Report how well it fits: the pixel residual for each landmark and each photo, and how sure each number is (for example, the range that keeps the residuals within 2 px more).
5. Sanity-check against real cars: two-seat hypercars are typically 4.2 to 4.7 m long, 1.95 to 2.10 m wide and 1.10 to 1.25 m high, on 0.68 to 0.76 m tyres. Say if the result falls outside those ranges and why.

## Output folder

`{OUT}`

Write `proportions.json` (each unknown in metres and as a ratio to the wheelbase, with its uncertainty), `cameras.json` (the solved camera for each photo), `landmarks.json` (each pixel landmark per photo), and `renders/fit-<photo>.png` (the parametric car's outline over each photo). Save the scripts you used. Don't write anywhere else.

## Finish

End with a short report: the solved proportions in a table next to the current spec, the residuals, how confident you are, and what the spec should change to.
