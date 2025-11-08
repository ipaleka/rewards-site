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
    alertSpy = jest.spyOn(window, 'alert').mockImplementation(() => {})
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
    ;(mockRewardsClient.fetchClaimableStatus as jest.Mock).mockResolvedValue({
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
    ;(mockRewardsClient.fetchClaimableStatus as jest.Mock).mockResolvedValue({
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
    ;(mockRewardsClient.fetchClaimableStatus as jest.Mock).mockResolvedValue({
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
    ;(mockRewardsClient.fetchClaimableStatus as jest.Mock).mockResolvedValueOnce({ claimable: true })
    claimComponent = new ClaimComponent(mockRewardsClient, mockWalletManager)
    claimComponent.bind(container)
    await new Promise(process.nextTick)

    // Mock a successful claim, then set next status to not claimable
    ;(mockRewardsClient.claim as jest.Mock).mockResolvedValue(undefined)
    ;(mockRewardsClient.fetchClaimableStatus as jest.Mock).mockResolvedValueOnce({ claimable: false })

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
})
