#if DTS_UNITY_IAP
using System;
using UnityEngine;
using UnityEngine.Purchasing;
using UnityEngine.Purchasing.Extension;

namespace DribbleToSchool.Store
{
    /// <summary>
    /// Unity IAP (com.unity.purchasing 4.x) adapter. Enabled by adding the
    /// scripting define DTS_UNITY_IAP after installing the package
    /// (see docs/RELEASE.md). Not compiled otherwise.
    /// </summary>
    public class UnityIapStore : IStoreService, IDetailedStoreListener
    {
        IStoreController controller;
        IExtensionProvider extensions;
        Action<bool> onReady;
        Action<PurchaseResult> pending;

        public bool IsReady { get { return controller != null; } }

        public void Initialize(Action<bool> ready)
        {
            onReady = ready;
            var builder = ConfigurationBuilder.Instance(StandardPurchasingModule.Instance());
            builder.AddProduct(Monetization.FullGameProductId, ProductType.NonConsumable);
            UnityPurchasing.Initialize(this, builder);
        }

        public string PriceOf(string productId)
        {
            var p = controller != null ? controller.products.WithID(productId) : null;
            return p != null && p.availableToPurchase ? p.metadata.localizedPriceString : null;
        }

        public bool Owns(string productId)
        {
            var p = controller != null ? controller.products.WithID(productId) : null;
            return p != null && p.hasReceipt;
        }

        public void Purchase(string productId, Action<PurchaseResult> onDone)
        {
            if (controller == null) { if (onDone != null) onDone(PurchaseResult.Unavailable); return; }
            pending = onDone;
            controller.InitiatePurchase(productId);
        }

        public void Restore(Action<bool> onDone)
        {
            if (extensions == null) { if (onDone != null) onDone(false); return; }
#if UNITY_IOS
            extensions.GetExtension<IAppleExtensions>().RestoreTransactions((ok, message) => { if (onDone != null) onDone(ok); });
#else
            if (onDone != null) onDone(true);   // Google Play restores automatically on init.
#endif
        }

        public void OnInitialized(IStoreController c, IExtensionProvider e)
        {
            controller = c;
            extensions = e;
            if (Owns(Monetization.FullGameProductId)) StoreService.GrantFullGame();
            if (onReady != null) onReady(true);
        }

        public void OnInitializeFailed(InitializationFailureReason error) { OnInitializeFailed(error, null); }

        public void OnInitializeFailed(InitializationFailureReason error, string message)
        {
            Debug.LogWarning("[IAP] Init failed: " + error + " " + message);
            if (onReady != null) onReady(false);
        }

        public PurchaseProcessingResult ProcessPurchase(PurchaseEventArgs args)
        {
            if (args.purchasedProduct.definition.id == Monetization.FullGameProductId) StoreService.GrantFullGame();
            var done = pending;
            pending = null;
            if (done != null) done(PurchaseResult.Success);
            return PurchaseProcessingResult.Complete;
        }

        public void OnPurchaseFailed(Product product, PurchaseFailureReason reason)
        {
            var done = pending;
            pending = null;
            if (done != null) done(reason == PurchaseFailureReason.UserCancelled ? PurchaseResult.Cancelled : PurchaseResult.Failed);
        }

        public void OnPurchaseFailed(Product product, PurchaseFailureDescription description)
        {
            OnPurchaseFailed(product, description.reason);
        }
    }
}
#endif
