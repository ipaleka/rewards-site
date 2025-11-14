import { RewardsClient } from "./RewardsClient";
import { WalletManager } from "@txnlab/use-wallet";

/**
 * Component for handling reward claim operations.
 *
 * Manages the logic for submitting claim transactions to the blockchain.
 * No longer handles UI rendering - relies on Django template for initial state.
 *
 * @example
 * ```typescript
 * const claimComponent = new ClaimComponent(rewardsClient, walletManager)
 * claimComponent.bind(document.getElementById('claim-container'))
 * ```
 */
export class ClaimComponent {
  private element: HTMLElement | null = null;
  private rewardsClient: RewardsClient;
  private walletManager: WalletManager;

  /**
   * Creates an instance of ClaimComponent.
   *
   * @param rewardsClient - The client for interacting with rewards contract and API
   * @param walletManager - The wallet manager for account and network state
   */
  constructor(rewardsClient: RewardsClient, walletManager: WalletManager) {
    this.rewardsClient = rewardsClient;
    this.walletManager = walletManager;
  }

  /**
   * Binds the component to a DOM element and initializes event listeners.
   *
   * @param element - The HTML element to bind the component to
   */
  bind(element: HTMLElement) {
    this.element = element;
    this.addEventListeners();
  }

  /**
   * Handles the claim transaction submission.
   *
   * Submits a claim transaction to the blockchain and notifies the backend
   * on success. Refreshes the page after successful claim to show updated state.
   *
   * @private
   */
  private async handleClaim() {
    try {
      console.info("[ClaimComponent] Initiating claim...");

      // Step 1: Call smart contract
      const txID = await this.rewardsClient.claimRewards();
      console.log("[DEBUG] claimRewards completed, txID:", txID);

      // Step 2: Notify backend (fail silently)
      try {
        const activeAddress = this.walletManager.activeAccount?.address;
        console.log("[DEBUG] Active address:", activeAddress);
        if (activeAddress) {
          await this.rewardsClient.userClaimed(activeAddress, txID);
          console.log("[DEBUG] userClaimed completed");
        }
      } catch (notificationError) {
        console.error("Backend notification failed:", notificationError);
        // Silently continue - the blockchain transaction succeeded
      }

      // Step 3: Reload to show updated state
      console.log("[DEBUG] About to call location.reload()");
      location.reload();
      console.log("[DEBUG] After location.reload()");
    } catch (error) {
      console.error("[ClaimComponent] Error during claim:", error);
      alert(
        `Claim failed: ${
          error instanceof Error ? error.message : String(error)
        }`
      );
    }
  }

  /**
   * Adds event listeners for user interactions.
   *
   * Listens for click events on the claim button.
   *
   * @private
   */
  private addEventListeners() {
    if (!this.element) return;

    this.element.addEventListener("click", (e: Event) => {
      const target = e.target as HTMLElement;

      // Check if the clicked element is a button and has the claim-button ID
      if (
        target.id === "claim-button" &&
        target instanceof HTMLButtonElement &&
        !target.disabled
      ) {
        this.handleClaim();
      }
    });
  }

  /**
   * Cleans up the component.
   *
   * Currently no specific cleanup needed, but provided for interface consistency.
   */
  destroy() {
    // No specific cleanup needed for now
  }
}
