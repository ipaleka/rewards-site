import { ReclaimAllocationsComponent } from "./ReclaimAllocationsComponent";
import { RewardsClient } from "./RewardsClient";

// Mock RewardsClient
jest.mock("./RewardsClient", () => {
  return {
    RewardsClient: jest.fn().mockImplementation(() => {
      return {
        fetchReclaimAllocationsData: jest.fn(),
        reclaimAllocation: jest.fn(),
      };
    }),
  };
});

describe("ReclaimAllocationsComponent", () => {
  let mockRewardsClient: jest.Mocked<RewardsClient>;
  let mockWalletManager: jest.Mocked<WalletManager>;
  let reclaimAllocationsComponent: ReclaimAllocationsComponent;
  let alertSpy: jest.SpyInstance;

  beforeEach(() => {
    alertSpy = jest.spyOn(window, "alert").mockImplementation(() => {});
    mockRewardsClient = new RewardsClient(
      null as any,
      null as any
    ) as jest.Mocked<RewardsClient>;
    mockWalletManager = {
      activeAccount: { address: "test-address" },
      subscribe: jest.fn(),
    } as any;
  });

  afterEach(() => {
    document.body.innerHTML = "";
    alertSpy.mockRestore();
  });

  it("should fetch and display reclaimable addresses on initialization", async () => {
    const data = { addresses: ["addr1", "addr2"] };
    (
      mockRewardsClient.fetchReclaimAllocationsData as jest.Mock
    ).mockResolvedValue(data);

    reclaimAllocationsComponent = new ReclaimAllocationsComponent(
      mockRewardsClient,
      mockWalletManager
    );
    document.body.appendChild(reclaimAllocationsComponent.element);
    await new Promise(process.nextTick);

    const listItems =
      reclaimAllocationsComponent.element.querySelectorAll("li");
    expect(listItems.length).toBe(2);
    expect(listItems[0].textContent).toContain("addr1");
    expect(listItems[1].textContent).toContain("addr2");
    expect(mockRewardsClient.fetchReclaimAllocationsData).toHaveBeenCalledWith(
      "test-address"
    );
  });

  it("should display a message when no reclaimable allocations are found", async () => {
    const data = { addresses: [] };
    (
      mockRewardsClient.fetchReclaimAllocationsData as jest.Mock
    ).mockResolvedValue(data);

    reclaimAllocationsComponent = new ReclaimAllocationsComponent(
      mockRewardsClient,
      mockWalletManager
    );
    document.body.appendChild(reclaimAllocationsComponent.element);
    await new Promise(process.nextTick);

    const paragraph = reclaimAllocationsComponent.element.querySelector("p");
    expect(paragraph?.textContent).toBe("No reclaimable allocations found.");
  });

  it("should call reclaimAllocation with the correct address when a reclaim button is clicked", async () => {
    const data = { addresses: ["addr-to-reclaim"] };
    (
      mockRewardsClient.fetchReclaimAllocationsData as jest.Mock
    ).mockResolvedValue(data);
    reclaimAllocationsComponent = new ReclaimAllocationsComponent(
      mockRewardsClient,
      mockWalletManager
    );
    document.body.appendChild(reclaimAllocationsComponent.element);
    await new Promise(process.nextTick);

    const button = reclaimAllocationsComponent.element.querySelector(
      "#reclaim-button-addr-to-reclaim"
    ) as HTMLButtonElement;
    await button.click();

    expect(mockRewardsClient.reclaimAllocation).toHaveBeenCalledWith(
      "addr-to-reclaim"
    );
  });

  it("should re-fetch data after a successful reclaim call", async () => {
    const data = { addresses: ["addr1"] };
    (
      mockRewardsClient.fetchReclaimAllocationsData as jest.Mock
    ).mockResolvedValueOnce(data);
    reclaimAllocationsComponent = new ReclaimAllocationsComponent(
      mockRewardsClient,
      mockWalletManager
    );
    document.body.appendChild(reclaimAllocationsComponent.element);
    await new Promise(process.nextTick);

    (mockRewardsClient.reclaimAllocation as jest.Mock).mockResolvedValue(
      undefined
    );
    (
      mockRewardsClient.fetchReclaimAllocationsData as jest.Mock
    ).mockResolvedValueOnce({ addresses: [] });

    const button = reclaimAllocationsComponent.element.querySelector(
      "#reclaim-button-addr1"
    ) as HTMLButtonElement;
    await button.click();

    expect(mockRewardsClient.reclaimAllocation).toHaveBeenCalledTimes(1);
    // fetch is called once on init and once after reclaiming
    expect(mockRewardsClient.fetchReclaimAllocationsData).toHaveBeenCalledTimes(
      2
    );
  });

  it("should not fetch data if no active account", async () => {
    mockWalletManager.activeAccount = null;
    reclaimAllocationsComponent = new ReclaimAllocationsComponent(
      mockRewardsClient,
      mockWalletManager
    );
    document.body.appendChild(reclaimAllocationsComponent.element);
    await new Promise(process.nextTick);

    expect(
      mockRewardsClient.fetchReclaimAllocationsData
    ).not.toHaveBeenCalled();
  });

  describe("ReclaimAllocationsComponent Error Scenarios", () => {
    let mockRewardsClient: jest.Mocked<RewardsClient>;
    let mockWalletManager: jest.Mocked<WalletManager>;
    let reclaimAllocationsComponent: ReclaimAllocationsComponent;
    let alertSpy: jest.SpyInstance;
    let consoleErrorSpy: jest.SpyInstance;

    beforeEach(() => {
      alertSpy = jest.spyOn(window, "alert").mockImplementation(() => {});
      consoleErrorSpy = jest
        .spyOn(console, "error")
        .mockImplementation(() => {});

      mockRewardsClient = new RewardsClient(
        null as any,
        null as any
      ) as jest.Mocked<RewardsClient>;

      mockWalletManager = {
        activeAccount: { address: "test-address" },
        subscribe: jest.fn(),
      } as any;
    });

    afterEach(() => {
      document.body.innerHTML = "";
      alertSpy.mockRestore();
      consoleErrorSpy.mockRestore();
    });

    describe("fetchReclaimAllocationsData error handling", () => {
      it("should handle fetchReclaimAllocationsData errors and show alert", async () => {
        const error = new Error("API error");
        (
          mockRewardsClient.fetchReclaimAllocationsData as jest.Mock
        ).mockRejectedValue(error);

        reclaimAllocationsComponent = new ReclaimAllocationsComponent(
          mockRewardsClient,
          mockWalletManager
        );
        document.body.appendChild(reclaimAllocationsComponent.element);

        await new Promise(process.nextTick);

        expect(alertSpy).toHaveBeenCalledWith(
          "Failed to fetch reclaim allocations data: API error"
        );
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[ReclaimAllocationsComponent] Error fetching reclaim allocations data:",
          error
        );
      });

      it("should handle fetchReclaimAllocationsData network errors", async () => {
        const networkError = new Error("Network request failed");
        (
          mockRewardsClient.fetchReclaimAllocationsData as jest.Mock
        ).mockRejectedValue(networkError);

        reclaimAllocationsComponent = new ReclaimAllocationsComponent(
          mockRewardsClient,
          mockWalletManager
        );
        document.body.appendChild(reclaimAllocationsComponent.element);

        await new Promise(process.nextTick);

        expect(alertSpy).toHaveBeenCalledWith(
          "Failed to fetch reclaim allocations data: Network request failed"
        );
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[ReclaimAllocationsComponent] Error fetching reclaim allocations data:",
          networkError
        );
      });

      it("should handle fetchReclaimAllocationsData HTTP errors", async () => {
        const httpError = new Error("HTTP error! status: 500");
        (
          mockRewardsClient.fetchReclaimAllocationsData as jest.Mock
        ).mockRejectedValue(httpError);

        reclaimAllocationsComponent = new ReclaimAllocationsComponent(
          mockRewardsClient,
          mockWalletManager
        );
        document.body.appendChild(reclaimAllocationsComponent.element);

        await new Promise(process.nextTick);

        expect(alertSpy).toHaveBeenCalledWith(
          "Failed to fetch reclaim allocations data: HTTP error! status: 500"
        );
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[ReclaimAllocationsComponent] Error fetching reclaim allocations data:",
          httpError
        );
      });

      it("should handle non-Error objects in fetch errors", async () => {
        const stringError = "Unknown fetch error";
        (
          mockRewardsClient.fetchReclaimAllocationsData as jest.Mock
        ).mockRejectedValue(stringError);

        reclaimAllocationsComponent = new ReclaimAllocationsComponent(
          mockRewardsClient,
          mockWalletManager
        );
        document.body.appendChild(reclaimAllocationsComponent.element);

        await new Promise(process.nextTick);

        expect(alertSpy).toHaveBeenCalledWith(
          "Failed to fetch reclaim allocations data: Unknown fetch error"
        );
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[ReclaimAllocationsComponent] Error fetching reclaim allocations data:",
          stringError
        );
      });

      it("should clear reclaimable addresses and render when fetch fails", async () => {
        const error = new Error("Fetch failed");
        (
          mockRewardsClient.fetchReclaimAllocationsData as jest.Mock
        ).mockRejectedValue(error);

        reclaimAllocationsComponent = new ReclaimAllocationsComponent(
          mockRewardsClient,
          mockWalletManager
        );
        document.body.appendChild(reclaimAllocationsComponent.element);

        await new Promise(process.nextTick);

        const paragraph =
          reclaimAllocationsComponent.element.querySelector("p");
        expect(paragraph?.textContent).toBe(
          "No reclaimable allocations found."
        );
      });
    });

    describe("handleReclaimAllocation error handling", () => {
      beforeEach(async () => {
        // Set up with reclaimable addresses
        const data = { addresses: ["addr-to-reclaim", "addr-to-reclaim-2"] };
        (
          mockRewardsClient.fetchReclaimAllocationsData as jest.Mock
        ).mockResolvedValue(data);

        reclaimAllocationsComponent = new ReclaimAllocationsComponent(
          mockRewardsClient,
          mockWalletManager
        );
        document.body.appendChild(reclaimAllocationsComponent.element);
        await new Promise(process.nextTick);
      });

      it("should handle reclaimAllocation transaction errors and show alert", async () => {
        const reclaimError = new Error(
          "Transaction failed: insufficient balance"
        );
        (mockRewardsClient.reclaimAllocation as jest.Mock).mockRejectedValue(
          reclaimError
        );

        const button = reclaimAllocationsComponent.element.querySelector(
          "#reclaim-button-addr-to-reclaim"
        ) as HTMLButtonElement;
        await button.click();

        expect(alertSpy).toHaveBeenCalledWith(
          "Reclaim for addr-to-reclaim failed: Transaction failed: insufficient balance"
        );
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          `[ReclaimAllocationsComponent] Error during reclaim for addr-to-reclaim:`,
          reclaimError
        );
      });

      it("should handle reclaimAllocation network errors", async () => {
        const networkError = new Error("Network connection lost");
        (mockRewardsClient.reclaimAllocation as jest.Mock).mockRejectedValue(
          networkError
        );

        const button = reclaimAllocationsComponent.element.querySelector(
          "#reclaim-button-addr-to-reclaim"
        ) as HTMLButtonElement;
        await button.click();

        expect(alertSpy).toHaveBeenCalledWith(
          "Reclaim for addr-to-reclaim failed: Network connection lost"
        );
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          `[ReclaimAllocationsComponent] Error during reclaim for addr-to-reclaim:`,
          networkError
        );
      });

      it("should handle reclaimAllocation contract execution errors", async () => {
        const contractError = new Error("Smart contract execution reverted");
        (mockRewardsClient.reclaimAllocation as jest.Mock).mockRejectedValue(
          contractError
        );

        const button = reclaimAllocationsComponent.element.querySelector(
          "#reclaim-button-addr-to-reclaim-2"
        ) as HTMLButtonElement;
        await button.click();

        expect(alertSpy).toHaveBeenCalledWith(
          "Reclaim for addr-to-reclaim-2 failed: Smart contract execution reverted"
        );
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          `[ReclaimAllocationsComponent] Error during reclaim for addr-to-reclaim-2:`,
          contractError
        );
      });

      it("should handle non-Error objects in reclaim errors", async () => {
        const stringError = "Unknown reclaim error";
        (mockRewardsClient.reclaimAllocation as jest.Mock).mockRejectedValue(
          stringError
        );

        const button = reclaimAllocationsComponent.element.querySelector(
          "#reclaim-button-addr-to-reclaim"
        ) as HTMLButtonElement;
        await button.click();

        expect(alertSpy).toHaveBeenCalledWith(
          "Reclaim for addr-to-reclaim failed: Unknown reclaim error"
        );
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          `[ReclaimAllocationsComponent] Error during reclaim for addr-to-reclaim:`,
          stringError
        );
      });

      it("should NOT re-fetch data after a failed reclaim call", async () => {
        const reclaimError = new Error("Reclaim failed");
        (mockRewardsClient.reclaimAllocation as jest.Mock).mockRejectedValue(
          reclaimError
        );

        // Clear the initial fetch call count
        (
          mockRewardsClient.fetchReclaimAllocationsData as jest.Mock
        ).mockClear();

        const button = reclaimAllocationsComponent.element.querySelector(
          "#reclaim-button-addr-to-reclaim"
        ) as HTMLButtonElement;
        await button.click();

        // Should NOT re-fetch data after failure
        expect(
          mockRewardsClient.fetchReclaimAllocationsData
        ).not.toHaveBeenCalled();
      });
    });

    describe("Wallet subscription error scenarios", () => {
      it("should handle wallet manager subscription callback errors", async () => {
        const subscriptionError = new Error("Subscription callback failed");
        (
          mockRewardsClient.fetchReclaimAllocationsData as jest.Mock
        ).mockRejectedValue(subscriptionError);

        reclaimAllocationsComponent = new ReclaimAllocationsComponent(
          mockRewardsClient,
          mockWalletManager
        );

        // Trigger the subscription callback manually
        const subscribeCallback = mockWalletManager.subscribe.mock.calls[0][0];
        await subscribeCallback();

        expect(alertSpy).toHaveBeenCalledWith(
          "Failed to fetch reclaim allocations data: Subscription callback failed"
        );
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[ReclaimAllocationsComponent] Error fetching reclaim allocations data:",
          subscriptionError
        );
      });

      it("should handle wallet changes gracefully when fetch fails", async () => {
        const fetchError = new Error("Failed to fetch data");
        (
          mockRewardsClient.fetchReclaimAllocationsData as jest.Mock
        ).mockRejectedValue(fetchError);

        reclaimAllocationsComponent = new ReclaimAllocationsComponent(
          mockRewardsClient,
          mockWalletManager
        );

        // Simulate wallet change by calling subscription callback
        const subscribeCallback = mockWalletManager.subscribe.mock.calls[0][0];
        await subscribeCallback();

        const paragraph =
          reclaimAllocationsComponent.element.querySelector("p");
        expect(paragraph?.textContent).toBe(
          "No reclaimable allocations found."
        );
      });
    });
  });
});
