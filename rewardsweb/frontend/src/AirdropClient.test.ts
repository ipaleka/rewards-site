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

// Mock the ActiveNetwork module
jest.mock("./ActiveNetwork", () => ({
  getAlgodClient: jest.fn().mockReturnValue({
    getTransactionParams: jest.fn().mockReturnValue({
      do: jest.fn().mockResolvedValue({
        fee: 1000,
        firstRound: 1,
        lastRound: 1001,
        genesisHash: "test-hash",
        genesisID: "test-id",
      }),
    }),
  }),
}));

// Mock the ABI import
jest.mock(
  "../../contract/Airdrop.arc56.json",
  () => ({
    name: "Airdrop",
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
import { AirdropClient } from "./AirdropClient";
import { BaseWallet, WalletManager } from "@txnlab/use-wallet";
import * as algosdk from "algosdk";

// Create mock functions
const mockAddMethodCall = jest.fn();
const mockExecute = jest.fn().mockResolvedValue({
  confirmedRound: 123,
  txIDs: ["txid123"],
});

// Mock algosdk
jest.mock("algosdk", () => {
  const originalAlgosdk = jest.requireActual("algosdk");

  const MockAtomicTransactionComposer = jest.fn(() => ({
    addMethodCall: mockAddMethodCall,
    execute: mockExecute,
  }));

  return {
    ...originalAlgosdk,
    AtomicTransactionComposer: MockAtomicTransactionComposer,
  };
});

describe("AirdropClient", () => {
  let mockWallet: jest.Mocked<BaseWallet>;
  let mockManager: jest.Mocked<WalletManager>;
  let airdropClient: AirdropClient;

  beforeEach(() => {
    jest.clearAllMocks();

    mockWallet = {
      activeAccount: { address: "test-address" },
      transactionSigner: jest.fn(),
    } as any;

    mockManager = {
      activeNetwork: "testnet",
    } as any;

    airdropClient = new AirdropClient(mockWallet, mockManager);
  });

  describe("Smart Contract Interactions", () => {
    it("should call addAllocations method on the smart contract", async () => {
      const addresses = ["addr1"];
      const amounts = [100];
      await airdropClient.addAllocations(addresses, amounts);

      expect(mockAddMethodCall).toHaveBeenCalledWith(
        expect.objectContaining({
          method: expect.any(Object),
          methodArgs: [addresses, amounts],
          sender: "test-address",
          signer: mockWallet.transactionSigner,
        })
      );
      expect(mockExecute).toHaveBeenCalled();
    });

    it("should call reclaimAllocation method on the smart contract", async () => {
      const userAddress = "addr-to-reclaim";
      await airdropClient.reclaimAllocation(userAddress);

      expect(mockAddMethodCall).toHaveBeenCalledWith(
        expect.objectContaining({
          method: expect.any(Object),
          methodArgs: [userAddress],
          sender: "test-address",
          signer: mockWallet.transactionSigner,
        })
      );
      expect(mockExecute).toHaveBeenCalled();
    });

    it("should call claim method on the smart contract", async () => {
      await airdropClient.claim();

      expect(mockAddMethodCall).toHaveBeenCalledWith(
        expect.objectContaining({
          method: expect.any(Object),
          methodArgs: [],
          sender: "test-address",
          signer: mockWallet.transactionSigner,
          appForeignAssets: [1],
        })
      );
      expect(mockExecute).toHaveBeenCalled();
    });

    it("should throw an error if no active account is selected", async () => {
      mockWallet.activeAccount = null;
      airdropClient = new AirdropClient(mockWallet, mockManager);

      await expect(
        airdropClient.addAllocations(["addr1"], [100])
      ).rejects.toThrow("No active account selected.");
      await expect(airdropClient.reclaimAllocation("addr1")).rejects.toThrow(
        "No active account selected."
      );
      await expect(airdropClient.claim()).rejects.toThrow(
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

      const result = await airdropClient.fetchClaimableStatus("test-address");
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

      const result = await airdropClient.fetchAddAllocationsData(
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

      const result = await airdropClient.fetchReclaimAllocationsData(
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
        airdropClient.fetchClaimableStatus("test-address")
      ).rejects.toThrow("HTTP error! status: 404");
    });
  });

  describe("AirdropClient Error Scenarios", () => {
    describe("addAllocations", () => {
      it("should throw error when addresses and amounts arrays have different lengths", async () => {
        const addresses = ["addr1", "addr2"];
        const amounts = [100];

        await expect(
          airdropClient.addAllocations(addresses, amounts)
        ).rejects.toThrow(
          "Addresses and amounts arrays must have the same non-zero length."
        );
      });

      it("should throw error when addresses array is empty", async () => {
        const addresses: string[] = [];
        const amounts: number[] = [];

        await expect(
          airdropClient.addAllocations(addresses, amounts)
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
          airdropClient.addAllocations(addresses, amounts)
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
          airdropClient.addAllocations(addresses, amounts)
        ).rejects.toThrow("Contract execution failed");

        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[AirdropClient] Error adding allocations:",
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
          airdropClient.reclaimAllocation(userAddress)
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
          airdropClient.reclaimAllocation(userAddress)
        ).rejects.toThrow("Reclaim execution failed");

        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[AirdropClient] Error reclaiming allocation:",
          error
        );

        consoleErrorSpy.mockRestore();
      });
    });

    describe("claim", () => {
      it("should throw error when contract call fails", async () => {
        mockExecute.mockRejectedValueOnce(new Error("Claim execution failed"));

        await expect(airdropClient.claim()).rejects.toThrow(
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

        await expect(airdropClient.claim()).rejects.toThrow(
          "Claim execution failed"
        );

        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[AirdropClient] Error claiming allocation:",
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
          airdropClient.fetchClaimableStatus("test-address")
        ).rejects.toThrow("HTTP error! status: 500");
      });

      it("should log error when fetch fails", async () => {
        const consoleErrorSpy = jest
          .spyOn(console, "error")
          .mockImplementation();
        const error = new Error("Network error");

        (fetch as jest.Mock).mockRejectedValueOnce(error);

        await expect(
          airdropClient.fetchClaimableStatus("test-address")
        ).rejects.toThrow("Network error");

        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[AirdropClient] Error fetching claimable status:",
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
          airdropClient.fetchAddAllocationsData("test-address")
        ).rejects.toThrow("HTTP error! status: 400");
      });

      it("should log error when fetch fails", async () => {
        const consoleErrorSpy = jest
          .spyOn(console, "error")
          .mockImplementation();
        const error = new Error("Network error");

        (fetch as jest.Mock).mockRejectedValueOnce(error);

        await expect(
          airdropClient.fetchAddAllocationsData("test-address")
        ).rejects.toThrow("Network error");

        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[AirdropClient] Error fetching add allocations data:",
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
          airdropClient.fetchReclaimAllocationsData("test-address")
        ).rejects.toThrow("HTTP error! status: 403");
      });

      it("should log error when fetch fails", async () => {
        const consoleErrorSpy = jest
          .spyOn(console, "error")
          .mockImplementation();
        const error = new Error("Network error");

        (fetch as jest.Mock).mockRejectedValueOnce(error);

        await expect(
          airdropClient.fetchReclaimAllocationsData("test-address")
        ).rejects.toThrow("Network error");

        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[AirdropClient] Error fetching reclaim allocations data:",
          error
        );

        consoleErrorSpy.mockRestore();
      });
    });

    describe("No active account scenarios", () => {
      it("should throw error when no active account for addAllocations", async () => {
        mockWallet.activeAccount = null;
        airdropClient = new AirdropClient(mockWallet, mockManager);

        await expect(
          airdropClient.addAllocations(["addr1"], [100])
        ).rejects.toThrow("No active account selected.");
      });

      it("should throw error when no active account for reclaimAllocation", async () => {
        mockWallet.activeAccount = null;
        airdropClient = new AirdropClient(mockWallet, mockManager);

        await expect(airdropClient.reclaimAllocation("addr1")).rejects.toThrow(
          "No active account selected."
        );
      });

      it("should throw error when no active account for claim", async () => {
        mockWallet.activeAccount = null;
        airdropClient = new AirdropClient(mockWallet, mockManager);

        await expect(airdropClient.claim()).rejects.toThrow(
          "No active account selected."
        );
      });
    });
  });
});
