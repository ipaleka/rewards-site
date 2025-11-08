import { AddAllocationsComponent } from './AddAllocationsComponent'
import { RewardsClient } from './RewardsClient'
import { WalletManager } from '@txnlab/use-wallet'

// Mock RewardsClient
jest.mock('./RewardsClient', () => {
  return {
    RewardsClient: jest.fn().mockImplementation(() => {
      return {
        fetchAddAllocationsData: jest.fn(),
        addAllocations: jest.fn(),
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
    alertSpy = jest.spyOn(window, 'alert').mockImplementation(() => {})
    mockRewardsClient = new RewardsClient(null as any, null as any) as jest.Mocked<RewardsClient>
    mockWalletManager = {
      activeAccount: { address: 'test-address' },
      subscribe: jest.fn(),
    } as any

    // Set up the DOM structure
    container = document.createElement('div')
    container.id = 'add-allocations-container'
    container.innerHTML = `
      <textarea id="addresses-input"></textarea>
      <textarea id="amounts-input"></textarea>
      <button id="add-allocations-button"></button>
      <pre id="allocations-data"></pre>
    `
    document.body.appendChild(container)
  })

  afterEach(() => {
    document.body.innerHTML = ''
    alertSpy.mockRestore()
  })

  it('should fetch and display allocations data on initialization', async () => {
    const data = { addresses: ['addr1'], amounts: [100] }
    ;(mockRewardsClient.fetchAddAllocationsData as jest.Mock).mockResolvedValue(data)

    addAllocationsComponent = new AddAllocationsComponent(mockRewardsClient, mockWalletManager)
    addAllocationsComponent.bind(container)
    await new Promise(process.nextTick)

    const addressesInput = container.querySelector('#addresses-input') as HTMLTextAreaElement
    const amountsInput = container.querySelector('#amounts-input') as HTMLTextAreaElement
    const allocationsData = container.querySelector('#allocations-data') as HTMLPreElement

    expect(addressesInput.value).toBe('addr1')
    expect(amountsInput.value).toBe('100')
    expect(allocationsData.textContent).toBe(JSON.stringify(data, null, 2))
    expect(mockRewardsClient.fetchAddAllocationsData).toHaveBeenCalledWith('test-address')
  })

  it('should call addAllocations with data from textareas when button is clicked', async () => {
    ;(mockRewardsClient.fetchAddAllocationsData as jest.Mock).mockResolvedValue({
      addresses: [],
      amounts: [],
    })
    addAllocationsComponent = new AddAllocationsComponent(mockRewardsClient, mockWalletManager)
    addAllocationsComponent.bind(container)
    await new Promise(process.nextTick)

    const addressesInput = container.querySelector('#addresses-input') as HTMLTextAreaElement
    const amountsInput = container.querySelector('#amounts-input') as HTMLTextAreaElement

    addressesInput.value = 'addr1\naddr2'
    amountsInput.value = '100\n200'

    const button = container.querySelector('#add-allocations-button') as HTMLButtonElement
    await button.click()

    expect(mockRewardsClient.addAllocations).toHaveBeenCalledWith(['addr1', 'addr2'], [100, 200])
  })

  it('should re-fetch data after a successful addAllocations call', async () => {
    ;(mockRewardsClient.fetchAddAllocationsData as jest.Mock).mockResolvedValue({
      addresses: [],
      amounts: [],
    })
    addAllocationsComponent = new AddAllocationsComponent(mockRewardsClient, mockWalletManager)
    addAllocationsComponent.bind(container)
    await new Promise(process.nextTick)

    ;(mockRewardsClient.addAllocations as jest.Mock).mockResolvedValue(undefined)

    const button = container.querySelector('#add-allocations-button') as HTMLButtonElement
    await button.click()

    expect(mockRewardsClient.addAllocations).toHaveBeenCalledTimes(1)
    // fetch is called once on init and once after adding allocations
    expect(mockRewardsClient.fetchAddAllocationsData).toHaveBeenCalledTimes(2)
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
    alertSpy = jest.spyOn(window, 'alert').mockImplementation(() => {})
    consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {})
    mockRewardsClient = new RewardsClient(null as any, null as any) as jest.Mocked<RewardsClient>
    mockWalletManager = {
      activeAccount: { address: 'test-address' },
      subscribe: jest.fn(),
    } as any

    container = document.createElement('div')
    container.id = 'add-allocations-container'
    container.innerHTML = `
      <textarea id="addresses-input"></textarea>
      <textarea id="amounts-input"></textarea>
      <button id="add-allocations-button"></button>
      <pre id="allocations-data"></pre>
    `
    document.body.appendChild(container)
  })

  afterEach(() => {
    document.body.innerHTML = ''
    alertSpy.mockRestore()
    consoleErrorSpy.mockRestore()
  })

  describe('fetchAllocationsData error handling', () => {
    it('should handle Error instance when fetching allocations data fails', async () => {
      const testError = new Error('Network error')
      ;(mockRewardsClient.fetchAddAllocationsData as jest.Mock).mockRejectedValue(testError)

      addAllocationsComponent = new AddAllocationsComponent(mockRewardsClient, mockWalletManager)
      addAllocationsComponent.bind(container)
      await new Promise(process.nextTick)

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[AddAllocationsComponent] Error fetching add allocations data:',
        testError
      )
      expect(alertSpy).toHaveBeenCalledWith('Failed to fetch allocations data: Network error')
    })

    it('should handle non-Error object when fetching allocations data fails', async () => {
      const testError = 'Simple string error'
      ;(mockRewardsClient.fetchAddAllocationsData as jest.Mock).mockRejectedValue(testError)

      addAllocationsComponent = new AddAllocationsComponent(mockRewardsClient, mockWalletManager)
      addAllocationsComponent.bind(container)
      await new Promise(process.nextTick)

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[AddAllocationsComponent] Error fetching add allocations data:',
        testError
      )
      expect(alertSpy).toHaveBeenCalledWith('Failed to fetch allocations data: Simple string error')
    })

    it('should clear data and render when no active account', async () => {
      mockWalletManager.activeAccount = null
      ;(mockRewardsClient.fetchAddAllocationsData as jest.Mock).mockResolvedValue({
        addresses: ['addr1'],
        amounts: [100]
      })

      addAllocationsComponent = new AddAllocationsComponent(mockRewardsClient, mockWalletManager)
      addAllocationsComponent.bind(container)
      await new Promise(process.nextTick)

      const addressesInput = container.querySelector('#addresses-input') as HTMLTextAreaElement
      const amountsInput = container.querySelector('#amounts-input') as HTMLTextAreaElement
      const allocationsData = container.querySelector('#allocations-data') as HTMLPreElement

      expect(addressesInput.value).toBe('')
      expect(amountsInput.value).toBe('')
      expect(allocationsData.textContent).toBe(JSON.stringify({ addresses: [], amounts: [] }, null, 2))
      expect(mockRewardsClient.fetchAddAllocationsData).not.toHaveBeenCalled()
    })
  })

  describe('handleAddAllocations error handling', () => {
    beforeEach(async () => {
      ;(mockRewardsClient.fetchAddAllocationsData as jest.Mock).mockResolvedValue({
        addresses: [],
        amounts: [],
      })
      addAllocationsComponent = new AddAllocationsComponent(mockRewardsClient, mockWalletManager)
      addAllocationsComponent.bind(container)
      await new Promise(process.nextTick)
    })

    it('should handle Error instance when addAllocations fails', async () => {
      const testError = new Error('Transaction failed')
      ;(mockRewardsClient.addAllocations as jest.Mock).mockRejectedValue(testError)

      const button = container.querySelector('#add-allocations-button') as HTMLButtonElement
      await button.click()

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[AddAllocationsComponent] Error during add allocations:',
        testError
      )
      expect(alertSpy).toHaveBeenCalledWith('Add allocations failed: Transaction failed')
      expect(mockRewardsClient.fetchAddAllocationsData).toHaveBeenCalledTimes(1) // Only initial fetch, no re-fetch after error
    })

    it('should handle non-Error object when addAllocations fails', async () => {
      const testError = 'Transaction rejected'
      ;(mockRewardsClient.addAllocations as jest.Mock).mockRejectedValue(testError)

      const button = container.querySelector('#add-allocations-button') as HTMLButtonElement
      await button.click()

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[AddAllocationsComponent] Error during add allocations:',
        testError
      )
      expect(alertSpy).toHaveBeenCalledWith('Add allocations failed: Transaction rejected')
      expect(mockRewardsClient.fetchAddAllocationsData).toHaveBeenCalledTimes(1) // Only initial fetch, no re-fetch after error
    })

    it('should handle complex error objects when addAllocations fails', async () => {
      const testError = { code: 400, message: 'Bad request', details: 'Invalid parameters' }
      ;(mockRewardsClient.addAllocations as jest.Mock).mockRejectedValue(testError)

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

  describe('edge cases', () => {
    it('should handle empty textarea inputs gracefully', async () => {
      ;(mockRewardsClient.fetchAddAllocationsData as jest.Mock).mockResolvedValue({
        addresses: [],
        amounts: [],
      })
      addAllocationsComponent = new AddAllocationsComponent(mockRewardsClient, mockWalletManager)
      addAllocationsComponent.bind(container)
      await new Promise(process.nextTick)

      const addressesInput = container.querySelector('#addresses-input') as HTMLTextAreaElement
      const amountsInput = container.querySelector('#amounts-input') as HTMLTextAreaElement

      addressesInput.value = ''
      amountsInput.value = ''

      const button = container.querySelector('#add-allocations-button') as HTMLButtonElement
      await button.click()

      expect(mockRewardsClient.addAllocations).toHaveBeenCalledWith([], [])
    })

    it('should filter out invalid amounts from textarea input', async () => {
      ;(mockRewardsClient.fetchAddAllocationsData as jest.Mock).mockResolvedValue({
        addresses: [],
        amounts: [],
      })
      addAllocationsComponent = new AddAllocationsComponent(mockRewardsClient, mockWalletManager)
      addAllocationsComponent.bind(container)
      await new Promise(process.nextTick)

      const addressesInput = container.querySelector('#addresses-input') as HTMLTextAreaElement
      const amountsInput = container.querySelector('#amounts-input') as HTMLTextAreaElement

      addressesInput.value = 'addr1\naddr2\naddr3'
      amountsInput.value = '100\ninvalid\n300'

      const button = container.querySelector('#add-allocations-button') as HTMLButtonElement
      await button.click()

      expect(mockRewardsClient.addAllocations).toHaveBeenCalledWith(['addr1', 'addr2', 'addr3'], [100, 300])
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
      <textarea id="addresses-input"></textarea>
      <textarea id="amounts-input"></textarea>
      <button id="add-allocations-button"></button>
      <pre id="allocations-data"></pre>
    `
    document.body.appendChild(container)
  })

  afterEach(() => {
    document.body.innerHTML = ''
  })

  describe('render method edge cases', () => {
    it('should return early from render when element is null', () => {
      ;(mockRewardsClient.fetchAddAllocationsData as jest.Mock).mockResolvedValue({
        addresses: ['addr1'],
        amounts: [100]
      })

      addAllocationsComponent = new AddAllocationsComponent(mockRewardsClient, mockWalletManager)
      
      // Don't call bind(), so this.element remains null
      expect(() => {
        addAllocationsComponent.render()
      }).not.toThrow()
      
      // Verify no DOM operations were attempted
      const addressesInput = container.querySelector('#addresses-input') as HTMLTextAreaElement
      const amountsInput = container.querySelector('#amounts-input') as HTMLTextAreaElement
      const allocationsData = container.querySelector('#allocations-data') as HTMLPreElement

      expect(addressesInput.value).toBe('')
      expect(amountsInput.value).toBe('')
      expect(allocationsData.textContent).toBe('')
    })

    it('should handle render when element is bound but querySelectors return null', async () => {
      ;(mockRewardsClient.fetchAddAllocationsData as jest.Mock).mockResolvedValue({
        addresses: ['addr1'],
        amounts: [100]
      })

      addAllocationsComponent = new AddAllocationsComponent(mockRewardsClient, mockWalletManager)
      
      // Create container with missing elements
      const brokenContainer = document.createElement('div')
      brokenContainer.id = 'broken-container'
      // No textareas or pre element inside
      document.body.appendChild(brokenContainer)
      
      addAllocationsComponent.bind(brokenContainer)
      await new Promise(process.nextTick)

      // Should not throw when elements are missing
      expect(() => {
        addAllocationsComponent.render()
      }).not.toThrow()

      document.body.removeChild(brokenContainer)
    })
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
      ;(mockRewardsClient.fetchAddAllocationsData as jest.Mock).mockResolvedValue({
        addresses: [],
        amounts: [],
      })
      ;(mockRewardsClient.addAllocations as jest.Mock).mockResolvedValue(undefined)

      addAllocationsComponent = new AddAllocationsComponent(mockRewardsClient, mockWalletManager)
      addAllocationsComponent.bind(container)

      // Simulate click event without the expected button structure
      const mockEvent = new Event('click', { bubbles: true })
      expect(() => {
        container.dispatchEvent(mockEvent)
      }).not.toThrow()
    })

    it('should handle click events on non-button elements gracefully', () => {
      ;(mockRewardsClient.fetchAddAllocationsData as jest.Mock).mockResolvedValue({
        addresses: [],
        amounts: [],
      })

      addAllocationsComponent = new AddAllocationsComponent(mockRewardsClient, mockWalletManager)
      addAllocationsComponent.bind(container)

      // Click on a non-button element
      const addressesInput = container.querySelector('#addresses-input') as HTMLTextAreaElement
      expect(() => {
        addressesInput.click()
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
      firstContainer.innerHTML = '<textarea id="addresses-input"></textarea>'
      
      const secondContainer = document.createElement('div')  
      secondContainer.innerHTML = '<textarea id="addresses-input"></textarea>'

      expect(() => {
        addAllocationsComponent.bind(firstContainer)
        addAllocationsComponent.bind(secondContainer)
      }).not.toThrow()
    })



    
  })
})
