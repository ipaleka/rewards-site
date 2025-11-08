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
    alertSpy = jest.spyOn(window, 'alert').mockImplementation(() => {})
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
    ;(mockRewardsClient.fetchReclaimAllocationsData as jest.Mock).mockResolvedValue(data)

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
    ;(mockRewardsClient.fetchReclaimAllocationsData as jest.Mock).mockResolvedValue(data)

    reclaimAllocationsComponent = new ReclaimAllocationsComponent(mockRewardsClient, mockWalletManager)
    reclaimAllocationsComponent.bind(container)
    await new Promise(process.nextTick)

    const paragraph = container.querySelector('p')
    expect(paragraph?.textContent).toBe('No reclaimable allocations found.')
  })

  it('should call reclaimAllocation with the correct address when a reclaim button is clicked', async () => {
    const data = { addresses: ['addr-to-reclaim'] }
    ;(mockRewardsClient.fetchReclaimAllocationsData as jest.Mock).mockResolvedValue(data)
    reclaimAllocationsComponent = new ReclaimAllocationsComponent(mockRewardsClient, mockWalletManager)
    reclaimAllocationsComponent.bind(container)
    await new Promise(process.nextTick)

    const button = container.querySelector('#reclaim-button-addr-to-reclaim') as HTMLButtonElement
    await button.click()

    expect(mockRewardsClient.reclaimAllocation).toHaveBeenCalledWith('addr-to-reclaim')
  })

  it('should re-fetch data after a successful reclaim call', async () => {
    const data = { addresses: ['addr1'] }
    ;(mockRewardsClient.fetchReclaimAllocationsData as jest.Mock).mockResolvedValueOnce(data)
    reclaimAllocationsComponent = new ReclaimAllocationsComponent(mockRewardsClient, mockWalletManager)
    reclaimAllocationsComponent.bind(container)
    await new Promise(process.nextTick)

    ;(mockRewardsClient.reclaimAllocation as jest.Mock).mockResolvedValue(undefined)
    ;(mockRewardsClient.fetchReclaimAllocationsData as jest.Mock).mockResolvedValueOnce({ addresses: [] })

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
})
