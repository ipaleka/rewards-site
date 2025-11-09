import { RewardsClient } from './RewardsClient'
import { WalletManager } from '@txnlab/use-wallet'

export class AddAllocationsComponent {
  private element: HTMLElement | null = null
  private rewardsClient: RewardsClient
  private walletManager: WalletManager
  private addresses: string[] = []
  private amounts: number[] = []

  constructor(rewardsClient: RewardsClient, walletManager: WalletManager) {
    this.rewardsClient = rewardsClient
    this.walletManager = walletManager
    this.walletManager.subscribe(() => this.fetchAllocationsData())
  }

  bind(element: HTMLElement) {
    this.element = element
    this.addEventListeners()
    this.fetchAllocationsData()
  }

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

  destroy() {
    // No specific cleanup needed for now
  }
}
