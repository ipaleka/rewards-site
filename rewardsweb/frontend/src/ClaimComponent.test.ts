import { ClaimComponent } from './ClaimComponent'
import { RewardsClient } from './RewardsClient'
import { WalletManager } from '@txnlab/use-wallet'

// Mock RewardsClient
jest.mock('./RewardsClient', () => {
  return {
    RewardsClient: jest.fn().mockImplementation(() => {
      return {
        fetchClaimableStatus: jest.fn(),
        claim: jest.fn(),
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
    mockRewardsClient = new RewardsClient(null as any, null as any) as jest.Mocked<RewardsClient>
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

  it('should call rewardsClient.claim when claim button is clicked', async () => {
    ; (mockRewardsClient.fetchClaimableStatus as jest.Mock).mockResolvedValue({
      claimable: true,
    })
    claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager)
    claimComponent.bind(container)
    await new Promise(process.nextTick)

    const button = container.querySelector('#claim-button') as HTMLButtonElement
    button.click()

    expect(mockRewardsClient.claim).toHaveBeenCalled()
  })

  it('should re-check claimable status after a successful claim', async () => {
    ; (mockRewardsClient.fetchClaimableStatus as jest.Mock).mockResolvedValueOnce({ claimable: true })
    claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager)
    claimComponent.bind(container)
    await new Promise(process.nextTick)

      // Mock a successful claim, then set next status to not claimable
      ; (mockRewardsClient.claim as jest.Mock).mockResolvedValue(undefined)
      ; (mockRewardsClient.fetchClaimableStatus as jest.Mock).mockResolvedValueOnce({ claimable: false })

    const button = container.querySelector('#claim-button') as HTMLButtonElement
    await button.click()

    expect(mockRewardsClient.claim).toHaveBeenCalledTimes(1)
    // fetchClaimableStatus is called once on init and once after claim
    expect(mockRewardsClient.fetchClaimableStatus).toHaveBeenCalledTimes(2)
  })

  it('should not fetch status if no active account', async () => {
    mockWalletManager.activeAccount = null
    claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager)
    claimComponent.bind(container)
    await new Promise(process.nextTick)

    expect(mockRewardsClient.fetchClaimableStatus).not.toHaveBeenCalled()
  })


  it('should handle errors when checking claimable status', async () => {
    const testError = new Error('network down')

      // override only the NEXT call
      ; (mockRewardsClient.fetchClaimableStatus as jest.Mock)
        .mockRejectedValueOnce(testError)

    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => { })

    claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager)
    claimComponent.bind(container)

    await new Promise(process.nextTick)

    expect(consoleSpy).toHaveBeenCalledWith(
      '[ClaimComponent] Error checking claimable status:',
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
    mockRewardsClient = new RewardsClient(null as any, null as any) as jest.Mocked<RewardsClient>
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
        ; (mockRewardsClient.claim as jest.Mock).mockRejectedValue(testError)
        ; (mockRewardsClient.fetchClaimableStatus as jest.Mock).mockResolvedValue({ claimable: false })

      const button = container.querySelector('#claim-button') as HTMLButtonElement
      await button.click()

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[ClaimComponent] Error during claim:',
        testError
      )
      expect(alertSpy).toHaveBeenCalledWith('Claim failed: Transaction failed')
      expect(mockRewardsClient.fetchClaimableStatus).toHaveBeenCalledTimes(2) // Initial + after error
    })

    it('should handle non-Error object when claim fails', async () => {
      const testError = 'Simple string error'
        ; (mockRewardsClient.claim as jest.Mock).mockRejectedValue(testError)
        ; (mockRewardsClient.fetchClaimableStatus as jest.Mock).mockResolvedValue({ claimable: false })

      const button = container.querySelector('#claim-button') as HTMLButtonElement
      await button.click()

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[ClaimComponent] Error during claim:',
        testError
      )
      expect(alertSpy).toHaveBeenCalledWith('Claim failed: Simple string error')
      expect(mockRewardsClient.fetchClaimableStatus).toHaveBeenCalledTimes(2)
    })

    it('should handle complex error objects when claim fails', async () => {
      const testError = { code: 400, message: 'Bad request', details: 'Invalid parameters' }
        ; (mockRewardsClient.claim as jest.Mock).mockRejectedValue(testError)
        ; (mockRewardsClient.fetchClaimableStatus as jest.Mock).mockResolvedValue({ claimable: false })

      const button = container.querySelector('#claim-button') as HTMLButtonElement
      await button.click()

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[ClaimComponent] Error during claim:',
        testError
      )
      expect(alertSpy).toHaveBeenCalledWith('Claim failed: [object Object]')
      expect(mockRewardsClient.fetchClaimableStatus).toHaveBeenCalledTimes(2)
    })

    it('should handle status re-check error after failed claim', async () => {
      const claimError = new Error('Transaction failed')
      const statusError = new Error('Status check failed')
        ; (mockRewardsClient.claim as jest.Mock).mockRejectedValue(claimError)
        ; (mockRewardsClient.fetchClaimableStatus as jest.Mock)
          .mockResolvedValueOnce({ claimable: true }) // Initial call
          .mockRejectedValueOnce(statusError) // Call after failed claim

      const button = container.querySelector('#claim-button') as HTMLButtonElement
      await button.click()

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[ClaimComponent] Error during claim:',
        claimError
      )
      // Should also log the status check error (but in checkClaimableStatus)
      expect(mockRewardsClient.fetchClaimableStatus).toHaveBeenCalledTimes(2)
    })
  })

  describe('checkClaimableStatus error handling', () => {
    it('should handle errors and set claimable to false when checking status', async () => {
      const testError = new Error('Network down')
        ; (mockRewardsClient.fetchClaimableStatus as jest.Mock).mockRejectedValue(testError)

      claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager)
      claimComponent.bind(container)
      await new Promise(process.nextTick)

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[ClaimComponent] Error checking claimable status:',
        testError
      )

      const button = container.querySelector('#claim-button') as HTMLButtonElement
      expect(button.disabled).toBe(true)
      expect(button.textContent?.trim()).toBe('No Claim Available')
    })

    it('should handle various error types when checking status', async () => {
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
          '[ClaimComponent] Error checking claimable status:',
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

      expect(mockRewardsClient.claim).not.toHaveBeenCalled()
    })
  })
})