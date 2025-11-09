import { RewardsClient } from './RewardsClient'
import { WalletManager } from '@txnlab/use-wallet'

/**
 * Component for managing and adding reward allocations to multiple addresses.
 * 
 * This component handles the UI and logic for adding allocations to various addresses
 * with corresponding amounts. It integrates with the RewardsClient to fetch data
 * and submit transactions to the blockchain.
 * 
 * @example
 * ```typescript
 * const addAllocationsComponent = new AddAllocationsComponent(rewardsClient, walletManager)
 * addAllocationsComponent.bind(document.getElementById('add-allocations-container'))
 * ```
 */
export class AddAllocationsComponent {
  private element: HTMLElement | null = null
  private rewardsClient: RewardsClient
  private walletManager: WalletManager
  private addresses: string[] = []
  private amounts: number[] = []

  /**
   * Creates an instance of AddAllocationsComponent.
   *
   * @param rewardsClient - The client for interacting with rewards contract and API
   * @param walletManager - The wallet manager for account and network state
   */
  constructor(rewardsClient: RewardsClient, walletManager: WalletManager) {
    this.rewardsClient = rewardsClient
    this.walletManager = walletManager
    this.walletManager.subscribe(() => this.fetchAllocationsData())
  }

  /**
   * Binds the component to a DOM element and initializes event listeners.
   *
   * @param element - The HTML element to bind the component to
   */
  bind(element: HTMLElement) {
    this.element = element
    this.addEventListeners()
    this.fetchAllocationsData()
  }

  /**
   * Fetches allocation data from the backend API for the active account.
   *
   * Updates the internal state with addresses and amounts, then re-renders the UI.
   * Handles errors by displaying alerts to the user.
   *
   * @private
   */
  private async fetchAllocationsData() {
    const activeAddress = this.walletManager.activeAccount?.address
    if (!activeAddress) {
      this.addresses = []
      this.amounts = []
      this.render()
      return
    }

    try {
      const data = await this.rewardsClient.fetchAddAllocationsData(activeAddress)
      this.addresses = data.addresses
      this.amounts = data.amounts
      this.render()
    } catch (error) {
      console.error('[AddAllocationsComponent] Error fetching add allocations data:', error)
      alert(`Failed to fetch allocations data: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  /**
   * Handles the add allocations transaction submission.
   *
   * Sends the current addresses and amounts to the blockchain via RewardsClient.
   * Displays success/error messages and refreshes data on success.
   *
   * @private
   */
  private async handleAddAllocations() {
    try {
      console.info('[AddAllocationsComponent] Initiating add allocations...')
      await this.rewardsClient.addAllocations(this.addresses, this.amounts)
      alert('Add allocations transaction sent successfully!')
      // Re-fetch data after successful transaction
      await this.fetchAllocationsData()
    } catch (error) {
      console.error('[AddAllocationsComponent] Error during add allocations:', error)
      alert(`Add allocations failed: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  /**
   * Renders the current allocation data to the UI.
   *
   * Updates textareas and display elements with current addresses and amounts.
   *
   * @private
   */
  render() {
    if (!this.element) return

    const addressesInput = this.element.querySelector<HTMLTextAreaElement>('#addresses-input')
    const amountsInput = this.element.querySelector<HTMLTextAreaElement>('#amounts-input')
    const allocationsData = this.element.querySelector<HTMLPreElement>('#allocations-data')

    if (addressesInput) {
      addressesInput.value = this.addresses.join('\n')
    }
    if (amountsInput) {
      amountsInput.value = this.amounts.join('\n')
    }
    if (allocationsData) {
      allocationsData.textContent = JSON.stringify({ addresses: this.addresses, amounts: this.amounts }, null, 2)
    }
  }

  /**
   * Adds event listeners for user interactions.
   *
   * Listens for click events on the add allocations button and updates
   * internal state from textarea inputs before submission.
   *
   * @private
   */
  addEventListeners() {
    if (!this.element) return

    this.element.addEventListener('click', (e: Event) => {
      const target = e.target as HTMLElement
      if (target.id === 'add-allocations-button') {
        // Update internal state from textareas before sending
        const addressesInput = this.element!.querySelector('#addresses-input') as HTMLTextAreaElement
        const amountsInput = this.element!.querySelector('#amounts-input') as HTMLTextAreaElement
        this.addresses = addressesInput.value.split('\n').map(s => s.trim()).filter(s => s !== '')
        this.amounts = amountsInput.value.split('\n').map(s => parseInt(s.trim(), 10)).filter(n => !isNaN(n))
        this.handleAddAllocations()
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
