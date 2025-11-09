import { RewardsClient } from './RewardsClient'
import { WalletManager } from '@txnlab/use-wallet'

/**
 * Component for managing and reclaiming allocated rewards.
 * 
 * Handles the display and transaction submission for reclaiming allocations
 * from addresses that are no longer eligible. Provides a list of reclaimable
 * addresses with individual reclaim buttons.
 * 
 * @example
 * ```typescript
 * const reclaimComponent = new ReclaimAllocationsComponent(rewardsClient, walletManager)
 * reclaimComponent.bind(document.getElementById('reclaim-allocations-container'))
 * ```
 */
export class ReclaimAllocationsComponent {
  private element: HTMLElement | null = null
  private rewardsClient: RewardsClient
  private walletManager: WalletManager
  private reclaimableAddresses: string[] = []

  /**
   * Creates an instance of ReclaimAllocationsComponent.
   *
   * @param rewardsClient - The client for interacting with rewards contract and API
   * @param walletManager - The wallet manager for account and network state
   */
  constructor(rewardsClient: RewardsClient, walletManager: WalletManager) {
    this.rewardsClient = rewardsClient
    this.walletManager = walletManager
    this.walletManager.subscribe(() => this.fetchReclaimAllocationsData())
  }

  /**
   * Binds the component to a DOM element and initializes event listeners.
   *
   * @param element - The HTML element to bind the component to
   */
  bind(element: HTMLElement) {
    this.element = element
    this.addEventListeners()
    this.fetchReclaimAllocationsData()
  }

  /**
   * Fetches reclaimable allocation data from the backend API.
   *
   * Retrieves the list of addresses that have allocations that can be reclaimed.
   * Updates the internal state with the results.
   *
   * @private
   */
  private async fetchReclaimAllocationsData() {
    const activeAddress = this.walletManager.activeAccount?.address
    if (!activeAddress) {
      this.reclaimableAddresses = []
      return
    }

    try {
      const data = await this.rewardsClient.fetchReclaimAllocationsData(activeAddress)
      this.reclaimableAddresses = data.addresses
    } catch (error) {
      console.error('[ReclaimAllocationsComponent] Error fetching reclaim allocations data:', error)
      alert(`Failed to fetch reclaim allocations data: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  /**
   * Handles errors during reclaim operations.
   *
   * Logs the error and displays an alert to the user with the specific address
   * that failed and the error message.
   *
   * @param address - The address that failed to reclaim
   * @param error - The error that occurred
   * @private
   */
  private handleReclaimError(address: string, error: unknown) {
    console.error(`[ReclaimAllocationsComponent] Error during reclaim for ${address}:`, error)
    alert(`Reclaim for ${address} failed: ${error instanceof Error ? error.message : String(error)}`)
  }

  /**
   * Handles reclaim transaction submission for a specific address.
   *
   * Submits a reclaim transaction for the specified address and refreshes
   * the data on success. Handles errors appropriately.
   *
   * @param address - The address to reclaim allocations from
   * @private
   */
  private async handleReclaimAllocation(address: string) {
    try {
      console.info(`[ReclaimAllocationsComponent] Initiating reclaim for ${address}...`)
      await this.rewardsClient.reclaimAllocation(address)
      alert(`Reclaim transaction for ${address} sent successfully!`)

      // Re-fetch data after successful transaction
      await this.fetchReclaimAllocationsData()

    } catch (error) {
      this.handleReclaimError(address, error)
    }
  }

  /**
   * Adds event listeners for reclaim button clicks.
   *
   * Listens for click events on dynamically generated reclaim buttons
   * and triggers the reclaim process for the corresponding address.
   *
   * @private
   */
  addEventListeners() {
    if (!this.element) return

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

  /**
   * Gets the current list of reclaimable addresses.
   *
   * @returns Array of reclaimable addresses
   */
  getReclaimableAddresses(): string[] {
    return [...this.reclaimableAddresses]
  }

  /**
   * Cleans up the component.
   *
   * Currently no specific cleanup needed, but provided for interface consistency.
   */
  destroy() {
    // No specific cleanup needed for now
  }
}
