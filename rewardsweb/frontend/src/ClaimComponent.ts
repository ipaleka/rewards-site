import { RewardsClient } from './RewardsClient'
import { WalletManager } from '@txnlab/use-wallet'

export class ClaimComponent {
  private element: HTMLElement | null = null
  private rewardsClient: RewardsClient
  private walletManager: WalletManager
  private claimable: boolean = false

  constructor(rewardsClient: RewardsClient, walletManager: WalletManager) {
    this.rewardsClient = rewardsClient
    this.walletManager = walletManager
    this.walletManager.subscribe(() => this.checkClaimableStatus())
  }

  bind(element: HTMLElement) {
    this.element = element
    this.addEventListeners()
    this.checkClaimableStatus()
  }

  private async checkClaimableStatus() {
    const activeAddress = this.walletManager.activeAccount?.address
    if (!activeAddress) {
      this.claimable = false
      this.render()
      return
    }

    try {
      const status = await this.rewardsClient.fetchClaimableStatus(activeAddress)
      this.claimable = status.claimable
      this.render()
    } catch (error) {
      console.error('[ClaimComponent] Error checking claimable status:', error)
      this.claimable = false
      this.render()
    }
  }

  private async handleClaim() {
    try {
      console.info('[ClaimComponent] Initiating claim...')
      await this.rewardsClient.claim()
      alert('Claim transaction sent successfully!')
      // Re-check status after successful claim
      await this.checkClaimableStatus()
    } catch (error) {
      console.error('[ClaimComponent] Error during claim:', error)
      alert(`Claim failed: ${error instanceof Error ? error.message : String(error)}`)
      // Also re-check status after failed claim to ensure UI is up to date
      await this.checkClaimableStatus()
    }
  }

  render() {
    if (!this.element) return

    const claimButton = this.element.querySelector<HTMLButtonElement>('#claim-button')
    if (claimButton) {
      claimButton.disabled = !this.claimable
      claimButton.textContent = this.claimable ? 'Claim' : 'No Claim Available'
    }
  }

  addEventListeners() {
    if (!this.element) return

    this.element.addEventListener('click', (e: Event) => {
      const target = e.target as HTMLElement
      if (target.id === 'claim-button') {
        this.handleClaim()
      }
    })
  }

  destroy() {
    // No specific cleanup needed for now
  }
}
