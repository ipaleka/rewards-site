import { RewardsClient } from './RewardsClient'
import { WalletManager } from '@txnlab/use-wallet'

/**
 * Component for handling reward claim operations.
 * 
 * Manages the UI and logic for checking claimable status and submitting
 * claim transactions to the blockchain. Automatically updates when wallet
 * state changes.
 * 
 * @example
 * ```typescript
 * const claimComponent = new ClaimComponent(rewardsClient, walletManager)
 * claimComponent.bind(document.getElementById('claim-container'))
 * ```
 */
export class ClaimComponent {
  private element: HTMLElement | null = null
  private rewardsClient: RewardsClient
  private walletManager: WalletManager
  private claimable: boolean = false

  /**
   * Creates an instance of ClaimComponent.
   *
   * @param rewardsClient - The client for interacting with rewards contract and API
   * @param walletManager - The wallet manager for account and network state
   */
  constructor(rewardsClient: RewardsClient, walletManager: WalletManager) {
    this.rewardsClient = rewardsClient
    this.walletManager = walletManager
    this.walletManager.subscribe(() => this.fetchClaimableStatus())
  }

  /**
   * Binds the component to a DOM element and initializes event listeners.
   *
   * @param element - The HTML element to bind the component to
   */
  bind(element: HTMLElement) {
    this.element = element
    this.addEventListeners()
    // Ensure the DOM is fully loaded before fetching data to ensure CSRF token is available
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.fetchClaimableStatus());
    } else {
      this.fetchClaimableStatus();
    }
  }

  /**
   * Fetches claimable status data from the backend API.
   *
   * Retrieves whether the current account has any claimable rewards.
   * Updates the internal state with the results and re-renders the UI.
   *
   * @private
   */
  private async fetchClaimableStatus() {
    const activeAddress = this.walletManager.activeAccount?.address
    if (!activeAddress) {
      this.claimable = false
      this.render()
      return
    }

    try {
      const status = await this.rewardsClient.fetchClaimableStatus(activeAddress)
      this.claimable = status.claimable
    } catch (error) {
      console.error('[ClaimComponent] Error fetching claimable status:', error)
      // Don't show alert for initial data load - it's not user-initiated
      // Just log it and set claimable to false
      this.claimable = false
    } finally {
      this.render()
    }
  }

  /**
   * Handles the claim transaction submission.
   *
   * Submits a claim transaction to the blockchain and notifies the backend
   * on success. Refreshes the page after successful claim to show updated state.
   *
   * @private
   */
  private async handleClaim() {
    try {
      console.info('[ClaimComponent] Initiating claim...')

      // Step 1: Call smart contract
      const txID = await this.rewardsClient.claimRewards()
  
      // Step 2: Notify backend (fail silently)
      try {
        const activeAddress = this.walletManager.activeAccount?.address
        if (activeAddress) {
          await this.rewardsClient.userClaimed(activeAddress, txID)
        }
      } catch (notificationError) {
        console.error('Backend notification failed:', notificationError)
        // Silently continue - the blockchain transaction succeeded
      }

      // Step 3: Reload to show updated state
      location.reload()

    } catch (error) {
      // Only handle smart contract errors with alerts
      console.error('[ClaimComponent] Error during claim:', error)
      alert(`Claim failed: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  /**
   * Renders the current claimable status to the UI.
   *
   * Updates the claim button state and text based on whether rewards
   * are currently claimable.
   *
   * @private
   */
  private render() {
    if (!this.element) return

    const claimButton = this.element.querySelector<HTMLButtonElement>('#claim-button')
    if (claimButton) {
      claimButton.disabled = !this.claimable
      claimButton.textContent = this.claimable ? 'Claim' : 'No Claim Available'
    }
  }

  /**
   * Adds event listeners for user interactions.
   *
   * Listens for click events on the claim button.
   *
   * @private
   */
  private addEventListeners() {
    if (!this.element) return

    this.element.addEventListener('click', (e: Event) => {
      const target = e.target as HTMLElement
      if (target.id === 'claim-button') {
        this.handleClaim()
      }
    })
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