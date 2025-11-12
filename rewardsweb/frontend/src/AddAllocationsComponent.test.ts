import { AddAllocationsComponent } from './AddAllocationsComponent'
import { RewardsClient } from './RewardsClient'
import { WalletManager } from '@txnlab/use-wallet'

// Mock window.location.reload
Object.defineProperty(window, 'location', {
  value: {
    reload: jest.fn(),
  },
  writable: true,
});

// Mock RewardsClient
jest.mock('./RewardsClient', () => {
  return {
    RewardsClient: jest.fn().mockImplementation(() => {
      return {
        fetchAddAllocationsData: jest.fn(),
        addAllocations: jest.fn(),
        notifyAllocationsSuccessful: jest.fn().mockResolvedValue(undefined),
      }
    }),
  }
})

describe('AddAllocationsComponent', () => {
  let mockRewardsClient: jest.Mocked<RewardsClient>
  let mockWalletManager: jest.Mocked<WalletManager>
  let addAllocationsComponent: AddAllocationsComponent
  let alertSpy: jest.SpyInstance
  let container: HTMLElement

  beforeEach(() => {
    alertSpy = jest.spyOn(window, 'alert').mockImplementation(() => { })
    // Fix: Updated constructor to match new signature (only WalletManager)
    mockRewardsClient = new RewardsClient(null as any) as jest.Mocked<RewardsClient>
    mockWalletManager = {
      activeAccount: { address: 'test-address' },
      subscribe: jest.fn(),
    } as any

    // Initialize container before setting innerHTML
    container = document.createElement('div')
    container.id = 'add-allocations-container'
    container.innerHTML = `
      <table class="table w-full">
        <thead>
          <tr>
            <th>Address</th>
            <th>Amount</th>
          </tr>
        </thead>
        <tbody id="allocations-table-body">
          <tr>
            <td>addr1</td>
            <td>100</td>
          </tr>
        </tbody>
      </table>
      <button id="add-allocations-button"></button>
    `
    document.body.appendChild(container)
  })

  afterEach(() => {
    document.body.innerHTML = ''
    alertSpy.mockRestore()
    jest.clearAllMocks()
  })

  it('should call addAllocations with fetched data when button is clicked', async () => {
    const data = { addresses: ['addr1', 'addr2'], amounts: [100, 200] }
      ; (mockRewardsClient.fetchAddAllocationsData as jest.Mock).mockResolvedValue(data)
      ; (mockRewardsClient.addAllocations as jest.Mock).mockResolvedValue({ txIDs: ['test-tx'] })

    addAllocationsComponent = new AddAllocationsComponent(mockRewardsClient, mockWalletManager)
    addAllocationsComponent.bind(container)
    await new Promise(process.nextTick)

    const button = container.querySelector('#add-allocations-button') as HTMLButtonElement
    await button.click()

    // Updated to include the decimals parameter
    expect(mockRewardsClient.addAllocations).toHaveBeenCalledWith(['addr1', 'addr2'], [100, 200], 6)
  })

  it('should not fetch data if no active account', async () => {
    mockWalletManager.activeAccount = null
    addAllocationsComponent = new AddAllocationsComponent(mockRewardsClient, mockWalletManager)
    addAllocationsComponent.bind(container)
    await new Promise(process.nextTick)

    expect(mockRewardsClient.fetchAddAllocationsData).not.toHaveBeenCalled()
  })
})

describe('AddAllocationsComponent Error Handling', () => {
  let mockRewardsClient: jest.Mocked<RewardsClient>
  let mockWalletManager: jest.Mocked<WalletManager>
  let addAllocationsComponent: AddAllocationsComponent
  let alertSpy: jest.SpyInstance
  let consoleErrorSpy: jest.SpyInstance
  let container: HTMLElement

  beforeEach(() => {
    alertSpy = jest.spyOn(window, 'alert').mockImplementation(() => { })
    consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => { })
    // Fix: Updated constructor to match new signature (only WalletManager)
    mockRewardsClient = new RewardsClient(null as any) as jest.Mocked<RewardsClient>
    mockWalletManager = {
      activeAccount: { address: 'test-address' },
      subscribe: jest.fn(),
    } as any

    container = document.createElement('div')
    container.id = 'add-allocations-container'
    container.innerHTML = `
      <table class="table w-full">
        <thead>
          <tr>
            <th>Address</th>
            <th>Amount</th>
          </tr>
        </thead>
        <tbody id="allocations-table-body">
          <tr>
            <td>addr1</td>
            <td>100</td>
          </tr>
        </tbody>
      </table>
      <button id="add-allocations-button"></button>
    `
    document.body.appendChild(container)
  })

  afterEach(() => {
    document.body.innerHTML = ''
    alertSpy.mockRestore()
    consoleErrorSpy.mockRestore()
    jest.clearAllMocks()
  })

  describe('fetchAllocationsData error handling', () => {
    it('should handle Error instance when fetching allocations data fails', async () => {
      const testError = new Error('Network error')
        ; (mockRewardsClient.fetchAddAllocationsData as jest.Mock).mockRejectedValue(testError)

      addAllocationsComponent = new AddAllocationsComponent(mockRewardsClient, mockWalletManager)
      addAllocationsComponent.bind(container)
      await new Promise(process.nextTick)

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[AddAllocationsComponent] Error fetching add allocations data:',
        testError
      )
      // Component no longer shows alert for fetch errors, only logs to console
      expect(alertSpy).not.toHaveBeenCalled()
    })

    it('should handle non-Error object when fetching allocations data fails', async () => {
      const testError = 'Simple string error'
        ; (mockRewardsClient.fetchAddAllocationsData as jest.Mock).mockRejectedValue(testError)

      addAllocationsComponent = new AddAllocationsComponent(mockRewardsClient, mockWalletManager)
      addAllocationsComponent.bind(container)
      await new Promise(process.nextTick)

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[AddAllocationsComponent] Error fetching add allocations data:',
        testError
      )
      // Component no longer shows alert for fetch errors, only logs to console
      expect(alertSpy).not.toHaveBeenCalled()
    })

    it('should clear data and render when no active account', async () => {
      mockWalletManager.activeAccount = null
      addAllocationsComponent = new AddAllocationsComponent(mockRewardsClient, mockWalletManager)
      addAllocationsComponent.bind(container)
      await new Promise(process.nextTick)

      // Since the render method is now empty (as per the component comment),
      // we should verify that the internal state is cleared instead
      expect(addAllocationsComponent['addresses']).toEqual([])
      expect(addAllocationsComponent['amounts']).toEqual([])
      expect(mockRewardsClient.fetchAddAllocationsData).not.toHaveBeenCalled()
    })
  })

  describe('handleAddAllocations error handling', () => {
    beforeEach(async () => {
      ; (mockRewardsClient.fetchAddAllocationsData as jest.Mock).mockResolvedValue({
        addresses: ['addr1', 'addr2'],
        amounts: [100, 200],
      })
      addAllocationsComponent = new AddAllocationsComponent(mockRewardsClient, mockWalletManager)
      addAllocationsComponent.bind(container)
      await new Promise(process.nextTick)
    })

    it('should handle Error instance when addAllocations fails', async () => {
      const testError = new Error('Transaction failed')
        ; (mockRewardsClient.addAllocations as jest.Mock).mockRejectedValue(testError)

      const button = container.querySelector('#add-allocations-button') as HTMLButtonElement
      await button.click()

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[AddAllocationsComponent] Error during add allocations:',
        testError
      )
      expect(alertSpy).toHaveBeenCalledWith('Add allocations failed: Transaction failed')
      // Component reloads page on success, not re-fetches data
      expect(mockRewardsClient.fetchAddAllocationsData).toHaveBeenCalledTimes(1)
    })

    it('should handle non-Error object when addAllocations fails', async () => {
      const testError = 'Transaction rejected'
        ; (mockRewardsClient.addAllocations as jest.Mock).mockRejectedValue(testError)

      const button = container.querySelector('#add-allocations-button') as HTMLButtonElement
      await button.click()

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[AddAllocationsComponent] Error during add allocations:',
        testError
      )
      expect(alertSpy).toHaveBeenCalledWith('Add allocations failed: Transaction rejected')
      expect(mockRewardsClient.fetchAddAllocationsData).toHaveBeenCalledTimes(1)
    })

    it('should handle complex error objects when addAllocations fails', async () => {
      const testError = { code: 400, message: 'Bad request', details: 'Invalid parameters' }
        ; (mockRewardsClient.addAllocations as jest.Mock).mockRejectedValue(testError)

      const button = container.querySelector('#add-allocations-button') as HTMLButtonElement
      await button.click()

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[AddAllocationsComponent] Error during add allocations:',
        testError
      )
      expect(alertSpy).toHaveBeenCalledWith('Add allocations failed: [object Object]')
      expect(mockRewardsClient.fetchAddAllocationsData).toHaveBeenCalledTimes(1)
    })
  })
})

describe('AddAllocationsComponent Edge Cases', () => {
  let mockRewardsClient: jest.Mocked<RewardsClient>
  let mockWalletManager: jest.Mocked<WalletManager>
  let addAllocationsComponent: AddAllocationsComponent
  let container: HTMLElement

  beforeEach(() => {
    mockRewardsClient = new RewardsClient(null as any, null as any) as jest.Mocked<RewardsClient>
    mockWalletManager = {
      activeAccount: { address: 'test-address' },
      subscribe: jest.fn(),
    } as any

    container = document.createElement('div')
    container.id = 'add-allocations-container'
    container.innerHTML = `
      <table class="table w-full">
        <thead>
          <tr>
            <th>Address</th>
            <th>Amount</th>
          </tr>
        </thead>
        <tbody id="allocations-table-body">
          <tr>
            <td>addr1</td>
            <td>100</td>
          </tr>
        </tbody>
      </table>
      <button id="add-allocations-button"></button>
    `
    document.body.appendChild(container)
  })

  afterEach(() => {
    document.body.innerHTML = ''
  })

  describe('addEventListeners method edge cases', () => {
    it('should return early from addEventListeners when element is null', () => {
      addAllocationsComponent = new AddAllocationsComponent(mockRewardsClient, mockWalletManager)

      // Don't call bind(), so this.element remains null
      expect(() => {
        addAllocationsComponent.addEventListeners()
      }).not.toThrow()
    })

    it('should not throw when event listener is called without proper target structure', () => {
      ; (mockRewardsClient.fetchAddAllocationsData as jest.Mock).mockResolvedValue({
        addresses: [],
        amounts: [],
      })
        ; (mockRewardsClient.addAllocations as jest.Mock).mockResolvedValue(undefined)

      addAllocationsComponent = new AddAllocationsComponent(mockRewardsClient, mockWalletManager)
      addAllocationsComponent.bind(container)

      // Simulate click event without the expected button structure
      const mockEvent = new Event('click', { bubbles: true })
      expect(() => {
        container.dispatchEvent(mockEvent)
      }).not.toThrow()
    })

    it('should handle click events on non-button elements gracefully', () => {
      addAllocationsComponent = new AddAllocationsComponent(mockRewardsClient, mockWalletManager)
      addAllocationsComponent.bind(container)

      // Click on a non-button element
      const tableBody = container.querySelector('#allocations-table-body') as HTMLTableSectionElement
      expect(() => {
        tableBody.click()
      }).not.toThrow()

      expect(mockRewardsClient.addAllocations).not.toHaveBeenCalled()
    })
  })

  describe('component lifecycle', () => {
    it('should handle destroy method without errors', () => {
      addAllocationsComponent = new AddAllocationsComponent(mockRewardsClient, mockWalletManager)
      addAllocationsComponent.bind(container)

      expect(() => {
        addAllocationsComponent.destroy()
      }).not.toThrow()
    })

    it('should handle multiple bind calls', () => {
      addAllocationsComponent = new AddAllocationsComponent(mockRewardsClient, mockWalletManager)

      const firstContainer = document.createElement('div')
      firstContainer.innerHTML = '<table id="allocations-table-body"></table>'

      const secondContainer = document.createElement('div')
      secondContainer.innerHTML = '<table id="allocations-table-body"></table>'

      expect(() => {
        addAllocationsComponent.bind(firstContainer)
        addAllocationsComponent.bind(secondContainer)
      }).not.toThrow()
    })
  })
  describe('DOM ready state handling', () => {
    let addEventListenerSpy: jest.SpyInstance;
    let originalReadyState: DocumentReadyState;

    beforeEach(() => {
      addEventListenerSpy = jest.spyOn(document, 'addEventListener');
      originalReadyState = document.readyState;
    });

    afterEach(() => {
      addEventListenerSpy.mockRestore();
      Object.defineProperty(document, 'readyState', {
        value: originalReadyState,
        writable: true
      });
    });

    it('should add DOMContentLoaded listener when document is loading', () => {
      // Patch document.readyState to 'loading'
      Object.defineProperty(document, 'readyState', {
        value: 'loading',
        writable: true
      });

      const data = { addresses: ['addr1', 'addr2'], amounts: [100, 200] };
      (mockRewardsClient.fetchAddAllocationsData as jest.Mock).mockResolvedValue(data);

      addAllocationsComponent = new AddAllocationsComponent(mockRewardsClient, mockWalletManager);
      addAllocationsComponent.bind(container);

      // Should add event listener for DOMContentLoaded
      expect(addEventListenerSpy).toHaveBeenCalledWith(
        'DOMContentLoaded',
        expect.any(Function)
      );
    });

    it('should fetch data immediately when document is loaded', async () => {
      // Patch document.readyState to 'complete'
      Object.defineProperty(document, 'readyState', {
        value: 'complete',
        writable: true
      });

      const data = { addresses: ['addr1', 'addr2'], amounts: [100, 200] };
      (mockRewardsClient.fetchAddAllocationsData as jest.Mock).mockResolvedValue(data);

      addAllocationsComponent = new AddAllocationsComponent(mockRewardsClient, mockWalletManager);
      addAllocationsComponent.bind(container);

      // Should fetch data immediately (not add event listener)
      expect(addEventListenerSpy).not.toHaveBeenCalledWith(
        'DOMContentLoaded',
        expect.any(Function)
      );

      await new Promise(process.nextTick);
      expect(mockRewardsClient.fetchAddAllocationsData).toHaveBeenCalledWith('test-address');
    });

    it('should fetch data immediately when document is interactive', async () => {
      // Patch document.readyState to 'interactive'
      Object.defineProperty(document, 'readyState', {
        value: 'interactive',
        writable: true
      });

      const data = { addresses: ['addr1', 'addr2'], amounts: [100, 200] };
      (mockRewardsClient.fetchAddAllocationsData as jest.Mock).mockResolvedValue(data);

      addAllocationsComponent = new AddAllocationsComponent(mockRewardsClient, mockWalletManager);
      addAllocationsComponent.bind(container);

      // Should fetch data immediately (not add event listener)
      expect(addEventListenerSpy).not.toHaveBeenCalledWith(
        'DOMContentLoaded',
        expect.any(Function)
      );

      await new Promise(process.nextTick);
      expect(mockRewardsClient.fetchAddAllocationsData).toHaveBeenCalledWith('test-address');
    });
  });

})
