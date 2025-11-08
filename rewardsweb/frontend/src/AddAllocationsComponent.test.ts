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
