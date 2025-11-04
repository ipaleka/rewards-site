// Mock algosdk first
jest.mock("algosdk", () => {
  const mockAlgodv2 = jest.fn();
  return {
    Algodv2: mockAlgodv2.mockImplementation(
      (token: string, server: string, port: string) => ({
        token,
        server,
        port,
        // Add any other methods that might be used by the client
        getTransactionParams: jest.fn(),
      })
    ),
  };
});

jest.mock("@txnlab/use-wallet", () => ({
  NetworkId: {
    TESTNET: "testnet",
    MAINNET: "mainnet",
  },
  WalletManager: jest.fn(),
}));

import { ActiveNetwork, getAlgodClient } from "./ActiveNetwork";
import { WalletManager, NetworkId } from "@txnlab/use-wallet";
import algosdk from "algosdk";

describe("ActiveNetwork", () => {
  let mockManager: jest.Mocked<WalletManager>;
  let activeNetwork: ActiveNetwork;

  beforeEach(() => {
    mockManager = {
      activeNetwork: NetworkId.TESTNET,
      setActiveNetwork: jest.fn(),
    } as any;

    activeNetwork = new ActiveNetwork(mockManager);
  });

  afterEach(() => {
    activeNetwork.destroy();
  });
  describe("getAlgodClient", () => {
    beforeEach(() => {
      jest.clearAllMocks();
    });

    it("should return testnet client for TESTNET network", () => {
      const client = getAlgodClient(NetworkId.TESTNET);

      expect(algosdk.Algodv2).toHaveBeenCalledWith(
        "", // token
        "https://testnet-api.algonode.cloud", // server
        "" // port
      );
      expect(client.server).toBe("https://testnet-api.algonode.cloud");
    });

    it("should return mainnet client for MAINNET network", () => {
      const client = getAlgodClient(NetworkId.MAINNET);

      expect(algosdk.Algodv2).toHaveBeenCalledWith(
        "", // token
        "https://mainnet-api.algonode.cloud", // server
        "" // port
      );
      expect(client.server).toBe("https://mainnet-api.algonode.cloud");
    });

    it("should return testnet client as fallback for unknown network", () => {
      const client = getAlgodClient("UNKNOWN_NETWORK" as NetworkId);

      expect(algosdk.Algodv2).toHaveBeenCalledWith(
        "", // token
        "https://testnet-api.algonode.cloud", // server
        "" // port
      );
      expect(client.server).toBe("https://testnet-api.algonode.cloud");
    });

    it("should return testnet client for BETANET network (uses default case)", () => {
      const client = getAlgodClient("betanet" as NetworkId);

      expect(algosdk.Algodv2).toHaveBeenCalledWith(
        "", // token
        "https://testnet-api.algonode.cloud", // server
        "" // port
      );
      expect(client.server).toBe("https://testnet-api.algonode.cloud");
    });

    it("should use empty token and port as configured", () => {
      const client = getAlgodClient(NetworkId.TESTNET);

      expect(client.token).toBe("");
      expect(client.port).toBe("");
    });

    it("should create different instances for different networks", () => {
      const testnetClient = getAlgodClient(NetworkId.TESTNET);
      const mainnetClient = getAlgodClient(NetworkId.MAINNET);

      expect(testnetClient.server).toBe("https://testnet-api.algonode.cloud");
      expect(mainnetClient.server).toBe("https://mainnet-api.algonode.cloud");
      // Verify different instances were created
      expect(algosdk.Algodv2).toHaveBeenCalledTimes(2);
    });

    it("should handle network case sensitivity", () => {
      // Test that the function properly handles the NetworkId enum values
      const testnetClient = getAlgodClient(NetworkId.TESTNET);
      const mainnetClient = getAlgodClient(NetworkId.MAINNET);

      expect(testnetClient.server).toContain("testnet");
      expect(mainnetClient.server).toContain("mainnet");
    });
  });

  describe("Constructor", () => {
    it("should initialize with correct properties", () => {
      expect(activeNetwork.manager).toBe(mockManager);
      expect(activeNetwork.element).toBeDefined();
      expect(activeNetwork.element.className).toBe("network-group");
    });

    it("should render on initialization", () => {
      expect(activeNetwork.element.innerHTML).toContain("Current Network");
      expect(activeNetwork.element.innerHTML).toContain("testnet");
    });
  });

  describe("setActiveNetwork", () => {
    it("should set active network and re-render", () => {
      activeNetwork.setActiveNetwork(NetworkId.MAINNET);

      expect(mockManager.setActiveNetwork).toHaveBeenCalledWith(
        NetworkId.MAINNET
      );
      // Should re-render to reflect the new network
      expect(activeNetwork.element.innerHTML).toContain("Current Network");
    });
  });

  describe("render", () => {
    it("should render with current network", () => {
      activeNetwork.render();

      expect(activeNetwork.element.innerHTML).toContain("Current Network");
      expect(activeNetwork.element.innerHTML).toContain("testnet");
    });

    it("should disable current network button", () => {
      activeNetwork.render();

      // Current network button should be disabled
      expect(activeNetwork.element.innerHTML).toMatch(
        /id="set-testnet".*disabled/
      );

      // Other network buttons should be enabled
      expect(activeNetwork.element.innerHTML).toContain('id="set-mainnet"');
      expect(activeNetwork.element.innerHTML).not.toMatch(
        /id="set-mainnet".*disabled/
      );
    });

    it("should render different network as active", () => {
      mockManager.activeNetwork = NetworkId.MAINNET;
      activeNetwork.render();

      expect(activeNetwork.element.innerHTML).toMatch(
        /id="set-mainnet".*disabled/
      );
      expect(activeNetwork.element.innerHTML).toContain("mainnet");
    });
  });

  describe("Event Listeners", () => {
    it("should handle testnet button click", () => {
      const testnetButton = document.createElement("button");
      testnetButton.id = "set-testnet";

      activeNetwork.element.appendChild(testnetButton);
      testnetButton.click();

      expect(mockManager.setActiveNetwork).toHaveBeenCalledWith(
        NetworkId.TESTNET
      );
    });

    it("should handle mainnet button click", () => {
      const mainnetButton = document.createElement("button");
      mainnetButton.id = "set-mainnet";

      activeNetwork.element.appendChild(mainnetButton);
      mainnetButton.click();

      expect(mockManager.setActiveNetwork).toHaveBeenCalledWith(
        NetworkId.MAINNET
      );
    });

    it("should ignore clicks on non-button elements", () => {
      const div = document.createElement("div");

      activeNetwork.element.appendChild(div);
      div.click();

      expect(mockManager.setActiveNetwork).not.toHaveBeenCalled();
    });
  });

  describe("destroy", () => {
    it("should remove event listeners", () => {
      // Mock the removeEventListener
      const removeSpy = jest.spyOn(
        activeNetwork.element,
        "removeEventListener"
      );

      activeNetwork.destroy();

      expect(removeSpy).toHaveBeenCalledWith(
        "click",
        activeNetwork.addEventListeners
      );
    });
  });

  it("should render without betanet button", () => {
    activeNetwork.render();

    // Should not contain betanet button
    expect(activeNetwork.element.innerHTML).not.toContain("set-betanet");
    expect(activeNetwork.element.innerHTML).toContain("set-testnet");
    expect(activeNetwork.element.innerHTML).toContain("set-mainnet");
  });

  it("should handle network changes without betanet", () => {
    // Test that only testnet and mainnet buttons work
    const testnetButton = document.createElement("button");
    testnetButton.id = "set-testnet";
    activeNetwork.element.appendChild(testnetButton);
    testnetButton.click();
    expect(mockManager.setActiveNetwork).toHaveBeenCalledWith(
      NetworkId.TESTNET
    );

    const mainnetButton = document.createElement("button");
    mainnetButton.id = "set-mainnet";
    activeNetwork.element.appendChild(mainnetButton);
    mainnetButton.click();
    expect(mockManager.setActiveNetwork).toHaveBeenCalledWith(
      NetworkId.MAINNET
    );
  });
});
