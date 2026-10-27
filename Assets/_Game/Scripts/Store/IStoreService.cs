using System;

namespace DribbleToSchool.Store
{
    public enum PurchaseResult { Success, Cancelled, Failed, Unavailable }

    /// <summary>Platform store abstraction so the game never talks to a store SDK directly.</summary>
    public interface IStoreService
    {
        bool IsReady { get; }
        void Initialize(Action<bool> onReady);
        /// <summary>Localized price string, or null if unknown.</summary>
        string PriceOf(string productId);
        bool Owns(string productId);
        void Purchase(string productId, Action<PurchaseResult> onDone);
        /// <summary>Restore non-consumables (required on iOS).</summary>
        void Restore(Action<bool> onDone);
    }
}
