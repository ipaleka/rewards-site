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
   * @param rewardsClient - The client for interacting with rewards contract
   * @param walletManager - The wallet manager for account state management
   */
  constructor(rewardsClient: RewardsClient, walletManager: WalletManager) {
    this.rewardsClient = rewardsClient
    this.walletManager = walletManager
    this.walletManager.subscribe(() => this.checkClaimableStatus())
  }

  /**
   * Binds the component to a DOM element and initializes event listeners.
   *
   * @param element - The HTML element to bind the component to
   */
  bind(element: HTMLElement) {
    this.element = element
    this.addEventListeners()
    this.checkClaimableStatus()
  }

  /**
   * Checks if the current account has any claimable rewards.
   *
   * Fetches claimable status from the backend API and updates the UI accordingly.
   * Handles errors by setting claimable to false and re-rendering.
   *
   * @private
   */
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

  /**
   * Handles the claim transaction submission.
   *
   * Submits a claim transaction to the blockchain and updates the UI
   * based on the result. Re-checks claimable status after completion.
   *
   * @private
   */
  private async handleClaim() {
    try {
      console.info('[ClaimComponent] Initiating claim...')
      await this.rewardsClient.claim()
      alert('Claim transaction sent successfully!')

      const activeAddress = this.walletManager.activeAccount?.address
      if (activeAddress) {
        await this.rewardsClient.userClaimed(activeAddress)
      }
      // Re-check status after successful claim
      await this.checkClaimableStatus()
    } catch (error) {
      console.error('[ClaimComponent] Error during claim:', error)
      alert(`Claim failed: ${error instanceof Error ? error.message : String(error)}`)
      // Also re-check status after failed claim to ensure UI is up to date
      await this.checkClaimableStatus()
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
  render() {
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
  addEventListeners() {
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
