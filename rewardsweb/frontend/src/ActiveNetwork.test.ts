jest.mock('@txnlab/use-wallet', () => ({
  NetworkId: {
    TESTNET: 'testnet',
    MAINNET: 'mainnet'
  },
  WalletManager: jest.fn()
}))

import { ActiveNetwork } from './ActiveNetwork'
import { WalletManager, NetworkId } from '@txnlab/use-wallet'

describe('ActiveNetwork', () => {
  let mockManager: jest.Mocked<WalletManager>
  let activeNetwork: ActiveNetwork
  let element: HTMLElement

  beforeEach(() => {
    // Mock WalletManager
    mockManager = {
      setActiveNetwork: jest.fn(),
      subscribe: jest.fn(), // Add mock for subscribe
    } as any

    // Create ActiveNetwork instance
    activeNetwork = new ActiveNetwork(mockManager)

    // Create mock DOM element
    element = document.createElement('div')
    element.innerHTML = `
      <button data-network="testnet">Testnet</button>
      <button data-network="mainnet">Mainnet</button>
      <span>Some other element</span>
    `
    document.body.appendChild(element)
  })

  afterEach(() => {
    document.body.innerHTML = ''
    jest.clearAllMocks()
  })

  describe('bind', () => {
    it('should add a click event listener to the element', () => {
      const addEventListenerSpy = jest.spyOn(element, 'addEventListener')
      activeNetwork.bind(element)
      expect(addEventListenerSpy).toHaveBeenCalledWith('click', expect.any(Function))
    })

    it('should call setActiveNetwork with the correct network on button click', () => {
      activeNetwork.bind(element)
      const testnetButton = element.querySelector<HTMLButtonElement>('[data-network="testnet"]')!
      testnetButton.click()

      expect(mockManager.setActiveNetwork).toHaveBeenCalledWith(NetworkId.TESTNET)
    })

    it('should not call setActiveNetwork if clicked element has no network data', () => {
      activeNetwork.bind(element)
      const spanElement = element.querySelector('span')!
      spanElement.click()

      expect(mockManager.setActiveNetwork).not.toHaveBeenCalled()
    })

    it('should handle multiple clicks correctly', () => {
      activeNetwork.bind(element)
      const testnetButton = element.querySelector<HTMLButtonElement>('[data-network="testnet"]')!
      const mainnetButton = element.querySelector<HTMLButtonElement>('[data-network="mainnet"]')!

      testnetButton.click()
      expect(mockManager.setActiveNetwork).toHaveBeenCalledWith(NetworkId.TESTNET)
      expect(mockManager.setActiveNetwork).toHaveBeenCalledTimes(1)

      mainnetButton.click()
      expect(mockManager.setActiveNetwork).toHaveBeenCalledWith(NetworkId.MAINNET)
      expect(mockManager.setActiveNetwork).toHaveBeenCalledTimes(2)
    })

    it('should make a fetch call to update the active network on the backend', async () => {
      global.fetch = jest.fn().mockResolvedValue({ ok: true }) as jest.Mock
      jest.spyOn(activeNetwork as any, 'getCsrfToken').mockReturnValue('test-csrf-token')

      activeNetwork.bind(element)
      const testnetButton = element.querySelector<HTMLButtonElement>('[data-network="testnet"]')!
      await testnetButton.click()

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/wallet/active-network/',
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': 'test-csrf-token',
          },
          body: JSON.stringify({ network: NetworkId.TESTNET }),
        }),
      )
    })
  })

  describe('render', () => {
    let networkSpan: HTMLSpanElement
    let testnetButton: HTMLButtonElement
    let mainnetButton: HTMLButtonElement

    beforeEach(() => {
      element.innerHTML = `
        <button data-network="testnet">Testnet</button>
        <button data-network="mainnet">Mainnet</button>
        <span></span>
      `
      document.body.appendChild(element)
      networkSpan = element.querySelector('span')!
      testnetButton = element.querySelector<HTMLButtonElement>('[data-network="testnet"]')!
      mainnetButton = element.querySelector<HTMLButtonElement>('[data-network="mainnet"]')!
      activeNetwork.bind(element)
    })

    it('should update the network span with the active network', () => {
      // Simulate a state change from the WalletManager subscription
      const subscribeCallback = mockManager.subscribe.mock.calls[0][0]
      subscribeCallback({ activeNetwork: NetworkId.MAINNET })

      expect(networkSpan.textContent).toBe('mainnet')
    })

    it('should add "disabled" class to the active network button', () => {
      const subscribeCallback = mockManager.subscribe.mock.calls[0][0]
      subscribeCallback({ activeNetwork: NetworkId.TESTNET })

      expect(testnetButton.classList.contains('disabled')).toBe(true)
      expect(mainnetButton.classList.contains('disabled')).toBe(false)
    })

    it('should remove "disabled" class from inactive network buttons', () => {
      // Initially set testnet as active
      const subscribeCallback = mockManager.subscribe.mock.calls[0][0]
      subscribeCallback({ activeNetwork: NetworkId.TESTNET })

      // Then change to mainnet
      subscribeCallback({ activeNetwork: NetworkId.MAINNET })

      expect(testnetButton.classList.contains('disabled')).toBe(false)
      expect(mainnetButton.classList.contains('disabled')).toBe(true)
    })

    it('should display "none" if activeNetwork is null', () => {
      const subscribeCallback = mockManager.subscribe.mock.calls[0][0]
      subscribeCallback({ activeNetwork: null })

      expect(networkSpan.textContent).toBe('none')
    })
  })
})

describe('ActiveNetwork Error Handling and Cleanup', () => {
  let mockManager: jest.Mocked<WalletManager>
  let activeNetwork: ActiveNetwork
  let element: HTMLElement
  let consoleErrorSpy: jest.SpyInstance
  let fetchMock: jest.Mock

  beforeEach(() => {
    consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => { })

    mockManager = {
      setActiveNetwork: jest.fn(),
      subscribe: jest.fn(),
    } as any

    activeNetwork = new ActiveNetwork(mockManager)

    element = document.createElement('div')
    element.innerHTML = `
      <button data-network="testnet">Testnet</button>
      <button data-network="mainnet">Mainnet</button>
      <span></span>
    `
    document.body.appendChild(element)

    fetchMock = jest.fn()
    global.fetch = fetchMock
  })

  afterEach(() => {
    document.body.innerHTML = ''
    jest.clearAllMocks()
    consoleErrorSpy.mockRestore()
  })

  describe('handleClick error handling', () => {
    it('should catch and log fetch errors when setting active network', async () => {
      const testError = new Error('Network request failed')
      fetchMock.mockRejectedValue(testError)
      jest.spyOn(activeNetwork as any, 'getCsrfToken').mockReturnValue('test-csrf-token')

      activeNetwork.bind(element)
      const testnetButton = element.querySelector<HTMLButtonElement>('[data-network="testnet"]')!

      await testnetButton.click()

      expect(consoleErrorSpy).toHaveBeenCalledWith('Error setting active network:', testError)
      // Should still call setActiveNetwork even if fetch fails
      expect(mockManager.setActiveNetwork).toHaveBeenCalledWith('testnet')
    })

    it('should handle fetch errors without breaking the click handler', async () => {
      fetchMock.mockRejectedValue(new Error('Server error'))
      jest.spyOn(activeNetwork as any, 'getCsrfToken').mockReturnValue('test-csrf-token')

      activeNetwork.bind(element)
      const testnetButton = element.querySelector<HTMLButtonElement>('[data-network="testnet"]')!
      const mainnetButton = element.querySelector<HTMLButtonElement>('[data-network="mainnet"]')!

      // First click should fail but not break subsequent clicks
      await testnetButton.click()
      expect(mockManager.setActiveNetwork).toHaveBeenCalledWith('testnet')

      await mainnetButton.click()
      expect(mockManager.setActiveNetwork).toHaveBeenCalledWith('mainnet')
      expect(mockManager.setActiveNetwork).toHaveBeenCalledTimes(2)
    })

    it('should handle various types of fetch errors gracefully', async () => {
      const errorScenarios = [
        new Error('Network error'),
        'String error',
        { status: 500, message: 'Server error' },
        null,
        undefined
      ]

      for (const error of errorScenarios) {
        fetchMock.mockRejectedValueOnce(error)
        jest.spyOn(activeNetwork as any, 'getCsrfToken').mockReturnValue('test-csrf-token')

        activeNetwork.bind(element)
        const testnetButton = element.querySelector<HTMLButtonElement>('[data-network="testnet"]')!

        await testnetButton.click()

        expect(consoleErrorSpy).toHaveBeenCalledWith('Error setting active network:', error)
        // Reset for next iteration
        activeNetwork.destroy()
        consoleErrorSpy.mockClear()
      }
    })
  })

  describe('destroy method cleanup', () => {
    it('should call unsubscribe when destroy is called and unsubscribe exists', () => {
      const mockUnsubscribe = jest.fn()
      mockManager.subscribe.mockReturnValue(mockUnsubscribe)

      activeNetwork.bind(element)
      activeNetwork.destroy()

      expect(mockUnsubscribe).toHaveBeenCalledTimes(1)
    })

    it('should not throw when destroy is called without unsubscribe', () => {
      // Don't call bind, so unsubscribe remains null
      expect(() => {
        activeNetwork.destroy()
      }).not.toThrow()
    })

    it('should remove click event listener when destroy is called and element exists', () => {
      const removeEventListenerSpy = jest.spyOn(element, 'removeEventListener')

      activeNetwork.bind(element)
      activeNetwork.destroy()

      expect(removeEventListenerSpy).toHaveBeenCalledWith('click', expect.any(Function))
    })

    it('should not throw when destroy is called without element', () => {
      // Don't call bind, so element remains null
      expect(() => {
        activeNetwork.destroy()
      }).not.toThrow()
    })

    it('should handle multiple destroy calls with current implementation', () => {
      const mockUnsubscribe = jest.fn()
      mockManager.subscribe.mockReturnValue(mockUnsubscribe)
      const removeEventListenerSpy = jest.spyOn(element, 'removeEventListener')

      activeNetwork.bind(element)

      // Call destroy multiple times
      activeNetwork.destroy()
      activeNetwork.destroy()
      activeNetwork.destroy()

      // Current behavior: unsubscribe is called each time (or at least the function is invoked)
      // But the actual wallet manager might handle multiple unsubscribe calls gracefully
      expect(mockUnsubscribe).toHaveBeenCalledTimes(1) // This is what's actually happening
      expect(removeEventListenerSpy).toHaveBeenCalledTimes(3)
    })

    it('should clean up both unsubscribe and event listener', () => {
      const mockUnsubscribe = jest.fn()
      mockManager.subscribe.mockReturnValue(mockUnsubscribe)
      const removeEventListenerSpy = jest.spyOn(element, 'removeEventListener')

      activeNetwork.bind(element)
      activeNetwork.destroy()

      expect(mockUnsubscribe).toHaveBeenCalledTimes(1)
      expect(removeEventListenerSpy).toHaveBeenCalledWith('click', expect.any(Function))
    })

    it('should demonstrate the improved behavior after adding null check', () => {
      const mockUnsubscribe = jest.fn()
      mockManager.subscribe.mockReturnValue(mockUnsubscribe)
      const removeEventListenerSpy = jest.spyOn(element, 'removeEventListener')

      activeNetwork.bind(element)

      // First destroy call
      activeNetwork.destroy()
      expect(mockUnsubscribe).toHaveBeenCalledTimes(1)
      expect(removeEventListenerSpy).toHaveBeenCalledTimes(1)

      // Second destroy call - should not call unsubscribe again
      activeNetwork.destroy()
      expect(mockUnsubscribe).toHaveBeenCalledTimes(1) // Still only called once
      expect(removeEventListenerSpy).toHaveBeenCalledTimes(2) // removeEventListener still called

      // Third destroy call
      activeNetwork.destroy()
      expect(mockUnsubscribe).toHaveBeenCalledTimes(1) // Still only called once
      expect(removeEventListenerSpy).toHaveBeenCalledTimes(3) // removeEventListener still called
    })
  })

  describe('edge cases', () => {
    it('should handle render when element exists but child elements are missing', () => {
      const emptyElement = document.createElement('div')
      // No child elements inside
      document.body.appendChild(emptyElement)

      activeNetwork.bind(emptyElement)

      // This should not throw even though querySelectors will return null
      expect(() => {
        (activeNetwork as any).render('testnet')
      }).not.toThrow()

      document.body.removeChild(emptyElement)
    })

    it('should handle getCsrfToken when cookie does not exist', () => {
      // Clear cookies
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: ''
      })

      const csrfToken = (activeNetwork as any).getCsrfToken()
      expect(csrfToken).toBe('')
    })

    it('should handle getCsrfToken with multiple cookies', () => {
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: 'sessionid=abc123; csrftoken=test-token-123; othercookie=value'
      })

      const csrfToken = (activeNetwork as any).getCsrfToken()
      expect(csrfToken).toBe('test-token-123')
    })

    it('should handle getCsrfToken with malformed cookie string', () => {
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: 'invalid=cookie=string; csrftoken=valid-token'
      })

      const csrfToken = (activeNetwork as any).getCsrfToken()
      expect(csrfToken).toBe('valid-token')
    })
  })

  describe('render method edge cases', () => {
    it('should return early from render when element is null', () => {
      // Don't call bind(), so this.element remains null
      expect(() => {
        (activeNetwork as any).render('testnet')
      }).not.toThrow()
    })

    it('should handle render when element exists but child elements are missing', () => {
      const emptyElement = document.createElement('div')
      // No child elements inside
      document.body.appendChild(emptyElement)

      activeNetwork.bind(emptyElement)

      // This should not throw even though querySelectors will return null
      expect(() => {
        (activeNetwork as any).render('testnet')
      }).not.toThrow()

      document.body.removeChild(emptyElement)
    })

    it('should handle render when span element is missing', () => {
      const elementWithoutSpan = document.createElement('div')
      elementWithoutSpan.innerHTML = `
      <button data-network="testnet">Testnet</button>
      <button data-network="mainnet">Mainnet</button>
      <!-- No span element -->
    `
      document.body.appendChild(elementWithoutSpan)

      activeNetwork.bind(elementWithoutSpan)

      expect(() => {
        (activeNetwork as any).render('testnet')
      }).not.toThrow()

      document.body.removeChild(elementWithoutSpan)
    })

    it('should handle render when button elements are missing', () => {
      const elementWithoutButtons = document.createElement('div')
      elementWithoutButtons.innerHTML = `
      <span></span>
      <!-- No button elements -->
    `
      document.body.appendChild(elementWithoutButtons)

      activeNetwork.bind(elementWithoutButtons)

      expect(() => {
        (activeNetwork as any).render('testnet')
      }).not.toThrow()

      document.body.removeChild(elementWithoutButtons)
    })
  })

  describe('bind method edge cases', () => {
    it('should initialize properly even with minimal DOM structure', () => {
      const minimalElement = document.createElement('div')
      // No inner HTML at all
      document.body.appendChild(minimalElement)

      expect(() => {
        activeNetwork.bind(minimalElement)
        // Trigger render through subscription
        const subscribeCallback = mockManager.subscribe.mock.calls[0][0]
        subscribeCallback({ activeNetwork: 'testnet' })
      }).not.toThrow()

      document.body.removeChild(minimalElement)
    })
  })

  // Add this to the existing 'edge cases' describe block or create a new one
  describe('component initialization edge cases', () => {
    it('should handle calling render before bind', () => {
      // Create instance but don't call bind
      const network = new ActiveNetwork(mockManager)

      // Call render directly without binding to an element
      expect(() => {
        (network as any).render('testnet')
      }).not.toThrow()
    })

    it('should handle calling render after destroy', () => {
      activeNetwork.bind(element)
      activeNetwork.destroy()

      // Call render after destroy (when this.element is still set but component is destroyed)
      expect(() => {
        (activeNetwork as any).render('testnet')
      }).not.toThrow()
    })
  })

})