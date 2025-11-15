/**
 * Full, updated test suite for the new RewardsClient
 * - Updated constructor to only use WalletManager
 * - Fixed mock setup for algodClient
 * - Added tests for new methods
 */

// Mock the use-wallet module first
jest.mock("@txnlab/use-wallet", () => ({
  BaseWallet: jest.fn(),
  WalletManager: jest.fn(),
  NetworkId: {
    TESTNET: "testnet",
    MAINNET: "mainnet",
    BETANET: "betanet",
  },
}));

// Mock the ABI import (Rewards ABI in the new code)
jest.mock(
  "../../contract/artifacts/Rewards.arc56.json",
  () => ({
    name: "Rewards",
    methods: [
      {
        name: "add_allocations",
        args: [{ type: "address[]" }, { type: "uint64[]" }],
        returns: { type: "void" },
      },
      {
        name: "reclaim_allocation",
        args: [{ type: "address" }],
        returns: { type: "void" },
      },
      { name: "claim", args: [], returns: { type: "void" } },
    ],
  }),
  { virtual: true }
);

// Now import the actual modules
import { RewardsClient } from "./RewardsClient";
import { BaseWallet, WalletManager } from "@txnlab/use-wallet";
import * as algosdk from "algosdk";

// Create mock functions
const mockAddMethodCall = jest.fn();
const mockAddTransaction = jest.fn();
const mockExecute = jest.fn().mockResolvedValue({
  confirmedRound: 123,
  txIDs: ["txid123"],
});

// Mock algosdk
jest.mock("algosdk", () => {
  const originalAlgosdk = jest.requireActual("algosdk");

  const MockAtomicTransactionComposer = jest.fn(() => ({
    addMethodCall: mockAddMethodCall,
    addTransaction: mockAddTransaction,
    execute: mockExecute,
  }));

  return {
    ...originalAlgosdk,
    AtomicTransactionComposer: MockAtomicTransactionComposer,
    makeAssetTransferTxnWithSuggestedParamsFromObject: jest
      .fn()
      .mockReturnValue({ mockTxn: true }),
  };
});

// Valid Algorand test addresses (58 characters)
const TEST_ADDRESS_1 = "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU";
const TEST_ADDRESS_2 = "VW55KZ3NF4GDOWI7IPWLGZDFWNXWKSRD5PETRLDABZVU5XPKRJJRK3CBSU";
const TEST_ADDRESS_3 = "LXJ3Q6RZ2TJ6VCJDFMSM4ZVNYYYE4KVSL3N2TYR23PLNCJCIXBM3NYTBYE";

describe("RewardsClient", () => {
  let mockManager: jest.Mocked<WalletManager>;
  let rewardsClient: RewardsClient;

  beforeEach(() => {
    jest.clearAllMocks();

    // Setup CSRF token for tests
    Object.defineProperty(document, 'cookie', {
      writable: true,
      value: 'csrftoken=test-csrf-token',
    });

    // Create a proper mock algod client
    const mockAlgodClient = {
      getTransactionParams: jest.fn().mockReturnValue({
        do: jest.fn().mockResolvedValue({
          fee: 1000,
          firstRound: 1,
          lastRound: 1001,
          genesisHash: "test-hash",
          genesisID: "test-id",
        }),
      }),
      getApplicationByID: jest.fn().mockReturnValue({
        do: jest.fn().mockResolvedValue({
          params: {
            globalState: [
              {
                key: btoa("token_id"),
                value: { uint: 1 }
              }
            ]
          }
        })
      })
    };

    mockManager = {
      activeAccount: { address: TEST_ADDRESS_1 },
      activeNetwork: "testnet",
      algodClient: mockAlgodClient,
      transactionSigner: jest.fn(),
      wallets: [],
      subscribe: jest.fn(),
      resumeSessions: jest.fn(),
      getWallet: jest.fn(),
    } as any;

    rewardsClient = new RewardsClient(mockManager);
  });

  describe("Smart Contract Interactions", () => {
    it("should call addAllocations method on the smart contract", async () => {
      const addresses = [TEST_ADDRESS_2];
      const amounts = [100];
      await rewardsClient.addAllocations(addresses, amounts, 6);

      expect(mockAddMethodCall).toHaveBeenCalledWith(
        expect.objectContaining({
          method: expect.any(Object),
          methodArgs: [addresses, expect.any(Array)], // amounts are converted to micro amounts
          signer: mockManager.transactionSigner,
        })
      );
      expect(mockExecute).toHaveBeenCalled();
    });

    it("should call reclaimAllocation method on the smart contract", async () => {
      const userAddress = TEST_ADDRESS_2;
      await rewardsClient.reclaimAllocation(userAddress);

      expect(mockAddMethodCall).toHaveBeenCalledWith(
        expect.objectContaining({
          method: expect.any(Object),
          methodArgs: [userAddress],
          signer: mockManager.transactionSigner,
          boxes: expect.any(Array), // Should include box reference
        })
      );
      expect(mockExecute).toHaveBeenCalled();
    });


    it("should call claim method on the smart contract", async () => {
      await rewardsClient.claimRewards();

      // Opt-in txn created
      expect(
        algosdk.makeAssetTransferTxnWithSuggestedParamsFromObject
      ).toHaveBeenCalled();

      // Method call with appForeignAssets includes tokenId=1
      expect(mockAddMethodCall).toHaveBeenCalledWith(
        expect.objectContaining({
          method: expect.any(Object),
          methodArgs: [],
          signer: mockManager.transactionSigner,
          appForeignAssets: [1],
        })
      );
      expect(mockExecute).toHaveBeenCalled();
    });

    it("should throw an error if no active account is selected", async () => {
      mockManager.activeAccount = null;

      await expect(
        rewardsClient.addAllocations([TEST_ADDRESS_2], [100], 6)
      ).rejects.toThrow("No active account selected.");
      await expect(rewardsClient.reclaimAllocation(TEST_ADDRESS_2)).rejects.toThrow(
        "No active account selected."
      );
      await expect(rewardsClient.claimRewards()).rejects.toThrow(
        "No active account selected."
      );
    });
  });

  describe("API Interactions", () => {
    beforeEach(() => {
      global.fetch = jest.fn();
    });

    it("should fetch add allocations data", async () => {
      const data = { addresses: [TEST_ADDRESS_2], amounts: [100] };
      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(data),
      });

      const result = await rewardsClient.fetchAddAllocationsData(TEST_ADDRESS_1);
      expect(result).toEqual(data);
      expect(fetch).toHaveBeenCalledWith(
        "/api/wallet/add-allocations/",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ address: TEST_ADDRESS_1 }),
        })
      );
    });

    it("should fetch reclaim allocations data", async () => {
      const data = { addresses: [TEST_ADDRESS_2] };
      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(data),
      });

      const result = await rewardsClient.fetchReclaimAllocationsData(TEST_ADDRESS_1);
      expect(result).toEqual(data);
      expect(fetch).toHaveBeenCalledWith(
        "/api/wallet/reclaim-allocations/",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ address: TEST_ADDRESS_1 }),
        })
      );
    });

    it("should notify allocations successful", async () => {
      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ success: true }),
      });

      const addresses = [TEST_ADDRESS_2, TEST_ADDRESS_3];
      const txIDs = ["tx1", "tx2"];
      const result = await rewardsClient.notifyAllocationsSuccessful(addresses, txIDs);

      expect(result).toEqual({ success: true });
      expect(fetch).toHaveBeenCalledWith(
        "/api/wallet/allocations-successful/",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ addresses, txIDs }),
        })
      );
    });

    it("should notify reclaim successful", async () => {
      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
      });

      const address = TEST_ADDRESS_2;
      const txID = "tx1";
      await rewardsClient.notifyReclaimSuccessful(address, txID);

      expect(fetch).toHaveBeenCalledWith(
        "/api/wallet/reclaim-successful/",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ address, txID }),
        })
      );
    });
  });

  describe("RewardsClient Error Scenarios", () => {
    describe("addAllocations", () => {
      it("should throw error when addresses and amounts arrays have different lengths", async () => {
        const addresses = [TEST_ADDRESS_2, TEST_ADDRESS_3];
        const amounts = [100];

        await expect(
          rewardsClient.addAllocations(addresses, amounts, 6)
        ).rejects.toThrow(
          "Addresses and amounts arrays must have the same non-zero length."
        );
      });

      it("should throw error when addresses array is empty", async () => {
        const addresses: string[] = [];
        const amounts: number[] = [];

        await expect(
          rewardsClient.addAllocations(addresses, amounts, 6)
        ).rejects.toThrow(
          "Addresses and amounts arrays must have the same non-zero length."
        );
      });
      it("should throw error when contract call fails", async () => {
        const addresses = [TEST_ADDRESS_2];
        const amounts = [100];

        // Mock the boxNameFromAddress to avoid address validation for this test
        const boxNameFromAddressSpy = jest.spyOn(rewardsClient as any, 'boxNameFromAddress');
        boxNameFromAddressSpy.mockReturnValue(new Uint8Array());

        mockExecute.mockRejectedValueOnce(
          new Error("Contract execution failed")
        );

        await expect(
          rewardsClient.addAllocations(addresses, amounts, 6)
        ).rejects.toThrow("Contract execution failed");

        expect(mockExecute).toHaveBeenCalled();
        boxNameFromAddressSpy.mockRestore();
      });

      it("should log error when contract call fails", async () => {
        const consoleErrorSpy = jest
          .spyOn(console, "error")
          .mockImplementation();
        const addresses = [TEST_ADDRESS_2];
        const amounts = [100];

        // Mock the boxNameFromAddress to avoid address validation for this test
        const boxNameFromAddressSpy = jest.spyOn(rewardsClient as any, 'boxNameFromAddress');
        boxNameFromAddressSpy.mockReturnValue(new Uint8Array());

        const error = new Error("Contract execution failed");

        mockExecute.mockRejectedValueOnce(error);

        await expect(
          rewardsClient.addAllocations(addresses, amounts, 6)
        ).rejects.toThrow("Contract execution failed");

        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[RewardsClient] Error adding allocations:",
          error
        );

        consoleErrorSpy.mockRestore();
        boxNameFromAddressSpy.mockRestore();
      });
    });

    describe("reclaimAllocation", () => {
      it("should throw error when contract call fails", async () => {
        const userAddress = TEST_ADDRESS_2;

        // Mock the boxNameFromAddress to avoid address validation for this test
        const boxNameFromAddressSpy = jest.spyOn(rewardsClient as any, 'boxNameFromAddress');
        boxNameFromAddressSpy.mockReturnValue(new Uint8Array());

        mockExecute.mockRejectedValueOnce(
          new Error("Reclaim execution failed")
        );

        await expect(
          rewardsClient.reclaimAllocation(userAddress)
        ).rejects.toThrow("Reclaim execution failed");

        expect(mockExecute).toHaveBeenCalled();
        boxNameFromAddressSpy.mockRestore();
      });

      it("should log error when reclaim contract call fails", async () => {
        const consoleErrorSpy = jest
          .spyOn(console, "error")
          .mockImplementation();
        const userAddress = TEST_ADDRESS_2;

        // Mock the boxNameFromAddress to avoid address validation for this test
        const boxNameFromAddressSpy = jest.spyOn(rewardsClient as any, 'boxNameFromAddress');
        boxNameFromAddressSpy.mockReturnValue(new Uint8Array());

        const error = new Error("Reclaim execution failed");

        mockExecute.mockRejectedValueOnce(error);

        await expect(
          rewardsClient.reclaimAllocation(userAddress)
        ).rejects.toThrow("Reclaim execution failed");

        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[RewardsClient] Error reclaiming allocation:",
          error
        );

        consoleErrorSpy.mockRestore();
        boxNameFromAddressSpy.mockRestore();
      });
    });

    describe("claim", () => {
      it("should throw error when contract call fails", async () => {
        mockExecute.mockRejectedValueOnce(new Error("Claim execution failed"));

        await expect(rewardsClient.claimRewards()).rejects.toThrow(
          "Claim execution failed"
        );

        expect(mockExecute).toHaveBeenCalled();
      });

      it("should log error when claim contract call fails", async () => {
        const consoleErrorSpy = jest
          .spyOn(console, "error")
          .mockImplementation();
        const error = new Error("Claim execution failed");

        mockExecute.mockRejectedValueOnce(error);

        await expect(rewardsClient.claimRewards()).rejects.toThrow(
          "Claim execution failed"
        );

        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[RewardsClient] Error claiming allocation:",
          error
        );

        consoleErrorSpy.mockRestore();
      });
    });

    describe("fetchAddAllocationsData", () => {
      it("should throw error when HTTP response is not ok", async () => {
        (fetch as jest.Mock).mockResolvedValue({
          ok: false,
          status: 400,
        });

        await expect(
          rewardsClient.fetchAddAllocationsData("test-address")
        ).rejects.toThrow("HTTP error! status: 400");
      });

      it("should log error when fetch fails", async () => {
        const consoleErrorSpy = jest
          .spyOn(console, "error")
          .mockImplementation();
        const error = new Error("Network error");

        (fetch as jest.Mock).mockRejectedValueOnce(error);

        await expect(
          rewardsClient.fetchAddAllocationsData("test-address")
        ).rejects.toThrow("Network error");

        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[RewardsClient] Error fetching add allocations data:",
          error
        );

        consoleErrorSpy.mockRestore();
      });
    });

    describe("fetchReclaimAllocationsData", () => {
      it("should throw error when HTTP response is not ok", async () => {
        (fetch as jest.Mock).mockResolvedValue({
          ok: false,
          status: 403,
        });

        await expect(
          rewardsClient.fetchReclaimAllocationsData("test-address")
        ).rejects.toThrow("HTTP error! status: 403");
      });

      it("should log error when fetch fails", async () => {
        const consoleErrorSpy = jest
          .spyOn(console, "error")
          .mockImplementation();
        const error = new Error("Network error");

        (fetch as jest.Mock).mockRejectedValueOnce(error);

        await expect(
          rewardsClient.fetchReclaimAllocationsData("test-address")
        ).rejects.toThrow("Network error");

        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[RewardsClient] Error fetching reclaim allocations data:",
          error
        );

        consoleErrorSpy.mockRestore();
      });
    });

    describe("No active account scenarios", () => {
      it("should throw error when no active account for addAllocations", async () => {
        mockManager.activeAccount = null;

        await expect(
          rewardsClient.addAllocations(["addr1"], [100], 6)
        ).rejects.toThrow("No active account selected.");
      });

      it("should throw error when no active account for reclaimAllocation", async () => {
        mockManager.activeAccount = null;

        await expect(rewardsClient.reclaimAllocation("addr1")).rejects.toThrow(
          "No active account selected."
        );
      });

      it("should throw error when no active account for claim", async () => {
        mockManager.activeAccount = null;

        await expect(rewardsClient.claimRewards()).rejects.toThrow(
          "No active account selected."
        );
      });
    });
  });

  describe("App ID Missing & Global State Error Scenarios", () => {
    it("should throw error when App ID is not configured for addAllocations()", async () => {
      mockManager.activeNetwork = "betanet"; // betanet has no AppId configured

      await expect(
        rewardsClient.addAllocations([TEST_ADDRESS_2], [100], 6)
      ).rejects.toThrow("App ID not configured for network: betanet");
    });

    it("should throw error when App ID is not configured for reclaimAllocation()", async () => {
      mockManager.activeNetwork = "betanet";

      await expect(
        rewardsClient.reclaimAllocation(TEST_ADDRESS_2)
      ).rejects.toThrow("App ID not configured for network: betanet");
    });

    it("should throw error when App ID is not configured for claimRewards()", async () => {
      mockManager.activeNetwork = "betanet";

      await expect(rewardsClient.claimRewards()).rejects.toThrow(
        "App ID not configured for network: betanet"
      );
    });

    it("should throw error if contract global state is empty", async () => {
      mockManager.algodClient.getApplicationByID = jest.fn().mockReturnValue({
        do: jest.fn().mockResolvedValue({
          params: {
            globalState: [], // <-- simulate empty state
          },
        }),
      });

      await expect(rewardsClient.claimRewards()).rejects.toThrow(
        "Contract global state is empty or not found"
      );
    });

    it("should throw error when token_id key is missing in global state", async () => {
      mockManager.algodClient.getApplicationByID = jest.fn().mockReturnValue({
        do: jest.fn().mockResolvedValue({
          params: {
            globalState: [
              { key: btoa("something_else"), value: { uint: 55 } }, // <-- no token_id here
            ],
          },
        }),
      });

      await expect(rewardsClient.claimRewards()).rejects.toThrow(
        "token_id not found in contract's global state"
      );
    });
  });
});

describe('RewardsClient notifyClaimSuccessful method', () => {
  let mockManager: jest.Mocked<WalletManager>;
  let rewardsClient: RewardsClient;

  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch = jest.fn();

    // Setup CSRF token for tests
    Object.defineProperty(document, 'cookie', {
      writable: true,
      value: 'csrftoken=test-csrf-token',
    });

    const mockAlgodClient = {
      getTransactionParams: jest.fn().mockReturnValue({
        do: jest.fn().mockResolvedValue({
          fee: 1000,
          firstRound: 1,
          lastRound: 1001,
          genesisHash: 'test-hash',
          genesisID: 'test-id',
        }),
      }),
      getApplicationByID: jest.fn().mockReturnValue({
        do: jest.fn().mockResolvedValue({
          params: {
            globalState: [
              {
                key: btoa('token_id'),
                value: { uint: 1 }
              }
            ]
          }
        })
      })
    };

    mockManager = {
      activeAccount: { address: TEST_ADDRESS_1 },
      activeNetwork: 'testnet',
      algodClient: mockAlgodClient,
      transactionSigner: jest.fn(),
      wallets: [],
      subscribe: jest.fn(),
      resumeSessions: jest.fn(),
      getWallet: jest.fn(),
    } as any;

    rewardsClient = new RewardsClient(mockManager);
  });

  describe('successful notifyClaimSuccessful calls', () => {
    it('should call notifyClaimSuccessful API endpoint with correct parameters', async () => {
      const address = TEST_ADDRESS_2;
      const mockResponse = { success: true };

      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await rewardsClient.notifyClaimSuccessful(address);

      expect(result).toEqual(mockResponse);
      expect(fetch).toHaveBeenCalledWith(
        '/api/wallet/claim-successful/',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'X-CSRFToken': 'test-csrf-token',
          }),
          body: JSON.stringify({ address }),
        })
      );
    });

    it('should handle successful notifyClaimSuccessful response', async () => {
      const address = 'test-address-123';
      const expectedResponse = { success: true };

      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(expectedResponse),
      });

      const result = await rewardsClient.notifyClaimSuccessful(address);

      expect(result).toBe(expectedResponse);
    });

    it('should include CSRF token in headers', async () => {
      // Mock document.cookie to return a CSRF token
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: 'csrftoken=test-csrf-token-123',
      });

      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ success: true }),
      });

      await rewardsClient.notifyClaimSuccessful('test-address');

      expect(fetch).toHaveBeenCalledWith(
        '/api/wallet/claim-successful/',
        expect.objectContaining({
          headers: expect.objectContaining({
            'X-CSRFToken': 'test-csrf-token-123',
          }),
        })
      );
    });

    it('should fall back to form input CSRF token if cookie not available', async () => {
      // Clear cookies
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: '',
      });

      // Create a mock form input
      const mockInput = document.createElement('input');
      mockInput.name = 'csrfmiddlewaretoken';
      mockInput.value = 'form-csrf-token-456';
      document.body.appendChild(mockInput);

      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ success: true }),
      });

      await rewardsClient.notifyClaimSuccessful('test-address');

      expect(fetch).toHaveBeenCalledWith(
        '/api/wallet/claim-successful/',
        expect.objectContaining({
          headers: expect.objectContaining({
            'X-CSRFToken': 'form-csrf-token-456',
          }),
        })
      );

      document.body.removeChild(mockInput);
    });
  });

  describe('notifyClaimSuccessful error handling', () => {
    it('should throw error when HTTP response is not ok', async () => {
      const address = 'test-address';

      (fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 500,
      });

      await expect(rewardsClient.notifyClaimSuccessful(address)).rejects.toThrow('HTTP error! status: 500');
    });

    it('should throw error when HTTP response is 400', async () => {
      const address = 'test-address';

      (fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 400,
      });

      await expect(rewardsClient.notifyClaimSuccessful(address)).rejects.toThrow('HTTP error! status: 400');
    });

    it('should throw error when HTTP response is 403', async () => {
      const address = 'test-address';

      (fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 403,
      });

      await expect(rewardsClient.notifyClaimSuccessful(address)).rejects.toThrow('HTTP error! status: 403');
    });

    it('should throw error when HTTP response is 404', async () => {
      const address = 'test-address';

      (fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 404,
      });

      await expect(rewardsClient.notifyClaimSuccessful(address)).rejects.toThrow('HTTP error! status: 404');
    });

    it('should log error when fetch fails', async () => {
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => { });
      const address = 'test-address';
      const error = new Error('Network connection failed');

      (fetch as jest.Mock).mockRejectedValue(error);

      await expect(rewardsClient.notifyClaimSuccessful(address)).rejects.toThrow('Network connection failed');

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[RewardsClient] Error sending user claimed:',
        error
      );

      consoleErrorSpy.mockRestore();
    });
  });


  describe("RewardsClient Global State Error Scenarios", () => {
    it("should throw error when global state is empty in addAllocations", async () => {
      mockManager.algodClient.getApplicationByID = jest.fn().mockReturnValue({
        do: jest.fn().mockResolvedValue({
          params: {
            globalState: [], // Empty global state
          },
        }),
      });

      await expect(
        rewardsClient.addAllocations([TEST_ADDRESS_2], [100], 6)
      ).rejects.toThrow("Contract global state is empty or not found");
    });

    it("should throw error when token_id is missing in global state for addAllocations", async () => {
      mockManager.algodClient.getApplicationByID = jest.fn().mockReturnValue({
        do: jest.fn().mockResolvedValue({
          params: {
            globalState: [
              { key: btoa("some_other_key"), value: { uint: 123 } }, // No token_id
            ],
          },
        }),
      });

      await expect(
        rewardsClient.addAllocations([TEST_ADDRESS_2], [100], 6)
      ).rejects.toThrow("token_id not found in contract's global state");
    });

    it("should throw error when global state is empty in reclaimAllocation", async () => {
      mockManager.algodClient.getApplicationByID = jest.fn().mockReturnValue({
        do: jest.fn().mockResolvedValue({
          params: {
            globalState: [], // Empty global state
          },
        }),
      });

      await expect(
        rewardsClient.reclaimAllocation(TEST_ADDRESS_2)
      ).rejects.toThrow("Contract global state is empty or not found");
    });

    it("should throw error when token_id is missing in global state for reclaimAllocation", async () => {
      mockManager.algodClient.getApplicationByID = jest.fn().mockReturnValue({
        do: jest.fn().mockResolvedValue({
          params: {
            globalState: [
              { key: btoa("different_key"), value: { uint: 456 } }, // No token_id
            ],
          },
        }),
      });

      await expect(
        rewardsClient.reclaimAllocation(TEST_ADDRESS_2)
      ).rejects.toThrow("token_id not found in contract's global state");
    });

    it("should throw error when global state is empty in claim", async () => {
      mockManager.algodClient.getApplicationByID = jest.fn().mockReturnValue({
        do: jest.fn().mockResolvedValue({
          params: {
            globalState: [], // Empty global state
          },
        }),
      });

      await expect(rewardsClient.claimRewards()).rejects.toThrow(
        "Contract global state is empty or not found"
      );
    });

    it("should throw error when token_id is missing in global state for claim", async () => {
      mockManager.algodClient.getApplicationByID = jest.fn().mockReturnValue({
        do: jest.fn().mockResolvedValue({
          params: {
            globalState: [
              { key: btoa("not_token_id"), value: { uint: 789 } }, // No token_id
            ],
          },
        }),
      });

      await expect(rewardsClient.claimRewards()).rejects.toThrow(
        "token_id not found in contract's global state"
      );
    });
  });

  describe("RewardsClient API Error Scenarios", () => {
    beforeEach(() => {
      global.fetch = jest.fn();
    });

    describe("notifyAllocationsSuccessful error handling", () => {
      it("should throw error when HTTP response is not ok", async () => {
        const addresses = [TEST_ADDRESS_2];
        const txIDs = ["tx1"];

        (fetch as jest.Mock).mockResolvedValue({
          ok: false,
          status: 500,
        });

        await expect(
          rewardsClient.notifyAllocationsSuccessful(addresses, txIDs)
        ).rejects.toThrow("HTTP error! status: 500");
      });

      it("should log error and rethrow when fetch fails in notifyAllocationsSuccessful", async () => {
        const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation();
        const addresses = [TEST_ADDRESS_2];
        const txIDs = ["tx1"];
        const error = new Error("Network failure");

        (fetch as jest.Mock).mockRejectedValue(error);

        await expect(
          rewardsClient.notifyAllocationsSuccessful(addresses, txIDs)
        ).rejects.toThrow("Network failure");

        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[RewardsClient] Error notifying allocations successful:",
          error
        );

        consoleErrorSpy.mockRestore();
      });

      it("should handle various HTTP error statuses in notifyAllocationsSuccessful", async () => {
        const addresses = [TEST_ADDRESS_2];
        const txIDs = ["tx1"];
        const errorStatuses = [400, 401, 403, 404, 500, 503];

        for (const status of errorStatuses) {
          (fetch as jest.Mock).mockResolvedValueOnce({
            ok: false,
            status,
          });

          await expect(
            rewardsClient.notifyAllocationsSuccessful(addresses, txIDs)
          ).rejects.toThrow(`HTTP error! status: ${status}`);

          (fetch as jest.Mock).mockClear();
        }
      });
    });

    describe("notifyReclaimSuccessful error handling", () => {
      it("should throw error when CSRF token is not found", async () => {
        // Clear CSRF token
        Object.defineProperty(document, 'cookie', {
          writable: true,
          value: '',
        });

        // Remove any form inputs
        const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (csrfInput) {
          csrfInput.remove();
        }

        await expect(
          rewardsClient.notifyReclaimSuccessful(TEST_ADDRESS_2, ["tx1"])
        ).rejects.toThrow("CSRF token not found");
      });

      it("should throw error with status and error text when HTTP response is not ok", async () => {
        const address = TEST_ADDRESS_2;
        const txIDs = ["tx1"];
        const errorText = "Internal server error";

        (fetch as jest.Mock).mockResolvedValue({
          ok: false,
          status: 500,
          text: () => Promise.resolve(errorText),
        });

        await expect(
          rewardsClient.notifyReclaimSuccessful(address, txIDs)
        ).rejects.toThrow("Failed to notify reclaim success: 500 Internal server error");
      });

      it("should handle different error responses in notifyReclaimSuccessful", async () => {
        const address = TEST_ADDRESS_2;
        const txIDs = ["tx1"];
        const errorScenarios = [
          { status: 400, text: "Bad request" },
          { status: 401, text: "Unauthorized" },
          { status: 403, text: "Forbidden" },
          { status: 404, text: "Not found" },
          { status: 422, text: "Validation error" },
        ];

        for (const scenario of errorScenarios) {
          (fetch as jest.Mock).mockResolvedValueOnce({
            ok: false,
            status: scenario.status,
            text: () => Promise.resolve(scenario.text),
          });

          await expect(
            rewardsClient.notifyReclaimSuccessful(address, txIDs)
          ).rejects.toThrow(`Failed to notify reclaim success: ${scenario.status} ${scenario.text}`);

          (fetch as jest.Mock).mockClear();
        }
      });

      it("should handle network errors in notifyReclaimSuccessful", async () => {
        const address = TEST_ADDRESS_2;
        const txIDs = ["tx1"];
        const networkError = new Error("Network connection failed");

        (fetch as jest.Mock).mockRejectedValue(networkError);

        await expect(
          rewardsClient.notifyReclaimSuccessful(address, txIDs)
        ).rejects.toThrow("Network connection failed");
      });
    });

    describe("CSRF token scenarios", () => {
      it("should use CSRF token from cookie when available", async () => {
        const cookieToken = "cookie-csrf-token";
        Object.defineProperty(document, 'cookie', {
          writable: true,
          value: `csrftoken=${cookieToken}`,
        });

        (fetch as jest.Mock).mockResolvedValue({
          ok: true,
          json: () => Promise.resolve({ success: true }),
        });

        await rewardsClient.notifyClaimSuccessful(TEST_ADDRESS_2);

        expect(fetch).toHaveBeenCalledWith(
          '/api/wallet/claim-successful/',
          expect.objectContaining({
            headers: expect.objectContaining({
              'X-CSRFToken': cookieToken,
            }),
          })
        );
      });

      it("should use CSRF token from form input when cookie is not available", async () => {
        // Clear cookie
        Object.defineProperty(document, 'cookie', {
          writable: true,
          value: '',
        });

        // Create form input with CSRF token
        const formToken = "form-csrf-token";
        const input = document.createElement('input');
        input.name = 'csrfmiddlewaretoken';
        input.value = formToken;
        document.body.appendChild(input);

        (fetch as jest.Mock).mockResolvedValue({
          ok: true,
          json: () => Promise.resolve({ success: true }),
        });

        await rewardsClient.notifyClaimSuccessful(TEST_ADDRESS_2);

        expect(fetch).toHaveBeenCalledWith(
          '/api/wallet/claim-successful/',
          expect.objectContaining({
            headers: expect.objectContaining({
              'X-CSRFToken': formToken,
            }),
          })
        );

        document.body.removeChild(input);
      });

      it("should handle missing CSRF token gracefully in API calls", async () => {
        // Clear both cookie and form input
        Object.defineProperty(document, 'cookie', {
          writable: true,
          value: '',
        });

        const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (csrfInput) {
          csrfInput.remove();
        }

        (fetch as jest.Mock).mockResolvedValue({
          ok: true,
          json: () => Promise.resolve({ success: true }),
        });

        // Should not throw for regular API calls, only for notifyReclaimSuccessful
        await expect(rewardsClient.notifyClaimSuccessful(TEST_ADDRESS_2)).resolves.toEqual({ success: true });

        expect(fetch).toHaveBeenCalledWith(
          '/api/wallet/claim-successful/',
          expect.objectContaining({
            headers: expect.objectContaining({
              'X-CSRFToken': '',
            }),
          })
        );
      });
    });
  });

  describe("RewardsClient Edge Cases", () => {
    it("should handle null global state in contract calls", async () => {
      mockManager.algodClient.getApplicationByID = jest.fn().mockReturnValue({
        do: jest.fn().mockResolvedValue({
          params: {
            globalState: null, // Null global state
          },
        }),
      });

      await expect(rewardsClient.claimRewards()).rejects.toThrow(
        "Contract global state is empty or not found"
      );
    });

    it("should handle undefined global state in contract calls", async () => {
      mockManager.algodClient.getApplicationByID = jest.fn().mockReturnValue({
        do: jest.fn().mockResolvedValue({
          params: {}, // No global state property
        }),
      });

      await expect(
        rewardsClient.addAllocations([TEST_ADDRESS_2], [100], 6)
      ).rejects.toThrow("Contract global state is empty or not found");
    });

    it("should handle malformed global state entries", async () => {
      mockManager.algodClient.getApplicationByID = jest.fn().mockReturnValue({
        do: jest.fn().mockResolvedValue({
          params: {
            globalState: [
              { key: "malformed_key", value: { uint: 1 } }, // Not base64 encoded
            ],
          },
        }),
      });

      // This should still find the token_id but might fail elsewhere
      // The test ensures we don't crash on malformed data
      await expect(rewardsClient.claimRewards()).rejects.toThrow(); // Any error is acceptable
    });
  });

});

