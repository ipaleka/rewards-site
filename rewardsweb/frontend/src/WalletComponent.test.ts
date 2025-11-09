/**
 * @jest-environment jsdom
 */

import { WalletComponent } from "./WalletComponent";
import { AtomicTransactionComposer, isValidAddress } from "algosdk";

// ─────────────────────────────────────────────────────────────
// FULL Mocks for algosdk
// ─────────────────────────────────────────────────────────────
jest.mock("algosdk", () => ({
  AtomicTransactionComposer: jest.fn().mockImplementation(() => ({
    addTransaction: jest.fn(),
    execute: jest.fn().mockResolvedValue({ confirmedRound: 999, txIDs: ["TX123"] }),
  })),
  makePaymentTxnWithSuggestedParamsFromObject: jest.fn(() => ({ txnMock: true })),
  encodeUnsignedTransaction: jest.fn(() => new Uint8Array([1, 2, 3])),
  isValidAddress: jest.fn(() => true),
}));

let unsubscribeMock = jest.fn();

const mockWallet: any = {
  id: "testwallet",
  metadata: { name: "TestWallet" },
  isConnected: false,
  isActive: false,
  accounts: [],
  activeAccount: null,

  subscribe: jest.fn(callback => {
    mockWallet._cb = callback;
    return unsubscribeMock;
  }),

  connect: jest.fn(),
  disconnect: jest.fn(),
  setActive: jest.fn(),
  setActiveAccount: jest.fn(),
  transactionSigner: jest.fn(),
  signTransactions: jest.fn(async () => [new Uint8Array([10, 11, 12])]),
};

const mockManager: any = {
  algodClient: {
    getTransactionParams: jest.fn().mockReturnValue({
      do: jest.fn().mockResolvedValue({ fee: 1000 }),
    }),
  },
};

// ─────────────────────────────────────────────────────────────
// DOM helper (matches component requirements)
// ─────────────────────────────────────────────────────────────
function setupDOM() {
  document.body.innerHTML = `
    <div id="wallet">
      <h4></h4>
      <button id="connect-button-testwallet"></button>
      <button id="disconnect-button-testwallet"></button>
      <button id="set-active-button-testwallet"></button>
      <button id="auth-button-testwallet"></button>
      <button id="transaction-button-testwallet"></button>
      <select></select>
    </div>
  `;
  return document.getElementById("wallet")!;
}

let component: WalletComponent;
let root: HTMLElement;

// ─────────────────────────────────────────────────────────────
// beforeEach – reset fresh environment
// ─────────────────────────────────────────────────────────────
beforeEach(() => {
  jest.clearAllMocks();
  unsubscribeMock = jest.fn();
  mockWallet.subscribe.mockImplementation(cb => {
    mockWallet._cb = cb;
    return unsubscribeMock;
  });
  root = setupDOM();
  component = new WalletComponent(mockWallet, mockManager);
  component.bind(root);
});

// ─────────────────────────────────────────────────────────────
// UI tests
// ─────────────────────────────────────────────────────────────
describe("WalletComponent DOM + UI State", () => {
  it("renders inactive state (shows connect button)", () => {
    mockWallet._cb(mockWallet);

    const connectBtn = root.querySelector("#connect-button-testwallet")!;
    const disconnectBtn = root.querySelector("#disconnect-button-testwallet")!;
    expect(connectBtn.style.display).toBe("block");
    expect(disconnectBtn.style.display).toBe("none");
  });

  it("connected + active state adds ACTIVE badge", () => {
    mockWallet.isConnected = true;
    mockWallet.isActive = true;
    mockWallet.accounts = [{ address: "ADDR123456789" }];
    mockWallet.activeAccount = mockWallet.accounts[0];
    mockWallet._cb(mockWallet);

    const badge = root.querySelector("h4 .badge");
    expect(badge).not.toBeNull();
    expect(badge?.textContent).toBe("Active");
  });

  it("connected + no accounts renders disabled <option>", () => {
    mockWallet.isConnected = true;
    mockWallet.accounts = [];
    mockWallet._cb(mockWallet);

    const option = root.querySelector("select option")!;
    expect(option.textContent).toBe("No accounts");
    expect(option.disabled).toBe(true);
  });
});

// ─────────────────────────────────────────────────────────────
// Actions (connect / disconnect / activate / dropdown)
// ─────────────────────────────────────────────────────────────
describe("WalletComponent interaction", () => {
  it("connect calls wallet.connect()", () => {
    root.querySelector("#connect-button-testwallet")!.click();
    expect(mockWallet.connect).toHaveBeenCalledTimes(1);
  });

  it("disconnect calls wallet.disconnect()", () => {
    root.querySelector("#disconnect-button-testwallet")!.click();
    expect(mockWallet.disconnect).toHaveBeenCalledTimes(1);
  });

  it("setActive calls wallet.setActive()", () => {
    root.querySelector("#set-active-button-testwallet")!.click();
    expect(mockWallet.setActive).toHaveBeenCalledTimes(1);
  });

  it("dropdown calls wallet.setActiveAccount()", () => {
    mockWallet.isConnected = true;
    mockWallet.accounts = [{ address: "MOCKADDR" }];
    mockWallet.activeAccount = mockWallet.accounts[0];

    mockWallet._cb(mockWallet); // render updated state

    const select = root.querySelector("select")!;
    select.value = "MOCKADDR";

    select.dispatchEvent(new Event("change", { bubbles: true })); // ✅ THIS FIXES IT

    expect(mockWallet.setActiveAccount).toHaveBeenCalledWith("MOCKADDR");
  });
});

// ─────────────────────────────────────────────────────────────
// sendTransaction tests
// ─────────────────────────────────────────────────────────────
describe("WalletComponent transactions", () => {
  it("sends transaction successfully", async () => {
    mockWallet.activeAccount = { address: "OK_ADDRESS" };
    await component.sendTransaction();

    expect(AtomicTransactionComposer).toHaveBeenCalled();
  });

  it("handles invalid address (branch: !isValidAddress)", async () => {
    (isValidAddress as jest.Mock).mockReturnValue(false);

    console.error = jest.fn();
    mockWallet.activeAccount = { address: "INVALID" };

    await component.sendTransaction();
    expect(console.error).toHaveBeenCalled();
  });



});

// ─────────────────────────────────────────────────────────────
// auth tests
// ─────────────────────────────────────────────────────────────
describe("WalletComponent authentication flow", () => {

  it("auth success triggers signing and 2 fetch calls", async () => {
    (isValidAddress as jest.Mock).mockReturnValue(true);       // ✅ allow auth() to proceed
    mockWallet.activeAccount = { address: "VALID123ADDRESS" }; // ✅ required

    global.fetch = jest
      .fn()
      // nonce response (first fetch call)
      .mockResolvedValueOnce({ json: async () => ({ nonce: "NONCE123", prefix: "MSG_" }) })
      // verify response (second fetch call)
      .mockResolvedValueOnce({ json: async () => ({ success: true, redirect_url: "/" }) }) as any;

    await component.auth();

    expect(mockWallet.signTransactions).toHaveBeenCalled();   // ✅ FIXED
    expect(fetch).toHaveBeenCalledTimes(2);                   // ✅ confirm nonce + verify
  });


  it("auth failure shows an error alert", async () => {
    (isValidAddress as jest.Mock).mockReturnValue(true);       // ✅ must allow fetch to run

    mockWallet.activeAccount = { address: "ADDR999" };

    // nonce fetch returns error JSON
    global.fetch = jest.fn().mockResolvedValue({
      json: async () => ({ error: "BAD" })
    }) as any;

    await component.auth();

    const alert = root.querySelector(".alert.alert-error")!;
    expect(alert).not.toBeNull();
    expect(alert.textContent).toContain("BAD");
  });

  it("throws when activeAddress is missing OR invalid", async () => {
    console.error = jest.fn();

    // Case #1: no active account
    mockWallet.activeAccount = null;
    await component.sendTransaction();

    expect(console.error).toHaveBeenCalledWith(
      "[App] Error signing transaction:",
      expect.any(Error)
    );

    // Case #2: invalid address format
    mockWallet.activeAccount = { address: "BADFORMAT" };
    (isValidAddress as jest.Mock).mockReturnValueOnce(false);

    await component.sendTransaction();

    expect(console.error).toHaveBeenCalled();
    expect((console.error as jest.Mock).mock.calls.at(-1)[1].message)
      .toContain("Invalid address format");
  });

});

describe("Additional render test", () => {

  it("render removes Active badge when wallet becomes inactive", () => {
    // Start active (badge should be created)
    mockWallet.isConnected = true;
    mockWallet.isActive = true;
    mockWallet.accounts = [{ address: "ADDR123456" }];
    mockWallet.activeAccount = mockWallet.accounts[0];
    mockWallet._cb(mockWallet);

    expect(root.querySelector("h4 .badge")).not.toBeNull(); // badge exists

    // Now wallet becomes INACTIVE → badge must be removed
    mockWallet.isActive = false;
    mockWallet._cb(mockWallet);

    expect(root.querySelector("h4 .badge")).toBeNull();
  });

  // -----------------------------------------------------------------------------
  // sendTransaction: no active address
  // -----------------------------------------------------------------------------
  it("sendTransaction throws when there is no active account", async () => {
    console.error = jest.fn();
    mockWallet.activeAccount = null; // ← force missing account

    await component.sendTransaction();

    expect(console.error).toHaveBeenCalledWith(
      "[App] Error signing transaction:",
      expect.any(Error)
    );
  });

  // -----------------------------------------------------------------------------
  // sendTransaction: invalid address
  // -----------------------------------------------------------------------------
  it("sendTransaction throws when address format is invalid", async () => {
    console.error = jest.fn();
    (isValidAddress as jest.Mock).mockReturnValue(false);

    mockWallet.activeAccount = { address: "BADADDR" };

    await component.sendTransaction();

    expect(console.error).toHaveBeenCalled();
    expect((console.error as jest.Mock).mock.calls[0][1].message)
      .toContain("Invalid address format");
  });

  // -----------------------------------------------------------------------------
  // auth(): no signedTx returned
  // -----------------------------------------------------------------------------
  it("auth throws when wallet does not return signed transaction", async () => {
    (isValidAddress as jest.Mock).mockReturnValue(true);
    mockWallet.activeAccount = { address: "ADDR123" };
    mockWallet.signTransactions.mockResolvedValueOnce([undefined]); // ← force missing signed tx

    global.fetch = jest
      .fn()
      .mockResolvedValueOnce({ json: async () => ({ nonce: "NONCE", prefix: "MSG_" }) });

    await component.auth();

    const alert = root.querySelector(".alert.alert-error")!;
    expect(alert.textContent).toContain("No signed transaction returned");
  });

  // -----------------------------------------------------------------------------
  // auth(): verification fails
  // -----------------------------------------------------------------------------
  it("auth throws when verification response is not success", async () => {
    (isValidAddress as jest.Mock).mockReturnValue(true);
    mockWallet.activeAccount = { address: "ADDR123" };

    mockWallet.signTransactions.mockResolvedValueOnce([new Uint8Array([1, 2, 3])]);

    global.fetch = jest
      .fn()
      // nonce ok
      .mockResolvedValueOnce({ json: async () => ({ nonce: "NONCE", prefix: "MSG_" }) })
      // server rejects the login
      .mockResolvedValueOnce({ json: async () => ({ success: false, error: "SERVER-FAIL" }) });

    await component.auth();

    const alert = root.querySelector(".alert.alert-error")!;
    expect(alert.textContent).toContain("Verification failed: SERVER-FAIL");
  });

  // -----------------------------------------------------------------------------
  // Click routing: transaction-button triggers sendTransaction()
  // -----------------------------------------------------------------------------
  it("clicking transaction-button triggers sendTransaction()", () => {
    const spy = jest.spyOn(component, "sendTransaction");
    const btn = root.querySelector(`#transaction-button-testwallet`)!;
    btn.click();
    expect(spy).toHaveBeenCalled();
  });

  // -----------------------------------------------------------------------------
  // Click routing: auth-button triggers auth()
  // -----------------------------------------------------------------------------
  it("clicking auth-button triggers auth()", () => {
    const spy = jest.spyOn(component, "auth");
    const btn = root.querySelector(`#auth-button-testwallet`)!;
    btn.click();
    expect(spy).toHaveBeenCalled();
  });

  // -----------------------------------------------------------------------------
  // destroy(): removing event listeners triggers catch block
  // -----------------------------------------------------------------------------
  it("destroy() catches cleanup errors", () => {
    console.debug = jest.fn();

    Object.defineProperty(root, "removeEventListener", {
      value: () => {
        throw new Error("boom");
      },
    });

    component.destroy();

    expect(console.debug).toHaveBeenCalledWith(
      "[WalletComponent] Error during event listener cleanup:",
      expect.any(Error)
    );
  });
});


describe('WalletComponent line 152 coverage', () => {
  it('should cover the auth address validation error', async () => {
    // Create proper DOM structure
    const freshElement = document.createElement('div');
    freshElement.innerHTML = `
      <button id="connect-button-testwallet"></button>
      <button id="disconnect-button-testwallet"></button>
      <button id="set-active-button-testwallet"></button>
      <button id="auth-button-testwallet"></button>
      <button id="transaction-button-testwallet"></button>
      <select></select>
      <h4></h4>
    `;
    
    // Create a fresh component instance just for this test
    const freshWallet = {
      ...mockWallet,
      isConnected: true,
      isActive: true,
      activeAccount: null // This will trigger the error on line 152
    };
    
    const freshComponent = new WalletComponent(freshWallet, mockManager);
    freshComponent.bind(freshElement);
    
    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    
    // This should trigger the specific error on line 152
    await freshComponent.auth();
    
    // Verify the error was thrown and handled
    expect(consoleErrorSpy).toHaveBeenCalledWith(
      '[App] Error signing data:',
      expect.any(Error)
    );
    
    consoleErrorSpy.mockRestore();
    freshComponent.destroy();
  });
});

// ─────────────────────────────────────────────────────────────
// cleanup
// ─────────────────────────────────────────────────────────────
describe("WalletComponent cleanup", () => {
  it("destroy unsubscribes events", () => {
    component.destroy();
    expect(unsubscribeMock).toHaveBeenCalledTimes(1);
  });
});
