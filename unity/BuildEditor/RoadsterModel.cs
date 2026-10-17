#nullable enable
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.AI;
using Object = UnityEngine.Object;

namespace Roadster.BuildEditor
{
    // Puts the Roadster model (art/roadster-free/Roadster-game.fbx and game-export.json, copied into Vehicles/RoadsterArt
    // by tools/build-mod.sh) into the prefab copied from the SDK's example car. The FBX has seven objects:
    // Roadster_Body, Roadster_Wheel_FL/FR/RL/RR (origins on the hubs), Roadster_Wing (origin on its hinge) and
    // Roadster_Collision. The model is untextured: each FBX material becomes an HDRP/Lit material with the flat values
    // from game-export.json.
    internal static class RoadsterModel
    {
        internal const string ArtFolder = ModAssets.ModFolder + "/Vehicles/RoadsterArt";
        internal const string FbxPath = ArtFolder + "/Roadster_Model.fbx";
        private const string ExportPath = ArtFolder + "/game-export.json";

        // Blender (x, y, z), front −Y, left +X, to Unity (−x, z, −y): the mapping the FBX export settings produce.
        internal static Vector3 ToUnity(JToken v) => new Vector3(-(float)v[0]!, (float)v[2]!, -(float)v[1]!);

        private static readonly (string Prefab, string Fbx, string Key)[] Wheels =
        {
            ("FrontLeft", "Roadster_Wheel_FL", "FL"),
            ("FrontRight", "Roadster_Wheel_FR", "FR"),
            ("RearLeft", "Roadster_Wheel_RL", "RL"),
            ("RearRight", "Roadster_Wheel_RR", "RR"),
        };

        // Suspension. The example car's springs (5,000 N over 0.6 m per wheel, dampers 5,000) suit a 120 kW city car; on
        // the Roadster the axle that takes the load under hard acceleration or braking ran near the end of that travel
        // and the body hit the road ("like driving into a wall", Peter, 17 October 2026). A short, stiff sports set-up:
        // 15,000 N over 0.25 m (60,000 N/m), so the static 3,430 N per wheel uses 23% of the travel, a 1 g load transfer
        // about 40%, and only a hard landing reaches the stop. Dampers 9,000 N s/m, about critical for a 350 kg corner on
        // that spring, as the example's are on its own.
        private const float SpringMaxForce = 15000f;
        private const float SpringLength = 0.25f;
        private const float DamperRate = 9000f;
        private const float CornerWeight = 1400f * 9.81f / 4f;
        // The controller sits the spring's resting length above the hub, so the wheel rests where the model has it.
        private const float ControllerLift = SpringLength * (1f - CornerWeight / SpringMaxForce);
        // The example's wheel shadow casters are a unit shape scaled to the wheel: 1.213 x width, 0.471 x diameter.

        internal static bool Available => File.Exists(Path.Combine(ProjectRoot, FbxPath)) && File.Exists(Path.Combine(ProjectRoot, ExportPath));

        internal sealed class Fit
        {
            public float WheelRadius;
            public Vector3 BoundsMin, BoundsMax;
        }

        // Fills root (the opened prefab contents) from the model. Returns the sizes the drivetrain needs.
        internal static Fit Apply(GameObject root)
        {
            var export = JObject.Parse(File.ReadAllText(Path.Combine(ProjectRoot, ExportPath)));
            ConfigureImport();
            var model = AssetDatabase.LoadAssetAtPath<GameObject>(FbxPath) ?? throw new InvalidOperationException($"{FbxPath} didn't import.");
            var parts = model.GetComponentsInChildren<MeshFilter>(true).ToDictionary(f => f.name, f => f);
            var needed = Wheels.Select(w => w.Fbx).Concat(new[] { "Roadster_Body", "Roadster_Wing", "Roadster_Collision" });
            var missing = needed.Where(n => !parts.ContainsKey(n)).ToList();
            if (missing.Count > 0) throw new InvalidOperationException($"{FbxPath} lacks {string.Join(", ", missing)}.");
            var materials = Materials(export);

            // Body: the example's body renderer takes the whole body mesh, one material per FBX submesh.
            var body = Find(root, "CarHolder/Body/CheapSaloon");
            body.GetComponent<MeshFilter>().sharedMesh = parts["Roadster_Body"].sharedMesh;
            body.GetComponent<MeshRenderer>().sharedMaterials = Remap(parts["Roadster_Body"], materials);

            // Wing: a hinge transform on its axis, the mesh below it, so the runtime can rotate the hinge to deploy it.
            var wingExport = export["wing"] ?? throw new InvalidOperationException("game-export.json has no wing.");
            var hinge = new GameObject("WingHinge").transform;
            hinge.SetParent(body.transform.parent, false);
            hinge.localPosition = ToUnity(wingExport["hinge_point"]!);
            var wing = new GameObject("Roadster_Wing");
            wing.layer = body.layer;
            wing.transform.SetParent(hinge, false);
            wing.AddComponent<MeshFilter>().sharedMesh = parts["Roadster_Wing"].sharedMesh;
            var wingRenderer = wing.AddComponent<MeshRenderer>();
            wingRenderer.sharedMaterials = Remap(parts["Roadster_Wing"], materials);
            Append(root, "renderers", wingRenderer);
            Append(root, "bodyMeshes", wingRenderer);

            // Wheels: visual on the hub, controller above it with the tyre's radius and width.
            var radius = 0f;
            foreach (var (prefabName, fbxName, key) in Wheels)
            {
                var w = WheelExport(export, key, fbxName);
                var hub = ToUnity(w["hub"]!);
                var r = (float)w["radius"]!;
                var width = (float)w["width"]!;
                radius = Mathf.Max(radius, r);

                var visual = Find(root, "CarHolder/Wheels/" + prefabName);
                visual.transform.localPosition = hub;
                visual.GetComponent<MeshFilter>().sharedMesh = parts[fbxName].sharedMesh;
                visual.GetComponent<MeshRenderer>().sharedMaterials = Remap(parts[fbxName], materials);
                foreach (Transform child in visual.transform)
                    if (child.name.StartsWith("ShadowCaster", StringComparison.Ordinal))
                        child.localScale = new Vector3(1.213f * width, 0.471f * 2f * r, 0.471f * 2f * r);

                var controller = Find(root, prefabName + "_WheelController");
                controller.transform.localPosition = hub + new Vector3(0f, ControllerLift, 0f);
                ModAssets.Set(controller, "wheel.radius", r);
                ModAssets.Set(controller, "wheel.width", width);
                ModAssets.Set(controller, "spring.maxForce", SpringMaxForce);
                ModAssets.Set(controller, "spring.maxLength", SpringLength);
                ModAssets.Set(controller, "damper.bumpRate", DamperRate);
                ModAssets.Set(controller, "damper.reboundRate", DamperRate);
            }

            var collider = Find(root, "CarHolder/Colliders/BodyCollider").GetComponent<MeshCollider>();
            collider.sharedMesh = parts["Roadster_Collision"].sharedMesh;
            collider.convex = true;

            // Bounds in Unity axes (the Blender min and max swap on the mirrored axes).
            var b = export["bounds"] ?? throw new InvalidOperationException("game-export.json has no bounds.");
            var a = ToUnity(b["min"]!);
            var c = ToUnity(b["max"]!);
            var min = Vector3.Min(a, c);
            var max = Vector3.Max(a, c);
            var obstacle = body.GetComponent<NavMeshObstacle>();
            if (obstacle != null)
            {
                obstacle.center = (min + max) / 2f;
                obstacle.size = max - min;
            }

            var spoiler = root.transform.Find("Spoiler");
            if (spoiler != null) Object.DestroyImmediate(spoiler.gameObject);
            NoStreetDecals(root);
            return new Fit { WheelRadius = radius, BoundsMin = min, BoundsMax = max };
        }

        private static JToken WheelExport(JObject export, string key, string fbxName)
        {
            var wheels = export["wheels"] ?? throw new InvalidOperationException("game-export.json has no wheels.");
            // Accept either an object keyed by FL/FR/RL/RR (or the object names) or a list of entries with a name.
            if (wheels is JObject keyed)
                return keyed[key] ?? keyed[fbxName] ?? throw new InvalidOperationException($"game-export.json has no wheel {key}.");
            return wheels.FirstOrDefault(w => (string?)w["name"] == fbxName || (string?)w["name"] == key)
                   ?? throw new InvalidOperationException($"game-export.json has no wheel {key}.");
        }

        // One HDRP/Lit material per entry in game-export.json "materials", named M_Roadster_<name>.
        private static Dictionary<string, Material> Materials(JObject export)
        {
            var list = export["materials"] ?? throw new InvalidOperationException("game-export.json has no materials.");
            var entries = list is JObject keyed
                ? keyed.Properties().Select(p => (Name: p.Name, Value: p.Value))
                : list.Select(m => (Name: (string)m["name"]!, Value: m));
            var result = new Dictionary<string, Material>();
            var shader = Shader.Find("HDRP/Lit") ?? throw new InvalidOperationException("HDRP/Lit shader not found.");
            foreach (var (name, value) in entries)
            {
                var path = $"{ArtFolder}/M_Roadster_{Safe(name)}.mat";
                var material = AssetDatabase.LoadAssetAtPath<Material>(path);
                if (material == null)
                {
                    material = new Material(shader);
                    AssetDatabase.CreateAsset(material, path);
                }
                // Blender's values are linear; Unity's material colours are sRGB.
                var linear = Rgb(value["base_color"]!);
                material.SetColor("_BaseColor", linear.gamma);
                material.SetFloat("_Metallic", (float)value["metallic"]!);
                material.SetFloat("_Smoothness", (float)value["smoothness"]!);
                var emission = value["emission"];
                if (emission != null && emission.Type != JTokenType.Null)
                {
                    // HDR and linear; the factor lifts Blender's unit emission to a lamp that reads at night.
                    material.SetColor("_EmissiveColor", Rgb(emission) * 8f);
                    material.SetColor("_EmissiveColorLDR", Rgb(emission).gamma);
                    material.SetFloat("_EmissiveIntensity", 8f);
                }
                material.SetFloat("_SupportDecals", 0f);
                material.EnableKeyword("_DISABLE_DECALS");
                EditorUtility.SetDirty(material);
                result[name] = material;
            }
            return result;
        }

        private static Color Rgb(JToken v) => new Color((float)v[0]!, (float)v[1]!, (float)v[2]!, 1f);

        // The FBX's imported materials, in submesh order, swapped for ours by name.
        private static Material[] Remap(MeshFilter part, Dictionary<string, Material> materials)
        {
            var imported = part.GetComponent<MeshRenderer>().sharedMaterials;
            return imported.Select(m =>
            {
                var name = m == null ? "" : m.name;
                if (materials.TryGetValue(name, out var ours)) return ours;
                throw new InvalidOperationException($"{part.name} uses material '{name}', which game-export.json doesn't list.");
            }).ToArray();
        }

        private static string Safe(string name) => new string(name.Select(ch => char.IsLetterOrDigit(ch) ? ch : '_').ToArray());

        // Normals from the FBX (creases and weighted normals carry the look), readable meshes for the game's damage
        // deformation, and the materials imported only so their names tell us which submesh is which.
        private static void ConfigureImport()
        {
            var importer = (ModelImporter)AssetImporter.GetAtPath(FbxPath);
            if (importer == null) throw new InvalidOperationException($"{FbxPath} is not a model.");
            if (importer.importNormals == ModelImporterNormals.Import && importer.isReadable && !importer.importAnimation
                && importer.materialImportMode == ModelImporterMaterialImportMode.ImportStandard
                && importer.materialLocation == ModelImporterMaterialLocation.InPrefab) return;
            importer.importNormals = ModelImporterNormals.Import;
            importer.importTangents = ModelImporterTangents.CalculateMikk;
            importer.isReadable = true;
            importer.importAnimation = false;
            importer.materialImportMode = ModelImporterMaterialImportMode.ImportStandard;
            importer.materialLocation = ModelImporterMaterialLocation.InPrefab;
            importer.SaveAndReimport();
        }

        // Every renderer leaves HDRP's default decal layer, so street dirt never projects onto it (the game's vehicles do the same).
        private static void NoStreetDecals(GameObject root)
        {
            foreach (var renderer in root.GetComponentsInChildren<Renderer>(true))
                renderer.renderingLayerMask = 1;
        }

        private static GameObject Find(GameObject root, string path) =>
            root.transform.Find(path)?.gameObject ?? throw new InvalidOperationException($"Example prefab has no {path}.");

        private static void Append(GameObject owner, string path, Object value)
        {
            var hits = 0;
            foreach (var component in owner.GetComponents<MonoBehaviour>().Where(c => c != null))
            {
                var serialized = new SerializedObject(component);
                var property = serialized.FindProperty(path);
                if (property == null || !property.isArray) continue;
                property.arraySize++;
                property.GetArrayElementAtIndex(property.arraySize - 1).objectReferenceValue = value;
                serialized.ApplyModifiedPropertiesWithoutUndo();
                hits++;
            }
            if (hits == 0) throw new InvalidOperationException($"No component on {owner.name} has the list {path}.");
        }

        private static string ProjectRoot => Path.GetDirectoryName(Application.dataPath)!;
    }
}
