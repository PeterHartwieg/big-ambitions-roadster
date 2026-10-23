#nullable enable
using System;
using System.Linq;
using System.Collections.Generic;
using System.IO;
using Data.VehicleColors;
using NWH.VehiclePhysics2.Effects;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;

namespace Roadster.BuildEditor
{
    // Offline Unity checks against the real CarFeatures/LightSource implementations in the supplied DLLs.
    // Empty editor scene only: never boots Big Ambitions, connects to a rig or loads a save.
    [InitializeOnLoad]
    public static class AppearanceChecks
    {
        private const string Running = "Roadster.AppearanceChecks.Running";
        private const string Started = "Roadster.AppearanceChecks.Started";
        private const string BaselineOnly = "Roadster.AppearanceChecks.BaselineOnly";
        private static readonly List<string> Errors = new List<string>();
        [Serializable] private sealed class Diagnostics { public string[] errors = Array.Empty<string>(); }
        private const string BundlePath = "Roadster.AppearanceChecks.BundlePath";
        private static int passed;
        private static GameObject? testedPrefab;

        static AppearanceChecks()
        {
            Application.logMessageReceived += (message, stack, type) =>
            {
                if (SessionState.GetBool(Running, false) &&
                    (type == LogType.Error || type == LogType.Exception || type == LogType.Assert))
                    Errors.Add(message);
            };
            EditorApplication.playModeStateChanged += state =>
            {
                if (state == PlayModeStateChange.EnteredPlayMode && SessionState.GetBool(Running, false))
                    EditorApplication.delayCall += Execute;
            };
            EditorApplication.update += () =>
            {
                if (SessionState.GetBool(Running, false) &&
                    long.TryParse(SessionState.GetString(Started, ""), out var ticks) &&
                    DateTime.UtcNow - new DateTime(ticks, DateTimeKind.Utc) > TimeSpan.FromMinutes(3))
                    Finish(1, "Timed out entering/running the offline Unity checks.");
            };
        }

        public static void Run()
        {
            var args = Environment.GetCommandLineArgs();
            SessionState.SetBool(BaselineOnly, args.Contains("-roadsterCheckBaseline"));
            var index = Array.IndexOf(args, "-roadsterCheckBundle");
            SessionState.SetString(BundlePath, index >= 0 ? args[index + 1] : "");
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            SessionState.SetString(Started, DateTime.UtcNow.Ticks.ToString());
            SessionState.SetBool(Running, true);
            EditorApplication.isPlaying = true;
        }

        private static void Execute()
        {
            try
            {
                // The partial SDK has no game catalogues, arcade dependency or game managers. Its unrelated
                // runtime initializers report errors before the fixture runs. Require the exact same diagnostics
                // as a fresh empty-scene baseline, then fail on any error from the actual checks.
                var baselinePath = Path.GetFullPath(Path.Combine(Application.dataPath, "../../logs/appearance-baseline.json"));
                var startupErrors = Errors.OrderBy(message => message, StringComparer.Ordinal).ToArray();
                if (SessionState.GetBool(BaselineOnly, false))
                {
                    File.WriteAllText(baselinePath, JsonUtility.ToJson(new Diagnostics { errors = startupErrors }, true));
                    Finish(0, $"Empty SDK scene baseline recorded: {startupErrors.Length} bootstrap diagnostics; no appearance fixture run.");
                    return;
                }
                var baseline = JsonUtility.FromJson<Diagnostics>(File.ReadAllText(baselinePath));
                Check(baseline.errors.SequenceEqual(startupErrors), "SDK startup diagnostics match empty-scene baseline: " + string.Join(" | ", startupErrors));
                Errors.Clear();
                Check(Application.isPlaying, "native LightSource shader writes run in play mode");
                var bundlePath = SessionState.GetString(BundlePath, "");
                AssetBundle? bundle = null;
                if (bundlePath.Length > 0)
                {
                    bundle = AssetBundle.LoadFromFile(bundlePath);
                    Check(bundle != null, "packaged Mac bundle loads in the Mac editor");
                }
                var prefabPath = ModAssets.ModFolder + "/Vehicles/Roadster.prefab";
                var prefab = (bundle == null ? AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath) : bundle.LoadAsset<GameObject>(prefabPath))
                    ?? throw new InvalidOperationException("Roadster prefab is missing.");
                testedPrefab = prefab;
                Check((bool)prefab, "generated prefab exists");
                var features = prefab.GetComponent<CarFeatures>();
                var body = prefab.transform.Find("CarHolder/Body/CheapSaloon").GetComponent<MeshRenderer>();
                var wing = prefab.transform.Find("CarHolder/Body/WingHinge/Roadster_Wing").GetComponent<MeshRenderer>();
                Check(features.bodyMeshes.Contains(body) && features.bodyMeshes.Contains(wing), "body and wing receive native colour updates");
                var paint = Material("Paint");
                var head = Material("HeadLight");
                var tail = Material("TailLight");
                var marker = Material("Indicator");
                var vehicleShader = AssetDatabase.LoadAssetAtPath<Shader>(RoadsterMaterials.ShaderPath);
                foreach (var material in new[] { paint, head, tail, marker })
                {
                    Check(bundle == null ? material.shader == vehicleShader : material.shader.name == vehicleShader.name, material.name + " uses SDK vehicle shader");
                    Check(!ShaderUtil.ShaderHasError(material.shader), material.name + " shader imports without errors");
                    foreach (var property in new[] { RoadsterMaterials.Tint, RoadsterMaterials.Fresnel,
                                 RoadsterMaterials.FresnelPower, "_FrontLightStrength", "_BackLightStrength" })
                        Check(material.HasProperty(property), material.name + " accepts " + property);
                    Check(Pixel(material, RoadsterMaterials.Diffuse).a == (material == paint ? 1f : 0f), material.name + " paint mask");
                    Check(Pixel(material, "_IndicatorsMask") == Color.clear, material.name + " no inherited indicator texture");
                    Check(Pixel(material, "_DirtDiffuse") == Color.clear, material.name + " no inherited example dirt texture");
                    foreach (var property in new[] { "_FrontLightStrength", "_BackLightStrength", "_ReverseLightStrength" })
                        Near(0f, material.GetFloat(property), material.name + " initially off: " + property);
                }
                Near(0.74f, Pixel(head, RoadsterMaterials.Diffuse).r, "headlight diffuse keeps linear export colour");
                Check(!((Texture2D)head.GetTexture(RoadsterMaterials.Diffuse)).isDataSRGB, "flat float textures are linear");
                Check(Pixel(paint, "_EmissionMask") == Color.clear, "paint never emits");
                Check(Pixel(head, "_EmissionMask") == Color.red, "headlights use front channel only");
                Check(Pixel(tail, "_EmissionMask") == Color.green, "tail/brake lights use rear channel only");
                Check(Pixel(marker, "_EmissionMask") == Color.red, "amber markers follow front channel");
                Near(40f, Pixel(head, "_EmissionTexture").b * 50000f, "headlight lit intensity preserved");
                Near(10.4f, Pixel(tail, "_EmissionTexture").r * 20000f, "tail light lit intensity preserved");
                foreach (var name in new[] { "Glass", "Carbon", "Rubber", "Alloy", "Metal", "Black", "Bronze", "Plate", "WheelPaint" })
                {
                    var material = Material(name);
                    Check(material.shader.name == "HDRP/Lit", name + " keeps original shader");
                    Check(!material.HasProperty(RoadsterMaterials.Tint), name + " ignores dealer tint");
                    Check(material.GetColor("_EmissiveColor").maxColorComponent == 0f, name + " does not glow");
                }
                Check(body.sharedMaterials.Contains(paint) && wing.sharedMaterials.Contains(paint), "body and wing actually bind Paint");
                Check(body.sharedMaterials.Contains(head) && body.sharedMaterials.Contains(tail) && body.sharedMaterials.Contains(marker), "body binds all lamp materials");
                Check(!body.HasPropertyBlock() && !wing.HasPropertyBlock(), "prefab has no baked per-instance overrides");

                var wheels = new[] { "FrontLeft", "FrontRight", "RearLeft", "RearRight" }.Select(name =>
                    prefab.transform.Find("CarHolder/Wheels/" + name).GetComponent<MeshRenderer>()).ToArray();
                foreach (var wheel in wheels)
                {
                    Check(wheel.sharedMaterials.Contains(Material("WheelPaint")), wheel.name + " retains original wheel paint finish");
                    Check(wheel.sharedMaterials.All(material => !material.HasProperty(RoadsterMaterials.Tint)), wheel.name + " cannot take dealer body tint");
                }
                var renderers = new[] { body, wing }.Concat(wheels).ToArray();
                var first = Fixture("first", renderers);
                var second = Fixture("second", renderers);
                var originalTint = paint.GetColor(RoadsterMaterials.Tint);
                var red = ScriptableObject.CreateInstance<VehicleColor>();
                red.tint = new Color32(220, 20, 30, 255);
                red.fresnelColor = new Color32(240, 80, 70, 255);
                red.fresnelPower = 3.5f;
                var blue = ScriptableObject.CreateInstance<VehicleColor>();
                blue.tint = new Color32(20, 50, 220, 255);
                blue.fresnelColor = new Color32(70, 100, 240, 255);
                blue.fresnelPower = 2f;
                first.SetDirtiness(0.4f);
                first.SetColor(red);
                second.SetColor(blue);
                Check(first.VehicleColor == red && second.VehicleColor == blue, "native colour state remains per vehicle");
                AssertColour(first, red);
                AssertColour(second, blue);
                Near(0.4f, Block(first.bodyMeshes[0]).GetFloat("_Dirtiness"), "colour retains existing property block values");
                Check(paint.GetColor(RoadsterMaterials.Tint) == originalTint, "dealer choices never mutate shared Paint material");

                var native = prefab.GetComponent<NWH.VehiclePhysics2.VehicleController>().effectsManager.lightsManager;
                var low = Clone(native.lowBeamLights, body, (MeshRenderer)first.bodyMeshes[0]);
                var rear = Clone(native.tailLights, body, (MeshRenderer)first.bodyMeshes[0]);
                var brake = Clone(native.brakeLights, body, (MeshRenderer)first.bodyMeshes[0]);
                Near(50000f, low.lightSources.Single().shaderPropertyBrightness, "native front brightness matches material coefficient");
                Near(20000f, rear.lightSources.Single().shaderPropertyBrightness, "native tail brightness matches material coefficient");
                Near(40000f, brake.lightSources.Single().shaderPropertyBrightness, "native brake brightness is twice tail");
                low.TurnOff(); rear.TurnOff();
                AssertLights(first, 0f, 0f, "fresh daylight/parked");
                low.TurnOn(); rear.TurnOn();
                AssertLights(first, 50000f, 20000f, "night/rain vehicle state");
                AssertColour(first, red);
                first.SetColor(blue);
                AssertLights(first, 50000f, 20000f, "repaint retains lights");
                AssertColour(first, blue);
                brake.TurnOn();
                AssertLights(first, 50000f, 40000f, "braking at night");
                brake.TurnOff(); rear.TurnOff(); rear.TurnOn(); // NWH's brake-release ordering.
                AssertLights(first, 50000f, 20000f, "brake release restores tail");
                low.TurnOff(); rear.TurnOff();
                AssertLights(first, 0f, 0f, "daylight/exit switches emission off");
                brake.TurnOn();
                AssertLights(first, 0f, 40000f, "daylight brake only");
                brake.TurnOff();
                AssertLights(first, 0f, 0f, "daylight brake release");
                AssertLights(second, 0f, 0f, "second car lights remain independent");
                AssertColour(second, blue);
                Check(head.GetFloat("_FrontLightStrength") == 0f && tail.GetFloat("_BackLightStrength") == 0f, "light writes never mutate shared materials");
                Object.DestroyImmediate(first.gameObject);
                Object.DestroyImmediate(second.gameObject);
                Object.DestroyImmediate(red);
                Object.DestroyImmediate(blue);
                if (bundle != null) bundle.Unload(true);
                Check(Errors.Count == 0, "no errors during appearance checks: " + string.Join(" | ", Errors));
                Finish(0, passed + " offline appearance checks passed (" + (bundlePath.Length > 0 ? "Mac bundle" : "source assets") + ").");
            }
            catch (Exception ex) { Finish(1, ex.ToString()); }
        }

        private static CarFeatures Fixture(string name, params MeshRenderer[] sources)
        {
            var root = new GameObject("Roadster offline test " + name);
            var features = root.AddComponent<CarFeatures>();
            features.bodyMeshes = sources.Select(source =>
            {
                var child = new GameObject(source.name);
                child.transform.SetParent(root.transform);
                var renderer = child.AddComponent<MeshRenderer>();
                renderer.sharedMaterials = source.sharedMaterials;
                return (Renderer)renderer;
            }).ToArray();
            return features;
        }

        private static VehicleLight Clone(VehicleLight source, MeshRenderer expected, MeshRenderer target)
        {
            var result = new VehicleLight();
            foreach (var light in source.lightSources.Where(s => s.type == LightSource.LightType.ShaderProperty))
            {
                Check(light.meshRenderer == expected, "native light points to Roadster body");
                Check(light.rendererMaterialIndex == -1, "native light addresses all body materials");
                result.lightSources.Add(new LightSource { type = light.type, meshRenderer = target,
                    rendererMaterialIndex = light.rendererMaterialIndex, shaderPropertyName = light.shaderPropertyName,
                    shaderPropertyBrightness = light.shaderPropertyBrightness });
            }
            Check(result.lightSources.Count == 1, "one native mesh light source per channel");
            return result;
        }

        private static void AssertColour(CarFeatures car, VehicleColor color)
        {
            foreach (var renderer in car.bodyMeshes)
            {
                var block = Block(renderer);
                Check(block.GetColor(RoadsterMaterials.Tint) == (Color)color.tint, renderer.name + " native tint");
                Check(block.GetColor(RoadsterMaterials.Fresnel) == (Color)color.fresnelColor, renderer.name + " native fresnel");
                Near(color.fresnelPower, block.GetFloat(RoadsterMaterials.FresnelPower), renderer.name + " native fresnel power");
            }
        }

        private static void AssertLights(CarFeatures car, float front, float rear, string label)
        {
            var block = Block(car.bodyMeshes[0]);
            Near(front, block.GetFloat("_FrontLightStrength"), label + " front");
            Near(rear, block.GetFloat("_BackLightStrength"), label + " rear");
        }

        private static MaterialPropertyBlock Block(Renderer renderer)
        {
            var block = new MaterialPropertyBlock();
            renderer.GetPropertyBlock(block);
            return block;
        }

        private static Material Material(string name) => testedPrefab!.GetComponentsInChildren<Renderer>(true)
            .SelectMany(renderer => renderer.sharedMaterials).Where(material => material != null)
            .Distinct().Single(material => material.name == "M_Roadster_" + name);
        private static Color Pixel(Material material, string property) => ((Texture2D)material.GetTexture(property)).GetPixel(0, 0);
        private static void Near(float expected, float actual, string label) => Check(Mathf.Abs(expected - actual) <= Math.Max(0.0001f, Math.Abs(expected) * 0.0001f), label + $" (expected {expected}, got {actual})");
        private static void Check(bool condition, string label)
        {
            if (!condition) throw new InvalidOperationException(label);
            passed++;
        }

        private static void Finish(int code, string message)
        {
            SessionState.SetBool(Running, false);
            Debug.Log($"[RoadsterBuild] {(code == 0 ? "OK" : "FAILED")}: {message}");
            EditorApplication.Exit(code);
        }
    }
}
