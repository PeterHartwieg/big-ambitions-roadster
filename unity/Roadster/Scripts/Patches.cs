#nullable enable
using System;
using System.Reflection;
using Buildings;
using Dialogs;
using HarmonyLib;

namespace Roadster
{
    // Harmony patches. Each one logs an Active or Not active line at startup.
    internal static class Patches
    {
        private const string HarmonyId = "roadster.mod";
        private static Harmony? harmony;

        public static void Apply()
        {
            if (harmony != null) return;
            harmony = new Harmony(HarmonyId);
            Log.Info($"Harmony {typeof(Harmony).Assembly.GetName().Version}.");
            // Dealer: list the Roadster next to the vanilla stock at one dealer with a spawn point.
            Patch(typeof(VehicleContractSettings), "SetListOfVehiclesForSale", nameof(DealerStock));
        }

        public static void Remove()
        {
            harmony?.UnpatchAll(HarmonyId);
            harmony = null;
        }

        private static void Patch(Type type, string method, string postfix)
        {
            var target = AccessTools.Method(type, method, Type.EmptyTypes);
            if (target == null)
            {
                Log.Error($"Not active: {type.Name}.{method} (method not found).");
                return;
            }
            harmony!.Patch(target, postfix: new HarmonyMethod(typeof(Patches), postfix));
            Log.Info($"Active: {type.Name}.{method}.");
        }

        private static MethodInfo? addVehicle;

        // General US Trucks, 1 7th Avenue, the dealer the Food Trucks mod uses: a vehicle without a showcase model
        // needs the spawn point it has (ContractVehicleForSale.Purchase takes the building's first custom position).
        // Phase 0 only; a sports car dealer with a showcase comes with the model.
        private const string DealerStreet = "ba:street_seventhavenue";
        private const int DealerNumber = 1;

        private static void DealerStock(VehicleContractSettings __instance)
        {
            try
            {
                var dialog = DialogController.current;
                var address = dialog?.contact?.Address;
                if (dialog == null || dialog.dialogType != DialogType.Physical || address == null) return;
                if (address.streetName != DealerStreet || address.streetNumber != DealerNumber) return;
                addVehicle ??= AccessTools.Method(typeof(VehicleContractSettings), "TryAddVehicleByVehicleType");
                if (addVehicle == null || !RoadsterMod.Registered) return;
                addVehicle.Invoke(__instance, new object?[] { RoadsterMod.TypeName, null });
            }
            catch (Exception ex) { Log.Error(ex.ToString()); }
        }
    }
}
