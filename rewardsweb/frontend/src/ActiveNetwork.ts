import { NetworkId, WalletManager } from "@txnlab/use-wallet";

/**
 * ActiveNetwork class manages network selection and display in the UI.
 *
 * This class handles binding to DOM elements, rendering the current active network,
 * and providing click handlers for network selection. It also synchronizes
 * network changes with the backend server.
 *
 * @example
 * ```typescript
 * const activeNetwork = new ActiveNetwork(walletManager)
 * activeNetwork.bind(document.getElementById('network-selector'))
 * ```
 */
export class ActiveNetwork {
  private element: HTMLElement | null = null;
  private unsubscribe: (() => void) | null = null;

  /**
   * Creates an instance of ActiveNetwork.
   *
   * @param manager - The WalletManager instance for wallet and network operations
   */
  constructor(private manager: WalletManager) {}

  /**
   * Binds the ActiveNetwork instance to a DOM element.
   *
   * Sets up event listeners and subscribes to wallet manager state changes.
   * The element should contain network selection buttons with data-network attributes.
   *
   * @param element - The HTMLElement to bind network controls to
   * @throws {Error} If the element is null or invalid
   */
  bind(element: HTMLElement) {
    this.element = element;
    this.unsubscribe = this.manager.subscribe((state) => {
      this.render(state.activeNetwork);
    });
    this.element.addEventListener("click", this.handleClick);
    this.render(this.manager.activeNetwork);
  }

  /**
   * Handles click events on network selection buttons.
   *
   * Updates the active network in the wallet manager and sends the change
   * to the backend server via API call.
   *
   * @param e - The click event
   * @private
   */
  private handleClick = async (e: Event) => {
    const btn = e.target as HTMLElement;
    const network = btn.dataset.network as NetworkId;

    if (!network) return;

    this.manager.setActiveNetwork(network);

    try {
      const csrfToken = this.getCsrfToken();
      await fetch("/api/wallet/active-network/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({ network }),
      });
    } catch (error) {
      console.error("Error setting active network:", error);
    }
  };

  /**
   * Renders the current active network state in the UI.
   *
   * Updates the network display text and toggles disabled state
   * on network selection buttons.
   *
   * @param activeNetwork - The currently active network ID or null if none
   * @private
   */
  private render(activeNetwork: string | null) {
    if (!this.element) return;

    const networkSpan = this.element.querySelector("#network-name");
    if (networkSpan) {
      networkSpan.textContent = activeNetwork || "none";
    }

    const buttons = this.element.querySelectorAll("button");
    buttons.forEach((btn) => {
      if (btn.dataset.network === activeNetwork) {
        btn.classList.add("disabled");
      } else {
        btn.classList.remove("disabled");
      }
    });
  }

  /**
   * Retrieves the CSRF token from cookies for API requests.
   *
   * @returns The CSRF token as a string
   * @private
   */
  private getCsrfToken(): string {
    const csrfCookie = document.cookie
      .split(";")
      .find((c) => c.trim().startsWith("csrftoken="));
    return csrfCookie ? csrfCookie.split("=")[1] : "";
  }

  /**
   * Cleans up event listeners and subscriptions.
   *
   * Should be called when the ActiveNetwork instance is no longer needed
   * to prevent memory leaks and unwanted behavior.
   */
  destroy() {
    if (this.unsubscribe) {
      this.unsubscribe();
      this.unsubscribe = null; // Prevent multiple calls
    }
    if (this.element) {
      this.element.removeEventListener("click", this.handleClick);
      // Don't nullify element as it might be needed for other cleanup
    }
  }
}
