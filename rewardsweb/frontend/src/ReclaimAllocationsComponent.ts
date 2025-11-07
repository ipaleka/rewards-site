import { RewardsClient } from './RewardsClient'
import { WalletManager } from '@txnlab/use-wallet'

export class ReclaimAllocationsComponent {
  element: HTMLElement
  private rewardsClient: RewardsClient
  private walletManager: WalletManager
  private reclaimableAddresses: string[] = []

  constructor(rewardsClient: RewardsClient, walletManager: WalletManager) {
    this.rewardsClient = rewardsClient
    this.walletManager = walletManager
    this.element = document.createElement('div')
    this.render()
    this.addEventListeners()
    this.walletManager.subscribe(() => this.fetchReclaimAllocationsData())
    this.fetchReclaimAllocationsData()
  }

  private async fetchReclaimAllocationsData() {
    const activeAddress = this.walletManager.activeAccount?.address
    if (!activeAddress) {
      this.reclaimableAddresses = []
      this.render()
      return
    }

    try {
      const data = await this.rewardsClient.fetchReclaimAllocationsData(activeAddress)
      this.reclaimableAddresses = data.addresses
      this.render()
    } catch (error) {
      console.error('[ReclaimAllocationsComponent] Error fetching reclaim allocations data:', error)
      alert(`Failed to fetch reclaim allocations data: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  private async handleReclaimAllocation(address: string) {
    try {
      console.info(`[ReclaimAllocationsComponent] Initiating reclaim for ${address}...`)
      await this.rewardsClient.reclaimAllocation(address)
      alert(`Reclaim transaction for ${address} sent successfully!`)
      // Re-fetch data after successful transaction
      await this.fetchReclaimAllocationsData()
    } catch (error) {
      console.error(`[ReclaimAllocationsComponent] Error during reclaim for ${address}:`, error)
      alert(`Reclaim for ${address} failed: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  render() {
    this.element.innerHTML = `
      <div class="space-y-4 p-4 rounded-lg bg-base-200 mt-4">
        <h4 class="font-semibold text-lg">Reclaim Allocations (Superuser Only)</h4>
        ${this.reclaimableAddresses.length === 0
          ? '<p>No reclaimable allocations found.</p>'
          : `<ul class="list-disc pl-5">
              ${this.reclaimableAddresses.map(address => `
                <li class="flex items-center justify-between py-1">
                  <span>${address}</span>
                  <button
                    id="reclaim-button-${address}"
                    data-address="${address}"
                    type="button"
                    class="btn btn-warning btn-xs"
                  >
                    Reclaim
                  </button>
                </li>
              `).join('')}
            </ul>`
        }
      </div>
    `
  }

  addEventListeners() {
    this.element.addEventListener('click', (e: Event) => {
      const target = e.target as HTMLElement
      if (target.id.startsWith('reclaim-button-')) {
        const addressToReclaim = target.dataset.address
        if (addressToReclaim) {
          this.handleReclaimAllocation(addressToReclaim)
        }
      }
    })
  }

  destroy() {
    // No specific cleanup needed for now
  }
}
