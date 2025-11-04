import { AirdropClient } from './AirdropClient'
import { WalletManager } from '@txnlab/use-wallet'

export class ClaimComponent {
  element: HTMLElement
  private airdropClient: AirdropClient
  private walletManager: WalletManager
  private claimable: boolean = false

  constructor(airdropClient: AirdropClient, walletManager: WalletManager) {
    this.airdropClient = airdropClient
    this.walletManager = walletManager
    this.element = document.createElement('div')
    this.render()
    this.addEventListeners()
    this.walletManager.subscribe(() => this.checkClaimableStatus())
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
      const status = await this.airdropClient.fetchClaimableStatus(activeAddress)
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
      await this.airdropClient.claim()
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
    this.element.innerHTML = `
      <div class="space-y-4 p-4 rounded-lg bg-base-200 mt-4">
        <h4 class="font-semibold text-lg">Claim Your Airdrop</h4>
        <button
          id="claim-button"
          type="button"
          class="btn btn-success btn-sm"
          ${!this.claimable ? 'disabled' : ''}
        >
          ${this.claimable ? 'Claim' : 'No Claim Available'}
        </button>
      </div>
    `
  }

  addEventListeners() {
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
