#nullable enable
using System.Threading.Tasks;
using BAModAPI;
using BAModAPI.Services;
using UnityEngine;
using Vehicles.VehicleTypes;

[assembly: RegisterModClass(typeof(Roadster.RoadsterMod))]

namespace Roadster
{
    // Loads once at game start: the vehicle type, the dealer patch and the driving controller.
    [ModEntryOnInitializationLoad]
    public sealed class RoadsterMod : IModBigAmbitions
    {
        public const string Version = "0.0.3";
        internal const string BundleKey = "AssetBundles/roadster.unity3d";
        internal const string TypeName = "roadster:vehicletype_roadster";
        private const string TypeAssetPath = "Assets/Mods/Roadster/Vehicles/Roadster.asset";

        internal static bool Registered { get; private set; }

        private GameObject? driver;

        public string[] RelativeAssetBundlePaths => new[] { BundleKey };

        public Task OnLoadAsync(ModContext context)
        {
            Log.Init(context.Logger);
            Log.Info($"Version {Version} loading.");

            var bundle = AssetService.GetBundle(context.ModId, BundleKey);
            var type = bundle == null ? null : bundle.LoadAsset<VehicleType>(TypeAssetPath);
            if (type == null)
            {
                Log.Error($"Vehicle type '{TypeAssetPath}' not found in '{BundleKey}'; nothing registered.");
                return Task.CompletedTask;
            }
            Registered = ModdingAPI.RegisterModVehicleType(type);
            if (!Registered)
            {
                Log.Error($"Vehicle registration refused: {TypeName}.");
                return Task.CompletedTask;
            }
            Log.Info($"Vehicle registered: {TypeName} (price {type.price}).");

            Patches.Apply();
            driver = new GameObject("Roadster drive");
            Object.DontDestroyOnLoad(driver);
            driver.AddComponent<RoadsterDrive>();
            return Task.CompletedTask;
        }

        public Task OnUnloadAsync()
        {
            if (driver != null) Object.Destroy(driver);
            driver = null;
            Patches.Remove();
            if (Registered) ModdingAPI.UnregisterModVehicleType(TypeName);
            Registered = false;
            return Task.CompletedTask;
        }
    }

    internal static class Log
    {
        private static IModLogger? logger;

        public static void Init(IModLogger modLogger) => logger = modLogger;

        // The game's mod logger adds its own "[Mod:Roadster]" prefix.
        public static void Info(string message)
        {
            if (logger != null) logger.Info(message);
            else Debug.Log("[Roadster] " + message);
        }

        public static void Error(string message)
        {
            if (logger != null) logger.Error(message);
            else Debug.LogError("[Roadster] " + message);
        }
    }
}
