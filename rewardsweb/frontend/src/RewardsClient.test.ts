/**
 * Full, updated test suite (25 tests) for the new RewardsClient
 * - Mocks Rewards ABI
 * - Mocks getApplicationByID() to provide token_id
 * - Mocks makeAssetTransferTxnWithSuggestedParamsFromObject
 * - Keeps original tests, adjusted expectations for new behavior
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

// Mock the ActiveNetwork module (we’ll set its return in beforeEach)
jest.mock("./ActiveNetwork", () => ({
  getAlgodClient: jest.fn(),
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
import { getAlgodClient } from "./ActiveNetwork";

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

describe("RewardsClient", () => {
  let mockWallet: jest.Mocked<BaseWallet>;
  let mockManager: jest.Mocked<WalletManager>;
  let rewardsClient: RewardsClient;

  beforeEach(() => {
    jest.clearAllMocks();

    mockWallet = {
      activeAccount: { address: "test-address" },
      transactionSigner: jest.fn(),
    } as any;

    mockManager = {
      activeNetwork: "testnet",
      algodClient: {
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
      }
    } as any;

    // Provide full algod mock (params + app global state)
    (getAlgodClient as jest.Mock).mockReturnValue({
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
                value: { uint: 1 },
              },
            ],
          },
        }),
      }),
    });

    rewardsClient = new RewardsClient(mockWallet, mockManager);
  });

  describe("Smart Contract Interactions", () => {
    it("should call addAllocations method on the smart contract", async () => {
      const addresses = ["addr1"];
      const amounts = [100];
      await rewardsClient.addAllocations(addresses, amounts);

      expect(mockAddMethodCall).toHaveBeenCalledWith(
        expect.objectContaining({
          method: expect.any(Object),
          methodArgs: [addresses, amounts],
          // sender may be normalized by SDK; assert signer + args only
          signer: mockWallet.transactionSigner,
        })
      );
      expect(mockExecute).toHaveBeenCalled();
    });

    it("should call reclaimAllocation method on the smart contract", async () => {
      const userAddress = "addr-to-reclaim";
      await rewardsClient.reclaimAllocation(userAddress);

      expect(mockAddMethodCall).toHaveBeenCalledWith(
        expect.objectContaining({
          method: expect.any(Object),
          methodArgs: [userAddress],
          signer: mockWallet.transactionSigner,
        })
      );
      expect(mockExecute).toHaveBeenCalled();
    });

    it("should call claim method on the smart contract", async () => {
      await rewardsClient.claim();

      // Opt-in txn created
      expect(
        algosdk.makeAssetTransferTxnWithSuggestedParamsFromObject
      ).toHaveBeenCalled();

      // Method call with appForeignAssets includes tokenId=1
      expect(mockAddMethodCall).toHaveBeenCalledWith(
        expect.objectContaining({
          method: expect.any(Object),
          methodArgs: [],
          signer: mockWallet.transactionSigner,
          appForeignAssets: [1],
        })
      );
      expect(mockExecute).toHaveBeenCalled();
    });

    it("should throw an error if no active account is selected", async () => {
      mockWallet.activeAccount = null;
      rewardsClient = new RewardsClient(mockWallet, mockManager);

      await expect(
        rewardsClient.addAllocations(["addr1"], [100])
      ).rejects.toThrow("No active account selected.");
      await expect(rewardsClient.reclaimAllocation("addr1")).rejects.toThrow(
        "No active account selected."
      );
      await expect(rewardsClient.claim()).rejects.toThrow(
        "No active account selected."
      );
    });
  });

  describe("API Interactions", () => {
    beforeEach(() => {
      global.fetch = jest.fn();
    });

    it("should fetch claimable status", async () => {
      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ claimable: true }),
      });

      const result = await rewardsClient.fetchClaimableStatus("test-address");
      expect(result).toEqual({ claimable: true });
      expect(fetch).toHaveBeenCalledWith(
        "/api/wallet/claim-allocation/",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ address: "test-address" }),
        })
      );
    });

    it("should fetch add allocations data", async () => {
      const data = { addresses: ["addr1"], amounts: [100] };
      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(data),
      });

      const result = await rewardsClient.fetchAddAllocationsData(
        "test-address"
      );
      expect(result).toEqual(data);
      expect(fetch).toHaveBeenCalledWith(
        "/api/wallet/add-allocations/",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ address: "test-address" }),
        })
      );
    });

    it("should fetch reclaim allocations data", async () => {
      const data = { addresses: ["addr1"] };
      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(data),
      });

      const result = await rewardsClient.fetchReclaimAllocationsData(
        "test-address"
      );
      expect(result).toEqual(data);
      expect(fetch).toHaveBeenCalledWith(
        "/api/wallet/reclaim-allocations/",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ address: "test-address" }),
        })
      );
    });

    it("should handle API errors", async () => {
      (fetch as jest.Mock).mockResolvedValue({ ok: false, status: 404 });
      await expect(
        rewardsClient.fetchClaimableStatus("test-address")
      ).rejects.toThrow("HTTP error! status: 404");
    });
  });

  describe("RewardsClient Error Scenarios", () => {
    describe("addAllocations", () => {
      it("should throw error when addresses and amounts arrays have different lengths", async () => {
        const addresses = ["addr1", "addr2"];
        const amounts = [100];

        await expect(
          rewardsClient.addAllocations(addresses, amounts)
        ).rejects.toThrow(
          "Addresses and amounts arrays must have the same non-zero length."
        );
      });

      it("should throw error when addresses array is empty", async () => {
        const addresses: string[] = [];
        const amounts: number[] = [];

        await expect(
          rewardsClient.addAllocations(addresses, amounts)
        ).rejects.toThrow(
          "Addresses and amounts arrays must have the same non-zero length."
        );
      });

      it("should throw error when contract call fails", async () => {
        const addresses = ["addr1"];
        const amounts = [100];

        mockExecute.mockRejectedValueOnce(
          new Error("Contract execution failed")
        );

        await expect(
          rewardsClient.addAllocations(addresses, amounts)
        ).rejects.toThrow("Contract execution failed");

        expect(mockExecute).toHaveBeenCalled();
      });

      it("should log error when contract call fails", async () => {
        const consoleErrorSpy = jest
          .spyOn(console, "error")
          .mockImplementation();
        const addresses = ["addr1"];
        const amounts = [100];
        const error = new Error("Contract execution failed");

        mockExecute.mockRejectedValueOnce(error);

        await expect(
          rewardsClient.addAllocations(addresses, amounts)
        ).rejects.toThrow("Contract execution failed");

        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[RewardsClient] Error adding allocations:",
          error
        );

        consoleErrorSpy.mockRestore();
      });
    });

    describe("reclaimAllocation", () => {
      it("should throw error when contract call fails", async () => {
        const userAddress = "addr-to-reclaim";

        mockExecute.mockRejectedValueOnce(
          new Error("Reclaim execution failed")
        );

        await expect(
          rewardsClient.reclaimAllocation(userAddress)
        ).rejects.toThrow("Reclaim execution failed");

        expect(mockExecute).toHaveBeenCalled();
      });

      it("should log error when reclaim contract call fails", async () => {
        const consoleErrorSpy = jest
          .spyOn(console, "error")
          .mockImplementation();
        const userAddress = "addr-to-reclaim";
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
      });
    });

    describe("claim", () => {
      it("should throw error when contract call fails", async () => {
        mockExecute.mockRejectedValueOnce(new Error("Claim execution failed"));

        await expect(rewardsClient.claim()).rejects.toThrow(
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

        await expect(rewardsClient.claim()).rejects.toThrow(
          "Claim execution failed"
        );

        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[RewardsClient] Error claiming allocation:",
          error
        );

        consoleErrorSpy.mockRestore();
      });
    });

    describe("fetchClaimableStatus", () => {
      it("should throw error when HTTP response is not ok", async () => {
        (fetch as jest.Mock).mockResolvedValue({
          ok: false,
          status: 500,
        });

        await expect(
          rewardsClient.fetchClaimableStatus("test-address")
        ).rejects.toThrow("HTTP error! status: 500");
      });

      it("should log error when fetch fails", async () => {
        const consoleErrorSpy = jest
          .spyOn(console, "error")
          .mockImplementation();
        const error = new Error("Network error");

        (fetch as jest.Mock).mockRejectedValueOnce(error);

        await expect(
          rewardsClient.fetchClaimableStatus("test-address")
        ).rejects.toThrow("Network error");

        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[RewardsClient] Error fetching claimable status:",
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
        mockWallet.activeAccount = null;
        rewardsClient = new RewardsClient(mockWallet, mockManager);

        await expect(
          rewardsClient.addAllocations(["addr1"], [100])
        ).rejects.toThrow("No active account selected.");
      });

      it("should throw error when no active account for reclaimAllocation", async () => {
        mockWallet.activeAccount = null;
        rewardsClient = new RewardsClient(mockWallet, mockManager);

        await expect(rewardsClient.reclaimAllocation("addr1")).rejects.toThrow(
          "No active account selected."
        );
      });

      it("should throw error when no active account for claim", async () => {
        mockWallet.activeAccount = null;
        rewardsClient = new RewardsClient(mockWallet, mockManager);

        await expect(rewardsClient.claim()).rejects.toThrow(
          "No active account selected."
        );
      });
    });
  });

  describe("App ID Missing & Global State Error Scenarios", () => {
    it("should throw error when App ID is not configured for addAllocations()", async () => {
      mockManager.activeNetwork = "betanet"; // betanet has no AppId configured
      rewardsClient = new RewardsClient(mockWallet, mockManager);

      await expect(
        rewardsClient.addAllocations(["addr1"], [100])
      ).rejects.toThrow("App ID not configured for network: betanet");
    });

    it("should throw error when App ID is not configured for reclaimAllocation()", async () => {
      mockManager.activeNetwork = "betanet";
      rewardsClient = new RewardsClient(mockWallet, mockManager);

      await expect(
        rewardsClient.reclaimAllocation("addr1")
      ).rejects.toThrow("App ID not configured for network: betanet");
    });

    it("should throw error when App ID is not configured for claim()", async () => {
      mockManager.activeNetwork = "betanet";
      rewardsClient = new RewardsClient(mockWallet, mockManager);

      await expect(rewardsClient.claim()).rejects.toThrow(
        "App ID not configured for network: betanet"
      );
    });

    it("should throw error if contract global state is empty", async () => {
      // ✅ Override the ALGOD client on the manager, not getAlgodClient()
      mockManager.algodClient.getApplicationByID = jest.fn().mockReturnValue({
        do: jest.fn().mockResolvedValue({
          params: {
            globalState: [], // <-- simulate empty state
          },
        }),
      });

      rewardsClient = new RewardsClient(mockWallet, mockManager);

      await expect(rewardsClient.claim()).rejects.toThrow(
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

      rewardsClient = new RewardsClient(mockWallet, mockManager);

      await expect(rewardsClient.claim()).rejects.toThrow(
        "token_id not found in contract's global state"
      );
    });
  });
});

describe('RewardsClient userClaimed method', () => {
  let mockWallet: jest.Mocked<BaseWallet>;
  let mockManager: jest.Mocked<WalletManager>;
  let rewardsClient: RewardsClient;

  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch = jest.fn();

    mockWallet = {
      activeAccount: { address: 'test-address' },
      transactionSigner: jest.fn(),
    } as any;

    mockManager = {
      activeNetwork: 'testnet',
      algodClient: {
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
      }
    } as any;

    rewardsClient = new RewardsClient(mockWallet, mockManager);
  });

  describe('successful userClaimed calls', () => {
    it('should call userClaimed API endpoint with correct parameters', async () => {
      const address = 'test-user-address';
      const mockResponse = { success: true };

      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await rewardsClient.userClaimed(address);

      expect(result).toEqual(mockResponse);
      expect(fetch).toHaveBeenCalledWith(
        '/api/wallet/user-claimed/',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'X-CSRFToken': expect.any(String),
          }),
          body: JSON.stringify({ address }),
        })
      );
    });

    it('should handle successful userClaimed response', async () => {
      const address = 'test-address-123';
      const expectedResponse = { success: true };

      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(expectedResponse),
      });

      const result = await rewardsClient.userClaimed(address);

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

      await rewardsClient.userClaimed('test-address');

      expect(fetch).toHaveBeenCalledWith(
        '/api/wallet/user-claimed/',
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

      await rewardsClient.userClaimed('test-address');

      expect(fetch).toHaveBeenCalledWith(
        '/api/wallet/user-claimed/',
        expect.objectContaining({
          headers: expect.objectContaining({
            'X-CSRFToken': 'form-csrf-token-456',
          }),
        })
      );

      document.body.removeChild(mockInput);
    });
  });

  describe('userClaimed error handling', () => {
    it('should throw error when HTTP response is not ok', async () => {
      const address = 'test-address';

      (fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 500,
      });

      await expect(rewardsClient.userClaimed(address)).rejects.toThrow('HTTP error! status: 500');
    });

    it('should throw error when HTTP response is 400', async () => {
      const address = 'test-address';

      (fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 400,
      });

      await expect(rewardsClient.userClaimed(address)).rejects.toThrow('HTTP error! status: 400');
    });

    it('should throw error when HTTP response is 403', async () => {
      const address = 'test-address';

      (fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 403,
      });

      await expect(rewardsClient.userClaimed(address)).rejects.toThrow('HTTP error! status: 403');
    });

    it('should throw error when HTTP response is 404', async () => {
      const address = 'test-address';

      (fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 404,
      });

      await expect(rewardsClient.userClaimed(address)).rejects.toThrow('HTTP error! status: 404');
    });

    it('should log error when fetch fails', async () => {
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => { });
      const address = 'test-address';
      const error = new Error('Network connection failed');

      (fetch as jest.Mock).mockRejectedValue(error);

      await expect(rewardsClient.userClaimed(address)).rejects.toThrow('Network connection failed');

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[RewardsClient] Error sending user claimed:',
        error
      );

      consoleErrorSpy.mockRestore();
    });

    it('should handle various network error types', async () => {
      const errorScenarios = [
        new Error('DNS resolution failed'),
        'Simple network error string',
        { code: 'NETWORK_ERROR', message: 'Network unavailable' },
      ];

      for (const error of errorScenarios) {
        (fetch as jest.Mock).mockRejectedValueOnce(error);

        // For all cases, the method should reject (throw an error)
        await expect(rewardsClient.userClaimed('test-address')).rejects.toBeDefined();

        // Reset for next iteration
        (fetch as jest.Mock).mockClear();
      }
    });

  });

  describe('userClaimed edge cases', () => {
    it('should handle empty response body', async () => {
      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({}), // Empty object
      });

      const result = await rewardsClient.userClaimed('test-address');

      expect(result).toEqual({});
    });

    it('should handle different success response formats', async () => {
      const responseFormats = [
        { success: true },
        { success: true, message: 'User claimed recorded' },
        { status: 'success' },
        { result: 'ok' },
      ];

      for (const format of responseFormats) {
        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(format),
        });

        const result = await rewardsClient.userClaimed('test-address');

        expect(result).toEqual(format);
      }
    });

    it('should handle missing CSRF token gracefully', async () => {
      // Clear both cookie and form input
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: '',
      });

      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ success: true }),
      });

      // Should not throw when CSRF token is missing
      await expect(rewardsClient.userClaimed('test-address')).resolves.toEqual({ success: true });

      // Should call with empty CSRF token
      expect(fetch).toHaveBeenCalledWith(
        '/api/wallet/user-claimed/',
        expect.objectContaining({
          headers: expect.objectContaining({
            'X-CSRFToken': '',
          }),
        })
      );
    });
  });
});

