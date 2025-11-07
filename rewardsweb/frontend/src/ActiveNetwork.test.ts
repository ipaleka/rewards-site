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
      setActiveNetwork: jest.fn()
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

    it('should dispatch "networkChanged" event on button click', () => {
      const dispatchEventSpy = jest.spyOn(element, 'dispatchEvent')
      activeNetwork.bind(element)
      const mainnetButton = element.querySelector<HTMLButtonElement>('[data-network="mainnet"]')!
      mainnetButton.click()

      expect(dispatchEventSpy).toHaveBeenCalledWith(expect.any(CustomEvent))
      const customEvent = dispatchEventSpy.mock.calls[0][0] as CustomEvent
      expect(customEvent.type).toBe('networkChanged')
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
  })
})
