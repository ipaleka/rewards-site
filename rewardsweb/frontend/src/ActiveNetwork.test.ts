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
