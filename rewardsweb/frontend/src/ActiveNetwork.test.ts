jest.mock('@txnlab/use-wallet', () => ({
  NetworkId: {
    BETANET: 'betanet',
    TESTNET: 'testnet',
    MAINNET: 'mainnet'
  },
  WalletManager: jest.fn()
}));

import { ActiveNetwork } from './ActiveNetwork';
import { WalletManager, NetworkId } from '@txnlab/use-wallet';

describe('ActiveNetwork', () => {
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

  describe('Constructor', () => {
    it('should initialize with correct properties', () => {
      expect(activeNetwork.manager).toBe(mockManager);
      expect(activeNetwork.element).toBeDefined();
      expect(activeNetwork.element.className).toBe('network-group');
    });

    it('should render on initialization', () => {
      expect(activeNetwork.element.innerHTML).toContain('Current Network');
      expect(activeNetwork.element.innerHTML).toContain('testnet');
    });
  });

  describe('setActiveNetwork', () => {
    it('should set active network and re-render', () => {
      activeNetwork.setActiveNetwork(NetworkId.MAINNET);

      expect(mockManager.setActiveNetwork).toHaveBeenCalledWith(NetworkId.MAINNET);
      // Should re-render to reflect the new network
      expect(activeNetwork.element.innerHTML).toContain('Current Network');
    });
  });

  describe('render', () => {
    it('should render with current network', () => {
      activeNetwork.render();

      expect(activeNetwork.element.innerHTML).toContain('Current Network');
      expect(activeNetwork.element.innerHTML).toContain('testnet');
    });

    it('should disable current network button', () => {
      activeNetwork.render();

      // Current network button should be disabled
      expect(activeNetwork.element.innerHTML).toContain('id="set-testnet" disabled');
      // Other network buttons should be enabled
      expect(activeNetwork.element.innerHTML).toContain('id="set-betanet"');
      expect(activeNetwork.element.innerHTML).not.toContain('id="set-betanet" disabled');
      expect(activeNetwork.element.innerHTML).toContain('id="set-mainnet"');
      expect(activeNetwork.element.innerHTML).not.toContain('id="set-mainnet" disabled');
    });

    it('should render different network as active', () => {
      mockManager.activeNetwork = NetworkId.MAINNET;
      activeNetwork.render();

      expect(activeNetwork.element.innerHTML).toContain('id="set-mainnet" disabled');
      expect(activeNetwork.element.innerHTML).toContain('mainnet');
    });
  });

  describe('Event Listeners', () => {
    it('should handle betanet button click', () => {
      const betanetButton = document.createElement('button');
      betanetButton.id = 'set-betanet';

      activeNetwork.element.appendChild(betanetButton);
      betanetButton.click();

      expect(mockManager.setActiveNetwork).toHaveBeenCalledWith(NetworkId.BETANET);
    });

    it('should handle testnet button click', () => {
      const testnetButton = document.createElement('button');
      testnetButton.id = 'set-testnet';

      activeNetwork.element.appendChild(testnetButton);
      testnetButton.click();

      expect(mockManager.setActiveNetwork).toHaveBeenCalledWith(NetworkId.TESTNET);
    });

    it('should handle mainnet button click', () => {
      const mainnetButton = document.createElement('button');
      mainnetButton.id = 'set-mainnet';

      activeNetwork.element.appendChild(mainnetButton);
      mainnetButton.click();

      expect(mockManager.setActiveNetwork).toHaveBeenCalledWith(NetworkId.MAINNET);
    });

    it('should ignore clicks on non-button elements', () => {
      const div = document.createElement('div');

      activeNetwork.element.appendChild(div);
      div.click();

      expect(mockManager.setActiveNetwork).not.toHaveBeenCalled();
    });
  });

  describe('destroy', () => {
    it('should remove event listeners', () => {
      // Mock the removeEventListener
      const removeSpy = jest.spyOn(activeNetwork.element, 'removeEventListener');

      activeNetwork.destroy();

      expect(removeSpy).toHaveBeenCalledWith('click', activeNetwork.addEventListeners);
    });
  });
});