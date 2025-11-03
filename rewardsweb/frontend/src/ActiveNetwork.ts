import { NetworkId, WalletManager } from '@txnlab/use-wallet'

export class ActiveNetwork {
  manager: WalletManager
  element: HTMLElement

  constructor(manager: WalletManager) {
    this.manager = manager
    this.element = document.createElement('div')
    this.element.className = 'network-group'
    this.render()
    this.addEventListeners()
  }

  setActiveNetwork = (network: NetworkId) => {
    this.manager.setActiveNetwork(network)
    this.render()
  }

  render() {
    const activeNetwork = this.manager.activeNetwork

    this.element.innerHTML = `
      <div class="space-y-3">
        <h4 class="font-semibold text-lg">
          Current Network:
          <span class="badge badge-outline">${activeNetwork}</span>
        </h4>

        <div class="flex gap-2">
          <button
            type="button"
            id="set-testnet"
            class="btn btn-outline btn-sm"
            ${activeNetwork === NetworkId.TESTNET ? "disabled" : ""}
          >
            Set to Testnet
          </button>

          <button
            type="button"
            id="set-mainnet"
            class="btn btn-outline btn-sm"
            ${activeNetwork === NetworkId.MAINNET ? "disabled" : ""}
          >
            Set to Mainnet
          </button>
        </div>
      </div>
    `
  }

  addEventListeners() {
    this.element.addEventListener('click', (e: Event) => {
      const target = e.target as HTMLButtonElement
      if (target.id === 'set-testnet') {
        this.setActiveNetwork(NetworkId.TESTNET)
      } else if (target.id === 'set-mainnet') {
        this.setActiveNetwork(NetworkId.MAINNET)
      }
    })
  }

  destroy() {
    this.element.removeEventListener('click', this.addEventListeners)
  }
}
