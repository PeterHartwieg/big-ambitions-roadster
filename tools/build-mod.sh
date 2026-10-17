#!/usr/bin/env bash
# Builds the Roadster mod package with the official SDK in Unity batch mode.
# Usage: tools/build-mod.sh [--generate]   (--generate re-creates the generated Unity assets first)
# Output: build/Roadster/ (the folder that goes into the game's ModsLocal).
# Same pipeline as the Food Trucks mod (big-ambitions-food-trucks/tools/build-mod.sh), cut down to one vehicle.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
# A dedicated SDK clone, so other mods in a personal SDK project cannot break this build.
SDK="${BA_SDK:-$REPO/build/sdk}"
SDK_URL="https://github.com/hovgaardgames/bigambitions.git"
SDK_COMMIT="1e03ddd5071b77a32cfd8bba89f0c130ba6c7d73"
GAME_DLLS="${BA_GAME_DLLS:-$REPO/build/game-dlls}"
UNITY="${UNITY:-/Applications/Unity/Hub/Editor/2022.3.62f2/Unity.app/Contents/MacOS/Unity}"
HARMONY_URL="https://api.nuget.org/v3-flatcontainer/lib.harmony/2.4.2/lib.harmony.2.4.2.nupkg"
HARMONY_SHA256="d64592e53090464559fce48612c9ca7c8dc73113841376b7aa3455f46fc5d579"
HARMONY_DLL_SHA256="7b9e756306fa3d7620e02a857c8927a6ab04973f9bd8a77d3866700a6deac55c"
MOD_DIR="$REPO/unity/Roadster"
DEPS="$MOD_DIR/Dependencies"
LOG_DIR="$REPO/build/logs"
mkdir -p "$LOG_DIR" "$DEPS"

[ -x "$UNITY" ] || { echo "Unity 2022.3.62f2 not found at $UNITY" >&2; exit 1; }
[ -f "$GAME_DLLS/BigAmbitions.dll" ] || { echo "Game DLLs not found in $GAME_DLLS; copy them from the game's Managed folder" >&2; exit 1; }
if [ ! -d "$SDK/.git" ]; then
  git clone -q "$SDK_URL" "$SDK"
  git -C "$SDK" checkout -q "$SDK_COMMIT"
fi
[ "$(git -C "$SDK" rev-parse HEAD)" = "$SDK_COMMIT" ] || { echo "$SDK is not at the pinned SDK commit $SDK_COMMIT" >&2; exit 1; }
# The settings files Unity rewrites during a build; put back after every Unity run.
SDK_RESAVED=("Assets/Settings/HDRP Balanced.asset" "Assets/Settings/HDRP High Fidelity.asset" "Assets/Settings/HDRP Performant.asset" ProjectSettings/GraphicsSettings.asset ProjectSettings/QualitySettings.asset)
SDK_INPUTS=(Assets/Editor Assets/Mods/Example-Vehicle "Assets/_BaDependencies/Vehicle Dependencies" Packages ProjectSettings "${SDK_RESAVED[@]}")
if [ -n "$(git -C "$SDK" status --porcelain --untracked-files=no -- "${SDK_INPUTS[@]}")" ]; then
  echo "$SDK has local changes in ${SDK_INPUTS[*]}; refusing to build" >&2; exit 1
fi
rsync -a --checksum "$GAME_DLLS/" "$SDK/Assets/_BaDependencies/GameDlls/" --include='*.dll' --exclude='*'
python3 "$REPO/tools/write-dll-metas.py" "$SDK/Assets/_BaDependencies/GameDlls"

# Harmony and its required notice, recovered together from the checksum-pinned package. Never committed.
if [ ! -f "$DEPS/0Harmony.dll" ] || [ ! -f "$REPO/build/Harmony-LICENSE.txt" ]; then
  tmp="$(mktemp -d)"
  curl -fsSL "$HARMONY_URL" -o "$tmp/harmony.nupkg"
  echo "$HARMONY_SHA256  $tmp/harmony.nupkg" | shasum -a 256 -c - >/dev/null
  unzip -q -o "$tmp/harmony.nupkg" 'lib/net472/0Harmony.dll' LICENSE -d "$tmp"
  cp "$tmp/lib/net472/0Harmony.dll" "$DEPS/0Harmony.dll"
  cp "$tmp/LICENSE" "$REPO/build/Harmony-LICENSE.txt"
  rm -rf "$tmp"
fi
echo "$HARMONY_DLL_SHA256  $DEPS/0Harmony.dll" | shasum -a 256 -c - >/dev/null || { echo "Cached 0Harmony.dll does not match the pinned hash; delete it and rebuild" >&2; exit 1; }

# The model's game export from art/roadster-free (tools: art/roadster-free/feedback-4-game-export.md), copied in so the
# generator can build the prefab. Only the .meta files are committed (stable GUIDs for the prefab). The FBX goes in as
# Roadster_Model.fbx: the game finds a vehicle's prefab by file name in any bundle, so no model may share the prefab's name.
ART="$REPO/art/roadster-free"
MODEL_DIR="$MOD_DIR/Vehicles/RoadsterArt"
if [ -f "$ART/Roadster-game.fbx" ] && [ -f "$ART/game-export.json" ]; then
  mkdir -p "$MODEL_DIR"
  rsync -a --checksum "$ART/Roadster-game.fbx" "$MODEL_DIR/Roadster_Model.fbx"
  rsync -a --checksum "$ART/game-export.json" "$MODEL_DIR/game-export.json"
else
  echo "No game export in $ART; the prefab keeps the example car's body." >&2
fi

link() { # link <target> <link path>
  if [ -L "$2" ]; then [ "$(readlink "$2")" = "$1" ] || { rm "$2"; ln -s "$1" "$2"; }
  elif [ -e "$2" ]; then echo "$2 exists and is not a symlink; refusing to replace it" >&2; exit 1
  else ln -s "$1" "$2"; fi
}
link "$MOD_DIR" "$SDK/Assets/Mods/Roadster"
link "$REPO/unity/BuildEditor" "$SDK/Assets/Editor/RoadsterBuild"

run_unity() { # run_unity <method> <log name>
  local log="$LOG_DIR/$2.log" ok=1
  "$UNITY" -batchmode -nographics -projectPath "$SDK" -buildTarget Win64 \
      -executeMethod "$1" -modId Roadster -logFile "$log" || ok=0
  git -C "$SDK" checkout -q -- "${SDK_RESAVED[@]}"
  if [ "$ok" = 0 ]; then
    grep -E "RoadsterBuild|error CS|Exception" "$log" | tail -40 >&2
    echo "Unity step $1 failed; full log: $log" >&2
    exit 1
  fi
  grep "RoadsterBuild" "$log" || true
}

if [ "${1:-}" = "--generate" ]; then
  run_unity Roadster.BuildEditor.ModAssets.Generate generate
fi
run_unity Roadster.BuildEditor.BatchBuild.Build build

OUT="$REPO/build/Roadster"
rm -rf "$OUT"
cp -R "$SDK/Output/Roadster" "$OUT"
cp "$REPO/build/Harmony-LICENSE.txt" "$OUT/Dependencies/Harmony-LICENSE.txt"
cp "$REPO/README.md" "$OUT/"
( cd "$OUT" && find . -type f | sort | xargs shasum -a 256 ) > "$REPO/build/Roadster.sha256"
echo "Built $OUT"
cat "$REPO/build/Roadster.sha256"
