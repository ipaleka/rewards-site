import { NetworkId, WalletManager } from '@txnlab/use-wallet'
import algosdk from 'algosdk'

// Placeholder Algorand node configurations
const algodTestnetConfig = {
  token: '', // Replace with your Testnet Algod token
  server: 'https://testnet-api.algonode.cloud', // Replace with your Testnet Algod server
  port: '',
}

const algodMainnetConfig = {
  token: '', // Replace with your Mainnet Algod token
  server: 'https://mainnet-api.algonode.cloud', // Replace with your Mainnet Algod server
  port: '',
}

export function getAlgodClient(network: NetworkId): algosdk.Algodv2 {
  switch (network) {
    case NetworkId.TESTNET:
      return new algosdk.Algodv2(algodTestnetConfig.token, algodTestnetConfig.server, algodTestnetConfig.port)
    case NetworkId.MAINNET:
      return new algosdk.Algodv2(algodMainnetConfig.token, algodMainnetConfig.server, algodMainnetConfig.port)
    default:
      // Fallback to Testnet or throw an error
      return new algosdk.Algodv2(algodTestnetConfig.token, algodTestnetConfig.server, algodTestnetConfig.port)
  }
}

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
