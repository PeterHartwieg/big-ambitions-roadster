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
    internal static class RoadsterModel
    {
        internal const string ArtFolder = ModAssets.ModFolder + "/Vehicles/RoadsterArt";
        internal const string FbxPath = ArtFolder + "/Roadster_Model.fbx";
        private const string ExportPath = ArtFolder + "/game-export.json";

        internal static Vector3 ToUnity(JToken v) => new Vector3(-(float)v[0]!, (float)v[2]!, -(float)v[1]!);

        private static readonly (string Prefab, string Fbx, string Key)[] Wheels =
        {
            ("FrontLeft", "Roadster_Wheel_FL", "FL"),
            ("FrontRight", "Roadster_Wheel_FR", "FR"),
            ("RearLeft", "Roadster_Wheel_RL", "RL"),
            ("RearRight", "Roadster_Wheel_RR", "RR"),
        };

        private const float SpringMaxForce = 30000f;
        private const float SpringLength = 0.25f;
        private const float DamperRate = 12700f;
        private const float TyreLoadRating = 20000f;
        private const float FanLoadFactor = 3f;
        private const float CornerWeight = 1400f * 9.81f / 4f * FanLoadFactor;
        private const float ControllerLift = SpringLength * (1f - CornerWeight / SpringMaxForce);

        internal static bool Available => File.Exists(Path.Combine(ProjectRoot, FbxPath)) && File.Exists(Path.Combine(ProjectRoot, ExportPath));

        internal sealed class Fit
        {
            public float WheelRadius;
            public Vector3 BoundsMin, BoundsMax;
        }

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

            var body = Find(root, "CarHolder/Body/CheapSaloon");
            body.GetComponent<MeshFilter>().sharedMesh = parts["Roadster_Body"].sharedMesh;
            body.GetComponent<MeshRenderer>().sharedMaterials = Remap(parts["Roadster_Body"], materials);

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
                // The export reuses Paint on wheel details. Keep their original finish independent of body colour.
                visual.GetComponent<MeshRenderer>().sharedMaterials = Remap(parts[fbxName], materials)
                    .Select(m => m == materials["Paint"] ? materials["WheelPaint"] : m).ToArray();
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
                ModAssets.Set(controller, "loadRating", TyreLoadRating);
            }

            var collider = Find(root, "CarHolder/Colliders/BodyCollider").GetComponent<MeshCollider>();
            collider.sharedMesh = parts["Roadster_Collision"].sharedMesh;
            collider.convex = true;

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

            RoadsterPlume.Add(root, body.transform.parent);

            var spoiler = root.transform.Find("Spoiler");
            if (spoiler != null) Object.DestroyImmediate(spoiler.gameObject);
            NoStreetDecals(root);
            return new Fit { WheelRadius = radius, BoundsMin = min, BoundsMax = max };
        }

        private static JToken WheelExport(JObject export, string key, string fbxName)
        {
            var wheels = export["wheels"] ?? throw new InvalidOperationException("game-export.json has no wheels.");
            if (wheels is JObject keyed)
                return keyed[key] ?? keyed[fbxName] ?? throw new InvalidOperationException($"game-export.json has no wheel {key}.");
            return wheels.FirstOrDefault(w => (string?)w["name"] == fbxName || (string?)w["name"] == key)
                   ?? throw new InvalidOperationException($"game-export.json has no wheel {key}.");
        }

        private static Dictionary<string, Material> Materials(JObject export)
        {
            var list = export["materials"] ?? throw new InvalidOperationException("game-export.json has no materials.");
            var entries = list is JObject keyed
                ? keyed.Properties().Select(p => (Name: p.Name, Value: p.Value))
                : list.Select(m => (Name: (string)m["name"]!, Value: m));
            var result = new Dictionary<string, Material>();
            foreach (var (name, value) in entries)
            {
                result[name] = RoadsterMaterials.Create(name, value);
                if (name == "Paint") result["WheelPaint"] = RoadsterMaterials.Create("WheelPaint", value);
            }
            return result;
        }

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
