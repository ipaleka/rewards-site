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

    // Set up the DOM structure matching the Django template
    container = document.createElement('div')
    container.id = 'reclaim-allocations-container'
    container.innerHTML = `
      <div class="space-y-4 p-4 rounded-lg bg-base-200 mt-4">
        <h4 class="font-semibold text-lg">Reclaimable Addresses</h4>
        <table class="table w-full">
          <thead>
            <tr>
              <th>Address</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>addr1</td>
              <td class="text-right">
                <button
                  id="reclaim-button-addr1"
                  data-address="addr1"
                  type="button"
                  class="btn btn-warning btn-xs"
                >
                  Reclaim
                </button>
              </td>
            </tr>
            <tr>
              <td>addr2</td>
              <td class="text-right">
                <button
                  id="reclaim-button-addr2"
                  data-address="addr2"
                  type="button"
                  class="btn btn-warning btn-xs"
                >
                  Reclaim
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    `
    document.body.appendChild(container)
  })

  afterEach(() => {
    document.body.innerHTML = ''
    alertSpy.mockRestore()
  })

  it('should fetch reclaimable addresses on initialization', async () => {
    const data = { addresses: ['addr1', 'addr2'] }
      ; (mockRewardsClient.fetchReclaimAllocationsData as jest.Mock).mockResolvedValue(data)

    reclaimAllocationsComponent = new ReclaimAllocationsComponent(mockRewardsClient, mockWalletManager)
    reclaimAllocationsComponent.bind(container)
    await new Promise(process.nextTick)

    expect(mockRewardsClient.fetchReclaimAllocationsData).toHaveBeenCalledWith('test-address')
    expect(reclaimAllocationsComponent.getReclaimableAddresses()).toEqual(['addr1', 'addr2'])
  })

  it('should call reclaimAllocation with the correct address when a reclaim button is clicked', async () => {
    const data = { addresses: ['addr1', 'addr2'] }
      ; (mockRewardsClient.fetchReclaimAllocationsData as jest.Mock).mockResolvedValue(data)
    reclaimAllocationsComponent = new ReclaimAllocationsComponent(mockRewardsClient, mockWalletManager)
    reclaimAllocationsComponent.bind(container)
    await new Promise(process.nextTick)

    const button = container.querySelector('#reclaim-button-addr1') as HTMLButtonElement
    await button.click()

    expect(mockRewardsClient.reclaimAllocation).toHaveBeenCalledWith('addr1')
  })

  it('should re-fetch data after a successful reclaim call', async () => {
    const data = { addresses: ['addr1', 'addr2'] }
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

  it('should get reclaimable addresses via getReclaimableAddresses method', async () => {
    const data = { addresses: ['addr1', 'addr2'] }
      ; (mockRewardsClient.fetchReclaimAllocationsData as jest.Mock).mockResolvedValue(data)

    reclaimAllocationsComponent = new ReclaimAllocationsComponent(mockRewardsClient, mockWalletManager)
    reclaimAllocationsComponent.bind(container)
    await new Promise(process.nextTick)

    expect(reclaimAllocationsComponent.getReclaimableAddresses()).toEqual(['addr1', 'addr2'])
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
    container.innerHTML = `
      <table class="table w-full">
        <tbody>
          <tr>
            <td>addr1</td>
            <td class="text-right">
              <button id="reclaim-button-addr1" data-address="addr1" class="btn btn-warning btn-xs">Reclaim</button>
            </td>
          </tr>
          <tr>
            <td>addr2</td>
            <td class="text-right">
              <button id="reclaim-button-addr2" data-address="addr2" class="btn btn-warning btn-xs">Reclaim</button>
            </td>
          </tr>
        </tbody>
      </table>
    `
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
    it('should handle addEventListeners when element is null', () => {
      reclaimAllocationsComponent = new ReclaimAllocationsComponent(mockRewardsClient, mockWalletManager)
      // Don't call bind(), so this.element remains null
      expect(() => {
        reclaimAllocationsComponent.addEventListeners()
      }).not.toThrow()
    })

    it('should handle click events on non-reclaim-button elements gracefully', async () => {
      const data = { addresses: ['addr1'] }
        ; (mockRewardsClient.fetchReclaimAllocationsData as jest.Mock).mockResolvedValue(data)
      reclaimAllocationsComponent = new ReclaimAllocationsComponent(mockRewardsClient, mockWalletManager)
      reclaimAllocationsComponent.bind(container)
      await new Promise(process.nextTick)

      // Simulate click event on non-button element
      const tableRow = container.querySelector('tr') as HTMLTableRowElement
      expect(() => {
        tableRow.click()
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
  })
})
