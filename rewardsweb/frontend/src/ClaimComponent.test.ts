import { ClaimComponent } from "./ClaimComponent";
import { RewardsClient } from "./RewardsClient";

// Mock RewardsClient
jest.mock("./RewardsClient", () => {
  return {
    RewardsClient: jest.fn().mockImplementation(() => {
      return {
        fetchClaimableStatus: jest.fn(),
        claim: jest.fn(),
      };
    }),
  };
});

describe("ClaimComponent", () => {
  let mockRewardsClient: jest.Mocked<RewardsClient>;
  let mockWalletManager: jest.Mocked<WalletManager>;
  let claimComponent: ClaimComponent;
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

  it('should render with "No Claim Available" button when not claimable', async () => {
    (mockRewardsClient.fetchClaimableStatus as jest.Mock).mockResolvedValue({
      claimable: false,
    });

    claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager);
    document.body.appendChild(claimComponent.element);

    // Allow microtasks to run
    await new Promise(process.nextTick);

    const button = claimComponent.element.querySelector(
      "#claim-button"
    ) as HTMLButtonElement;
    expect(button.textContent?.trim()).toBe("No Claim Available");
    expect(button.disabled).toBe(true);
    expect(mockRewardsClient.fetchClaimableStatus).toHaveBeenCalledWith(
      "test-address"
    );
  });

  it('should render with "Claim" button when claimable', async () => {
    (mockRewardsClient.fetchClaimableStatus as jest.Mock).mockResolvedValue({
      claimable: true,
    });

    claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager);
    document.body.appendChild(claimComponent.element);

    await new Promise(process.nextTick);

    const button = claimComponent.element.querySelector(
      "#claim-button"
    ) as HTMLButtonElement;
    expect(button.textContent?.trim()).toBe("Claim");
    expect(button.disabled).toBe(false);
    expect(mockRewardsClient.fetchClaimableStatus).toHaveBeenCalledWith(
      "test-address"
    );
  });

  it("should call rewardsClient.claim when claim button is clicked", async () => {
    (mockRewardsClient.fetchClaimableStatus as jest.Mock).mockResolvedValue({
      claimable: true,
    });
    claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager);
    document.body.appendChild(claimComponent.element);
    await new Promise(process.nextTick);

    const button = claimComponent.element.querySelector(
      "#claim-button"
    ) as HTMLButtonElement;
    button.click();

    expect(mockRewardsClient.claim).toHaveBeenCalled();
  });

  it("should re-check claimable status after a successful claim", async () => {
    (mockRewardsClient.fetchClaimableStatus as jest.Mock).mockResolvedValueOnce(
      { claimable: true }
    );
    claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager);
    document.body.appendChild(claimComponent.element);
    await new Promise(process.nextTick);

    // Mock a successful claim, then set next status to not claimable
    (mockRewardsClient.claim as jest.Mock).mockResolvedValue(undefined);
    (mockRewardsClient.fetchClaimableStatus as jest.Mock).mockResolvedValueOnce(
      { claimable: false }
    );

    const button = claimComponent.element.querySelector(
      "#claim-button"
    ) as HTMLButtonElement;
    await button.click();

    expect(mockRewardsClient.claim).toHaveBeenCalledTimes(1);
    // fetchClaimableStatus is called once on init and once after claim
    expect(mockRewardsClient.fetchClaimableStatus).toHaveBeenCalledTimes(2);
  });

  it("should not fetch status if no active account", async () => {
    mockWalletManager.activeAccount = null;
    claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager);
    document.body.appendChild(claimComponent.element);
    await new Promise(process.nextTick);

    expect(mockRewardsClient.fetchClaimableStatus).not.toHaveBeenCalled();
  });

  describe("ClaimComponent Error Scenarios", () => {
    let mockRewardsClient: jest.Mocked<RewardsClient>;
    let mockWalletManager: jest.Mocked<WalletManager>;
    let claimComponent: ClaimComponent;
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

    describe("checkClaimableStatus error handling", () => {
      it("should handle fetchClaimableStatus errors and set claimable to false", async () => {
        const error = new Error("API error");
        (mockRewardsClient.fetchClaimableStatus as jest.Mock).mockRejectedValue(
          error
        );

        claimComponent = new ClaimComponent(
          mockRewardsClient,
          mockWalletManager
        );
        document.body.appendChild(claimComponent.element);

        // Wait for the async operation to complete
        await new Promise(process.nextTick);

        const button = claimComponent.element.querySelector(
          "#claim-button"
        ) as HTMLButtonElement;

        expect(button.textContent?.trim()).toBe("No Claim Available");
        expect(button.disabled).toBe(true);
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[ClaimComponent] Error checking claimable status:",
          error
        );
      });

      it("should handle fetchClaimableStatus network errors", async () => {
        const networkError = new Error("Network request failed");
        (mockRewardsClient.fetchClaimableStatus as jest.Mock).mockRejectedValue(
          networkError
        );

        claimComponent = new ClaimComponent(
          mockRewardsClient,
          mockWalletManager
        );
        document.body.appendChild(claimComponent.element);

        await new Promise(process.nextTick);

        const button = claimComponent.element.querySelector(
          "#claim-button"
        ) as HTMLButtonElement;

        expect(button.textContent?.trim()).toBe("No Claim Available");
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[ClaimComponent] Error checking claimable status:",
          networkError
        );
      });

      it("should handle fetchClaimableStatus HTTP errors", async () => {
        const httpError = new Error("HTTP error! status: 500");
        (mockRewardsClient.fetchClaimableStatus as jest.Mock).mockRejectedValue(
          httpError
        );

        claimComponent = new ClaimComponent(
          mockRewardsClient,
          mockWalletManager
        );
        document.body.appendChild(claimComponent.element);

        await new Promise(process.nextTick);

        const button = claimComponent.element.querySelector(
          "#claim-button"
        ) as HTMLButtonElement;

        expect(button.textContent?.trim()).toBe("No Claim Available");
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[ClaimComponent] Error checking claimable status:",
          httpError
        );
      });
    });

    describe("handleClaim error handling", () => {
      beforeEach(async () => {
        // Set up claimable state
        (mockRewardsClient.fetchClaimableStatus as jest.Mock).mockResolvedValue(
          {
            claimable: true,
          }
        );
        claimComponent = new ClaimComponent(
          mockRewardsClient,
          mockWalletManager
        );
        document.body.appendChild(claimComponent.element);
        await new Promise(process.nextTick);
      });

      it("should handle claim transaction errors and show alert", async () => {
        const claimError = new Error(
          "Transaction failed: insufficient balance"
        );
        (mockRewardsClient.claim as jest.Mock).mockRejectedValue(claimError);

        const button = claimComponent.element.querySelector(
          "#claim-button"
        ) as HTMLButtonElement;
        await button.click();

        expect(alertSpy).toHaveBeenCalledWith(
          "Claim failed: Transaction failed: insufficient balance"
        );
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[ClaimComponent] Error during claim:",
          claimError
        );
      });

      it("should handle claim network errors", async () => {
        const networkError = new Error("Network connection lost");
        (mockRewardsClient.claim as jest.Mock).mockRejectedValue(networkError);

        const button = claimComponent.element.querySelector(
          "#claim-button"
        ) as HTMLButtonElement;
        await button.click();

        expect(alertSpy).toHaveBeenCalledWith(
          "Claim failed: Network connection lost"
        );
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[ClaimComponent] Error during claim:",
          networkError
        );
      });

      it("should handle claim contract execution errors", async () => {
        const contractError = new Error("Smart contract execution reverted");
        (mockRewardsClient.claim as jest.Mock).mockRejectedValue(contractError);

        const button = claimComponent.element.querySelector(
          "#claim-button"
        ) as HTMLButtonElement;
        await button.click();

        expect(alertSpy).toHaveBeenCalledWith(
          "Claim failed: Smart contract execution reverted"
        );
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[ClaimComponent] Error during claim:",
          contractError
        );
      });

      it("should handle non-Error objects in claim errors", async () => {
        const stringError = "Unknown error occurred";
        (mockRewardsClient.claim as jest.Mock).mockRejectedValue(stringError);

        const button = claimComponent.element.querySelector(
          "#claim-button"
        ) as HTMLButtonElement;
        await button.click();

        expect(alertSpy).toHaveBeenCalledWith(
          "Claim failed: Unknown error occurred"
        );
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[ClaimComponent] Error during claim:",
          stringError
        );
      });

      it("should re-check claimable status even after claim failure", async () => {
        const claimError = new Error("Claim failed");
        (mockRewardsClient.claim as jest.Mock).mockRejectedValue(claimError);

        // Clear the initial fetch call count from constructor
        (mockRewardsClient.fetchClaimableStatus as jest.Mock).mockClear();

        const button = claimComponent.element.querySelector(
          "#claim-button"
        ) as HTMLButtonElement;
        await button.click();

        // Should still attempt to re-check status even after failure
        expect(mockRewardsClient.fetchClaimableStatus).toHaveBeenCalledTimes(1);
        expect(alertSpy).toHaveBeenCalledWith("Claim failed: Claim failed");
      });
    });

    describe("Wallet subscription error scenarios", () => {
      it("should handle wallet manager subscription callback errors", async () => {
        const subscriptionError = new Error("Subscription callback failed");
        (mockRewardsClient.fetchClaimableStatus as jest.Mock).mockRejectedValue(
          subscriptionError
        );

        claimComponent = new ClaimComponent(
          mockRewardsClient,
          mockWalletManager
        );

        // Trigger the subscription callback manually
        const subscribeCallback = mockWalletManager.subscribe.mock.calls[0][0];
        await subscribeCallback();

        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "[ClaimComponent] Error checking claimable status:",
          subscriptionError
        );
      });

      it("should handle wallet changes gracefully when fetch fails", async () => {
        const fetchError = new Error("Failed to fetch status");
        (mockRewardsClient.fetchClaimableStatus as jest.Mock).mockRejectedValue(
          fetchError
        );

        claimComponent = new ClaimComponent(
          mockRewardsClient,
          mockWalletManager
        );

        // Simulate wallet change by calling subscription callback
        const subscribeCallback = mockWalletManager.subscribe.mock.calls[0][0];
        await subscribeCallback();

        const button = claimComponent.element.querySelector(
          "#claim-button"
        ) as HTMLButtonElement;

        expect(button.textContent?.trim()).toBe("No Claim Available");
        expect(button.disabled).toBe(true);
      });
    });
  });
});
