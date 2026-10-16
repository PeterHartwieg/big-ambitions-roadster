#nullable enable
using System;
using System.IO;
using System.Linq;
using BAModTemplate.Editor;
using UnityEditor;
using UnityEditorInternal;
using UnityEngine;
using Vehicles.VehicleTypes;

namespace Roadster.BuildEditor
{
    // Generates the mod's Unity assets from code so they can be rebuilt and reviewed as text.
    // Entry point for `Unity -batchmode -executeMethod Roadster.BuildEditor.ModAssets.Generate`.
    public static class ModAssets
    {
        public const string ModFolder = "Assets/Mods/Roadster";
        private const string VehiclesFolder = ModFolder + "/Vehicles";
        public const string TypeName = "roadster:vehicletype_roadster";

        private const string ExampleVehicleType = "Assets/Mods/Example-Vehicle/TurboHonza.asset";
        private const string ExampleVehiclePrefab = "Assets/Mods/Example-Vehicle/TurboHonza.prefab";

        // Phase 0 placeholder: the SDK's example car body with the Roadster's drivetrain. The model comes in phase 2.
        private const float Price = 250000f; // the Thrust trim's quoted figure; placeholder until a balance pass
        // The game gives every car a 1,400 kg rigidbody; the Roadster keeps it.
        // Power and gearing: the example car has 120 kW and a final drive of 8.51 on 0.305 m wheels, which tops out at
        // about 64 km/h on its 2.108 top gear at the 10,000 rpm limiter. A final drive of 1.70 puts the limiter at
        // about 320 km/h. 600 kW is far more than four tyres can put down below 100 km/h; the launch to 60 mph comes
        // from the thrusters (RoadsterDrive), the engine carries on from there.
        private const float EnginePower = 600f; // kW
        private const float FinalGearRatio = 1.70f;
        private const int TopSpeed = 320; // km/h, for the showroom; the gearing sets the real one
        private const float BrakeTorque = 5000f; // N m on each wheel, double the example's for 320 km/h

        [MenuItem("Big Ambitions/Roadster/Generate assets")]
        public static void GenerateFromMenu() => Run(exitWhenDone: false);

        public static void Generate() => Run(exitWhenDone: true);

        private static void Run(bool exitWhenDone)
        {
            var code = 0;
            try
            {
                AssetDatabase.Refresh(ImportAssetOptions.ForceUpdate);
                EnsureFolder(VehiclesFolder);
                EnsureManifest();
                GenerateRoadster();
                AssetDatabase.SaveAssets();
                Debug.Log("[RoadsterBuild] OK: generated assets.");
            }
            catch (Exception ex)
            {
                Debug.LogError("[RoadsterBuild] FAILED: " + ex);
                code = 1;
            }
            if (exitWhenDone) EditorApplication.Exit(code);
        }

        private static void GenerateRoadster()
        {
            var typePath = VehiclesFolder + "/Roadster.asset";
            var prefabPath = VehiclesFolder + "/Roadster.prefab";
            CopyFresh(ExampleVehicleType, typePath);
            CopyFresh(ExampleVehiclePrefab, prefabPath);

            var type = AssetDatabase.LoadAssetAtPath<VehicleType>(typePath);
            type.name = "Roadster";
            type.vehicleTypeName = TypeName;
            type.price = Price;
            type.maxSpeed = TopSpeed;
            type.enginePower = EnginePower;
            type.brakeForce = BrakeTorque;
            EditorUtility.SetDirty(type);

            var root = PrefabUtility.LoadPrefabContents(prefabPath);
            try
            {
                var controller = root.GetComponent<VehicleController>();
                if (controller == null) throw new InvalidOperationException("Example prefab has no VehicleController.");
                controller.vehicleType = type;
                root.name = "Roadster";

                var body = root.GetComponent<Rigidbody>();
                // At 320 km/h the car moves 3 m per physics step; discrete checks would let it pass through walls.
                body.collisionDetectionMode = CollisionDetectionMode.ContinuousDynamic;
                Set(root, "powertrain.engine.maxPower", EnginePower);
                Set(root, "powertrain.transmission.finalGearRatio", FinalGearRatio);
                Set(root, "brakes.maxTorque", BrakeTorque);
                PrefabUtility.SaveAsPrefabAsset(root, prefabPath);
            }
            finally
            {
                PrefabUtility.UnloadPrefabContents(root);
            }
        }

        private static string RuntimeVersion()
        {
            var source = File.ReadAllText(ModFolder + "/Scripts/RoadsterMod.cs");
            var match = System.Text.RegularExpressions.Regex.Match(source, "const string Version = \"([^\"]+)\"");
            if (!match.Success) throw new InvalidOperationException("No Version constant in RoadsterMod.cs.");
            return match.Groups[1].Value;
        }

        private static void EnsureManifest()
        {
            var path = ModFolder + "/ModManifest.asset";
            var manifest = AssetDatabase.LoadAssetAtPath<BAModManifest>(path);
            if (manifest == null)
            {
                manifest = ScriptableObject.CreateInstance<BAModManifest>();
                AssetDatabase.CreateAsset(manifest, path);
            }
            manifest.ModId = "Roadster";
            manifest.DisplayName = "Roadster";
            manifest.Author = "Peter Hartwieg";
            // The runtime's Version constant is the one source; this assembly can't reference the mod's.
            manifest.Version = RuntimeVersion();
            manifest.AssetBundleName = "roadster.unity3d";
            manifest.ModAssembly = AssetDatabase.LoadAssetAtPath<AssemblyDefinitionAsset>(ModFolder + "/Roadster.asmdef");
            manifest.LocalesFolder = AssetDatabase.LoadAssetAtPath<DefaultAsset>(ModFolder + "/Locales");
            // Dependencies/ is found by convention; the folder is recreated by the build script.
            manifest.DependenciesFolder = null!;
            manifest.TargetPlatforms = ModTargetPlatforms.Windows | ModTargetPlatforms.Mac;
            if (manifest.ModAssembly == null) throw new InvalidOperationException("Roadster.asmdef not found.");
            EditorUtility.SetDirty(manifest);
        }

        private static void EnsureFolder(string path)
        {
            var parent = Path.GetDirectoryName(path)!.Replace('\\', '/');
            if (!AssetDatabase.IsValidFolder(parent)) EnsureFolder(parent);
            if (!AssetDatabase.IsValidFolder(path)) AssetDatabase.CreateFolder(parent, Path.GetFileName(path));
        }

        // Sets a serialized field on whichever components of the object have it, so the NWH types
        // need no compile-time reference. Fails when none has it, rather than building a wrong car.
        private static void Set(GameObject owner, string path, float value)
        {
            var hits = 0;
            foreach (var component in owner.GetComponents<MonoBehaviour>().Where(c => c != null))
            {
                var serialized = new SerializedObject(component);
                var property = serialized.FindProperty(path);
                if (property == null) continue;
                property.floatValue = value;
                serialized.ApplyModifiedPropertiesWithoutUndo();
                hits++;
            }
            if (hits == 0) throw new InvalidOperationException($"No component on {owner.name} has {path}.");
        }

        private static string ProjectRoot => Path.GetDirectoryName(Application.dataPath)!;

        private static void CopyFresh(string from, string to)
        {
            File.Copy(Path.Combine(ProjectRoot, from), Path.Combine(ProjectRoot, to), overwrite: true);
            AssetDatabase.ImportAsset(to, ImportAssetOptions.ForceUpdate);
        }
    }
}
