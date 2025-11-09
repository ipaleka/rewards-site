import { BaseWallet, WalletManager } from "@txnlab/use-wallet";
import {
  AtomicTransactionComposer,
  makePaymentTxnWithSuggestedParamsFromObject,
  encodeUnsignedTransaction,
  isValidAddress,
} from "algosdk";

/**
 * Component for managing individual wallet connections and interactions.
 * 
 * Handles the UI and logic for connecting/disconnecting wallets, setting
 * active accounts, sending transactions, and authentication. Each wallet
 * instance gets its own WalletComponent.
 * 
 * @example
 * ```typescript
 * const walletComponent = new WalletComponent(wallet, walletManager)
 * walletComponent.bind(document.getElementById('wallet-pera'))
 * ```
 */
export class WalletComponent {
  /** The wallet instance this component manages */
  wallet: BaseWallet;
  /** The wallet manager for broader wallet state management */
  manager: WalletManager;
  private unsubscribe?: () => void;
  private element: HTMLElement | null = null;

  /**
   * Creates an instance of WalletComponent.
   *
   * @param wallet - The wallet instance to manage
   * @param manager - The wallet manager for broader state management
   */
  constructor(wallet: BaseWallet, manager: WalletManager) {
    this.wallet = wallet;
    this.manager = manager;
    this.unsubscribe = wallet.subscribe(() => {
      console.info(`[${this.wallet.metadata.name}] State change detected. New state:`, this.wallet);
      this.render(this.wallet as any);
    });
  }

  /**
   * Binds the component to a DOM element and initializes event listeners.
   *
   * @param element - The HTML element to bind the component to
   */
  bind(element: HTMLElement) {
    this.element = element;
    this.addEventListeners();
    this.render(this.wallet as any);
  }

  /**
   * Renders the current wallet state to the UI.
   *
   * Updates button visibility, active status badges, and account dropdown
   * based on the wallet's connection and active state.
   *
   * @param state - The current wallet state
   * @private
   */
  private render(state: { isConnected: boolean, isActive: boolean, accounts: any[], activeAccount: any }) {
    /* istanbul ignore next */
    if (!this.element) return;

    const { isConnected, isActive, accounts, activeAccount } = state;

    const connectBtn = this.element.querySelector<HTMLButtonElement>(`#connect-button-${this.wallet.id}`)!;
    const disconnectBtn = this.element.querySelector<HTMLButtonElement>(`#disconnect-button-${this.wallet.id}`)!;
    const setActiveBtn = this.element.querySelector<HTMLButtonElement>(`#set-active-button-${this.wallet.id}`)!;
    const authBtn = this.element.querySelector<HTMLButtonElement>(`#auth-button-${this.wallet.id}`)!;
    const txnBtn = this.element.querySelector<HTMLButtonElement>(`#transaction-button-${this.wallet.id}`)!;
    const accountSelect = this.element.querySelector<HTMLSelectElement>('select')!;
    const nameHeader = this.element.querySelector<HTMLHeadingElement>('h4')!;

    // Toggle button visibility and state
    connectBtn.style.display = isConnected ? 'none' : 'block';
    disconnectBtn.style.display = isConnected ? 'block' : 'none';
    setActiveBtn.style.display = isConnected && !isActive ? 'block' : 'none';
    authBtn.style.display = isConnected && isActive ? 'block' : 'none';
    txnBtn.style.display = isConnected && isActive ? 'block' : 'none';

    // Active badge
    let activeBadge = nameHeader.querySelector('.badge');
    if (isActive && !activeBadge) {
      activeBadge = document.createElement('span');
      activeBadge.className = 'badge badge-success';
      activeBadge.textContent = 'Active';
      nameHeader.appendChild(activeBadge);
    } else if (!isActive && activeBadge) {
      activeBadge.remove();
    }

    // Accounts dropdown
    if (isConnected) {
      accountSelect.innerHTML = '';
      if (accounts.length > 0) {
        accounts.forEach(account => {
          const option = document.createElement('option');
          option.value = account.address;
          option.textContent = `${account.address.substring(0, 6)}...${account.address.substring(account.address.length - 6)}`;
          option.selected = account.address === activeAccount?.address;
          accountSelect.appendChild(option);
        });
      } else {
        const option = document.createElement('option');
        option.textContent = 'No accounts';
        option.disabled = true;
        accountSelect.appendChild(option);
      }
    } else {
      accountSelect.innerHTML = '';
      const option = document.createElement('option');
      option.textContent = 'No accounts';
      option.disabled = true;
      accountSelect.appendChild(option);
    }
  }

  /**
   * Connects the wallet.
   *
   * Initiates the wallet connection process.
   */
  connect = async () => {
    await this.wallet?.connect();
  };

  /**
   * Disconnects the wallet.
   *
   * Terminates the wallet connection and clears session data.
   */
  disconnect = async () => {
    await this.wallet?.disconnect();
  };

  /**
   * Sets this wallet as the active wallet.
   *
   * Makes this wallet the primary wallet for transactions and operations.
   */
  setActive = async () => {
    await this.wallet?.setActive();
  };

  /**
   * Sends a test transaction using the wallet.
   *
   * Creates and sends a zero-amount payment transaction to the active account
   * as a test of transaction signing capabilities.
   */
  sendTransaction = async () => {
    const txnButton = this.element?.querySelector(
      `#transaction-button-${this.wallet.id}`
    ) as HTMLButtonElement;
    /* istanbul ignore next */
    if (!txnButton) return;

    try {
      const activeAddress = this.wallet?.activeAccount?.address;
      if (!activeAddress) {
        throw new Error("[App] No active account");
      }

      if (!isValidAddress(activeAddress)) {
        throw new Error(`[App] Invalid address format: ${activeAddress}`);
      }

      const atc = new AtomicTransactionComposer();
      const suggestedParams = await this.manager.algodClient
        .getTransactionParams()
        .do();
      const transaction = makePaymentTxnWithSuggestedParamsFromObject({
        sender: activeAddress,
        receiver: activeAddress,
        amount: 0,
        suggestedParams,
      });

      atc.addTransaction({
        txn: transaction,
        signer: this.wallet.transactionSigner,
      });
      console.info(`[App] Sending transaction...`, transaction);

      txnButton.disabled = true;
      txnButton.textContent = "Sending Transaction...";

      const result = await atc.execute(this.manager.algodClient, 4);
      console.info(`[App] ✅ Successfully sent transaction!`, {
        confirmedRound: result.confirmedRound,
        txIDs: result.txIDs,
      });
    } catch (error) {
      console.error("[App] Error signing transaction:", error);
    } finally {
      txnButton.disabled = false;
      txnButton.textContent = "Send Transaction";
    }
  };

  /**
   * Authenticates the user with the backend using wallet signing.
   *
   * Performs a cryptographic authentication flow:
   * 1. Fetches a nonce from the backend
   * 2. Signs the nonce with the wallet
   * 3. Verifies the signature with the backend
   * 4. Redirects on successful authentication
   */
  auth = async (nextUrl?: string) => {
    try {
      const activeAddress = this.wallet?.activeAccount?.address;
      if (!activeAddress || !isValidAddress(activeAddress)) {
        throw new Error(
          `[App] Invalid or missing address: ${activeAddress || "undefined"}` 
        );
      }
      console.info(`[App] Authenticating with address: ${activeAddress}`);

      const getCsrfToken = () => {
        const name = "csrftoken";
        const cookieValue =
          document.cookie
            .match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)")
            ?.pop() || "";
        return (
          cookieValue ||
          (
            document.querySelector(
              'input[name="csrfmiddlewaretoken"]'
            ) as HTMLInputElement
          )?.value ||
          ""
        );
      };
      const headers = {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      };

      console.info("[App] Fetching nonce for address:", activeAddress);
      const nonceResponse = await fetch("/api/wallet/nonce/", {
        method: "POST",
        headers,
        body: JSON.stringify({ address: activeAddress }),
      });
      const nonceData = await nonceResponse.json();
      if (nonceData.error) {
        throw new Error(`[App] Failed to fetch nonce: ${nonceData.error}`);
      }
      const nonce = nonceData.nonce;
      const prefix = nonceData.prefix;
      console.info("[App] Received nonce:", nonce);

      const message = `${prefix}${nonce}`;
      const note = new TextEncoder().encode(message);
      const suggestedParams = await this.manager.algodClient
        .getTransactionParams()
        .do();
      const transaction = makePaymentTxnWithSuggestedParamsFromObject({
        sender: activeAddress,
        receiver: activeAddress,
        amount: 0,
        note,
        suggestedParams,
      });
      const encodedTx = encodeUnsignedTransaction(transaction);
      console.info("[App] Client encodedTx:", Array.from(encodedTx));
      console.info("[App] Signing transaction with note:", message);
      const signedTxs = await this.wallet.signTransactions([encodedTx]);

      if (!signedTxs[0]) {
        throw new Error("[App] No signed transaction returned");
      }
      const signedTxBytes = signedTxs[0];
      const signedTxBase64 = btoa(String.fromCharCode(...signedTxBytes));
      console.info(
        "[App] Signed transaction base64 length:",
        signedTxBase64.length
      );

      const body: {
        address: string;
        signedTransaction: string;
        nonce: string;
        next?: string;
      } = {
        address: activeAddress,
        signedTransaction: signedTxBase64,
        nonce,
      };

      if (nextUrl) {
        body.next = nextUrl;
      }

      const verifyResponse = await fetch("/api/wallet/verify/", {
        method: "POST",
        headers,
        body: JSON.stringify(body),
      });
      const verifyData = await verifyResponse.json();
      if (!verifyData.success) {
        throw new Error(`[App] Verification failed: ${verifyData.error}`);
      }

      console.info(
        `[App] ✅ Successfully authenticated with ${this.wallet.metadata.name}!`
      );
      /* istanbul ignore next */
      window.location.href = verifyData.redirect_url || "/"; 

    } catch (error: unknown) {
      /* istanbul ignore next */
      const errorMessage = error instanceof Error ? error.message : String(error); 
      console.error("[App] Error signing data:", error);
      if (this.element) {
        const errorDiv = document.createElement("div");
        errorDiv.className = "alert alert-error mt-4";
        errorDiv.textContent = errorMessage;
        this.element.appendChild(errorDiv);
        setTimeout(() => errorDiv.remove(), 5000);
      }
    }
  };

  /**
   * Sets the active account for the wallet.
   *
   * @param event - The change event from the account selection dropdown
   */
  setActiveAccount = async (event: Event) => {
    const target = event.target as HTMLSelectElement;
    await this.wallet?.setActiveAccount(target.value);
  };

  /**
   * Adds event listeners for user interactions.
   *
   * Handles clicks on connection buttons and changes to account selection.
   *
   * @private
   */
  addEventListeners() {
    /* istanbul ignore next */
    if (!this.element) return;

    this.element.addEventListener("click", async (e: Event) => {
      const target = e.target as HTMLElement;
      if (target.id === `connect-button-${this.wallet.id}`) {
        await this.connect();
      } else if (target.id === `disconnect-button-${this.wallet.id}`) {
        await this.disconnect();
      } else if (target.id === `set-active-button-${this.wallet.id}`) {
        await this.setActive();
      } else if (target.id === `transaction-button-${this.wallet.id}`) {
        await this.sendTransaction();
      } else if (target.id === `auth-button-${this.wallet.id}`) {
        const nextUrl = target.dataset.nextUrl;
        await this.auth(nextUrl);
      }
    });

    this.element.addEventListener("change", async (e: Event) => {
      const target = e.target as HTMLElement;
      if (target.tagName.toLowerCase() === "select") {
        await this.setActiveAccount(e);
      }
    });
  }

  /**
   * Cleans up the component by removing event listeners and subscriptions.
   *
   * Should be called when the component is no longer needed to prevent
   * memory leaks and unwanted behavior.
   */
  destroy() {
    if (this.unsubscribe) {
      this.unsubscribe();
    }
    if (this.element) {
      try {
        this.element.removeEventListener("click", this.addEventListeners as EventListener);
        this.element.removeEventListener("change", this.addEventListeners as EventListener);
      } catch (error) {
        console.debug(
          "[WalletComponent] Error during event listener cleanup:",
          error
        );
      }
    }
  }
}
