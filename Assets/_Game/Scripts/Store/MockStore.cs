using System;
using UnityEngine;

namespace DribbleToSchool.Store
{
    /// <summary>
    /// Stand-in store used until Unity IAP is enabled: purchases succeed
    /// instantly in the editor and development builds, and report Unavailable
    /// in release builds (so a misconfigured release can't give things away
    /// silently or lock players out with fake prompts).
    /// </summary>
    public class MockStore : IStoreService
    {
        public bool IsReady { get; private set; }

        static bool DevMode { get { return Application.isEditor || Debug.isDebugBuild; } }

        public void Initialize(Action<bool> onReady)
        {
            IsReady = true;
            if (onReady != null) onReady(true);
        }

        public string PriceOf(string productId) { return DevMode ? "$0.00 (test)" : null; }

        public bool Owns(string productId)
        {
            return productId == Monetization.FullGameProductId && Progression.SaveSystem.Data.fullGameUnlocked;
        }

        public void Purchase(string productId, Action<PurchaseResult> onDone)
        {
            if (!DevMode)
            {
                if (onDone != null) onDone(PurchaseResult.Unavailable);
                return;
            }
            Debug.Log("[MockStore] Test purchase of " + productId);
            if (onDone != null) onDone(PurchaseResult.Success);
        }

        public void Restore(Action<bool> onDone)
        {
            if (onDone != null) onDone(true);
        }
    }
}
