import { AirdropClient } from './AirdropClient'
import { WalletManager } from '@txnlab/use-wallet'

export class AddAllocationsComponent {
  element: HTMLElement
  private airdropClient: AirdropClient
  private walletManager: WalletManager
  private addresses: string[] = []
  private amounts: number[] = []

  constructor(airdropClient: AirdropClient, walletManager: WalletManager) {
    this.airdropClient = airdropClient
    this.walletManager = walletManager
    this.element = document.createElement('div')
    this.render()
    this.addEventListeners()
    this.walletManager.subscribe(() => this.fetchAllocationsData())
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
      const data = await this.airdropClient.fetchAddAllocationsData(activeAddress)
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
      await this.airdropClient.addAllocations(this.addresses, this.amounts)
      alert('Add allocations transaction sent successfully!')
      // Re-fetch data after successful transaction
      await this.fetchAllocationsData()
    } catch (error) {
      console.error('[AddAllocationsComponent] Error during add allocations:', error)
      alert(`Add allocations failed: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  render() {
    this.element.innerHTML = `
      <div class="space-y-4 p-4 rounded-lg bg-base-200 mt-4">
        <h4 class="font-semibold text-lg">Add Allocations (Superuser Only)</h4>
        <div class="form-control">
          <label class="label"><span class="label-text">Addresses</span></label>
          <textarea id="addresses-input" class="textarea textarea-bordered h-24" placeholder="Enter addresses, one per line"></textarea>
        </div>
        <div class="form-control">
          <label class="label"><span class="label-text">Amounts</span></label>
          <textarea id="amounts-input" class="textarea textarea-bordered h-24" placeholder="Enter amounts, one per line"></textarea>
        </div>
        <button
          id="add-allocations-button"
          type="button"
          class="btn btn-primary btn-sm"
        >
          Add Allocations
        </button>
        <div class="mt-4">
          <h5 class="font-semibold">Current Allocations Data (from backend):</h5>
          <pre>${JSON.stringify({ addresses: this.addresses, amounts: this.amounts }, null, 2)}</pre>
        </div>
      </div>
    `
    const addressesInput = this.element.querySelector('#addresses-input') as HTMLTextAreaElement
    if (addressesInput) {
      addressesInput.value = this.addresses.join('\n')
    }
    const amountsInput = this.element.querySelector('#amounts-input') as HTMLTextAreaElement
    if (amountsInput) {
      amountsInput.value = this.amounts.join('\n')
    }
  }

  addEventListeners() {
    this.element.addEventListener('click', (e: Event) => {
      const target = e.target as HTMLElement
      if (target.id === 'add-allocations-button') {
        // Update internal state from textareas before sending
        const addressesInput = this.element.querySelector('#addresses-input') as HTMLTextAreaElement
        const amountsInput = this.element.querySelector('#amounts-input') as HTMLTextAreaElement
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
