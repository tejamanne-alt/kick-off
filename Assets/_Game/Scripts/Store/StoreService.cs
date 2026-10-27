using System;
using DribbleToSchool.Core;
using UnityEngine;

namespace DribbleToSchool.Store
{
    /// <summary>Entry point for purchases. Picks Unity IAP when enabled, the mock store otherwise.</summary>
    public static class StoreService
    {
        static IStoreService service;

        public static IStoreService Instance
        {
            get
            {
                if (service == null)
                {
#if DTS_UNITY_IAP
                    service = new UnityIapStore();
#else
                    service = new MockStore();
#endif
                    service.Initialize(null);
                }
                return service;
            }
        }

        public static string FullGamePrice
        {
            get { return Instance.PriceOf(Monetization.FullGameProductId) ?? Monetization.FallbackPrice; }
        }

        public static void BuyFullGame(Action<PurchaseResult> onDone)
        {
            Instance.Purchase(Monetization.FullGameProductId, result =>
            {
                if (result == PurchaseResult.Success) GrantFullGame();
                Analytics.AnalyticsService.Track("purchase", "product", Monetization.FullGameProductId, "result", result.ToString());
                if (onDone != null) onDone(result);
            });
        }

        public static void Restore(Action<bool> onDone)
        {
            Instance.Restore(ok =>
            {
                if (Instance.Owns(Monetization.FullGameProductId)) GrantFullGame();
                if (onDone != null) onDone(ok);
            });
        }

        public static void GrantFullGame()
        {
            var data = Progression.SaveSystem.Data;
            if (data.fullGameUnlocked) return;
            data.fullGameUnlocked = true;
            Progression.SaveSystem.Save();
            GameEvents.Raise(GameEventType.Purchase, Vector2.zero);
        }
    }
}
