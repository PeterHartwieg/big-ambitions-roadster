# Photo review and evidence

Model/render is left in Blender coordinates: front −Y, driver's side +X. Comparison rows are front, elevated rear, rear three-quarter, side; model is on the left. Photos remain private reference and are not loaded into the final asset.

## Round 1 — blockout

Original evidence: `renders/history/compare-1-original.png` and `renders/01-blockout-*.png` from the first build (the current named blockout images may be refreshed by the regeneration test).

- Front: hood/fender surfaces overlapped; stacked patches produced broken highlights. Fender peaks sat too high and read as separate horns. Lens shapes were too vertical and the canopy appeared too short. Intake and nose lacked sufficient edge rounding. Corrected the surface boundaries, reduced the peaks, refined the light triangles and revisited the camera projection.
- Rear: tail fascia was too plain, rear glass perimeter was irregular, wing highlight was too pale. Fan bays were placeholders. Added a sculpted blank plate recess, reverse lights, inset bar, bronze wing finish and four turbine assemblies.
- Rear three-quarter: an early white sail panel cut into the side window. The flank had waviness and visible layer intersections. Replaced the sail boundary with a diagonal window termination; removed overlapping upper surfaces.
- Side: front fender hump was exaggerated, sill line wavered, body/window border had a vertical interruption, door gaps were weak. Reduced the hump, made the sill's rise straight, extended the side glass and made recessed door channels.

## Round 2 — detail

Original evidence: `renders/history/compare-2-original.png`; additional intermediate checks in `compare-3.png` and `compare-4.png`.

- Front: the hood/windscreen relationship was still too high. Small unlit trim pieces appeared above the hood because the trim path had not followed the revised surface. Matched the trim to the hood, then lowered the central nose/hood and windscreen foot while retaining the mandatory wheel-clearance surface. Added an open intake with a recessed grille and separate lamp faces.
- Rear: the fan back panels occluded the turbine blades. Moved those panels behind the fans. Reduced the fan blade brightness and deepened the framing. Added the four bronze diffuser nozzles, rear downward nozzles and vertical strakes.
- Rear three-quarter: planar side glass created large facet reflections. Replaced it with a sampled curved surface; increased the canopy sampling and used monotone surface interpolation to remove station flat spots. Rebuilt the rear buttresses and their connection to the window tip.
- Side: arch-to-tyre gaps were too large. Reduced the visible outboard arch radius to 0.395 m, while keeping all four specified inboard wheel-travel boxes completely empty. Broadened the swept twin spokes and added machined facets, brake discs, calipers and drilling detail.
- Shading/colour: the original disk softboxes made broad white patches on the warm dark glass. The final rig uses narrow studio strips. Pearl paint, dark titanium, rubber and satin bronze each use their actual texture channels.

## Final review

Evidence: `renders/compare-final.png`, `renders/review-sheet.png` and the individual `final-*.png` views. The review sheet is front three-quarter / rear three-quarter, side / top, chase / straight rear. The top view is rotated to fit the car across the panel.

- The central wedge, long continuous canopy, raised fenders, rising black sill, full-width lamps, recessed grille, blank tail recess, closed wing, ten throats, four fan bays and paired five-spoke pattern are present. The final pass replaced the lower door trim with a continuous inset channel, closing the remaining door-gap limitation.
- All visible mesh transforms, names, origins, texture sizes, UV layouts, wheel clearances and budgets are measured by the supplied scorer. Both the Blender scene and re-imported FBX must pass.
- Export review caught a tail-lens overhang and a tiny LED divider whose signed volume was unstable at FBX float precision. The tail lenses were inset to y = 2.23; the smallest divider was removed and the remaining dividers given a robust cross section. No scorer or spec changes.

Remaining likeness limits: the front corner/fender transitions are still squarer and the inner fender channels deeper than the reveal imagery. The precise rear canopy curvature, lamp optics, spoke machining and fan mounting details are interpretations of the available photographs. The fixed height, wheel positions and wheel-travel envelope take priority over changing those dimensions to chase a particular photograph's perspective. The wing remains closed as requested, whereas the third comparison photo has it raised. Paint/glass highlights also differ from the reveal's darker lighting.

The tangent normal map is flat, as explicitly permitted. All visible major details are geometry. The doors are closed static body geometry. Front/rear channels and the continuous lower seam are physically recessed (about 4 mm across, 5 mm deep); they are not separately rigged.

**Evidence status:** studio appearance and file/geometry checks checked; Unity import appearance, steering under the game's suspension and in-game behaviour pending. This task does not install the model into the game.
