import { AddAllocationsComponent } from "./AddAllocationsComponent";
import { RewardsClient } from "./RewardsClient";

// Mock RewardsClient
jest.mock("./RewardsClient", () => {
  return {
    RewardsClient: jest.fn().mockImplementation(() => {
      return {
        fetchAddAllocationsData: jest.fn(),
        addAllocations: jest.fn(),
      };
    }),
  };
});

describe("AddAllocationsComponent", () => {
  let mockRewardsClient: jest.Mocked<RewardsClient>;
  let mockWalletManager: jest.Mocked<WalletManager>;
  let addAllocationsComponent: AddAllocationsComponent;
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

  it("should fetch and display allocations data on initialization", async () => {
    const data = { addresses: ["addr1"], amounts: [100] };
    (mockRewardsClient.fetchAddAllocationsData as jest.Mock).mockResolvedValue(
      data
    );

    addAllocationsComponent = new AddAllocationsComponent(
      mockRewardsClient,
      mockWalletManager
    );
    document.body.appendChild(addAllocationsComponent.element);
    await new Promise(process.nextTick);

    const addressesInput = addAllocationsComponent.element.querySelector(
      "#addresses-input"
    ) as HTMLTextAreaElement;
    const amountsInput = addAllocationsComponent.element.querySelector(
      "#amounts-input"
    ) as HTMLTextAreaElement;

    expect(addressesInput.value).toBe("addr1");
    expect(amountsInput.value).toBe("100");
    expect(mockRewardsClient.fetchAddAllocationsData).toHaveBeenCalledWith(
      "test-address"
    );
  });

  it("should call addAllocations with data from textareas when button is clicked", async () => {
    (mockRewardsClient.fetchAddAllocationsData as jest.Mock).mockResolvedValue({
      addresses: [],
      amounts: [],
    });
    addAllocationsComponent = new AddAllocationsComponent(
      mockRewardsClient,
      mockWalletManager
    );
    document.body.appendChild(addAllocationsComponent.element);
    await new Promise(process.nextTick);

    const addressesInput = addAllocationsComponent.element.querySelector(
      "#addresses-input"
    ) as HTMLTextAreaElement;
    const amountsInput = addAllocationsComponent.element.querySelector(
      "#amounts-input"
    ) as HTMLTextAreaElement;

    addressesInput.value = "addr1\naddr2";
    amountsInput.value = "100\n200";

    const button = addAllocationsComponent.element.querySelector(
      "#add-allocations-button"
    ) as HTMLButtonElement;
    await button.click();

    expect(mockRewardsClient.addAllocations).toHaveBeenCalledWith(
      ["addr1", "addr2"],
      [100, 200]
    );
  });

  it("should re-fetch data after a successful addAllocations call", async () => {
    (mockRewardsClient.fetchAddAllocationsData as jest.Mock).mockResolvedValue({
      addresses: [],
      amounts: [],
    });
    addAllocationsComponent = new AddAllocationsComponent(
      mockRewardsClient,
      mockWalletManager
    );
    document.body.appendChild(addAllocationsComponent.element);
    await new Promise(process.nextTick);

    (mockRewardsClient.addAllocations as jest.Mock).mockResolvedValue(
      undefined
    );

    const button = addAllocationsComponent.element.querySelector(
      "#add-allocations-button"
    ) as HTMLButtonElement;
    await button.click();

    expect(mockRewardsClient.addAllocations).toHaveBeenCalledTimes(1);
    // fetch is called once on init and once after adding allocations
    expect(mockRewardsClient.fetchAddAllocationsData).toHaveBeenCalledTimes(2);
  });

  it("should not fetch data if no active account", async () => {
    mockWalletManager.activeAccount = null;
    addAllocationsComponent = new AddAllocationsComponent(
      mockRewardsClient,
      mockWalletManager
    );
    document.body.appendChild(addAllocationsComponent.element);
    await new Promise(process.nextTick);

    expect(mockRewardsClient.fetchAddAllocationsData).not.toHaveBeenCalled();
  });

  describe("AddAllocationsComponent Error Scenarios", () => {
    let mockRewardsClient: jest.Mocked<RewardsClient>;
    let mockWalletManager: jest.Mocked<WalletManager>;
    let addAllocationsComponent: AddAllocationsComponent;
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

    describe("fetchAllocationsData error handling", () => {
      it("should handle fetchAddAllocationsData errors and show alert", async () => {
        const error = new Error("API error");
        (
          mockRewardsClient.fetchAddAllocationsData as jest.Mock
        ).mockRejectedValue(error);

        addAllocationsComponent = new AddAllocationsComponent(
          mockRewardsClient,
          mockWalletManager
        );
        document.body.appendChild(addAllocationsComponent.element);

        await new Promise(process.nextTick);

        expect(alertSpy).toHaveBeenCalledWith(
          "Failed to fetch allocations data: API error"
        );
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[AddAllocationsComponent] Error fetching add allocations data:",
          error
        );
      });

      it("should handle fetchAddAllocationsData network errors", async () => {
        const networkError = new Error("Network request failed");
        (
          mockRewardsClient.fetchAddAllocationsData as jest.Mock
        ).mockRejectedValue(networkError);

        addAllocationsComponent = new AddAllocationsComponent(
          mockRewardsClient,
          mockWalletManager
        );
        document.body.appendChild(addAllocationsComponent.element);

        await new Promise(process.nextTick);

        expect(alertSpy).toHaveBeenCalledWith(
          "Failed to fetch allocations data: Network request failed"
        );
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[AddAllocationsComponent] Error fetching add allocations data:",
          networkError
        );
      });

      it("should handle fetchAddAllocationsData HTTP errors", async () => {
        const httpError = new Error("HTTP error! status: 500");
        (
          mockRewardsClient.fetchAddAllocationsData as jest.Mock
        ).mockRejectedValue(httpError);

        addAllocationsComponent = new AddAllocationsComponent(
          mockRewardsClient,
          mockWalletManager
        );
        document.body.appendChild(addAllocationsComponent.element);

        await new Promise(process.nextTick);

        expect(alertSpy).toHaveBeenCalledWith(
          "Failed to fetch allocations data: HTTP error! status: 500"
        );
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[AddAllocationsComponent] Error fetching add allocations data:",
          httpError
        );
      });

      it("should handle non-Error objects in fetch errors", async () => {
        const stringError = "Unknown fetch error";
        (
          mockRewardsClient.fetchAddAllocationsData as jest.Mock
        ).mockRejectedValue(stringError);

        addAllocationsComponent = new AddAllocationsComponent(
          mockRewardsClient,
          mockWalletManager
        );
        document.body.appendChild(addAllocationsComponent.element);

        await new Promise(process.nextTick);

        expect(alertSpy).toHaveBeenCalledWith(
          "Failed to fetch allocations data: Unknown fetch error"
        );
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[AddAllocationsComponent] Error fetching add allocations data:",
          stringError
        );
      });

      it("should clear addresses and amounts and render when fetch fails", async () => {
        const error = new Error("Fetch failed");
        (
          mockRewardsClient.fetchAddAllocationsData as jest.Mock
        ).mockRejectedValue(error);

        addAllocationsComponent = new AddAllocationsComponent(
          mockRewardsClient,
          mockWalletManager
        );
        document.body.appendChild(addAllocationsComponent.element);

        await new Promise(process.nextTick);

        const addressesInput = addAllocationsComponent.element.querySelector(
          "#addresses-input"
        ) as HTMLTextAreaElement;
        const amountsInput = addAllocationsComponent.element.querySelector(
          "#amounts-input"
        ) as HTMLTextAreaElement;

        expect(addressesInput.value).toBe("");
        expect(amountsInput.value).toBe("");
      });
    });

    describe("handleAddAllocations error handling", () => {
      beforeEach(async () => {
        // Set up with empty initial data
        (
          mockRewardsClient.fetchAddAllocationsData as jest.Mock
        ).mockResolvedValue({
          addresses: [],
          amounts: [],
        });

        addAllocationsComponent = new AddAllocationsComponent(
          mockRewardsClient,
          mockWalletManager
        );
        document.body.appendChild(addAllocationsComponent.element);
        await new Promise(process.nextTick);
      });

      it("should handle addAllocations transaction errors and show alert", async () => {
        const addError = new Error("Transaction failed: insufficient balance");
        (mockRewardsClient.addAllocations as jest.Mock).mockRejectedValue(
          addError
        );

        // Set up input values
        const addressesInput = addAllocationsComponent.element.querySelector(
          "#addresses-input"
        ) as HTMLTextAreaElement;
        const amountsInput = addAllocationsComponent.element.querySelector(
          "#amounts-input"
        ) as HTMLTextAreaElement;

        addressesInput.value = "addr1\naddr2";
        amountsInput.value = "100\n200";

        const button = addAllocationsComponent.element.querySelector(
          "#add-allocations-button"
        ) as HTMLButtonElement;
        await button.click();

        expect(alertSpy).toHaveBeenCalledWith(
          "Add allocations failed: Transaction failed: insufficient balance"
        );
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[AddAllocationsComponent] Error during add allocations:",
          addError
        );
      });

      it("should handle addAllocations validation errors", async () => {
        const validationError = new Error(
          "Addresses and amounts arrays must have the same non-zero length."
        );
        (mockRewardsClient.addAllocations as jest.Mock).mockRejectedValue(
          validationError
        );

        // Set up mismatched input values
        const addressesInput = addAllocationsComponent.element.querySelector(
          "#addresses-input"
        ) as HTMLTextAreaElement;
        const amountsInput = addAllocationsComponent.element.querySelector(
          "#amounts-input"
        ) as HTMLTextAreaElement;

        addressesInput.value = "addr1\naddr2";
        amountsInput.value = "100"; // Only one amount for two addresses

        const button = addAllocationsComponent.element.querySelector(
          "#add-allocations-button"
        ) as HTMLButtonElement;
        await button.click();

        expect(alertSpy).toHaveBeenCalledWith(
          "Add allocations failed: Addresses and amounts arrays must have the same non-zero length."
        );
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[AddAllocationsComponent] Error during add allocations:",
          validationError
        );
      });

      it("should handle addAllocations network errors", async () => {
        const networkError = new Error("Network connection lost");
        (mockRewardsClient.addAllocations as jest.Mock).mockRejectedValue(
          networkError
        );

        const addressesInput = addAllocationsComponent.element.querySelector(
          "#addresses-input"
        ) as HTMLTextAreaElement;
        const amountsInput = addAllocationsComponent.element.querySelector(
          "#amounts-input"
        ) as HTMLTextAreaElement;

        addressesInput.value = "addr1";
        amountsInput.value = "100";

        const button = addAllocationsComponent.element.querySelector(
          "#add-allocations-button"
        ) as HTMLButtonElement;
        await button.click();

        expect(alertSpy).toHaveBeenCalledWith(
          "Add allocations failed: Network connection lost"
        );
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[AddAllocationsComponent] Error during add allocations:",
          networkError
        );
      });

      it("should handle addAllocations contract execution errors", async () => {
        const contractError = new Error("Smart contract execution reverted");
        (mockRewardsClient.addAllocations as jest.Mock).mockRejectedValue(
          contractError
        );

        const addressesInput = addAllocationsComponent.element.querySelector(
          "#addresses-input"
        ) as HTMLTextAreaElement;
        const amountsInput = addAllocationsComponent.element.querySelector(
          "#amounts-input"
        ) as HTMLTextAreaElement;

        addressesInput.value = "addr1";
        amountsInput.value = "100";

        const button = addAllocationsComponent.element.querySelector(
          "#add-allocations-button"
        ) as HTMLButtonElement;
        await button.click();

        expect(alertSpy).toHaveBeenCalledWith(
          "Add allocations failed: Smart contract execution reverted"
        );
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[AddAllocationsComponent] Error during add allocations:",
          contractError
        );
      });

      it("should handle non-Error objects in add allocations errors", async () => {
        const stringError = "Unknown add allocations error";
        (mockRewardsClient.addAllocations as jest.Mock).mockRejectedValue(
          stringError
        );

        const addressesInput = addAllocationsComponent.element.querySelector(
          "#addresses-input"
        ) as HTMLTextAreaElement;
        const amountsInput = addAllocationsComponent.element.querySelector(
          "#amounts-input"
        ) as HTMLTextAreaElement;

        addressesInput.value = "addr1";
        amountsInput.value = "100";

        const button = addAllocationsComponent.element.querySelector(
          "#add-allocations-button"
        ) as HTMLButtonElement;
        await button.click();

        expect(alertSpy).toHaveBeenCalledWith(
          "Add allocations failed: Unknown add allocations error"
        );
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[AddAllocationsComponent] Error during add allocations:",
          stringError
        );
      });

      it("should NOT re-fetch data after a failed addAllocations call", async () => {
        const addError = new Error("Add allocations failed");
        (mockRewardsClient.addAllocations as jest.Mock).mockRejectedValue(
          addError
        );

        // Clear the initial fetch call count
        (mockRewardsClient.fetchAddAllocationsData as jest.Mock).mockClear();

        const addressesInput = addAllocationsComponent.element.querySelector(
          "#addresses-input"
        ) as HTMLTextAreaElement;
        const amountsInput = addAllocationsComponent.element.querySelector(
          "#amounts-input"
        ) as HTMLTextAreaElement;

        addressesInput.value = "addr1";
        amountsInput.value = "100";

        const button = addAllocationsComponent.element.querySelector(
          "#add-allocations-button"
        ) as HTMLButtonElement;
        await button.click();

        // Should NOT re-fetch data after failure
        expect(
          mockRewardsClient.fetchAddAllocationsData
        ).not.toHaveBeenCalled();
      });
    });

    describe("Input validation and parsing", () => {
      beforeEach(async () => {
        (
          mockRewardsClient.fetchAddAllocationsData as jest.Mock
        ).mockResolvedValue({
          addresses: [],
          amounts: [],
        });

        addAllocationsComponent = new AddAllocationsComponent(
          mockRewardsClient,
          mockWalletManager
        );
        document.body.appendChild(addAllocationsComponent.element);
        await new Promise(process.nextTick);
      });

      it("should handle empty addresses input - actual behavior sends amounts", async () => {
        const addressesInput = addAllocationsComponent.element.querySelector(
          "#addresses-input"
        ) as HTMLTextAreaElement;
        const amountsInput = addAllocationsComponent.element.querySelector(
          "#amounts-input"
        ) as HTMLTextAreaElement;

        addressesInput.value = "";
        amountsInput.value = "100";

        const button = addAllocationsComponent.element.querySelector(
          "#add-allocations-button"
        ) as HTMLButtonElement;
        await button.click();

        // Actual behavior: empty addresses but amounts are still sent
        // This will cause a validation error in the smart contract
        expect(mockRewardsClient.addAllocations).toHaveBeenCalledWith(
          [],
          [100]
        );
      });

      it("should handle empty amounts input - actual behavior sends addresses", async () => {
        const addressesInput = addAllocationsComponent.element.querySelector(
          "#addresses-input"
        ) as HTMLTextAreaElement;
        const amountsInput = addAllocationsComponent.element.querySelector(
          "#amounts-input"
        ) as HTMLTextAreaElement;

        addressesInput.value = "addr1";
        amountsInput.value = "";

        const button = addAllocationsComponent.element.querySelector(
          "#add-allocations-button"
        ) as HTMLButtonElement;
        await button.click();

        // Actual behavior: addresses are sent with empty amounts array
        // This will cause a validation error in the smart contract
        expect(mockRewardsClient.addAllocations).toHaveBeenCalledWith(
          ["addr1"],
          []
        );
      });

      it("should filter out invalid amounts (NaN) but keep all addresses - actual behavior creates mismatch", async () => {
        const addressesInput = addAllocationsComponent.element.querySelector(
          "#addresses-input"
        ) as HTMLTextAreaElement;
        const amountsInput = addAllocationsComponent.element.querySelector(
          "#amounts-input"
        ) as HTMLTextAreaElement;

        addressesInput.value = "addr1\naddr2\naddr3";
        amountsInput.value = "100\ninvalid\n200";

        const button = addAllocationsComponent.element.querySelector(
          "#add-allocations-button"
        ) as HTMLButtonElement;
        await button.click();

        // Actual behavior: keeps all addresses but filters invalid amounts
        // This creates mismatched arrays (3 addresses, 2 amounts)
        // The smart contract will reject this with validation error
        expect(mockRewardsClient.addAllocations).toHaveBeenCalledWith(
          ["addr1", "addr2", "addr3"], // All addresses kept
          [100, 200] // Only valid amounts kept
        );
      });

      it("should trim whitespace from addresses", async () => {
        const addressesInput = addAllocationsComponent.element.querySelector(
          "#addresses-input"
        ) as HTMLTextAreaElement;
        const amountsInput = addAllocationsComponent.element.querySelector(
          "#amounts-input"
        ) as HTMLTextAreaElement;

        addressesInput.value = "  addr1  \n  addr2  ";
        amountsInput.value = "100\n200";

        const button = addAllocationsComponent.element.querySelector(
          "#add-allocations-button"
        ) as HTMLButtonElement;
        await button.click();

        expect(mockRewardsClient.addAllocations).toHaveBeenCalledWith(
          ["addr1", "addr2"],
          [100, 200]
        );
      });

      it("should handle completely empty inputs", async () => {
        const addressesInput = addAllocationsComponent.element.querySelector(
          "#addresses-input"
        ) as HTMLTextAreaElement;
        const amountsInput = addAllocationsComponent.element.querySelector(
          "#amounts-input"
        ) as HTMLTextAreaElement;

        addressesInput.value = "";
        amountsInput.value = "";

        const button = addAllocationsComponent.element.querySelector(
          "#add-allocations-button"
        ) as HTMLButtonElement;
        await button.click();

        expect(mockRewardsClient.addAllocations).toHaveBeenCalledWith([], []);
      });

      it("should handle mixed valid and invalid inputs creating array length mismatch", async () => {
        const addressesInput = addAllocationsComponent.element.querySelector(
          "#addresses-input"
        ) as HTMLTextAreaElement;
        const amountsInput = addAllocationsComponent.element.querySelector(
          "#amounts-input"
        ) as HTMLTextAreaElement;

        addressesInput.value = "addr1\naddr2\naddr3\naddr4";
        amountsInput.value = "100\ninvalid\n200"; // Only 3 amounts for 4 addresses

        const button = addAllocationsComponent.element.querySelector(
          "#add-allocations-button"
        ) as HTMLButtonElement;
        await button.click();

        // This will create arrays with different lengths
        // The smart contract validation should catch this
        expect(mockRewardsClient.addAllocations).toHaveBeenCalledWith(
          ["addr1", "addr2", "addr3", "addr4"], // 4 addresses
          [100, 200] // 2 valid amounts
        );
      });
    });

    describe("Wallet subscription error scenarios", () => {
      it("should handle wallet manager subscription callback errors", async () => {
        const subscriptionError = new Error("Subscription callback failed");
        (
          mockRewardsClient.fetchAddAllocationsData as jest.Mock
        ).mockRejectedValue(subscriptionError);

        addAllocationsComponent = new AddAllocationsComponent(
          mockRewardsClient,
          mockWalletManager
        );

        // Trigger the subscription callback manually
        const subscribeCallback = mockWalletManager.subscribe.mock.calls[0][0];
        await subscribeCallback();

        expect(alertSpy).toHaveBeenCalledWith(
          "Failed to fetch allocations data: Subscription callback failed"
        );
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[AddAllocationsComponent] Error fetching add allocations data:",
          subscriptionError
        );
      });

      it("should handle wallet changes gracefully when fetch fails", async () => {
        const fetchError = new Error("Failed to fetch data");
        (
          mockRewardsClient.fetchAddAllocationsData as jest.Mock
        ).mockRejectedValue(fetchError);

        addAllocationsComponent = new AddAllocationsComponent(
          mockRewardsClient,
          mockWalletManager
        );

        // Simulate wallet change by calling subscription callback
        const subscribeCallback = mockWalletManager.subscribe.mock.calls[0][0];
        await subscribeCallback();

        const addressesInput = addAllocationsComponent.element.querySelector(
          "#addresses-input"
        ) as HTMLTextAreaElement;
        expect(addressesInput.value).toBe("");
      });
    });
  });
});
