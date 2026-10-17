# Build a highly detailed Blender model of this car

Build a highly detailed 3D model of the car in the attached reference images, as close to the real car as you can make it.

You are driving a running Blender 5.2 instance through the `blender` MCP server. Start with an empty scene (`bpy.ops.wm.read_homefile(use_empty=True)`). Work on your own until you are done; nobody will answer questions during the run.

The reference images are attached and are also in `{REPO}/art/reference/`. The four `*-4k.png` files are sharp frames from the official reveal livestream; `09-side-4k.png` is an eye-level side view.

Save the result as `{OUT}/Roadster.blend`, with any textures next to it, and renders of your model in `{OUT}/renders/`. Don't write anywhere else.

If you need to run Blender in the background, start it from the running Blender with `subprocess`; a `blender -b` started from your own shell crashes.
