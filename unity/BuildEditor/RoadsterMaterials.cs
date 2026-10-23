#nullable enable
using System;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEditor.Rendering.HighDefinition;
using UnityEngine;
using Object = UnityEngine.Object;

namespace Roadster.BuildEditor
{
    // CarFeatures and NWH LightSource write renderer property blocks for SH_Vehicle, not HDRP/Lit.
    // Use that same SDK shader for paint and lamps so the existing vehicle lifecycle owns their state.
    internal static class RoadsterMaterials
    {
        internal const string ShaderPath = "Assets/_BaDependencies/Shaders/Vehicles/SH_Vehicle.shadergraph";
        internal const string Tint = "Color_3d0f0cdbe6b74be28a1a5be5bab71dea";
        internal const string Fresnel = "Color_f78fac473bac467092fb27521e9f71ea";
        internal const string FresnelPower = "Vector1_481fa2a8a5e94165a039319bfd512b76";
        internal const string Diffuse = "Texture2D_3d0babbacbb04731a784ae3943688e65";
        internal const string Normal = "Texture2D_9b32f246716c41009146a43593b55e3f";
        internal const string Surface = "Texture2D_196dcf5fb385498aa0919d56d7cd684d";

        internal static Material Create(string name, JToken value)
        {
            var controlled = name == "Paint" || name == "HeadLight" || name == "TailLight" || name == "Indicator";
            var shader = controlled ? AssetDatabase.LoadAssetAtPath<Shader>(ShaderPath) : Shader.Find("HDRP/Lit");
            if (shader == null) throw new InvalidOperationException("Missing Roadster shader for " + name);
            var path = $"{RoadsterModel.ArtFolder}/M_Roadster_{Safe(name)}.mat";
            var material = AssetDatabase.LoadAssetAtPath<Material>(path);
            // Reset old HDRP/Lit emission and keywords while preserving the asset GUID.
            var fresh = new Material(shader) { name = "M_Roadster_" + name };
            if (material == null)
            {
                material = fresh;
                AssetDatabase.CreateAsset(material, path);
            }
            else
            {
                EditorUtility.CopySerialized(fresh, material);
                Object.DestroyImmediate(fresh);
            }
            var linear = Rgb(value["base_color"]!);
            var metallic = (float)value["metallic"]!;
            var smoothness = (float)value["smoothness"]!;
            if (controlled)
            {
                var paint = name == "Paint";
                var diffuse = linear;
                // SH_Vehicle's diffuse alpha is the paint mask: only Paint accepts the dealer tint/fresnel.
                diffuse.a = paint ? 1f : 0f;
                material.SetTexture(Diffuse, Solid(name + "_Diffuse", diffuse));
                material.SetTexture(Surface, Solid(name + "_Surface", new Color(metallic, 1f, 0f, smoothness)));
                var normal = Solid("FlatNormal", new Color(0.5f, 0.5f, 1f, 1f));
                material.SetTexture(Normal, normal);
                // Explicit neutral inputs avoid inheriting the example car's UV-mapped textures.
                material.SetTexture("_DirtNormal", normal);
                material.SetTexture("_DirtDiffuse", Solid("NoDirt", Color.clear));
                material.SetTexture("_Dirt_Met_AO_Smooth", Solid("NeutralSurface", new Color(0f, 1f, 0f, 0f)));
                material.SetTexture("_IndicatorsMask", Solid("NoEmission", Color.clear));
                material.SetColor(Tint, linear.gamma);
                material.SetColor(Fresnel, linear.gamma);
                material.SetFloat(FresnelPower, 1f);
                material.SetFloat("_Min", 0f);
                material.SetFloat("_Max", 1f);
                material.SetFloat("AOmin", 0f);
                material.SetFloat("AOmax", 1f);
                material.SetFloat("Vector1_41991b689ccf4932ad504975ac34399a", 1f);
                foreach (var property in new[] { "_FrontLightStrength", "_BackLightStrength", "_ReverseLightStrength",
                             "_LeftBlinkerStrength", "_RightBlinkerStrength", "_IsBlinkerOn", "_IsLeftBlinkerOn", "_IsRightBlinkerOn", "_Dirtiness" })
                    material.SetFloat(property, 0f);
                // The single amber material contains both sides: treat it as running/marker lamps, not turn signals.
                // Native prefab strengths are 50,000 front, 20,000 tail and 40,000 brake. Preserve the old model's
                // lit colour (emission * 8), with twice that brightness on braking, and zero emission when off.
                var mask = paint ? Color.clear : name == "TailLight" ? Color.green : Color.red;
                var emission = paint ? Color.clear : Rgb(value["emission"]!) * (8f / (name == "TailLight" ? 20000f : 50000f));
                material.SetTexture("_EmissionMask", Solid(name + "_EmissionMask", mask));
                material.SetTexture("_EmissionTexture", Solid(name + "_Emission", emission));
            }
            else
            {
                material.SetColor("_BaseColor", linear.gamma);
                material.SetFloat("_Metallic", metallic);
                material.SetFloat("_Smoothness", smoothness);
                if (value["emission"] != null && value["emission"]!.Type != JTokenType.Null)
                    throw new InvalidOperationException("Unmapped emissive Roadster material: " + name);
            }
            material.SetFloat("_SupportDecals", 0f);
            if (!HDShaderUtils.ResetMaterialKeywords(material))
                throw new InvalidOperationException("Cannot validate material " + name);
            EditorUtility.SetDirty(material);
            return material;
        }

        private static Texture2D Solid(string name, Color value)
        {
            var path = $"{RoadsterModel.ArtFolder}/T_Roadster_{Safe(name)}.asset";
            var texture = AssetDatabase.LoadAssetAtPath<Texture2D>(path);
            // All values are linear, including the export's diffuse RGB. Float textures preserve small emission
            // coefficients; explicitly linear storage avoids relying on unsupported sRGB float formats.
            var fresh = new Texture2D(1, 1, TextureFormat.RGBAFloat, mipChain: false, linear: true)
            {
                name = "T_Roadster_" + name, filterMode = FilterMode.Point, wrapMode = TextureWrapMode.Clamp
            };
            fresh.SetPixel(0, 0, value);
            fresh.Apply(updateMipmaps: false, makeNoLongerReadable: false);
            if (texture == null)
            {
                texture = fresh;
                AssetDatabase.CreateAsset(texture, path);
            }
            else
            {
                EditorUtility.CopySerialized(fresh, texture);
                Object.DestroyImmediate(fresh);
            }
            EditorUtility.SetDirty(texture);
            return texture;
        }

        private static Color Rgb(JToken v) => new Color((float)v[0]!, (float)v[1]!, (float)v[2]!, 1f);
        private static string Safe(string name) => new string(name.Select(ch => char.IsLetterOrDigit(ch) ? ch : '_').ToArray());
    }
}
