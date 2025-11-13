import { ClaimComponent } from './ClaimComponent'
import { RewardsClient } from './RewardsClient'
import { WalletManager } from '@txnlab/use-wallet'

// Mock RewardsClient
jest.mock('./RewardsClient', () => {
  return {
    RewardsClient: jest.fn().mockImplementation(() => {
      return {
        fetchClaimableStatus: jest.fn(),
        claimRewards: jest.fn(), // Updated from claim to claimRewards
        userClaimed: jest.fn(),
      }
    }),
  }
})

describe('ClaimComponent', () => {
  let mockRewardsClient: jest.Mocked<RewardsClient>
  let mockWalletManager: jest.Mocked<WalletManager>
  let claimComponent: ClaimComponent
  let alertSpy: jest.SpyInstance
  let container: HTMLElement

  beforeEach(() => {
    alertSpy = jest.spyOn(window, 'alert').mockImplementation(() => { })
    mockRewardsClient = new RewardsClient(null as any) as jest.Mocked<RewardsClient>
    mockWalletManager = {
      activeAccount: { address: 'test-address' },
      subscribe: jest.fn(),
    } as any

    // Set up the DOM structure
    container = document.createElement('div')
    container.id = 'claim-container'
    container.innerHTML = `<button id="claim-button"></button>`
    document.body.appendChild(container)
  })

  afterEach(() => {
    document.body.innerHTML = ''
    alertSpy.mockRestore()
  })

  it('should render with "No Claim Available" button when not claimable', async () => {
    ; (mockRewardsClient.fetchClaimableStatus as jest.Mock).mockResolvedValue({
      claimable: false,
    })

    claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager)
    claimComponent.bind(container)

    // Allow microtasks to run
    await new Promise(process.nextTick)

    const button = container.querySelector('#claim-button') as HTMLButtonElement
    expect(button.textContent?.trim()).toBe('No Claim Available')
    expect(button.disabled).toBe(true)
    expect(mockRewardsClient.fetchClaimableStatus).toHaveBeenCalledWith('test-address')
  })

  it('should render with "Claim" button when claimable', async () => {
    ; (mockRewardsClient.fetchClaimableStatus as jest.Mock).mockResolvedValue({
      claimable: true,
    })

    claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager)
    claimComponent.bind(container)

    await new Promise(process.nextTick)

    const button = container.querySelector('#claim-button') as HTMLButtonElement
    expect(button.textContent?.trim()).toBe('Claim')
    expect(button.disabled).toBe(false)
    expect(mockRewardsClient.fetchClaimableStatus).toHaveBeenCalledWith('test-address')
  })

  it('should call rewardsClient.claimRewards when claim button is clicked', async () => {
    ; (mockRewardsClient.fetchClaimableStatus as jest.Mock).mockResolvedValue({
      claimable: true,
    })
      ; (mockRewardsClient.claimRewards as jest.Mock).mockResolvedValue('test-tx-id') // Mock returning txID

    claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager)
    claimComponent.bind(container)
    await new Promise(process.nextTick)

    const button = container.querySelector('#claim-button') as HTMLButtonElement
    button.click()

    expect(mockRewardsClient.claimRewards).toHaveBeenCalled() // Updated to claimRewards
  })

  it('should not fetch status if no active account', async () => {
    mockWalletManager.activeAccount = null
    claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager)
    claimComponent.bind(container)
    await new Promise(process.nextTick)

    expect(mockRewardsClient.fetchClaimableStatus).not.toHaveBeenCalled()
  })

  it('should handle errors when fetching claimable status', async () => {
    const testError = new Error('network down')

      ; (mockRewardsClient.fetchClaimableStatus as jest.Mock)
        .mockRejectedValueOnce(testError)

    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => { })

    claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager)
    claimComponent.bind(container)

    await new Promise(process.nextTick)

    expect(consoleSpy).toHaveBeenCalledWith(
      '[ClaimComponent] Error fetching claimable status:', // Updated error message
      testError
    )

    consoleSpy.mockRestore()
  })
})

describe('ClaimComponent Error Handling', () => {
  let mockRewardsClient: jest.Mocked<RewardsClient>
  let mockWalletManager: jest.Mocked<WalletManager>
  let claimComponent: ClaimComponent
  let alertSpy: jest.SpyInstance
  let consoleErrorSpy: jest.SpyInstance
  let container: HTMLElement

  beforeEach(() => {
    alertSpy = jest.spyOn(window, 'alert').mockImplementation(() => { })
    consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => { })
    mockRewardsClient = new RewardsClient(null as any) as jest.Mocked<RewardsClient>
    mockWalletManager = {
      activeAccount: { address: 'test-address' },
      subscribe: jest.fn(),
    } as any

    container = document.createElement('div')
    container.id = 'claim-container'
    container.innerHTML = `<button id="claim-button"></button>`
    document.body.appendChild(container)
  })

  afterEach(() => {
    document.body.innerHTML = ''
    alertSpy.mockRestore()
    consoleErrorSpy.mockRestore()
  })

  describe('handleClaim error handling', () => {
    beforeEach(async () => {
      (mockRewardsClient.fetchClaimableStatus as jest.Mock).mockResolvedValue({
        claimable: true,
      })
      claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager)
      claimComponent.bind(container)
      await new Promise(process.nextTick)
    })

    it('should handle Error instance when claim fails', async () => {
      const testError = new Error('Transaction failed')
        ; (mockRewardsClient.claimRewards as jest.Mock).mockRejectedValue(testError) // Updated to claimRewards

      const button = container.querySelector('#claim-button') as HTMLButtonElement
      await button.click()

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[ClaimComponent] Error during claim:',
        testError
      )
      expect(alertSpy).toHaveBeenCalledWith('Claim failed: Transaction failed')
    })

    it('should handle non-Error object when claim fails', async () => {
      const testError = 'Simple string error'
        ; (mockRewardsClient.claimRewards as jest.Mock).mockRejectedValue(testError) // Updated to claimRewards

      const button = container.querySelector('#claim-button') as HTMLButtonElement
      await button.click()

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[ClaimComponent] Error during claim:',
        testError
      )
      expect(alertSpy).toHaveBeenCalledWith('Claim failed: Simple string error')
    })

    it('should handle complex error objects when claim fails', async () => {
      const testError = { code: 400, message: 'Bad request', details: 'Invalid parameters' }
        ; (mockRewardsClient.claimRewards as jest.Mock).mockRejectedValue(testError) // Updated to claimRewards

      const button = container.querySelector('#claim-button') as HTMLButtonElement
      await button.click()

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[ClaimComponent] Error during claim:',
        testError
      )
      expect(alertSpy).toHaveBeenCalledWith('Claim failed: [object Object]')
    })

    it('should handle status re-check error after failed claim', async () => {
      const claimError = new Error('Transaction failed')
        ; (mockRewardsClient.claimRewards as jest.Mock).mockRejectedValue(claimError) // Updated to claimRewards

      const button = container.querySelector('#claim-button') as HTMLButtonElement
      await button.click()

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[ClaimComponent] Error during claim:',
        claimError
      )
    })
  })

  describe('fetchClaimableStatus error handling', () => {
    it('should handle errors and set claimable to false when fetching status', async () => {
      const testError = new Error('Network down')
        ; (mockRewardsClient.fetchClaimableStatus as jest.Mock).mockRejectedValue(testError)

      claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager)
      claimComponent.bind(container)
      await new Promise(process.nextTick)

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[ClaimComponent] Error fetching claimable status:', // Updated error message
        testError
      )

      const button = container.querySelector('#claim-button') as HTMLButtonElement
      expect(button.disabled).toBe(true)
      expect(button.textContent?.trim()).toBe('No Claim Available')
    })

    it('should handle various error types when fetching status', async () => {
      const errorScenarios = [
        new Error('Network error'),
        'String error',
        { status: 500, message: 'Server error' },
        null,
        undefined
      ]

      for (const error of errorScenarios) {
        (mockRewardsClient.fetchClaimableStatus as jest.Mock).mockRejectedValueOnce(error)
        claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager)
        claimComponent.bind(container)
        await new Promise(process.nextTick)

        expect(consoleErrorSpy).toHaveBeenCalledWith(
          '[ClaimComponent] Error fetching claimable status:', // Updated error message
          error
        )

        const button = container.querySelector('#claim-button') as HTMLButtonElement
        expect(button.disabled).toBe(true)
        expect(button.textContent?.trim()).toBe('No Claim Available')

        // Clean up for next iteration
        claimComponent.destroy()
        consoleErrorSpy.mockClear()
        document.body.innerHTML = '<div id="claim-container"><button id="claim-button"></button></div>'
        container = document.querySelector('#claim-container') as HTMLElement
      }
    })
  })

  describe('edge cases', () => {
    it('should handle no active account by setting claimable to false', async () => {
      mockWalletManager.activeAccount = null
        ; (mockRewardsClient.fetchClaimableStatus as jest.Mock).mockResolvedValue({ claimable: true })

      claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager)
      claimComponent.bind(container)
      await new Promise(process.nextTick)

      const button = container.querySelector('#claim-button') as HTMLButtonElement
      expect(button.disabled).toBe(true)
      expect(button.textContent?.trim()).toBe('No Claim Available')
      expect(mockRewardsClient.fetchClaimableStatus).not.toHaveBeenCalled()
    })

    it('should handle render when element is null', () => {
      claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager)
      // Don't call bind(), so this.element remains null
      expect(() => {
        claimComponent.render()
      }).not.toThrow()
    })

    it('should handle addEventListeners when element is null', () => {
      claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager)
      // Don't call bind(), so this.element remains null
      expect(() => {
        claimComponent.addEventListeners()
      }).not.toThrow()
    })

    it('should handle missing claim button in render', () => {
      const containerWithoutButton = document.createElement('div')
      containerWithoutButton.innerHTML = `<div>No button here</div>`
      document.body.appendChild(containerWithoutButton)

      claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager)
      claimComponent.bind(containerWithoutButton)

      expect(() => {
        claimComponent.render()
      }).not.toThrow()

      document.body.removeChild(containerWithoutButton)
    })

    it('should handle click events on non-button elements gracefully', () => {
      ; (mockRewardsClient.fetchClaimableStatus as jest.Mock).mockResolvedValue({
        claimable: true,
      })
      claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager)
      claimComponent.bind(container)

      // Simulate click event without the expected button structure
      const mockEvent = new Event('click', { bubbles: true })
      expect(() => {
        container.dispatchEvent(mockEvent)
      }).not.toThrow()

      expect(mockRewardsClient.claimRewards).not.toHaveBeenCalled() // Updated to claimRewards
    })
  })
})

describe('ClaimComponent userClaimed functionality', () => {
  let mockRewardsClient: jest.Mocked<RewardsClient>
  let mockWalletManager: jest.Mocked<WalletManager>
  let claimComponent: ClaimComponent
  let alertSpy: jest.SpyInstance
  let container: HTMLElement

  beforeEach(() => {
    alertSpy = jest.spyOn(window, 'alert').mockImplementation(() => { })
    mockRewardsClient = new RewardsClient(null as any) as jest.Mocked<RewardsClient>
    mockWalletManager = {
      activeAccount: { address: 'test-address' },
      subscribe: jest.fn(),
    } as any

    container = document.createElement('div')
    container.id = 'claim-container'
    container.innerHTML = `<button id="claim-button"></button>`
    document.body.appendChild(container)
  })

  afterEach(() => {
    document.body.innerHTML = ''
    alertSpy.mockRestore()
  })

  describe('successful userClaimed calls', () => {
    it('should call userClaimed after successful claim transaction', async () => {
      (mockRewardsClient.fetchClaimableStatus as jest.Mock).mockResolvedValue({
        claimable: true,
      })
        ; (mockRewardsClient.claimRewards as jest.Mock).mockResolvedValue('test-tx-id')
        ; (mockRewardsClient.userClaimed as jest.Mock).mockResolvedValue({ success: true })

      claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager)
      claimComponent.bind(container)
      await new Promise(process.nextTick)

      const button = container.querySelector('#claim-button') as HTMLButtonElement
      await button.click()

      expect(mockRewardsClient.userClaimed).toHaveBeenCalledWith('test-address', 'test-tx-id')
      expect(mockRewardsClient.userClaimed).toHaveBeenCalledTimes(1)
    })

    it('should call userClaimed with correct active address and txID', async () => {
      const testAddress = 'special-test-address-123'
      const testTxID = 'test-transaction-id-456'
      mockWalletManager.activeAccount = { address: testAddress }

        ; (mockRewardsClient.fetchClaimableStatus as jest.Mock).mockResolvedValue({
          claimable: true,
        })
        ; (mockRewardsClient.claimRewards as jest.Mock).mockResolvedValue(testTxID)
        ; (mockRewardsClient.userClaimed as jest.Mock).mockResolvedValue({ success: true })

      claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager)
      claimComponent.bind(container)
      await new Promise(process.nextTick)

      const button = container.querySelector('#claim-button') as HTMLButtonElement
      await button.click()

      expect(mockRewardsClient.userClaimed).toHaveBeenCalledWith(testAddress, testTxID)
    })
  })
  describe('userClaimed error handling', () => {
    it('should handle userClaimed API failure gracefully', async () => {
      // Set up console spy BEFORE component initialization
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => { })

        ; (mockRewardsClient.fetchClaimableStatus as jest.Mock).mockResolvedValue({
          claimable: true,
        })
        ; (mockRewardsClient.claimRewards as jest.Mock).mockResolvedValue('test-tx-id')
        ; (mockRewardsClient.userClaimed as jest.Mock).mockRejectedValue(new Error('API unavailable'))

      claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager)
      claimComponent.bind(container)
      await new Promise(process.nextTick)

      const button = container.querySelector('#claim-button') as HTMLButtonElement

      // Use await to ensure the async handleClaim completes
      await button.click()

      // Wait for any microtasks to complete
      await new Promise(process.nextTick)

      // userClaimed should still be called even if it fails
      expect(mockRewardsClient.userClaimed).toHaveBeenCalledWith('test-address', 'test-tx-id')
      // Should log the backend notification error
      expect(consoleErrorSpy).toHaveBeenCalledWith('Backend notification failed:', expect.any(Error))

      consoleErrorSpy.mockRestore()
    })
  })

  describe('edge cases for userClaimed', () => {
    it('should not call userClaimed if claim transaction fails', async () => {
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => { })

        ; (mockRewardsClient.fetchClaimableStatus as jest.Mock).mockResolvedValue({
          claimable: true,
        })
        ; (mockRewardsClient.claimRewards as jest.Mock).mockRejectedValue(new Error('Transaction failed'))
        ; (mockRewardsClient.userClaimed as jest.Mock).mockResolvedValue({ success: true })

      claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager)
      claimComponent.bind(container)
      await new Promise(process.nextTick)

      const button = container.querySelector('#claim-button') as HTMLButtonElement
      await button.click()

      expect(mockRewardsClient.userClaimed).not.toHaveBeenCalled()
      expect(alertSpy).toHaveBeenCalledWith('Claim failed: Transaction failed')

      consoleErrorSpy.mockRestore()
    })

    it('should not call userClaimed if no active account after claim', async () => {
      ; (mockRewardsClient.fetchClaimableStatus as jest.Mock).mockResolvedValue({
        claimable: true,
      })
        ; (mockRewardsClient.claimRewards as jest.Mock).mockResolvedValue('test-tx-id')

      claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager)
      claimComponent.bind(container)
      await new Promise(process.nextTick)

      // Simulate wallet disconnecting after claim but before userClaimed call
      mockWalletManager.activeAccount = null

      const button = container.querySelector('#claim-button') as HTMLButtonElement
      await button.click()

      expect(mockRewardsClient.userClaimed).not.toHaveBeenCalled()
    })
    it('should handle various userClaimed error types', async () => {
      const errorScenarios = [
        new Error('Network error'),
        'String error message',
        { status: 500, message: 'Server error' },
      ]

      for (const error of errorScenarios) {
        // Set up console spy for each iteration
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => { })

          ; (mockRewardsClient.fetchClaimableStatus as jest.Mock).mockResolvedValue({
            claimable: true,
          })
          ; (mockRewardsClient.claimRewards as jest.Mock).mockResolvedValue('test-tx-id')
          ; (mockRewardsClient.userClaimed as jest.Mock).mockRejectedValueOnce(error)

        claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager)
        claimComponent.bind(container)
        await new Promise(process.nextTick)

        const button = container.querySelector('#claim-button') as HTMLButtonElement

        // Use await to ensure the async handleClaim completes
        await button.click()

        // Wait for any microtasks to complete
        await new Promise(process.nextTick)

        // userClaimed should still be called even if it will fail
        expect(mockRewardsClient.userClaimed).toHaveBeenCalledWith('test-address', 'test-tx-id')
        // Should log the backend notification error
        expect(consoleErrorSpy).toHaveBeenCalledWith('Backend notification failed:', expect.anything())

        // Clean up for next iteration
        claimComponent.destroy()
        consoleErrorSpy.mockRestore()
        document.body.innerHTML = '<div id="claim-container"><button id="claim-button"></button></div>'
        container = document.querySelector('#claim-container') as HTMLElement
      }
    })
  })

describe('ClaimComponent DOM ready state handling', () => {
  let mockRewardsClient: jest.Mocked<RewardsClient>
  let mockWalletManager: jest.Mocked<WalletManager>
  let claimComponent: ClaimComponent
  let container: HTMLElement

  beforeEach(() => {
    mockRewardsClient = new RewardsClient(null as any) as jest.Mocked<RewardsClient>
    mockWalletManager = {
      activeAccount: { address: 'test-address' },
      subscribe: jest.fn(),
    } as any

    container = document.createElement('div')
    container.id = 'claim-container'
    container.innerHTML = `<button id="claim-button"></button>`
    document.body.appendChild(container)
  })

  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('should defer fetchClaimableStatus until DOMContentLoaded when document is loading', async () => {
    // Mock document.readyState to be 'loading'
    Object.defineProperty(document, 'readyState', {
      value: 'loading',
      writable: true
    })

    const fetchClaimableStatusSpy = jest.spyOn(
      ClaimComponent.prototype as any,
      'fetchClaimableStatus'
    )

    claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager)
    claimComponent.bind(container)

    // Verify that fetchClaimableStatus was not called immediately
    expect(fetchClaimableStatusSpy).not.toHaveBeenCalled()

    // Simulate DOMContentLoaded event
    document.dispatchEvent(new Event('DOMContentLoaded'))

    // Verify that fetchClaimableStatus was called after DOMContentLoaded
    expect(fetchClaimableStatusSpy).toHaveBeenCalled()

    fetchClaimableStatusSpy.mockRestore()
    
    // Reset readyState
    Object.defineProperty(document, 'readyState', {
      value: 'complete',
      writable: true
    })
  })

  it('should call fetchClaimableStatus immediately when document is already loaded', async () => {
    // Mock document.readyState to be 'complete'
    Object.defineProperty(document, 'readyState', {
      value: 'complete',
      writable: true
    })

    const fetchClaimableStatusSpy = jest.spyOn(
      ClaimComponent.prototype as any,
      'fetchClaimableStatus'
    )

    claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager)
    claimComponent.bind(container)

    // Verify that fetchClaimableStatus was called immediately
    expect(fetchClaimableStatusSpy).toHaveBeenCalled()

    fetchClaimableStatusSpy.mockRestore()
  })

  it('should call fetchClaimableStatus immediately when document is interactive', async () => {
    // Mock document.readyState to be 'interactive'
    Object.defineProperty(document, 'readyState', {
      value: 'interactive',
      writable: true
    })

    const fetchClaimableStatusSpy = jest.spyOn(
      ClaimComponent.prototype as any,
      'fetchClaimableStatus'
    )

    claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager)
    claimComponent.bind(container)

    // Verify that fetchClaimableStatus was called immediately
    expect(fetchClaimableStatusSpy).toHaveBeenCalled()

    fetchClaimableStatusSpy.mockRestore()
    
    // Reset readyState
    Object.defineProperty(document, 'readyState', {
      value: 'complete',
      writable: true
    })
  })
})

})
