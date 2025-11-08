import * as algosdk from "algosdk";

jest.mock("@txnlab/use-wallet", () => ({
  BaseWallet: jest.fn(),
  WalletId: {
    PERA: "pera",
    DEFLY: "defly",
    LUTE: "lute",
  },
  WalletManager: jest.fn(),
}));

import { WalletComponent } from "./WalletComponent";
import { BaseWallet, WalletManager, WalletId } from "@txnlab/use-wallet";

// Mock algosdk functions at the module level
jest.mock("algosdk", () => {
  const originalModule = jest.requireActual("algosdk");
  return {
    ...originalModule,
    isValidAddress: jest.fn().mockReturnValue(true),
    AtomicTransactionComposer: jest.fn(() => ({
      addTransaction: jest.fn(),
      execute: jest.fn().mockResolvedValue({
        confirmedRound: 1234,
        txIDs: ["test-tx-id"],
      }),
    })),
    makePaymentTxnWithSuggestedParamsFromObject: jest.fn().mockReturnValue({
      type: "pay",
      from: "test-address",
      to: "test-address",
      amount: 0,
    }),
    encodeUnsignedTransaction: jest
      .fn()
      .mockReturnValue(new Uint8Array([1, 2, 3])),
  };
});

describe("WalletComponent", () => {
  let mockWallet: jest.Mocked<BaseWallet>;
  let mockManager: jest.Mocked<WalletManager>;
  let walletComponent: WalletComponent;
  let element: HTMLElement;
  let consoleErrorSpy: jest.SpyInstance; // Declare consoleErrorSpy here

  beforeEach(() => {
    jest.clearAllMocks();

    mockWallet = {
      id: "pera",
      metadata: { name: "Pera Wallet" },
      isConnected: false,
      isActive: false,
      accounts: [],
      activeAccount: null,
      connect: jest.fn(),
      disconnect: jest.fn(),
      setActive: jest.fn(),
      setActiveAccount: jest.fn(),
      subscribe: jest.fn(() => () => {}),
      transactionSigner: jest.fn(),
      signTransactions: jest
        .fn()
        .mockResolvedValue([new Uint8Array([1, 2, 3])]),
      canSignData: true,
    } as any;

    mockManager = {
      algodClient: {
        getTransactionParams: jest.fn().mockReturnValue({
          do: jest.fn().mockResolvedValue({
            fee: 1000,
            firstRound: 1000,
            lastRound: 2000,
            genesisID: "testnet-v1.0",
            genesisHash: "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI=",
          }),
        }),
      },
    } as any;

    // Mock document.cookie and CSRF token
    Object.defineProperty(document, "cookie", {
      writable: true,
      value: "csrftoken=test-csrf-token",
    });
    document.body.innerHTML =
      '<input name="csrfmiddlewaretoken" value="test-csrf-token" />';

    walletComponent = new WalletComponent(mockWallet, mockManager);

    // Create a mock DOM element for binding
    element = document.createElement("div"); // Initialize element here
    element.id = `wallet-${mockWallet.id}`;
    element.innerHTML = `
      <h4 id="wallet-name-${mockWallet.id}">${mockWallet.metadata.name}</h4>
      <div id="wallet-accounts-${mockWallet.id}"></div>
      <div id="wallet-balance-${mockWallet.id}"></div>
      <div id="wallet-status-${mockWallet.id}"></div>
      <div id="wallet-error-${mockWallet.id}"></div>
      <button id="connect-button-${mockWallet.id}"></button>
      <button id="disconnect-button-${mockWallet.id}"></button>
      <button id="set-active-button-${mockWallet.id}"></button>
      <button id="transaction-button-${mockWallet.id}"></button>
      <button id="auth-button-${mockWallet.id}"></button>
      <select id="account-select-${mockWallet.id}"></select>
    `;
    document.body.appendChild(element);
    walletComponent.bind(element);

    // Spy on dispatchEvent after binding
    jest.spyOn(element, "dispatchEvent");
    jest.spyOn(document.body, "dispatchEvent");
    consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    walletComponent.destroy();
    document.body.innerHTML = "";
    jest.resetModules();
    consoleErrorSpy.mockRestore();
  });

  describe("Constructor and Binding", () => {
    it("should initialize with wallet and manager", () => {
      expect(walletComponent.wallet).toBe(mockWallet);
      expect(walletComponent.manager).toBe(mockManager);
    });

    it("should subscribe to wallet state changes", () => {
      expect(mockWallet.subscribe).toHaveBeenCalledTimes(1);
    });

    it("should bind event listeners to the provided element", () => {
      const addEventListenerSpy = jest.spyOn(element, "addEventListener");
      const newElement = document.createElement("div");
      newElement.id = `wallet-${mockWallet.id}`;
      newElement.innerHTML = `
        <button id="connect-button-${mockWallet.id}"></button>
        <button id="disconnect-button-${mockWallet.id}"></button>
        <button id="set-active-button-${mockWallet.id}"></button>
        <button id="transaction-button-${mockWallet.id}"></button>
        <button id="auth-button-${mockWallet.id}"></button>
        <select id="account-select-${mockWallet.id}"></select>
      `;
      document.body.appendChild(newElement);
      walletComponent.bind(newElement);
      expect(addEventListenerSpy).toHaveBeenCalledWith(
        "click",
        expect.any(Function)
      );
      expect(addEventListenerSpy).toHaveBeenCalledWith(
        "change",
        expect.any(Function)
      );
      document.body.removeChild(newElement);
    });
  });

  describe("Event Handling", () => {
    it("should call connect on connect button click", async () => {
      const connectButton = element.querySelector(
        `#connect-button-${mockWallet.id}`
      ) as HTMLButtonElement;
      await connectButton.click();
      expect(mockWallet.connect).toHaveBeenCalledTimes(1);
    });

    it("should call disconnect on disconnect button click", async () => {
      const disconnectButton = element.querySelector(
        `#disconnect-button-${mockWallet.id}`
      ) as HTMLButtonElement;
      await disconnectButton.click();
      expect(mockWallet.disconnect).toHaveBeenCalledTimes(1);
    });

    it("should call setActive on set active button click", async () => {
      const setActiveButton = element.querySelector(
        `#set-active-button-${mockWallet.id}`
      ) as HTMLButtonElement;
      await setActiveButton.click();
      expect(mockWallet.setActive).toHaveBeenCalledTimes(1);
      expect(document.body.dispatchEvent).toHaveBeenCalledWith(
        expect.objectContaining({ type: "walletChanged" })
      );
    });

    it("should call sendTransaction on transaction button click", async () => {
      mockWallet.activeAccount = { address: "test-address" };
      const transactionButton = element.querySelector(
        `#transaction-button-${mockWallet.id}`
      ) as HTMLButtonElement;
      await transactionButton.click();
      expect(mockWallet.transactionSigner).toHaveBeenCalled();
    });

    it("should call auth on auth button click", async () => {
      mockWallet.activeAccount = { address: "test-address" };
      const authButton = element.querySelector(
        `#auth-button-${mockWallet.id}`
      ) as HTMLButtonElement;

      // Mock fetch for auth process
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: () =>
            Promise.resolve({
              nonce: "test-nonce",
              prefix: "test-prefix",
              error: null,
            }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () =>
            Promise.resolve({
              success: true,
              redirect_url: "/dashboard",
              error: null,
            }),
        });

      await authButton.click();
      expect(mockWallet.signTransactions).toHaveBeenCalled();
    });

    it("should call setActiveAccount on select change", async () => {
      const selectElement = element.querySelector(
        `#account-select-${mockWallet.id}`
      ) as HTMLSelectElement;
      selectElement.innerHTML = `<option value="new-address">new-address</option>`;
      selectElement.value = "new-address";
      await selectElement.dispatchEvent(new Event("change"));
      expect(mockWallet.setActiveAccount).toHaveBeenCalledWith("new-address");
    });
  });

  describe("Error Handling in Auth", () => {
    beforeEach(() => {
      mockWallet.activeAccount = { address: "test-address" };
      jest.spyOn(element, "dispatchEvent"); // Spy on dispatchEvent
    });

    it("should display error message on auth failure", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ error: "Auth failed" }),
      });

      await walletComponent.auth();

      const errorDiv = element.querySelector(`#wallet-error-${mockWallet.id}`);
      expect(errorDiv).toBeTruthy();
      expect(errorDiv?.textContent).toContain("Auth failed");
    });

    it("should remove error message after timeout", async () => {
      jest.useFakeTimers();
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ error: "Auth failed" }),
      });

      await walletComponent.auth();

      const errorDiv = element.querySelector(`#wallet-error-${mockWallet.id}`);
      expect(errorDiv).toBeTruthy();

      jest.runAllTimers();

      expect(element.querySelector(`#wallet-error-${mockWallet.id}`)).toBeFalsy();
      jest.useRealTimers();
    });
  });

  describe("Destroy", () => {
    it("should unsubscribe from wallet and remove event listeners", () => {
      const unsubscribeSpy = jest.fn();
      mockWallet.subscribe.mockReturnValue(unsubscribeSpy);

      const wc = new WalletComponent(mockWallet, mockManager);
      const el = document.createElement("div");
      el.id = `wallet-${mockWallet.id}`;
      el.innerHTML = `
        <h4 id="wallet-name-${mockWallet.id}">${mockWallet.metadata.name}</h4>
        <div id="wallet-accounts-${mockWallet.id}"></div>
        <div id="wallet-balance-${mockWallet.id}"></div>
        <div id="wallet-status-${mockWallet.id}"></div>
        <div id="wallet-error-${mockWallet.id}"></div>
        <button id="connect-button-${mockWallet.id}"></button>
        <button id="disconnect-button-${mockWallet.id}"></button>
        <button id="set-active-button-${mockWallet.id}"></button>
        <button id="transaction-button-${mockWallet.id}"></button>
        <button id="auth-button-${mockWallet.id}"></button>
        <select id="account-select-${mockWallet.id}"></select>
      `;
      document.body.appendChild(el);
      wc.bind(el);

      const removeEventListenerSpy = jest.spyOn(el, "removeEventListener");

      wc.destroy();

      expect(unsubscribeSpy).toHaveBeenCalledTimes(1);
      expect(removeEventListenerSpy).toHaveBeenCalledWith(
        "click",
        expect.any(Function)
      );
      expect(removeEventListenerSpy).toHaveBeenCalledWith(
        "change",
        expect.any(Function)
      );
      document.body.removeChild(el);
    });

    it("should handle destroy gracefully if element is null", () => {
      const unsubscribeSpy = jest.fn();
      mockWallet.subscribe.mockReturnValue(unsubscribeSpy);

      const wc = new WalletComponent(mockWallet, mockManager);
      // Do not bind element, so it remains null

      expect(() => wc.destroy()).not.toThrow();
      expect(unsubscribeSpy).toHaveBeenCalledTimes(1);
    });
  });
});