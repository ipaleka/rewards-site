import { ClaimComponent } from "./ClaimComponent";
import { RewardsClient } from "./RewardsClient";
import { WalletManager } from "@txnlab/use-wallet";

// Mock RewardsClient
jest.mock("./RewardsClient", () => {
  return {
    RewardsClient: jest.fn().mockImplementation(() => {
      return {
        claimRewards: jest.fn(),
        userClaimed: jest.fn(),
      };
    }),
  };
});

// Mock window.location.reload
Object.defineProperty(window, "location", {
  value: {
    reload: jest.fn(),
  },
  writable: true,
});

describe("ClaimComponent", () => {
  let mockRewardsClient: jest.Mocked<RewardsClient>;
  let mockWalletManager: jest.Mocked<WalletManager>;
  let claimComponent: ClaimComponent;
  let alertSpy: jest.SpyInstance;
  let container: HTMLElement;

  beforeEach(() => {
    alertSpy = jest.spyOn(window, "alert").mockImplementation(() => {});
    mockRewardsClient = new RewardsClient(
      null as any
    ) as jest.Mocked<RewardsClient>;
    mockWalletManager = {
      activeAccount: { address: "test-address" },
      subscribe: jest.fn(),
    } as any;

    // Set up the DOM structure with enabled button (as rendered by Django)
    container = document.createElement("div");
    container.id = "claim-container";
    container.innerHTML = `<button id="claim-button">Claim Rewards</button>`;
    document.body.appendChild(container);
  });

  afterEach(() => {
    document.body.innerHTML = "";
    alertSpy.mockRestore();
    jest.clearAllMocks();
  });

  it("should call rewardsClient.claimRewards when claim button is clicked", async () => {
    (mockRewardsClient.claimRewards as jest.Mock).mockResolvedValue(
      "test-tx-id"
    );

    claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager);
    claimComponent.bind(container);

    const button = container.querySelector(
      "#claim-button"
    ) as HTMLButtonElement;
    button.click();

    expect(mockRewardsClient.claimRewards).toHaveBeenCalled();
  });

  it("should not call claimRewards when disabled button is clicked", async () => {
    // Set up DOM with disabled button (as rendered by Django when no rewards)
    container.innerHTML = `<button id="claim-button" disabled>No Claim Available</button>`;

    claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager);
    claimComponent.bind(container);

    const button = container.querySelector(
      "#claim-button"
    ) as HTMLButtonElement;
    button.click();

    expect(mockRewardsClient.claimRewards).not.toHaveBeenCalled();
  });

  it("should handle errors when claim transaction fails", async () => {
    const testError = new Error("Transaction failed");
    (mockRewardsClient.claimRewards as jest.Mock).mockRejectedValue(testError);

    const consoleSpy = jest
      .spyOn(console, "error")
      .mockImplementation(() => {});

    claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager);
    claimComponent.bind(container);

    const button = container.querySelector(
      "#claim-button"
    ) as HTMLButtonElement;
    await button.click();

    expect(consoleSpy).toHaveBeenCalledWith(
      "[ClaimComponent] Error during claim:",
      testError
    );
    expect(alertSpy).toHaveBeenCalledWith("Claim failed: Transaction failed");

    consoleSpy.mockRestore();
  });

  it("should handle non-Error object when claim fails", async () => {
    const testError = "Simple string error";
    (mockRewardsClient.claimRewards as jest.Mock).mockRejectedValue(testError);

    const consoleSpy = jest
      .spyOn(console, "error")
      .mockImplementation(() => {});

    claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager);
    claimComponent.bind(container);

    const button = container.querySelector(
      "#claim-button"
    ) as HTMLButtonElement;
    await button.click();

    expect(consoleSpy).toHaveBeenCalledWith(
      "[ClaimComponent] Error during claim:",
      testError
    );
    expect(alertSpy).toHaveBeenCalledWith("Claim failed: Simple string error");

    consoleSpy.mockRestore();
  });

  it("should call userClaimed after successful claim transaction", async () => {
    (mockRewardsClient.claimRewards as jest.Mock).mockResolvedValue(
      "test-tx-id"
    );
    (mockRewardsClient.userClaimed as jest.Mock).mockResolvedValue({
      success: true,
    });

    claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager);
    claimComponent.bind(container);

    const button = container.querySelector(
      "#claim-button"
    ) as HTMLButtonElement;
    await button.click();

    expect(mockRewardsClient.userClaimed).toHaveBeenCalledWith(
      "test-address",
      "test-tx-id"
    );
  });

  it("should handle userClaimed API failure gracefully", async () => {
    // Set up console spy BEFORE component initialization and click
    const consoleErrorSpy = jest
      .spyOn(console, "error")
      .mockImplementation(() => {});

    (mockRewardsClient.claimRewards as jest.Mock).mockResolvedValue(
      "test-tx-id"
    );
    (mockRewardsClient.userClaimed as jest.Mock).mockRejectedValue(
      new Error("API unavailable")
    );

    claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager);
    claimComponent.bind(container);

    const button = container.querySelector(
      "#claim-button"
    ) as HTMLButtonElement;

    // Use await to ensure the async handleClaim completes
    await button.click();

    // Wait for any microtasks to complete
    await new Promise(process.nextTick);

    expect(mockRewardsClient.userClaimed).toHaveBeenCalledWith(
      "test-address",
      "test-tx-id"
    );
    expect(consoleErrorSpy).toHaveBeenCalledWith(
      "Backend notification failed:",
      expect.any(Error)
    );

    consoleErrorSpy.mockRestore();
  });

  it("should not call userClaimed if no active account after claim", async () => {
    (mockRewardsClient.claimRewards as jest.Mock).mockResolvedValue(
      "test-tx-id"
    );

    claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager);
    claimComponent.bind(container);

    // Simulate wallet disconnecting after claim but before userClaimed call
    mockWalletManager.activeAccount = null;

    const button = container.querySelector(
      "#claim-button"
    ) as HTMLButtonElement;
    await button.click();

    expect(mockRewardsClient.userClaimed).not.toHaveBeenCalled();
  });

  it("should reload page after successful claim", async () => {
    // Mock location.reload
    const reloadSpy = jest.fn();
    Object.defineProperty(window, "location", {
      value: {
        reload: reloadSpy,
      },
      writable: true,
    });
    (mockRewardsClient.claimRewards as jest.Mock).mockResolvedValue(
      "test-tx-id"
    );
    (mockRewardsClient.userClaimed as jest.Mock).mockResolvedValue({
      success: true,
    });

    claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager);
    claimComponent.bind(container);

    const button = container.querySelector(
      "#claim-button"
    ) as HTMLButtonElement;

    console.log("Before click - reload calls:", reloadSpy.mock.calls.length);
    await button.click();
    console.log("After click - reload calls:", reloadSpy.mock.calls.length);

    // Add a small delay to ensure any async operations complete
    await new Promise((resolve) => setTimeout(resolve, 0));
    console.log("After timeout - reload calls:", reloadSpy.mock.calls.length);

    expect(reloadSpy).toHaveBeenCalled();
  });
});

describe("ClaimComponent Edge Cases", () => {
  let mockRewardsClient: jest.Mocked<RewardsClient>;
  let mockWalletManager: jest.Mocked<WalletManager>;
  let claimComponent: ClaimComponent;
  let container: HTMLElement;

  beforeEach(() => {
    mockRewardsClient = new RewardsClient(
      null as any
    ) as jest.Mocked<RewardsClient>;
    mockWalletManager = {
      activeAccount: { address: "test-address" },
      subscribe: jest.fn(),
    } as any;

    container = document.createElement("div");
    container.id = "claim-container";
    container.innerHTML = `<button id="claim-button">Claim Rewards</button>`;
    document.body.appendChild(container);
  });

  afterEach(() => {
    document.body.innerHTML = "";
    jest.clearAllMocks();
  });

  it("should handle addEventListeners when element is null", () => {
    claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager);
    // Don't call bind(), so this.element remains null
    expect(() => {
      claimComponent.addEventListeners();
    }).not.toThrow();
  });

  it("should handle click events on non-button elements gracefully", () => {
    claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager);
    claimComponent.bind(container);

    // Simulate click event without the expected button structure
    const mockEvent = new Event("click", { bubbles: true });
    expect(() => {
      container.dispatchEvent(mockEvent);
    }).not.toThrow();

    expect(mockRewardsClient.claimRewards).not.toHaveBeenCalled();
  });

  it("should handle missing claim button in event listener", () => {
    const containerWithoutButton = document.createElement("div");
    containerWithoutButton.innerHTML = `<div>No button here</div>`;

    claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager);
    claimComponent.bind(containerWithoutButton);

    // Should not throw when clicking on non-button element
    const clickEvent = new Event("click", { bubbles: true });
    expect(() => {
      containerWithoutButton.dispatchEvent(clickEvent);
    }).not.toThrow();
  });

  it("should not subscribe to wallet manager changes", () => {
    claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager);

    // Verify that subscribe is not called in constructor anymore
    expect(mockWalletManager.subscribe).not.toHaveBeenCalled();
  });

  it("should handle destroy method without errors", () => {
    claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager);
    claimComponent.bind(container);

    expect(() => {
      claimComponent.destroy();
    }).not.toThrow();
  });
});

describe("ClaimComponent Integration", () => {
  let mockRewardsClient: jest.Mocked<RewardsClient>;
  let mockWalletManager: jest.Mocked<WalletManager>;
  let claimComponent: ClaimComponent;
  let container: HTMLElement;
  let alertSpy: jest.SpyInstance;

  beforeEach(() => {
    alertSpy = jest.spyOn(window, "alert").mockImplementation(() => {});
    mockRewardsClient = new RewardsClient(
      null as any
    ) as jest.Mocked<RewardsClient>;
    mockWalletManager = {
      activeAccount: { address: "test-address" },
      subscribe: jest.fn(),
    } as any;

    container = document.createElement("div");
    container.id = "claim-container";
    container.innerHTML = `<button id="claim-button">Claim Rewards</button>`;
    document.body.appendChild(container);
  });

  afterEach(() => {
    document.body.innerHTML = "";
    alertSpy.mockRestore();
    jest.clearAllMocks();
  });

  it("should handle claim failure without calling userClaimed or reload", async () => {
    const reloadSpy = jest.spyOn(window.location, "reload");
    const claimError = new Error("Insufficient balance");
    (mockRewardsClient.claimRewards as jest.Mock).mockRejectedValue(claimError);

    claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager);
    claimComponent.bind(container);

    const button = container.querySelector(
      "#claim-button"
    ) as HTMLButtonElement;
    await button.click();

    expect(mockRewardsClient.claimRewards).toHaveBeenCalledTimes(1);
    expect(mockRewardsClient.userClaimed).not.toHaveBeenCalled();
    expect(reloadSpy).not.toHaveBeenCalled();
    expect(alertSpy).toHaveBeenCalledWith("Claim failed: Insufficient balance");
  });

  it("should not call claimRewards when disabled button is clicked", async () => {
    // Set up DOM with disabled button (as rendered by Django when no rewards)
    container.innerHTML = `<button id="claim-button" disabled>No Claim Available</button>`;

    claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager);
    claimComponent.bind(container);

    const button = container.querySelector(
      "#claim-button"
    ) as HTMLButtonElement;
    button.click();

    expect(mockRewardsClient.claimRewards).not.toHaveBeenCalled();
  });
});
