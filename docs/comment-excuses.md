# Comment excuses

Code comments are banned (see `AGENTS.md`). The comments below stay for now because each one records a
workaround, gap or compromise; each is a candidate issue. `tools/comment-ban.py` allows exactly these spans
and fails on any other comment that is not a tool directive. When a fix removes a comment, remove its line here;
when code above one moves, update its line numbers.

- `tools/Install-Windows.ps1:1-5`: workaround
- `tools/build-mod.sh:35`: workaround
- `tools/build-mod.sh:55-57`: workaround
- `unity/BuildEditor/AppearanceChecks.cs:74-76`: workaround
- `unity/BuildEditor/BatchBuild.cs:16-20`: workaround
- `unity/BuildEditor/BatchBuild.cs:97`: imperfect-choice
- `unity/BuildEditor/ModAssets.cs:23-24`: temporary
- `unity/BuildEditor/ModAssets.cs:25`: temporary
- `unity/BuildEditor/ModAssets.cs:131`: workaround
- `unity/BuildEditor/ModAssets.cs:149-153`: workaround
- `unity/BuildEditor/RoadsterMaterials.cs:67-69`: imperfect-choice
- `unity/BuildEditor/RoadsterMaterials.cs:94-95`: workaround
- `unity/BuildEditor/RoadsterModel.cs:86`: workaround
- `unity/Roadster/Scripts/Patches.cs:43-45`: temporary
- `unity/Roadster/Scripts/RoadsterDrive.cs:20-23`: workaround
- `unity/Roadster/Scripts/RoadsterDrive.cs:27`: known-gap
- `unity/Roadster/Scripts/RoadsterDrive.cs:29-30`: workaround
- `unity/Roadster/Scripts/RoadsterDrive.cs:37-42`: skipped
- `unity/Roadster/Scripts/RoadsterDrive.cs:51-52`: imperfect-choice
