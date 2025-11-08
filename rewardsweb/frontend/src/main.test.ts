import { WalletManager, WalletId } from '@txnlab/use-wallet'
import { ActiveNetwork } from './ActiveNetwork'
import { WalletComponent } from './WalletComponent'
import { ClaimComponent } from './ClaimComponent'
import { AddAllocationsComponent } from './AddAllocationsComponent'
import { ReclaimAllocationsComponent } from './ReclaimAllocationsComponent'
import { RewardsClient } from './RewardsClient'

// Mock everything at the top
jest.mock('@txnlab/use-wallet', () => {
  const mockSubscribe = jest.fn()
  const mockResumeSessions = jest.fn()

  const mockWalletManagerInstance = {
    wallets: [
      {
        id: 'pera',
        metadata: { name: 'Pera Wallet' },
        activeAccount: { address: 'test-address' },
      },
      {
        id: 'defly',
        metadata: { name: 'Defly Wallet' },
        activeAccount: null,
      },
      {
        id: 'lute',
        metadata: { name: 'Lute Wallet' },
        activeAccount: null,
      },
    ],
    resumeSessions: mockResumeSessions,
    subscribe: mockSubscribe,
    activeNetwork: 'testnet',
    activeWallet: null,
    setActiveNetwork: jest.fn(),
    getAlgodClient: jest.fn().mockReturnValue({
      getTransactionParams: jest.fn().mockReturnValue({
        do: jest.fn().mockResolvedValue({
          fee: 1000,
          firstRound: 1000,
          lastRound: 2000,
          genesisID: 'testnet-v1.0',
          genesisHash: 'SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI=',
        }),
      }),
    }),
  }

  return {
    NetworkId: {
      TESTNET: 'testnet',
      MAINNET: 'mainnet',
    },
    WalletId: {
      PERA: 'pera',
      DEFLY: 'defly',
      LUTE: 'lute',
    },
    WalletManager: jest.fn(() => mockWalletManagerInstance),
  }
})

const mockActiveNetworkInstance = {
  bind: jest.fn(),
  destroy: jest.fn(),
}

const mockWalletComponentInstance = {
  bind: jest.fn(),
  destroy: jest.fn(),
}

const mockClaimComponentInstance = {
  bind: jest.fn(),
  destroy: jest.fn(),
}

const mockAddAllocationsComponentInstance = {
  bind: jest.fn(),
  destroy: jest.fn(),
}

const mockReclaimAllocationsComponentInstance = {
  bind: jest.fn(),
  destroy: jest.fn(),
}

// Mock the ActiveNetwork component
jest.mock('./ActiveNetwork', () => ({
  ActiveNetwork: jest.fn(() => mockActiveNetworkInstance),
  getAlgodClient: jest.fn().mockReturnValue({
    getTransactionParams: jest.fn().mockReturnValue({
      do: jest.fn().mockResolvedValue({
        fee: 1000,
        firstRound: 1000,
        lastRound: 2000,
        genesisID: 'testnet-v1.0',
        genesisHash: 'SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI=',
      }),
    }),
  }),
}))

jest.mock('./WalletComponent', () => ({
  WalletComponent: jest.fn(() => mockWalletComponentInstance),
}))

jest.mock('./ClaimComponent', () => ({
  ClaimComponent: jest.fn(() => mockClaimComponentInstance),
}))

jest.mock('./AddAllocationsComponent', () => ({
  AddAllocationsComponent: jest.fn(() => mockAddAllocationsComponentInstance),
}))

jest.mock('./ReclaimAllocationsComponent', () => ({
  ReclaimAllocationsComponent: jest.fn(() => mockReclaimAllocationsComponentInstance),
}))

// Mock RewardsClient
jest.mock('./RewardsClient', () => ({
  RewardsClient: jest.fn().mockImplementation(() => ({
    fetchClaimableStatus: jest.fn(),
    claim: jest.fn(),
    addAllocations: jest.fn(),
    reclaimAllocation: jest.fn(),
    fetchAddAllocationsData: jest.fn(),
    fetchReclaimAllocationsData: jest.fn(),
  })),
}))

describe('main.ts', () => {
  let mockAppDiv: HTMLDivElement
  let mockActiveNetworkEl: HTMLDivElement
  let mockClaimContainer: HTMLDivElement
  let mockAddAllocationsContainer: HTMLDivElement
  let mockReclaimAllocationsContainer: HTMLDivElement
  let mockWalletEls: { [key: string]: HTMLDivElement }
  let mockAppErrorDiv: HTMLDivElement

  let originalQuerySelector: typeof document.querySelector
  let consoleErrorSpy: jest.SpyInstance

  beforeEach(() => {
    jest.clearAllMocks()
    jest.resetModules() // Reset modules to ensure fresh mocks for each test

    // Set up DOM
    mockAppDiv = document.createElement('div')
    mockAppDiv.id = 'app'
    document.body.appendChild(mockAppDiv)

    mockActiveNetworkEl = document.createElement('div')
    mockActiveNetworkEl.id = 'active-network'
    document.body.appendChild(mockActiveNetworkEl)

    mockClaimContainer = document.createElement('div')
    mockClaimContainer.id = 'claim-container'
    document.body.appendChild(mockClaimContainer)

    mockAddAllocationsContainer = document.createElement('div')
    mockAddAllocationsContainer.id = 'add-allocations-container'
    document.body.appendChild(mockAddAllocationsContainer)

    mockReclaimAllocationsContainer = document.createElement('div')
    mockReclaimAllocationsContainer.id = 'reclaim-allocations-container'
    document.body.appendChild(mockReclaimAllocationsContainer)

    mockWalletEls = {
      pera: document.createElement('div'),
      defly: document.createElement('div'),
      lute: document.createElement('div'),
    }
    mockWalletEls.pera.id = 'wallet-pera'
    mockWalletEls.defly.id = 'wallet-defly'
    mockWalletEls.lute.id = 'wallet-lute'
    document.body.appendChild(mockWalletEls.pera)
    document.body.appendChild(mockWalletEls.defly)
    document.body.appendChild(mockWalletEls.lute)

    mockAppErrorDiv = document.createElement('div')
    mockAppErrorDiv.id = 'app-error'
    mockAppErrorDiv.style.display = 'none'
    document.body.appendChild(mockAppErrorDiv)

    // Mock document.querySelector
    originalQuerySelector = document.querySelector
    document.querySelector = jest.fn((selector: string) => {
      if (selector === '#app') return mockAppDiv
      return originalQuerySelector.call(document, selector)
    })

    // Mock document.getElementById
    jest.spyOn(document, 'getElementById').mockImplementation((id: string) => {
      if (id === 'active-network') return mockActiveNetworkEl
      if (id === 'claim-container') return mockClaimContainer
      if (id === 'add-allocations-container') return mockAddAllocationsContainer
      if (id === 'reclaim-allocations-container') return mockReclaimAllocationsContainer
      if (id === 'wallet-pera') return mockWalletEls.pera
      if (id === 'wallet-defly') return mockWalletEls.defly
      if (id === 'wallet-lute') return mockWalletEls.lute
      if (id === 'app-error') return mockAppErrorDiv
      return null
    })

    consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {})

    // Mock fetch for initial data
    global.fetch = jest.fn((url) => {
      if (url === '/api/wallet/wallets/') {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve([
              { id: 'pera' },
              { id: 'defly' },
              { id: 'lute' },
            ]),
        })
      }
      if (url === '/api/wallet/active-network/') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ network: 'testnet' }),
        })
      }
      return Promise.reject(new Error(`Unhandled fetch for ${url}`))
    }) as jest.Mock
  })

  afterEach(() => {
    document.querySelector = originalQuerySelector
    document.body.innerHTML = ''
    consoleErrorSpy.mockRestore()
    jest.restoreAllMocks()
  })

  it('should initialize the application without errors', async () => {
    const { WalletManager } = require('@txnlab/use-wallet')
    const { ActiveNetwork } = require('./ActiveNetwork')
    const { WalletComponent } = require('./WalletComponent')
    const { ClaimComponent } = require('./ClaimComponent')
    const { AddAllocationsComponent } = require('./AddAllocationsComponent')
    const { ReclaimAllocationsComponent } = require('./ReclaimAllocationsComponent')
    const { RewardsClient } = require('./RewardsClient')

    require('./main')

    // Simulate DOMContentLoaded
    const event = new Event('DOMContentLoaded')
    document.dispatchEvent(event)

    await new Promise(process.nextTick) // Allow promises to resolve

    expect(WalletManager).toHaveBeenCalledWith({
      wallets: ['pera', 'defly', 'lute'],
      defaultNetwork: 'testnet',
    })
    expect(ActiveNetwork).toHaveBeenCalledTimes(1)
    expect(ActiveNetwork().bind).toHaveBeenCalledWith(mockActiveNetworkEl)
    expect(WalletComponent).toHaveBeenCalledTimes(3)
    expect(WalletComponent().bind).toHaveBeenCalledWith(mockWalletEls.pera)
    expect(WalletComponent().bind).toHaveBeenCalledWith(mockWalletEls.defly)
    expect(WalletComponent().bind).toHaveBeenCalledWith(mockWalletEls.lute)
    expect(RewardsClient).toHaveBeenCalledTimes(1)
    expect(ClaimComponent).toHaveBeenCalledTimes(1)
    expect(ClaimComponent().bind).toHaveBeenCalledWith(mockClaimContainer)
    expect(AddAllocationsComponent).toHaveBeenCalledTimes(1)
    expect(AddAllocationsComponent().bind).toHaveBeenCalledWith(mockAddAllocationsContainer)
    expect(ReclaimAllocationsComponent).toHaveBeenCalledTimes(1)
    expect(ReclaimAllocationsComponent().bind).toHaveBeenCalledWith(mockReclaimAllocationsContainer)
    expect(consoleErrorSpy).not.toHaveBeenCalled()
  })

  it('should handle initialization errors gracefully', async () => {
    // Force fetch to fail
    (global.fetch as jest.Mock).mockImplementationOnce(() =>
      Promise.resolve({ ok: false, status: 500 }),
    )

    require('./main')

    const event = new Event('DOMContentLoaded')
    document.dispatchEvent(event)

    await new Promise(process.nextTick)

    expect(consoleErrorSpy).toHaveBeenCalledWith(
      'Error initializing app:',
      expect.any(Error),
    )
    expect(mockAppErrorDiv.style.display).toBe('block')
  })

  it('should handle beforeunload event cleanup', async () => {
    const { WalletManager } = require('@txnlab/use-wallet')
    const { ActiveNetwork } = require('./ActiveNetwork')
    const { WalletComponent } = require('./WalletComponent')
    const { ClaimComponent } = require('./ClaimComponent')
    const { AddAllocationsComponent } = require('./AddAllocationsComponent')
    const { ReclaimAllocationsComponent } = require('./ReclaimAllocationsComponent')

    require('./main')

    const event = new Event('DOMContentLoaded')
    document.dispatchEvent(event)
    await new Promise(process.nextTick)

    // Trigger beforeunload event
    const beforeUnloadEvent = new Event('beforeunload')
    window.dispatchEvent(beforeUnloadEvent)

    expect(WalletManager().resumeSessions).toHaveBeenCalledTimes(1)
    expect(ActiveNetwork().destroy).toHaveBeenCalledTimes(1)
    expect(WalletComponent().destroy).toHaveBeenCalledTimes(3) // Called for each mocked wallet
    expect(ClaimComponent().destroy).toHaveBeenCalledTimes(1)
    expect(AddAllocationsComponent().destroy).toHaveBeenCalledTimes(1)
    expect(ReclaimAllocationsComponent().destroy).toHaveBeenCalledTimes(1)
  })
})
