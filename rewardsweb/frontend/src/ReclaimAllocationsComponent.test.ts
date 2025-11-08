import { ReclaimAllocationsComponent } from './ReclaimAllocationsComponent'
import { RewardsClient } from './RewardsClient'
import { WalletManager } from '@txnlab/use-wallet'

// Mock RewardsClient
jest.mock('./RewardsClient', () => {
  return {
    RewardsClient: jest.fn().mockImplementation(() => {
      return {
        fetchReclaimAllocationsData: jest.fn(),
        reclaimAllocation: jest.fn(),
      }
    }),
  }
})

describe('ReclaimAllocationsComponent', () => {
  let mockRewardsClient: jest.Mocked<RewardsClient>
  let mockWalletManager: jest.Mocked<WalletManager>
  let reclaimAllocationsComponent: ReclaimAllocationsComponent
  let alertSpy: jest.SpyInstance
  let container: HTMLElement

  beforeEach(() => {
    alertSpy = jest.spyOn(window, 'alert').mockImplementation(() => { })
    mockRewardsClient = new RewardsClient(null as any, null as any) as jest.Mocked<RewardsClient>
    mockWalletManager = {
      activeAccount: { address: 'test-address' },
      subscribe: jest.fn(),
    } as any

    // Set up the DOM structure
    container = document.createElement('div')
    container.id = 'reclaim-allocations-container'
    container.innerHTML = `<div id="reclaim-list"></div>`
    document.body.appendChild(container)
  })

  afterEach(() => {
    document.body.innerHTML = ''
    alertSpy.mockRestore()
  })

  it('should fetch and display reclaimable addresses on initialization', async () => {
    const data = { addresses: ['addr1', 'addr2'] }
      ; (mockRewardsClient.fetchReclaimAllocationsData as jest.Mock).mockResolvedValue(data)

    reclaimAllocationsComponent = new ReclaimAllocationsComponent(mockRewardsClient, mockWalletManager)
    reclaimAllocationsComponent.bind(container)
    await new Promise(process.nextTick)

    const listItems = container.querySelectorAll('li')
    expect(listItems.length).toBe(2)
    expect(listItems[0].textContent).toContain('addr1')
    expect(listItems[1].textContent).toContain('addr2')
    expect(mockRewardsClient.fetchReclaimAllocationsData).toHaveBeenCalledWith('test-address')
  })

  it('should display a message when no reclaimable allocations are found', async () => {
    const data = { addresses: [] }
      ; (mockRewardsClient.fetchReclaimAllocationsData as jest.Mock).mockResolvedValue(data)

    reclaimAllocationsComponent = new ReclaimAllocationsComponent(mockRewardsClient, mockWalletManager)
    reclaimAllocationsComponent.bind(container)
    await new Promise(process.nextTick)

    const paragraph = container.querySelector('p')
    expect(paragraph?.textContent).toBe('No reclaimable allocations found.')
  })

  it('should call reclaimAllocation with the correct address when a reclaim button is clicked', async () => {
    const data = { addresses: ['addr-to-reclaim'] }
      ; (mockRewardsClient.fetchReclaimAllocationsData as jest.Mock).mockResolvedValue(data)
    reclaimAllocationsComponent = new ReclaimAllocationsComponent(mockRewardsClient, mockWalletManager)
    reclaimAllocationsComponent.bind(container)
    await new Promise(process.nextTick)

    const button = container.querySelector('#reclaim-button-addr-to-reclaim') as HTMLButtonElement
    await button.click()

    expect(mockRewardsClient.reclaimAllocation).toHaveBeenCalledWith('addr-to-reclaim')
  })

  it('should re-fetch data after a successful reclaim call', async () => {
    const data = { addresses: ['addr1'] }
      ; (mockRewardsClient.fetchReclaimAllocationsData as jest.Mock).mockResolvedValueOnce(data)
    reclaimAllocationsComponent = new ReclaimAllocationsComponent(mockRewardsClient, mockWalletManager)
    reclaimAllocationsComponent.bind(container)
    await new Promise(process.nextTick)

      ; (mockRewardsClient.reclaimAllocation as jest.Mock).mockResolvedValue(undefined)
      ; (mockRewardsClient.fetchReclaimAllocationsData as jest.Mock).mockResolvedValueOnce({ addresses: [] })

    const button = container.querySelector('#reclaim-button-addr1') as HTMLButtonElement
    await button.click()

    expect(mockRewardsClient.reclaimAllocation).toHaveBeenCalledTimes(1)
    // fetch is called once on init and once after reclaiming
    expect(mockRewardsClient.fetchReclaimAllocationsData).toHaveBeenCalledTimes(2)
  })

  it('should not fetch data if no active account', async () => {
    mockWalletManager.activeAccount = null
    reclaimAllocationsComponent = new ReclaimAllocationsComponent(mockRewardsClient, mockWalletManager)
    reclaimAllocationsComponent.bind(container)
    await new Promise(process.nextTick)

    expect(mockRewardsClient.fetchReclaimAllocationsData).not.toHaveBeenCalled()
  })

  it('should handle errors when fetching reclaim allocations data', async () => {
    const fetchError = new Error('Network failure')
      ; (mockRewardsClient.fetchReclaimAllocationsData as jest.Mock).mockRejectedValue(fetchError)

    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => { })

    reclaimAllocationsComponent = new ReclaimAllocationsComponent(mockRewardsClient, mockWalletManager)
    reclaimAllocationsComponent.bind(container)
    await new Promise(process.nextTick)

    // assert console.error call from catch block
    expect(consoleSpy).toHaveBeenCalledWith(
      '[ReclaimAllocationsComponent] Error fetching reclaim allocations data:',
      fetchError
    )

    // assert alert call with formatted message
    expect(alertSpy).toHaveBeenCalledWith(
      `Failed to fetch reclaim allocations data: ${fetchError.message}`
    )

    consoleSpy.mockRestore()
  })

  it('should alert using String(error) when reclaim fails with non-Error value', () => {
    reclaimAllocationsComponent = new ReclaimAllocationsComponent(mockRewardsClient, mockWalletManager)

    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => { })

    // @ts-ignore private method – testing implementation on purpose
    reclaimAllocationsComponent.handleReclaimError('addr-x', 'boom')

    expect(consoleSpy).toHaveBeenCalledWith(
      `[ReclaimAllocationsComponent] Error during reclaim for addr-x:`,
      'boom'
    )

    expect(alertSpy).toHaveBeenCalledWith(
      `Reclaim for addr-x failed: boom`
    )

    consoleSpy.mockRestore()
  })
})

describe('ReclaimAllocationsComponent Error Handling', () => {
  let mockRewardsClient: jest.Mocked<RewardsClient>
  let mockWalletManager: jest.Mocked<WalletManager>
  let reclaimAllocationsComponent: ReclaimAllocationsComponent
  let alertSpy: jest.SpyInstance
  let consoleErrorSpy: jest.SpyInstance
  let container: HTMLElement

  beforeEach(() => {
    alertSpy = jest.spyOn(window, 'alert').mockImplementation(() => { })
    consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => { })
    mockRewardsClient = new RewardsClient(null as any, null as any) as jest.Mocked<RewardsClient>
    mockWalletManager = {
      activeAccount: { address: 'test-address' },
      subscribe: jest.fn(),
    } as any

    container = document.createElement('div')
    container.id = 'reclaim-allocations-container'
    container.innerHTML = `<div id="reclaim-list"></div>`
    document.body.appendChild(container)
  })

  afterEach(() => {
    document.body.innerHTML = ''
    alertSpy.mockRestore()
    consoleErrorSpy.mockRestore()
  })

  describe('handleReclaimAllocation error handling', () => {
    beforeEach(async () => {
      const data = { addresses: ['addr1', 'addr2'] }
        ; (mockRewardsClient.fetchReclaimAllocationsData as jest.Mock).mockResolvedValue(data)
      reclaimAllocationsComponent = new ReclaimAllocationsComponent(mockRewardsClient, mockWalletManager)
      reclaimAllocationsComponent.bind(container)
      await new Promise(process.nextTick)
    })

    it('should call handleReclaimError when reclaimAllocation fails with Error instance', async () => {
      const testError = new Error('Transaction failed')
        ; (mockRewardsClient.reclaimAllocation as jest.Mock).mockRejectedValue(testError)

      const button = container.querySelector('#reclaim-button-addr1') as HTMLButtonElement
      await button.click()

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        `[ReclaimAllocationsComponent] Error during reclaim for addr1:`,
        testError
      )
      expect(alertSpy).toHaveBeenCalledWith('Reclaim for addr1 failed: Transaction failed')
    })

    it('should call handleReclaimError when reclaimAllocation fails with non-Error object', async () => {
      const testError = 'Simple string error'
        ; (mockRewardsClient.reclaimAllocation as jest.Mock).mockRejectedValue(testError)

      const button = container.querySelector('#reclaim-button-addr1') as HTMLButtonElement
      await button.click()

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        `[ReclaimAllocationsComponent] Error during reclaim for addr1:`,
        testError
      )
      expect(alertSpy).toHaveBeenCalledWith('Reclaim for addr1 failed: Simple string error')
    })

    it('should call handleReclaimError when reclaimAllocation fails with complex object', async () => {
      const testError = { code: 400, message: 'Bad request', details: 'Invalid parameters' }
        ; (mockRewardsClient.reclaimAllocation as jest.Mock).mockRejectedValue(testError)

      const button = container.querySelector('#reclaim-button-addr1') as HTMLButtonElement
      await button.click()

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        `[ReclaimAllocationsComponent] Error during reclaim for addr1:`,
        testError
      )
      expect(alertSpy).toHaveBeenCalledWith('Reclaim for addr1 failed: [object Object]')
    })

    it('should not re-fetch data after a failed reclaim call', async () => {
      const testError = new Error('Transaction failed')
        ; (mockRewardsClient.reclaimAllocation as jest.Mock).mockRejectedValue(testError)

      const button = container.querySelector('#reclaim-button-addr1') as HTMLButtonElement
      await button.click()

      // fetchReclaimAllocationsData should only be called once (on init), not after failed reclaim
      expect(mockRewardsClient.fetchReclaimAllocationsData).toHaveBeenCalledTimes(1)
    })

    it('should handle multiple reclaim failures independently', async () => {
      const error1 = new Error('First transaction failed')
      const error2 = new Error('Second transaction failed')

        ; (mockRewardsClient.reclaimAllocation as jest.Mock)
          .mockRejectedValueOnce(error1)
          .mockRejectedValueOnce(error2)

      const button1 = container.querySelector('#reclaim-button-addr1') as HTMLButtonElement
      const button2 = container.querySelector('#reclaim-button-addr2') as HTMLButtonElement

      await button1.click()
      await button2.click()

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        `[ReclaimAllocationsComponent] Error during reclaim for addr1:`,
        error1
      )
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        `[ReclaimAllocationsComponent] Error during reclaim for addr2:`,
        error2
      )
      expect(alertSpy).toHaveBeenCalledWith('Reclaim for addr1 failed: First transaction failed')
      expect(alertSpy).toHaveBeenCalledWith('Reclaim for addr2 failed: Second transaction failed')
    })
  })

  describe('handleReclaimError method', () => {
    beforeEach(() => {
      reclaimAllocationsComponent = new ReclaimAllocationsComponent(mockRewardsClient, mockWalletManager)
    })

    it('should handle Error instances with proper message extraction', () => {
      const testError = new Error('Network timeout')
      const address = 'test-address-123'

      reclaimAllocationsComponent['handleReclaimError'](address, testError)

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        `[ReclaimAllocationsComponent] Error during reclaim for ${address}:`,
        testError
      )
      expect(alertSpy).toHaveBeenCalledWith(`Reclaim for ${address} failed: Network timeout`)
    })

    it('should handle string errors with String conversion', () => {
      const testError = 'Connection refused'
      const address = 'test-address-456'

      reclaimAllocationsComponent['handleReclaimError'](address, testError)

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        `[ReclaimAllocationsComponent] Error during reclaim for ${address}:`,
        testError
      )
      expect(alertSpy).toHaveBeenCalledWith(`Reclaim for ${address} failed: Connection refused`)
    })

    it('should handle null errors', () => {
      const address = 'test-address-null'

      reclaimAllocationsComponent['handleReclaimError'](address, null)

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        `[ReclaimAllocationsComponent] Error during reclaim for ${address}:`,
        null
      )
      expect(alertSpy).toHaveBeenCalledWith(`Reclaim for ${address} failed: null`)
    })

    it('should handle undefined errors', () => {
      const address = 'test-address-undefined'

      reclaimAllocationsComponent['handleReclaimError'](address, undefined)

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        `[ReclaimAllocationsComponent] Error during reclaim for ${address}:`,
        undefined
      )
      expect(alertSpy).toHaveBeenCalledWith(`Reclaim for ${address} failed: undefined`)
    })

    it('should handle complex objects with String conversion', () => {
      const testError = { status: 500, data: { message: 'Internal server error' } }
      const address = 'test-address-complex'

      reclaimAllocationsComponent['handleReclaimError'](address, testError)

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        `[ReclaimAllocationsComponent] Error during reclaim for ${address}:`,
        testError
      )
      expect(alertSpy).toHaveBeenCalledWith(`Reclaim for ${address} failed: [object Object]`)
    })
  })

  describe('edge cases', () => {
    it('should handle render when element is null', () => {
      reclaimAllocationsComponent = new ReclaimAllocationsComponent(mockRewardsClient, mockWalletManager)
      // Don't call bind(), so this.element remains null
      expect(() => {
        reclaimAllocationsComponent.render()
      }).not.toThrow()
    })

    it('should handle addEventListeners when element is null', () => {
      reclaimAllocationsComponent = new ReclaimAllocationsComponent(mockRewardsClient, mockWalletManager)
      // Don't call bind(), so this.element remains null
      expect(() => {
        reclaimAllocationsComponent.addEventListeners()
      }).not.toThrow()
    })

    it('should handle render when reclaim-list element is missing', () => {
      const containerWithoutList = document.createElement('div')
      containerWithoutList.innerHTML = `<div>No reclaim list here</div>`
      document.body.appendChild(containerWithoutList)

      reclaimAllocationsComponent = new ReclaimAllocationsComponent(mockRewardsClient, mockWalletManager)
      reclaimAllocationsComponent.bind(containerWithoutList)

      expect(() => {
        reclaimAllocationsComponent.render()
      }).not.toThrow()

      document.body.removeChild(containerWithoutList)
    })

    it('should handle click events on non-reclaim-button elements gracefully', async () => {
      const data = { addresses: ['addr1'] }
        ; (mockRewardsClient.fetchReclaimAllocationsData as jest.Mock).mockResolvedValue(data)
      reclaimAllocationsComponent = new ReclaimAllocationsComponent(mockRewardsClient, mockWalletManager)
      reclaimAllocationsComponent.bind(container)
      await new Promise(process.nextTick)

      // Simulate click event on non-button element
      const listItem = container.querySelector('li') as HTMLLIElement
      expect(() => {
        listItem.click()
      }).not.toThrow()

      expect(mockRewardsClient.reclaimAllocation).not.toHaveBeenCalled()
    })

    it('should handle click events with missing data-address attribute', async () => {
      const data = { addresses: ['addr1'] }
        ; (mockRewardsClient.fetchReclaimAllocationsData as jest.Mock).mockResolvedValue(data)
      reclaimAllocationsComponent = new ReclaimAllocationsComponent(mockRewardsClient, mockWalletManager)
      reclaimAllocationsComponent.bind(container)
      await new Promise(process.nextTick)

      // Remove data-attribute to simulate malformed button
      const button = container.querySelector('#reclaim-button-addr1') as HTMLButtonElement
      button.removeAttribute('data-address')

      await button.click()

      expect(mockRewardsClient.reclaimAllocation).not.toHaveBeenCalled()
    })

    it('should handle empty address in handleReclaimError', () => {
      reclaimAllocationsComponent = new ReclaimAllocationsComponent(mockRewardsClient, mockWalletManager)

      const testError = new Error('Test error')
      reclaimAllocationsComponent['handleReclaimError']('', testError)

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        `[ReclaimAllocationsComponent] Error during reclaim for :`,
        testError
      )
      expect(alertSpy).toHaveBeenCalledWith(`Reclaim for  failed: Test error`)
    })
  })
})

describe('ReclaimAllocationsComponent Fetch Error Handling', () => {
  let mockRewardsClient: jest.Mocked<RewardsClient>
  let mockWalletManager: jest.Mocked<WalletManager>
  let reclaimAllocationsComponent: ReclaimAllocationsComponent
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
    container.id = 'reclaim-allocations-container'
    container.innerHTML = `<div id="reclaim-list"></div>`
    document.body.appendChild(container)
  })

  afterEach(() => {
    document.body.innerHTML = ''
    alertSpy.mockRestore()
    consoleErrorSpy.mockRestore()
  })

  describe('fetchReclaimAllocationsData error handling', () => {
    it('should handle non-Error object when fetching reclaim allocations data fails', async () => {
      const testError = 'Simple string error - not an Error instance'
      ;(mockRewardsClient.fetchReclaimAllocationsData as jest.Mock).mockRejectedValue(testError)

      reclaimAllocationsComponent = new ReclaimAllocationsComponent(mockRewardsClient, mockWalletManager)
      reclaimAllocationsComponent.bind(container)
      await new Promise(process.nextTick)

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[ReclaimAllocationsComponent] Error fetching reclaim allocations data:',
        testError
      )
      expect(alertSpy).toHaveBeenCalledWith(
        'Failed to fetch reclaim allocations data: Simple string error - not an Error instance'
      )
    })

    it('should handle null when fetching reclaim allocations data fails', async () => {
      ;(mockRewardsClient.fetchReclaimAllocationsData as jest.Mock).mockRejectedValue(null)

      reclaimAllocationsComponent = new ReclaimAllocationsComponent(mockRewardsClient, mockWalletManager)
      reclaimAllocationsComponent.bind(container)
      await new Promise(process.nextTick)

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[ReclaimAllocationsComponent] Error fetching reclaim allocations data:',
        null
      )
      expect(alertSpy).toHaveBeenCalledWith('Failed to fetch reclaim allocations data: null')
    })

    it('should handle undefined when fetching reclaim allocations data fails', async () => {
      ;(mockRewardsClient.fetchReclaimAllocationsData as jest.Mock).mockRejectedValue(undefined)

      reclaimAllocationsComponent = new ReclaimAllocationsComponent(mockRewardsClient, mockWalletManager)
      reclaimAllocationsComponent.bind(container)
      await new Promise(process.nextTick)

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[ReclaimAllocationsComponent] Error fetching reclaim allocations data:',
        undefined
      )
      expect(alertSpy).toHaveBeenCalledWith('Failed to fetch reclaim allocations data: undefined')
    })

    it('should handle complex objects when fetching reclaim allocations data fails', async () => {
      const testError = { 
        status: 500, 
        statusText: 'Internal Server Error',
        data: { message: 'Something went wrong' }
      }
      ;(mockRewardsClient.fetchReclaimAllocationsData as jest.Mock).mockRejectedValue(testError)

      reclaimAllocationsComponent = new ReclaimAllocationsComponent(mockRewardsClient, mockWalletManager)
      reclaimAllocationsComponent.bind(container)
      await new Promise(process.nextTick)

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[ReclaimAllocationsComponent] Error fetching reclaim allocations data:',
        testError
      )
      expect(alertSpy).toHaveBeenCalledWith('Failed to fetch reclaim allocations data: [object Object]')
    })

    it('should handle numeric errors when fetching reclaim allocations data fails', async () => {
      const testError = 404
      ;(mockRewardsClient.fetchReclaimAllocationsData as jest.Mock).mockRejectedValue(testError)

      reclaimAllocationsComponent = new ReclaimAllocationsComponent(mockRewardsClient, mockWalletManager)
      reclaimAllocationsComponent.bind(container)
      await new Promise(process.nextTick)

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[ReclaimAllocationsComponent] Error fetching reclaim allocations data:',
        testError
      )
      expect(alertSpy).toHaveBeenCalledWith('Failed to fetch reclaim allocations data: 404')
    })

    it('should handle boolean errors when fetching reclaim allocations data fails', async () => {
      const testError = false
      ;(mockRewardsClient.fetchReclaimAllocationsData as jest.Mock).mockRejectedValue(testError)

      reclaimAllocationsComponent = new ReclaimAllocationsComponent(mockRewardsClient, mockWalletManager)
      reclaimAllocationsComponent.bind(container)
      await new Promise(process.nextTick)

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[ReclaimAllocationsComponent] Error fetching reclaim allocations data:',
        testError
      )
      expect(alertSpy).toHaveBeenCalledWith('Failed to fetch reclaim allocations data: false')
    })

    it('should handle array errors when fetching reclaim allocations data fails', async () => {
      const testError = ['error1', 'error2']
      ;(mockRewardsClient.fetchReclaimAllocationsData as jest.Mock).mockRejectedValue(testError)

      reclaimAllocationsComponent = new ReclaimAllocationsComponent(mockRewardsClient, mockWalletManager)
      reclaimAllocationsComponent.bind(container)
      await new Promise(process.nextTick)

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[ReclaimAllocationsComponent] Error fetching reclaim allocations data:',
        testError
      )
      expect(alertSpy).toHaveBeenCalledWith('Failed to fetch reclaim allocations data: error1,error2')
    })
  })

  describe('comprehensive error type coverage', () => {
    const errorScenarios = [
      { type: 'string', value: 'Network timeout', expectedAlert: 'Failed to fetch reclaim allocations data: Network timeout' },
      { type: 'number', value: 500, expectedAlert: 'Failed to fetch reclaim allocations data: 500' },
      { type: 'boolean', value: true, expectedAlert: 'Failed to fetch reclaim allocations data: true' },
      { type: 'null', value: null, expectedAlert: 'Failed to fetch reclaim allocations data: null' },
      { type: 'undefined', value: undefined, expectedAlert: 'Failed to fetch reclaim allocations data: undefined' },
      { type: 'object', value: { code: 400 }, expectedAlert: 'Failed to fetch reclaim allocations data: [object Object]' },
      { type: 'array', value: ['err1', 'err2'], expectedAlert: 'Failed to fetch reclaim allocations data: err1,err2' },
      { type: 'Error instance', value: new Error('Standard error'), expectedAlert: 'Failed to fetch reclaim allocations data: Standard error' },
    ]

    errorScenarios.forEach(({ type, value, expectedAlert }) => {
      it(`should handle ${type} errors in fetchReclaimAllocationsData`, async () => {
        ;(mockRewardsClient.fetchReclaimAllocationsData as jest.Mock).mockRejectedValue(value)

        reclaimAllocationsComponent = new ReclaimAllocationsComponent(mockRewardsClient, mockWalletManager)
        reclaimAllocationsComponent.bind(container)
        await new Promise(process.nextTick)

        expect(alertSpy).toHaveBeenCalledWith(expectedAlert)
      })
    })
  })
})