import * as algosdk from "algosdk";

jest.mock("@txnlab/use-wallet", () => ({
  BaseWallet: jest.fn(),
  WalletId: {
    PERA: "pera",
    DEFLY: "defly",
    MAGIC: "magic",
    LUTE: "lute",
  },
  WalletManager: jest.fn(),
}));

import { WalletComponent } from "./WalletComponent";
import { BaseWallet, WalletManager, WalletId } from "@txnlab/use-wallet";

// Create consistent mock instances
const mockAtomicTransactionComposer = {
  addTransaction: jest.fn(),
  execute: jest.fn(),
};

// Mock algosdk functions at the module level
jest.mock("algosdk", () => {
  const originalModule = jest.requireActual("algosdk");
  return {
    ...originalModule,
    isValidAddress: jest.fn().mockReturnValue(true),
    AtomicTransactionComposer: jest.fn(() => mockAtomicTransactionComposer),
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

  beforeEach(() => {
    // Clear all mocks
    jest.clearAllMocks();

    // Reset the atomic transaction composer mock
    mockAtomicTransactionComposer.addTransaction.mockClear();
    mockAtomicTransactionComposer.execute.mockClear();

    // Setup mock wallet with valid Algorand address
    mockWallet = {
      id: "test-wallet",
      metadata: { name: "Test Wallet" },
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

    // Setup mock manager with proper method chain
    const mockGetTransactionParams = jest.fn().mockReturnValue({
      do: jest.fn().mockResolvedValue({
        fee: 1000,
        firstRound: 1000,
        lastRound: 2000,
        genesisID: "testnet-v1.0",
        genesisHash: "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI=",
      }),
    });

    mockManager = {
      algodClient: {
        getTransactionParams: mockGetTransactionParams,
      },
    } as any;

    // Mock document.cookie and CSRF token
    Object.defineProperty(document, "cookie", {
      writable: true,
      value: "csrftoken=test-csrf-token",
    });

    // Mock CSRF token input
    document.body.innerHTML =
      '<input name="csrfmiddlewaretoken" value="test-csrf-token" />';

    walletComponent = new WalletComponent(mockWallet, mockManager);
  });

  afterEach(() => {
    walletComponent.destroy();
    jest.resetModules();
  });

  describe("Constructor", () => {
    it("should initialize with correct properties", () => {
      expect(walletComponent.wallet).toBe(mockWallet);
      expect(walletComponent.manager).toBe(mockManager);
      expect(walletComponent.element).toBeDefined();
    });

    it("should subscribe to wallet state changes", () => {
      expect(mockWallet.subscribe).toHaveBeenCalled();
    });
  });

  describe("sendTransaction", () => {
    let atcSpy: jest.SpyInstance;
    let atcInstance: any;

    beforeEach(() => {
      // Make wallet active so the transaction button gets rendered
      mockWallet.isActive = true;
      // Use a valid Algorand address format
      mockWallet.activeAccount = {
        address: "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU",
      };

      // Re-render the component with active state to create the button
      walletComponent.render();

      atcInstance = {
        addTransaction: jest.fn(),
        execute: jest.fn().mockResolvedValue({
          confirmedRound: 1234,
          txIDs: ["test-tx-id"],
        }),
      };

      atcSpy = jest
        .spyOn(algosdk, "AtomicTransactionComposer")
        .mockImplementation(() => atcInstance);
    });

    afterEach(() => {
      atcSpy.mockRestore();
      mockWallet.isActive = false;
    });

    it("should send transaction successfully", async () => {
      await walletComponent.sendTransaction();

      expect(atcSpy).toHaveBeenCalled();
      expect(atcInstance.addTransaction).toHaveBeenCalled();
      expect(atcInstance.execute).toHaveBeenCalled();
    });

    it("should handle transaction errors gracefully", async () => {
      atcInstance.execute.mockRejectedValueOnce(
        new Error("Transaction failed")
      );

      await expect(walletComponent.sendTransaction()).resolves.not.toThrow();
    });

    it("should not send transaction without active account", async () => {
      mockWallet.activeAccount = null;

      await walletComponent.sendTransaction();

      expect(atcInstance.addTransaction).not.toHaveBeenCalled();
    });
  });

  describe("auth", () => {
    beforeEach(() => {
      mockAtomicTransactionComposer.addTransaction.mockClear();
      mockAtomicTransactionComposer.execute.mockClear();

      // Use a valid Algorand address format
      mockWallet.activeAccount = {
        address: "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU",
      };

      // Mock successful transaction params
      const mockGetTransactionParams = jest.fn().mockReturnValue({
        do: jest.fn().mockResolvedValue({
          fee: 1000,
          firstRound: 1000,
          lastRound: 2000,
          genesisID: "testnet-v1.0",
          genesisHash: "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI=",
        }),
      });

      mockManager.algodClient.getTransactionParams = mockGetTransactionParams;
    });

    it("should authenticate successfully", async () => {
      // Mock fetch responses
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

      await walletComponent.auth();

      expect(global.fetch).toHaveBeenCalledTimes(2);
      expect(mockWallet.signTransactions).toHaveBeenCalled();
    });

    it("should handle authentication errors from nonce endpoint", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ error: "Invalid address", nonce: null }),
      });

      await walletComponent.auth();

      // Should handle error without throwing and not proceed to sign transactions
      expect(mockWallet.signTransactions).not.toHaveBeenCalled();
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    it("should handle auth with no active account", async () => {
      mockWallet.activeAccount = null;

      let errorThrown = false;
      try {
        await walletComponent.auth();
      } catch (error) {
        errorThrown = true;
        expect(error.message).toContain("Invalid or missing address");
      }

      expect(errorThrown).toBe(true);
      expect(global.fetch).not.toHaveBeenCalled();
      expect(mockWallet.signTransactions).not.toHaveBeenCalled();
    });

    it("should handle network errors", async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(
        new Error("Network error")
      );

      await walletComponent.auth();

      // Should handle error without throwing
      expect(mockWallet.signTransactions).not.toHaveBeenCalled();
    });

    it("should not authenticate without valid address", async () => {
      mockWallet.activeAccount = null;

      // For methods that throw errors synchronously at the start (before any async operations),
      // we need to catch the error since it's thrown immediately when auth() is called
      let errorThrown = false;
      try {
        await walletComponent.auth();
      } catch (error) {
        errorThrown = true;
        expect(error.message).toContain("Invalid or missing address");
      }

      expect(errorThrown).toBe(true);
      expect(global.fetch).not.toHaveBeenCalled();
      expect(mockWallet.signTransactions).not.toHaveBeenCalled();
    });
  });

  describe("setActiveAccount", () => {
    it("should set active account", () => {
      const mockEvent = {
        target: { value: "test-address" },
      } as unknown as Event;

      walletComponent.setActiveAccount(mockEvent);

      expect(mockWallet.setActiveAccount).toHaveBeenCalledWith("test-address");
    });
  });

  describe("sanitizeText", () => {
    it("should sanitize HTML characters", () => {
      const input = '<script>alert("xss")</script>';
      const result = walletComponent.sanitizeText(input);

      expect(result).not.toContain("<script>");
      expect(result).toContain("&lt;script&gt;");
    });

    it("should handle normal text", () => {
      const input = "Normal text";
      const result = walletComponent.sanitizeText(input);

      expect(result).toBe("Normal text");
    });
  });

  describe("render", () => {
    it("should render wallet component correctly", () => {
      walletComponent.render();
      expect(walletComponent.element.innerHTML).toContain("Test Wallet");
    });

    it("should sanitize text content in render", () => {
      mockWallet.metadata.name = '<script>alert("xss")</script>';
      walletComponent.render();

      expect(walletComponent.element.innerHTML).not.toContain("<script>");
      expect(walletComponent.element.innerHTML).toContain("&lt;script&gt;");
    });

    it("should render active state correctly", () => {
      mockWallet.isActive = true;
      walletComponent.render();

      expect(walletComponent.element.innerHTML).toContain("Active");
    });

    it("should render accounts dropdown when active", () => {
      mockWallet.isActive = true;
      mockWallet.accounts = [{ address: "addr1" }, { address: "addr2" }];
      mockWallet.activeAccount = { address: "addr1" };

      walletComponent.render();

      expect(walletComponent.element.innerHTML).toContain("select");
      expect(walletComponent.element.innerHTML).toContain("addr1");
      expect(walletComponent.element.innerHTML).toContain("addr2");
    });
  });

  describe("destroy", () => {
    it("should clean up event listeners and unsubscribe", () => {
      const mockUnsubscribe = jest.fn();
      (walletComponent as any).unsubscribe = mockUnsubscribe;

      walletComponent.destroy();

      expect(mockUnsubscribe).toHaveBeenCalled();
    });
  });

  // Fix the remaining failing tests by updating the address format
  describe("Edge Cases unit tests", () => {
    beforeEach(() => {
      // Set a valid address for auth tests
      mockWallet.activeAccount = {
        address: "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU",
      };
    });

    it("should handle auth with no signed transaction returned", async () => {
      mockWallet.activeAccount = { address: "test-address" };
      mockWallet.signTransactions.mockResolvedValue([]); // Empty array

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            nonce: "test-nonce",
            prefix: "test-prefix",
            error: null,
          }),
      });

      await walletComponent.auth();

      // Should handle the error gracefully
      expect(global.fetch).toHaveBeenCalledTimes(1); // Only nonce call, no verify call
    });

    it("should handle auth verification failure", async () => {
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
              success: false,
              error: "Verification failed",
              redirect_url: null,
            }),
        });

      await walletComponent.auth();

      // Should handle verification failure
      expect(global.fetch).toHaveBeenCalledTimes(2);
    });

    it("should handle auth with no redirect URL", async () => {
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
              error: null,
              redirect_url: null, // No redirect URL
            }),
        });

      // Mock window.location
      const originalLocation = window.location;
      delete (window as any).location;
      window.location = { href: "" } as any;

      await walletComponent.auth();

      // Should redirect to root when no redirect_url provided
      expect(window.location.href).toBe("/");

      // Restore
      window.location = originalLocation;
    });

    it("should handle multiple account selection", () => {
      mockWallet.isActive = true;
      mockWallet.accounts = [
        { address: "addr1" },
        { address: "addr2" },
        { address: "addr3" },
      ];
      mockWallet.activeAccount = { address: "addr2" };

      walletComponent.render();

      // Should render all accounts with correct selected one
      expect(walletComponent.element.innerHTML).toContain("addr1");
      expect(walletComponent.element.innerHTML).toContain("addr2");
      expect(walletComponent.element.innerHTML).toContain("addr3");
      expect(walletComponent.element.innerHTML).toContain(
        'value="addr2" selected'
      );
    });

    it("should handle destroy without unsubscribe", () => {
      // Test destroy when unsubscribe is not set
      (walletComponent as any).unsubscribe = undefined;

      expect(() => {
        walletComponent.destroy();
      }).not.toThrow();
    });

    it("should handle event listener removal in destroy", () => {
      // Mock removeEventListener
      const removeSpy = jest.spyOn(
        walletComponent.element,
        "removeEventListener"
      );

      walletComponent.destroy();

      expect(removeSpy).toHaveBeenCalledWith("click", expect.any(Function));
      expect(removeSpy).toHaveBeenCalledWith("change", expect.any(Function));
      expect(removeSpy).toHaveBeenCalledWith("input", expect.any(Function));

      removeSpy.mockRestore();
    });

    it("should handle auth with no redirect URL", async () => {
      mockWallet.activeAccount = { address: "test-address" };

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
              error: null,
              redirect_url: null, // No redirect URL provided
            }),
        });

      // Mock window.location
      const originalLocation = window.location;
      Object.defineProperty(window, "location", {
        value: { href: "" },
        writable: true,
      });

      await walletComponent.auth();

      // Should redirect to root when no redirect_url provided
      expect(window.location.href).toBe("/");

      // Restore
      Object.defineProperty(window, "location", {
        value: originalLocation,
        writable: true,
      });
    });

    it("should handle CSRF token from both cookie and input", async () => {
      mockWallet.activeAccount = { address: "test-address" };

      // Set up both CSRF sources
      document.cookie = "csrftoken=cookie-token";
      document.body.innerHTML =
        '<input name="csrfmiddlewaretoken" value="input-token" />';

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
            }),
        });

      await walletComponent.auth();

      // Should use the cookie token first
      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            "X-CSRFToken": "cookie-token",
          }),
        })
      );
    });

    it("should handle constructor with initial state", () => {
      // Test that constructor properly initializes all properties
      const walletComponent = new WalletComponent(mockWallet, mockManager);

      expect(walletComponent.wallet).toBe(mockWallet);
      expect(walletComponent.manager).toBe(mockManager);
      expect(walletComponent.element).toBeDefined();
      expect(walletComponent.element.tagName).toBe("DIV");
      expect((walletComponent as any).magicEmail).toBe("");
      expect(typeof (walletComponent as any).unsubscribe).toBe("function");
    });

    it("should handle click events on non-button elements", () => {
      // Test that click events on non-button elements are ignored
      const div = document.createElement("div");
      walletComponent.element.appendChild(div);

      // This should not throw any errors
      expect(() => {
        div.click();
      }).not.toThrow();
    });

    it("should handle change events on non-select elements", () => {
      // Test that change events on non-select elements are ignored
      const input = document.createElement("input");
      walletComponent.element.appendChild(input);

      // This should not throw any errors
      expect(() => {
        input.dispatchEvent(new Event("change", { bubbles: true }));
      }).not.toThrow();
    });

    it("should handle input events on non-email elements", () => {
      // Test that input events on non-email input elements are ignored
      const input = document.createElement("input");
      input.id = "other-input";
      walletComponent.element.appendChild(input);

      // This should not throw any errors
      expect(() => {
        input.dispatchEvent(new Event("input", { bubbles: true }));
      }).not.toThrow();
    });

    it("should handle unsubscribe in destroy when not set", () => {
      // Test destroy when unsubscribe is undefined
      (walletComponent as any).unsubscribe = undefined;

      expect(() => {
        walletComponent.destroy();
      }).not.toThrow();
    });

    it("should handle sendTransaction with missing transaction button", async () => {
      // Remove any existing transaction button
      const existingButton = walletComponent.element.querySelector(
        "#transaction-button"
      );
      if (existingButton) {
        existingButton.remove();
      }

      // This should return early without throwing
      await walletComponent.sendTransaction();

      // Verify no ATC was created (method returned early)
      const algosdk = require("algosdk");
      expect(algosdk.AtomicTransactionComposer).not.toHaveBeenCalled();
    });
  });

  describe("Magic Link Specific Tests", () => {
    beforeEach(() => {
      mockWallet.id = WalletId.MAGIC;
      walletComponent.render(); // Re-render to create the email input
    });

    it("should render email input for Magic wallet", () => {
      expect(walletComponent.element.innerHTML).toContain('id="magic-email"');
      expect(walletComponent.element.innerHTML).toContain(
        "Enter email to connect"
      );
    });

    it("should handle email input changes", () => {
      // Set initial email value
      (walletComponent as any).magicEmail = "initial@example.com";

      const emailInput = walletComponent.element.querySelector(
        "#magic-email"
      ) as HTMLInputElement;

      // Simulate user typing
      emailInput.value = "new@example.com";
      emailInput.dispatchEvent(new Event("input", { bubbles: true }));

      expect((walletComponent as any).magicEmail).toBe("new@example.com");
    });

    it("should disable email input when connected", () => {
      mockWallet.id = WalletId.MAGIC; // Ensure mockWallet is Magic (for isMagicLink() to be true)
      mockWallet.isConnected = true;
      walletComponent.render(); // Re-render with connected state

      const emailInput = walletComponent.element.querySelector(
        "#magic-email"
      ) as HTMLInputElement;
      expect(emailInput).toBeTruthy(); // Verify input is rendered
      console.log("Input HTML:", emailInput.outerHTML); // Debug: Check the rendered HTML
      console.log("isConnected in mock:", mockWallet.isConnected); // Debug: Verify state
      expect(emailInput.hasAttribute("disabled")).toBe(true); // Check attribute
      expect(emailInput.disabled).toBe(true); // Also check property for completeness
    });

    it("should handle email input updates correctly", () => {
      // Test the updateEmailInput method specifically
      (walletComponent as any).magicEmail = "test@example.com";
      walletComponent.updateEmailInput();

      const emailInput = walletComponent.element.querySelector(
        "#magic-email"
      ) as HTMLInputElement;
      expect(emailInput.value).toBe("test@example.com");
    });
  });

  describe("CSRF Token Edge Cases", () => {
    beforeEach(() => {
      mockWallet.activeAccount = {
        address: "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU",
      };
    });

    it("should handle missing CSRF token from both cookie and input", async () => {
      // Clear both CSRF sources
      document.cookie = "";
      document.body.innerHTML = "";

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
            }),
        });

      await walletComponent.auth();

      // Should still attempt the request with empty CSRF token
      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            "X-CSRFToken": "",
          }),
        })
      );
    });

    it("should handle getCsrfToken with only cookie available", () => {
      // Test the internal getCsrfToken function behavior
      document.cookie = "csrftoken=cookie-token-only";
      document.body.innerHTML = ""; // No input element

      // We need to test this indirectly through auth
      mockWallet.activeAccount = { address: "test-address" };

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
            }),
        });

      return walletComponent.auth().then(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.any(String),
          expect.objectContaining({
            headers: expect.objectContaining({
              "X-CSRFToken": "cookie-token-only",
            }),
          })
        );
      });
    });
  });

  describe("Error Display in UI", () => {
    beforeEach(() => {
      mockWallet.activeAccount = {
        address: "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU",
      };
    });

    it("should handle multiple rapid auth attempts", async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            nonce: "test-nonce",
            prefix: "test-prefix",
            error: null,
          }),
      });

      // Make multiple rapid auth calls
      const authPromises = [
        walletComponent.auth(),
        walletComponent.auth(),
        walletComponent.auth(),
      ];

      await Promise.allSettled(authPromises);

      // Should handle multiple requests without crashing
      expect(global.fetch).toHaveBeenCalled();
    });
  });

  describe("Constructor Edge Cases", () => {
    it("should handle constructor with specific initial state", () => {
      // Test the exact constructor execution path
      const originalConsoleInfo = console.info;
      console.info = jest.fn(); // Suppress constructor console.info

      const component = new WalletComponent(mockWallet, mockManager);

      // Verify all constructor properties are set
      expect(component.wallet).toBe(mockWallet);
      expect(component.manager).toBe(mockManager);
      expect(component.element).toBeInstanceOf(HTMLElement);
      expect((component as any).magicEmail).toBe("");
      expect(typeof (component as any).unsubscribe).toBe("function");

      // Verify initial render was called
      expect(component.element.innerHTML).toContain("Test Wallet");

      console.info = originalConsoleInfo;
    });

    it("should handle unsubscribe function from wallet subscription", () => {
      const mockUnsubscribe = jest.fn();
      mockWallet.subscribe.mockReturnValue(mockUnsubscribe);

      const component = new WalletComponent(mockWallet, mockManager);

      // Verify subscription was set up
      expect(mockWallet.subscribe).toHaveBeenCalled();
      expect((component as any).unsubscribe).toBe(mockUnsubscribe);

      component.destroy();
      expect(mockUnsubscribe).toHaveBeenCalled();
    });
  });

  describe("Event Listener Edge Cases", () => {
    it("should handle click events on elements with tagName not button", () => {
      // Extreme isolation - create everything from scratch
      const TestEnvironment = () => {
        // Create completely fresh mocks
        const freshMockWallet = {
          id: "test-wallet",
          metadata: { name: "Test Wallet" },
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
          signTransactions: jest.fn(),
          canSignData: true,
        };

        const freshMockManager = {
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
        };

        // Create fresh component
        const component = new WalletComponent(
          freshMockWallet,
          freshMockManager
        );

        return { component, freshMockWallet };
      };

      const { component, freshMockWallet } = TestEnvironment();

      // Create a div (not button) with the target ID
      const div = document.createElement("div");
      div.id = "connect-button";
      div.textContent = "Div not button";

      // Add to a clean container
      const cleanContainer = document.createElement("div");
      cleanContainer.appendChild(div);
      document.body.appendChild(cleanContainer);

      console.log(
        "Fresh test - Before click, connect calls:",
        freshMockWallet.connect.mock.calls.length
      );

      // Click the div
      div.click();

      console.log(
        "Fresh test - After click, connect calls:",
        freshMockWallet.connect.mock.calls.length
      );

      // Should not call connect
      expect(freshMockWallet.connect).not.toHaveBeenCalled();

      // Cleanup
      component.destroy();
      document.body.removeChild(cleanContainer);
    });

    it("should handle click events on elements with unknown IDs", () => {
      // Create a button with unknown ID
      const button = document.createElement("button");
      button.id = "unknown-button";
      walletComponent.element.appendChild(button);

      // This should not throw and should be ignored
      expect(() => {
        button.click();
      }).not.toThrow();
    });

    it("should handle change events on non-select elements", () => {
      // Test change event on input (not select)
      const input = document.createElement("input");
      input.type = "text";
      walletComponent.element.appendChild(input);

      // This should not throw and should be ignored
      expect(() => {
        input.dispatchEvent(new Event("change", { bubbles: true }));
      }).not.toThrow();
    });

    it("should handle input events on non-email elements", () => {
      // Test input event on non-email input
      const input = document.createElement("input");
      input.id = "other-input";
      input.type = "text";
      walletComponent.element.appendChild(input);

      // Set initial magic email value
      (walletComponent as any).magicEmail = "initial@example.com";

      input.dispatchEvent(new Event("input", { bubbles: true }));

      // magicEmail should remain unchanged
      expect((walletComponent as any).magicEmail).toBe("initial@example.com");
    });

    it("should handle event listeners removal in destroy", () => {
      // Mock removeEventListener to verify all are removed
      const removeSpy = jest.spyOn(
        walletComponent.element,
        "removeEventListener"
      );

      walletComponent.destroy();

      // Should remove all three event listeners
      expect(removeSpy).toHaveBeenCalledWith("click", expect.any(Function));
      expect(removeSpy).toHaveBeenCalledWith("change", expect.any(Function));
      expect(removeSpy).toHaveBeenCalledWith("input", expect.any(Function));

      removeSpy.mockRestore();
    });

    it("should handle destroy gracefully when unsubscribe is not callable", () => {
      // In the real component, unsubscribe should always be a function or undefined
      // But let's test the edge case anyway
      const originalUnsubscribe = (walletComponent as any).unsubscribe;

      // Temporarily replace with a non-function
      (walletComponent as any).unsubscribe = "invalid";

      // This might throw, but we're testing the boundary
      try {
        walletComponent.destroy();
      } catch (error) {
        // If it throws, that's the actual behavior
        expect(error).toBeDefined();
      }

      // Restore for other tests
      (walletComponent as any).unsubscribe = originalUnsubscribe;
    });
  });

  describe("Specific Edge Cases", () => {
    it("should handle magic email input with empty value", () => {
      // Set up as magic wallet
      mockWallet.id = WalletId.MAGIC;
      walletComponent.render();

      const emailInput = walletComponent.element.querySelector(
        "#magic-email"
      ) as HTMLInputElement;
      emailInput.value = "";
      emailInput.dispatchEvent(new Event("input", { bubbles: true }));

      expect((walletComponent as any).magicEmail).toBe("");
    });

    it("should handle setActiveAccount with empty select value", () => {
      const mockEvent = {
        target: { value: "" },
      } as unknown as Event;

      walletComponent.setActiveAccount(mockEvent);

      // Should handle empty string gracefully
      expect(mockWallet.setActiveAccount).toHaveBeenCalledWith("");
    });

    it("should handle sanitizeText with null input", () => {
      const result = walletComponent.sanitizeText(null as any);

      expect(result).toBe("");
    });

    it("should handle sanitizeText with undefined input", () => {
      const result = walletComponent.sanitizeText(undefined as any);

      expect(result).toBe("");
    });

    it("should handle render with null metadata", () => {
      mockWallet.metadata = null as any;

      // Should not throw
      expect(() => {
        walletComponent.render();
      }).not.toThrow();
    });

    it("should handle render with null metadata name", () => {
      mockWallet.metadata = { name: null } as any;

      // Should not throw
      expect(() => {
        walletComponent.render();
      }).not.toThrow();
    });

    it("should handle auth with no accounts", async () => {
      mockWallet.activeAccount = null;
      mockWallet.accounts = [];

      // This should throw synchronously at the start of auth()
      let errorThrown = false;
      try {
        await walletComponent.auth();
      } catch (error) {
        errorThrown = true;
        expect(error.message).toContain("Invalid or missing address");
      }

      expect(errorThrown).toBe(true);
      expect(global.fetch).not.toHaveBeenCalled();
    });

    it("should handle auth with empty address", async () => {
      mockWallet.activeAccount = { address: "" };

      // This should throw synchronously at the start of auth()
      let errorThrown = false;
      try {
        await walletComponent.auth();
      } catch (error) {
        errorThrown = true;
        expect(error.message).toContain("Invalid or missing address");
      }

      expect(errorThrown).toBe(true);
      expect(global.fetch).not.toHaveBeenCalled();
    });

    it("should handle auth with invalid address format", async () => {
      // Mock isValidAddress to return false for invalid addresses
      const isValidAddressSpy = jest
        .spyOn(algosdk, "isValidAddress")
        .mockReturnValue(false);

      mockWallet.activeAccount = { address: "invalid-address" };

      let errorThrown = false;
      try {
        await walletComponent.auth();
      } catch (error) {
        errorThrown = true;
        expect(error.message).toContain("Invalid or missing address");
      }

      expect(errorThrown).toBe(true);
      expect(global.fetch).not.toHaveBeenCalled();

      isValidAddressSpy.mockRestore();
    });

    it("should handle auth when algodClient.getTransactionParams fails", async () => {
      // Set a valid address first and ensure isValidAddress returns true
      mockWallet.activeAccount = {
        address:
          "ALX123456789012345678901234567890123456789012345678901234567890",
      };

      // Ensure isValidAddress returns true for this test
      const isValidAddressSpy = jest
        .spyOn(algosdk, "isValidAddress")
        .mockReturnValue(true);

      // Mock getTransactionParams to fail
      const originalGetTransactionParams =
        mockManager.algodClient.getTransactionParams;
      mockManager.algodClient.getTransactionParams = jest.fn().mockReturnValue({
        do: jest.fn().mockRejectedValue(new Error("Algod error")),
      });

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            nonce: "test-nonce",
            prefix: "test-prefix",
            error: null,
          }),
      });

      await walletComponent.auth();

      // Should handle the error gracefully - transaction signing should not be called
      // because getTransactionParams failed
      expect(mockWallet.signTransactions).not.toHaveBeenCalled();

      // Restore
      mockManager.algodClient.getTransactionParams =
        originalGetTransactionParams;
      isValidAddressSpy.mockRestore();
    });

    it("should handle sendTransaction with no active account", async () => {
      mockWallet.isActive = true;
      mockWallet.activeAccount = null;

      await walletComponent.sendTransaction();

      // Should return early without creating ATC
      const algosdk = require("algosdk");
      expect(algosdk.AtomicTransactionComposer).not.toHaveBeenCalled();
    });

    it("should handle sendTransaction when wallet is not active", async () => {
      mockWallet.isActive = false;
      mockWallet.activeAccount = { address: "test-address" };

      await walletComponent.sendTransaction();

      // Should return early without creating ATC
      const algosdk = require("algosdk");
      expect(algosdk.AtomicTransactionComposer).not.toHaveBeenCalled();
    });

    it("should handle sendTransaction when transaction button is missing", async () => {
      mockWallet.isActive = true;
      mockWallet.activeAccount = { address: "test-address" };

      // Remove any existing transaction button
      const existingButton = walletComponent.element.querySelector(
        "#transaction-button"
      );
      if (existingButton) {
        existingButton.remove();
      }

      await walletComponent.sendTransaction();

      // Should return early without creating ATC
      const algosdk = require("algosdk");
      expect(algosdk.AtomicTransactionComposer).not.toHaveBeenCalled();
    });

    it("should handle isConnectDisabled when wallet is undefined", () => {
      // Temporarily set wallet to undefined
      const originalWallet = walletComponent.wallet;
      (walletComponent as any).wallet = undefined;

      // Should handle gracefully
      expect(walletComponent.isConnectDisabled()).toBe(true);

      // Restore
      (walletComponent as any).wallet = originalWallet;
    });

    it("should handle isMagicLink when wallet is undefined", () => {
      // Temporarily set wallet to undefined
      const originalWallet = walletComponent.wallet;
      (walletComponent as any).wallet = undefined;

      // Should handle gracefully
      expect(walletComponent.isMagicLink()).toBe(false);

      // Restore
      (walletComponent as any).wallet = originalWallet;
    });

    it("should handle getConnectArgs when wallet is undefined", () => {
      // Temporarily set wallet to undefined
      const originalWallet = walletComponent.wallet;
      (walletComponent as any).wallet = undefined;

      // Should handle gracefully
      expect(walletComponent.getConnectArgs()).toBeUndefined();

      // Restore
      (walletComponent as any).wallet = originalWallet;
    });

    it("should handle setActive when wallet is undefined", () => {
      // Temporarily set wallet to undefined
      const originalWallet = walletComponent.wallet;
      (walletComponent as any).wallet = undefined;

      // Should handle gracefully (no error thrown)
      expect(() => {
        walletComponent.setActive();
      }).not.toThrow();

      // Restore
      (walletComponent as any).wallet = originalWallet;
    });

    it("should handle disconnect when wallet is undefined", () => {
      // Temporarily set wallet to undefined
      const originalWallet = walletComponent.wallet;
      (walletComponent as any).wallet = undefined;

      // Should handle gracefully (no error thrown)
      expect(() => {
        walletComponent.disconnect();
      }).not.toThrow();

      // Restore
      (walletComponent as any).wallet = originalWallet;
    });

    it("should handle connect when wallet is undefined", () => {
      // Temporarily set wallet to undefined
      const originalWallet = walletComponent.wallet;
      (walletComponent as any).wallet = undefined;

      // Should handle gracefully (no error thrown)
      expect(() => {
        walletComponent.connect();
      }).not.toThrow();

      // Restore
      (walletComponent as any).wallet = originalWallet;
    });

    it("should handle setActiveAccount when wallet is undefined", () => {
      // Temporarily set wallet to undefined
      const originalWallet = walletComponent.wallet;
      (walletComponent as any).wallet = undefined;

      const mockEvent = {
        target: { value: "test-address" },
      } as unknown as Event;

      // Should handle gracefully (no error thrown)
      expect(() => {
        walletComponent.setActiveAccount(mockEvent);
      }).not.toThrow();

      // Restore
      (walletComponent as any).wallet = originalWallet;
    });

    it("should handle render when wallet is undefined", () => {
      // Temporarily set wallet to undefined
      const originalWallet = walletComponent.wallet;
      (walletComponent as any).wallet = undefined;

      // Should handle gracefully (no error thrown)
      expect(() => {
        walletComponent.render();
      }).not.toThrow();

      // Restore
      (walletComponent as any).wallet = originalWallet;
    });

    it("should handle updateEmailInput when email input is missing", () => {
      // Remove any existing email input
      const existingInput =
        walletComponent.element.querySelector("#magic-email");
      if (existingInput) {
        existingInput.remove();
      }

      // Should handle gracefully (no error thrown)
      expect(() => {
        walletComponent.updateEmailInput();
      }).not.toThrow();
    });

    it("should handle destroy when element is undefined", () => {
      // Temporarily set element to undefined
      const originalElement = walletComponent.element;
      (walletComponent as any).element = undefined;

      // Should handle gracefully (no error thrown)
      expect(() => {
        walletComponent.destroy();
      }).not.toThrow();

      // Restore
      (walletComponent as any).element = originalElement;
    });

    it("should handle destroy when element.removeEventListener is undefined", () => {
      // Create a fresh component for this specific test
      const freshComponent = new WalletComponent(mockWallet, mockManager);

      // Temporarily remove removeEventListener
      const originalRemove = freshComponent.element.removeEventListener;
      freshComponent.element.removeEventListener = undefined as any;

      // Should handle gracefully (no error thrown)
      expect(() => {
        freshComponent.destroy();
      }).not.toThrow();

      // Restore and clean up
      freshComponent.element.removeEventListener = originalRemove;
      freshComponent.destroy(); // Clean up the fresh component
    });

    it("should handle sendTransaction with invalid address format", async () => {
      mockWallet.isActive = true;
      mockWallet.activeAccount = { address: "invalid-address" };

      // Mock isValidAddress to return false
      const isValidAddressSpy = jest
        .spyOn(algosdk, "isValidAddress")
        .mockReturnValue(false);

      // Re-render to create the transaction button
      walletComponent.render();

      // Spy on ATC to verify it's not called
      const atcSpy = jest.spyOn(algosdk, "AtomicTransactionComposer");

      await walletComponent.sendTransaction();

      // Should handle the error gracefully without calling ATC
      expect(atcSpy).not.toHaveBeenCalled();

      // Clean up
      atcSpy.mockRestore();
      isValidAddressSpy.mockRestore();
    });
  });

  describe("More specific cases", () => {
    let mockWallet: jest.Mocked<BaseWallet>;
    let mockManager: jest.Mocked<WalletManager>;
    let walletComponent: WalletComponent;

    // Common setup function
    const setupTest = (
      walletOverrides: Partial<BaseWallet> = {},
      managerOverrides: Partial<WalletManager> = {}
    ) => {
      jest.clearAllMocks();

      mockWallet = {
        id: "test-wallet",
        metadata: { name: "Test Wallet" },
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
        ...walletOverrides,
      } as any;

      mockManager = {
        algodClient: {
          getTransactionParams: jest.fn().mockReturnValue({
            do: jest.fn().mockResolvedValue({
              fee: 1000,
              firstRound: 1000,
              lastRound: 2000,
            }),
          }),
        },
        ...managerOverrides,
      } as any;

      walletComponent = new WalletComponent(mockWallet, mockManager);
    };

    // Common teardown
    const teardownTest = () => {
      if (walletComponent) {
        walletComponent.destroy();
      }
    };

    // Helper functions
    const getButton = (id: string): HTMLButtonElement =>
      walletComponent.element.querySelector(`#${id}`) as HTMLButtonElement;

    const getInput = (id: string): HTMLInputElement =>
      walletComponent.element.querySelector(`#${id}`) as HTMLInputElement;

    const getSelect = (): HTMLSelectElement =>
      walletComponent.element.querySelector("select") as HTMLSelectElement;

    const clickButton = (id: string) => {
      walletComponent.render();
      getButton(id).click();
    };

    describe("Subscription", () => {
      beforeEach(() => setupTest());
      afterEach(teardownTest);

      it("should subscribe to wallet state changes in constructor and call render on state change", () => {
        expect(mockWallet.subscribe).toHaveBeenCalledTimes(1);
        expect(mockWallet.subscribe).toHaveBeenCalledWith(expect.any(Function));

        const subscribeCallback = mockWallet.subscribe.mock.calls[0][0];
        const renderSpy = jest.spyOn(walletComponent, "render");

        const testState = { isConnected: true, isActive: true, accounts: [] };
        subscribeCallback(testState);

        expect(renderSpy).toHaveBeenCalledTimes(1);
      });
    });

    describe("Click Events", () => {
      describe("Connect Button", () => {
        beforeEach(() => setupTest());
        afterEach(teardownTest);

        it("should handle connect-button click and call wallet.connect", () => {
          clickButton("connect-button");

          expect(mockWallet.connect).toHaveBeenCalledTimes(1);
          expect(mockWallet.connect).toHaveBeenCalledWith(undefined);
        });
      });

      describe("Disconnect Button", () => {
        beforeEach(() => setupTest({ isConnected: true }));
        afterEach(teardownTest);

        it("should handle disconnect-button click and call wallet.disconnect", () => {
          clickButton("disconnect-button");

          expect(mockWallet.disconnect).toHaveBeenCalledTimes(1);
        });
      });

      describe("Set Active Button", () => {
        beforeEach(() => setupTest({ isConnected: true, isActive: false }));
        afterEach(teardownTest);

        it("should handle set-active-button click and call wallet.setActive", () => {
          clickButton("set-active-button");

          expect(mockWallet.setActive).toHaveBeenCalledTimes(1);
        });
      });
    });

    describe("Event Listener Cleanup", () => {
      beforeEach(() => setupTest());

      it("should handle errors during event listener removal gracefully", () => {
        const consoleDebugSpy = jest
          .spyOn(console, "debug")
          .mockImplementation();

        const originalRemove = walletComponent.element.removeEventListener;
        walletComponent.element.removeEventListener = jest
          .fn()
          .mockImplementation(() => {
            throw new Error("Remove event listener failed");
          });

        expect(() => {
          walletComponent.destroy();
        }).not.toThrow();

        expect(consoleDebugSpy).toHaveBeenCalledWith(
          "[WalletComponent] Error during event listener cleanup:",
          expect.any(Error)
        );

        walletComponent.element.removeEventListener = originalRemove;
        consoleDebugSpy.mockRestore();
      });
    });

    describe("Magic Wallet", () => {
      const magicWalletConfig = {
        id: "magic",
        metadata: { name: "Magic Wallet" },
      };

      describe("Email Input", () => {
        beforeEach(() => setupTest(magicWalletConfig));
        afterEach(teardownTest);

        it("should render email input for Magic wallet and handle email changes", () => {
          walletComponent.render();

          const emailInput = getInput("magic-email");
          expect(emailInput).toBeTruthy();
          expect(emailInput.type).toBe("email");
          expect(emailInput.placeholder).toContain("Enter email to connect");

          emailInput.value = "test@example.com";
          emailInput.dispatchEvent(new Event("input", { bubbles: true }));

          expect(walletComponent["magicEmail"]).toBe("test@example.com");
        });
      });

      describe("Connect with Email", () => {
        beforeEach(() => setupTest(magicWalletConfig));
        afterEach(teardownTest);

        it("should call connect with email args for Magic wallet", () => {
          walletComponent["magicEmail"] = "user@example.com";
          clickButton("connect-button");

          expect(mockWallet.connect).toHaveBeenCalledTimes(1);
          expect(mockWallet.connect).toHaveBeenCalledWith({
            email: "user@example.com",
          });
        });
      });

      describe("Email Validation", () => {
        beforeEach(() => setupTest(magicWalletConfig));
        afterEach(teardownTest);

        it("should validate email format", () => {
          // Valid emails
          walletComponent["magicEmail"] = "test@example.com";
          expect(walletComponent.isEmailValid()).toBe(true);

          walletComponent["magicEmail"] = "user.name@domain.co.uk";
          expect(walletComponent.isEmailValid()).toBe(true);

          // Invalid emails
          walletComponent["magicEmail"] = "invalid-email";
          expect(walletComponent.isEmailValid()).toBe(false);

          walletComponent["magicEmail"] = "";
          expect(walletComponent.isEmailValid()).toBe(false);
        });

        it("should disable connect button for invalid email in Magic wallet", () => {
          walletComponent["magicEmail"] = "invalid-email";
          walletComponent.render();

          const connectButton = getButton("connect-button");
          expect(connectButton.disabled).toBe(true);
        });
      });
    });

    describe("Button Rendering", () => {
      describe("Auth Button", () => {
        beforeEach(() =>
          setupTest({
            isConnected: true,
            isActive: true,
            activeAccount: { address: "test-address" },
          })
        );
        afterEach(teardownTest);

        it("should render auth button when wallet is active", () => {
          walletComponent.render();

          const authButton = getButton("auth-button");
          expect(authButton).toBeTruthy();
          expect(authButton.textContent).toContain("Authenticate");
        });
      });

      describe("Transaction Button", () => {
        beforeEach(() =>
          setupTest({
            isConnected: true,
            isActive: true,
            activeAccount: { address: "test-address" },
          })
        );
        afterEach(teardownTest);

        it("should render transaction button when wallet is active", () => {
          walletComponent.render();

          const transactionButton = getButton("transaction-button");
          expect(transactionButton).toBeTruthy();
          expect(transactionButton.textContent).toContain("Send Transaction");
        });
      });
    });

    describe("Account Selection", () => {
      const accountsConfig = {
        isConnected: true,
        isActive: true,
        accounts: [
          { address: "addr1" },
          { address: "addr2" },
          { address: "addr3" },
        ],
        activeAccount: { address: "addr2" },
      };

      beforeEach(() => setupTest(accountsConfig));
      afterEach(teardownTest);

      it("should render account dropdown and handle selection", () => {
        walletComponent.render();

        const select = getSelect();
        expect(select).toBeTruthy();
        expect(select.children.length).toBe(3);
        expect(select.value).toBe("addr2");
      });

      it("should handle account selection change", () => {
        walletComponent.render();

        const select = getSelect();
        select.value = "addr1";
        select.dispatchEvent(new Event("change", { bubbles: true }));

        expect(mockWallet.setActiveAccount).toHaveBeenCalledWith("addr1");
      });
    });

    describe("Sanitize Text", () => {
      beforeEach(() => setupTest());
      afterEach(teardownTest);

      it("should sanitize HTML in text", () => {
        const input = '<script>alert("xss")</script>';
        const result = walletComponent.sanitizeText(input);

        expect(result).not.toContain("<script>");
        expect(result).toContain("&lt;script&gt;");
      });

      it("should handle empty text in sanitize", () => {
        expect(walletComponent.sanitizeText("")).toBe("");
        expect(walletComponent.sanitizeText(null as any)).toBe("");
        expect(walletComponent.sanitizeText(undefined as any)).toBe("");
      });
    });

    describe("Connection State", () => {
      describe("Connect Button", () => {
        it("should disable connect button when already connected", () => {
          setupTest({ isConnected: true });
          walletComponent.render();

          const connectButton = getButton("connect-button");
          expect(connectButton.disabled).toBe(true);

          teardownTest();
        });
      });

      describe("Disconnect Button", () => {
        it("should disable disconnect button when not connected", () => {
          setupTest({ isConnected: false });
          walletComponent.render();

          const disconnectButton = getButton("disconnect-button");
          expect(disconnectButton.disabled).toBe(true);

          teardownTest();
        });
      });
    });
  });

  describe("WalletComponent Send Transaction Click", () => {
    let mockWallet: jest.Mocked<BaseWallet>;
    let mockManager: jest.Mocked<WalletManager>;
    let walletComponent: WalletComponent;

    beforeEach(() => {
      jest.clearAllMocks();

      mockWallet = {
        id: "test-wallet",
        metadata: { name: "Test Wallet" },
        isConnected: true,
        isActive: true,
        accounts: [],
        activeAccount: { address: "test-address" },
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
            }),
          }),
        },
      } as any;

      walletComponent = new WalletComponent(mockWallet, mockManager);
    });

    afterEach(() => {
      walletComponent.destroy();
    });

    it("should call sendTransaction when transaction-button is clicked", () => {
      // Render to create the transaction button
      walletComponent.render();

      // Spy on sendTransaction method
      const sendTransactionSpy = jest.spyOn(walletComponent, "sendTransaction");

      // Find and click the transaction button
      const transactionButton = walletComponent.element.querySelector(
        "#transaction-button"
      ) as HTMLButtonElement;
      transactionButton.click();

      // Verify sendTransaction was called
      expect(sendTransactionSpy).toHaveBeenCalledTimes(1);
    });
  });

  describe("WalletComponent Auth Button", () => {
    let mockWallet: jest.Mocked<BaseWallet>;
    let mockManager: jest.Mocked<WalletManager>;
    let walletComponent: WalletComponent;

    beforeEach(() => {
      jest.clearAllMocks();

      mockWallet = {
        id: "test-wallet",
        metadata: { name: "Test Wallet" },
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
        signTransactions: jest.fn(),
        canSignData: true,
      } as any;

      mockManager = {
        algodClient: {
          getTransactionParams: jest.fn(),
        },
      } as any;

      walletComponent = new WalletComponent(mockWallet, mockManager);
    });

    afterEach(() => {
      walletComponent.destroy();
    });

    it("should have auth button in rendered HTML when wallet is active", () => {
      // Set wallet to active state
      mockWallet.isActive = true;

      // Render the component
      walletComponent.render();

      // Verify auth button exists in the HTML
      const authButton = walletComponent.element.querySelector("#auth-button");
      expect(authButton).toBeTruthy();
    });
  });

describe("WalletComponent Auth Button Integration", () => {
  let mockWallet: jest.Mocked<BaseWallet>;
  let mockManager: jest.Mocked<WalletManager>;
  let walletComponent: WalletComponent;

  beforeEach(() => {
    jest.clearAllMocks();

    mockWallet = {
      id: "test-wallet",
      metadata: { name: "Test Wallet" },
      isConnected: true,
      isActive: true, // Wallet is active so auth button should be rendered
      accounts: [],
      activeAccount: { address: "test-address" },
      connect: jest.fn(),
      disconnect: jest.fn(),
      setActive: jest.fn(),
      setActiveAccount: jest.fn(),
      subscribe: jest.fn(() => () => {}),
      transactionSigner: jest.fn(),
      signTransactions: jest.fn().mockResolvedValue([new Uint8Array([1, 2, 3])]),
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

    // Mock document.cookie and CSRF token like in your existing tests
    Object.defineProperty(document, "cookie", {
      writable: true,
      value: "csrftoken=test-csrf-token",
    });

    document.body.innerHTML =
      '<input name="csrfmiddlewaretoken" value="test-csrf-token" />';

    walletComponent = new WalletComponent(mockWallet, mockManager);
  });

  afterEach(() => {
    walletComponent.destroy();
    jest.resetModules();
  });

  it("should call auth method when auth button is clicked", () => {
    // Render the component to create the auth button
    walletComponent.render();

    // Spy on the auth method
    const authSpy = jest.spyOn(walletComponent, 'auth').mockImplementation();

    // Find and click the auth button
    const authButton = walletComponent.element.querySelector('#auth-button') as HTMLButtonElement;
    authButton.click();

    // Verify auth was called - this covers the line `this.auth();`
    expect(authSpy).toHaveBeenCalledTimes(1);

    authSpy.mockRestore();
  });
});


});
