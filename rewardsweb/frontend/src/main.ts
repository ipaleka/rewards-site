import './style.css'
import { NetworkId, WalletId, WalletManager } from '@txnlab/use-wallet'
import { ActiveNetwork } from './ActiveNetwork'
import { WalletComponent } from './WalletComponent'

const walletManager = new WalletManager({
  wallets: [
    WalletId.PERA,
    WalletId.DEFLY,
    WalletId.LUTE
  ],
  defaultNetwork: NetworkId.MAINNET  // Start with Testnet for safety
})

const appDiv = document.querySelector<HTMLDivElement>('#app')!

// Add header
appDiv.innerHTML = `
  <div>
    <h1>Pera + Defly Wallet Connect for Django</h1>
    <p>Connect your wallet below. Transactions are signed client-side.</p>
  </div>
`

// Add network selector
const activeNetwork = new ActiveNetwork(walletManager)
appDiv.appendChild(activeNetwork.element)

// Add wallet components
const walletComponents = walletManager.wallets.map(
  (wallet) => new WalletComponent(wallet, walletManager)
)
walletComponents.forEach((walletComponent) => {
  appDiv.appendChild(walletComponent.element)
})

// Resume sessions on load
document.addEventListener('DOMContentLoaded', async () => {
  try {
    await walletManager.resumeSessions()
  } catch (error) {
    console.error('Error resuming sessions:', error)
  }
})

// Cleanup (optional for SPA; fine for page unload)
window.addEventListener('beforeunload', () => {
  walletComponents.forEach((wc) => wc.destroy())
})