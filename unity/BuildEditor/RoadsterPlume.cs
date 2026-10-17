#nullable enable
using System;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace Roadster.BuildEditor
{
    // The cold-gas plumes: a soft white streak at each thruster nozzle, three crossed planes that widen away from the
    // nozzle, with a generated gradient texture on an HDRP/Unlit transparent material. The material is a copy of the
    // SDK's GroundIndicatorSmall (HDRP/Unlit, transparent), which the game renders. The emitters are added to the prefab
    // hidden; RoadsterDrive shows and stretches them while the thrusters fire.
    internal static class RoadsterPlume
    {
        private const string TemplateMaterial = "Assets/_BaDependencies/Shared/Materials/GroundIndicator/GroundIndicatorSmall.mat";
        private const string TexturePath = RoadsterModel.ArtFolder + "/T_Plume.png";
        private const string MaterialPath = RoadsterModel.ArtFolder + "/M_Roadster_Plume.mat";
        private const string MeshPath = RoadsterModel.ArtFolder + "/Plume.asset";

        // The bronze nozzle mouths on the model (art/roadster-free/Roadster-game.blend, material Bronze), in Blender
        // coordinates, and the way each one blows. Four rear thrusters in the diffuser blow backwards (+Y in Blender);
        // two behind the rear wheels blow straight down.
        private static readonly (string Name, Vector3 Mouth, Vector3 Direction)[] Nozzles =
        {
            ("Plume_Rear_1", new Vector3(-0.396f, 2.286f, 0.416f), new Vector3(0f, 1f, 0f)),
            ("Plume_Rear_2", new Vector3(-0.132f, 2.286f, 0.416f), new Vector3(0f, 1f, 0f)),
            ("Plume_Rear_3", new Vector3(0.132f, 2.286f, 0.416f), new Vector3(0f, 1f, 0f)),
            ("Plume_Rear_4", new Vector3(0.396f, 2.286f, 0.416f), new Vector3(0f, 1f, 0f)),
            ("Plume_Down_1", new Vector3(-0.788f, 1.798f, 0.180f), new Vector3(0f, 0f, -1f)),
            ("Plume_Down_2", new Vector3(0.788f, 1.798f, 0.180f), new Vector3(0f, 0f, -1f)),
        };

        private static Vector3 ToUnity(Vector3 v) => new Vector3(-v.x, v.z, -v.y);

        internal static void Add(GameObject root, Transform parent)
        {
            var material = Material();
            var mesh = Mesh();
            foreach (var (name, mouth, direction) in Nozzles)
            {
                var plume = new GameObject(name);
                plume.layer = parent.gameObject.layer;
                plume.transform.SetParent(parent, false);
                plume.transform.localPosition = ToUnity(mouth);
                var along = ToUnity(direction);
                plume.transform.localRotation = Quaternion.LookRotation(along, Mathf.Abs(along.y) > 0.9f ? Vector3.forward : Vector3.up);
                plume.transform.localScale = new Vector3(0.35f, 0.35f, 1.6f); // RoadsterDrive sets the length while firing
                plume.AddComponent<MeshFilter>().sharedMesh = mesh;
                var renderer = plume.AddComponent<MeshRenderer>();
                renderer.sharedMaterial = material;
                renderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                renderer.receiveShadows = false;
                renderer.enabled = false;
            }
        }

        private static Material Material()
        {
            Texture();
            var text = File.ReadAllText(Path.Combine(ProjectRoot, TemplateMaterial)).Replace("m_Name: GroundIndicatorSmall", "m_Name: M_Roadster_Plume");
            File.WriteAllText(Path.Combine(ProjectRoot, MaterialPath), text);
            AssetDatabase.ImportAsset(MaterialPath, ImportAssetOptions.ForceUpdate);
            var material = AssetDatabase.LoadAssetAtPath<Material>(MaterialPath) ?? throw new InvalidOperationException($"{MaterialPath} didn't import.");
            var texture = AssetDatabase.LoadAssetAtPath<Texture2D>(TexturePath);
            material.SetTexture("_UnlitColorMap", texture);
            material.SetTextureScale("_UnlitColorMap", Vector2.one);
            material.SetColor("_UnlitColor", new Color(0.92f, 0.96f, 1f, 0.8f));
            // Soft edges, no cut-out: blend only.
            material.SetFloat("_AlphaCutoffEnable", 0f);
            material.DisableKeyword("_ALPHATEST_ON");
            // Seen from both sides, the crossed planes read as a volume.
            material.SetFloat("_DoubleSidedEnable", 1f);
            material.SetFloat("_CullMode", 0f);
            material.SetFloat("_CullModeForward", 0f);
            material.EnableKeyword("_DOUBLESIDED_ON");
            EditorUtility.SetDirty(material);
            return material;
        }

        // 64 x 256, RGBA: white, alpha falling off across the width (sine) and along the length, with streaks.
        private static void Texture()
        {
            const int w = 64, h = 256;
            var tex = new Texture2D(w, h, TextureFormat.RGBA32, false);
            var random = new System.Random(15102026);
            var streaks = new float[w];
            for (var x = 0; x < w; x++) streaks[x] = 0.75f + 0.25f * (float)random.NextDouble();
            for (var y = 0; y < h; y++)
            for (var x = 0; x < w; x++)
            {
                var u = (x + 0.5f) / w;
                var v = (y + 0.5f) / h; // 0 at the nozzle, 1 at the far end
                var across = Mathf.Pow(Mathf.Sin(Mathf.PI * u), 1.6f);
                var along = Mathf.SmoothStep(0f, 1f, v / 0.06f) * Mathf.Pow(1f - v, 1.4f);
                var streak = Mathf.Lerp(streaks[x], 1f, v);
                tex.SetPixel(x, y, new Color(1f, 1f, 1f, Mathf.Clamp01(across * along * streak)));
            }
            tex.Apply();
            File.WriteAllBytes(Path.Combine(ProjectRoot, TexturePath), tex.EncodeToPNG());
            UnityEngine.Object.DestroyImmediate(tex);
            AssetDatabase.ImportAsset(TexturePath, ImportAssetOptions.ForceUpdate);
            var importer = (TextureImporter)AssetImporter.GetAtPath(TexturePath);
            importer.textureType = TextureImporterType.Default;
            importer.alphaIsTransparency = true;
            importer.sRGBTexture = true;
            importer.wrapMode = TextureWrapMode.Clamp;
            importer.mipmapEnabled = true;
            importer.SaveAndReimport();
        }

        // Three planes crossed at 60 degrees about the local +Z axis, 1 long; 0.25 wide at the nozzle and 1 wide at the end.
        private static Mesh Mesh()
        {
            var mesh = AssetDatabase.LoadAssetAtPath<Mesh>(MeshPath);
            if (mesh == null)
            {
                mesh = new Mesh { name = "Plume" };
                AssetDatabase.CreateAsset(mesh, MeshPath);
            }
            mesh.Clear();
            var vertices = new Vector3[12];
            var uvs = new Vector2[12];
            var triangles = new int[18];
            for (var i = 0; i < 3; i++)
            {
                var axis = Quaternion.AngleAxis(60f * i, Vector3.forward) * Vector3.right;
                var o = i * 4;
                vertices[o] = -axis * 0.125f;
                vertices[o + 1] = axis * 0.125f;
                vertices[o + 2] = axis * 0.5f + Vector3.forward;
                vertices[o + 3] = -axis * 0.5f + Vector3.forward;
                uvs[o] = new Vector2(0f, 0f);
                uvs[o + 1] = new Vector2(1f, 0f);
                uvs[o + 2] = new Vector2(1f, 1f);
                uvs[o + 3] = new Vector2(0f, 1f);
                var t = i * 6;
                triangles[t] = o; triangles[t + 1] = o + 1; triangles[t + 2] = o + 2;
                triangles[t + 3] = o; triangles[t + 4] = o + 2; triangles[t + 5] = o + 3;
            }
            mesh.vertices = vertices;
            mesh.uv = uvs;
            mesh.triangles = triangles;
            mesh.RecalculateNormals();
            mesh.RecalculateBounds();
            EditorUtility.SetDirty(mesh);
            return mesh;
        }

        private static string ProjectRoot => Path.GetDirectoryName(Application.dataPath)!;
    }
}
