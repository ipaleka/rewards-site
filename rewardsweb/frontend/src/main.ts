import { NetworkId, WalletId, WalletManager } from '@txnlab/use-wallet'
import { ActiveNetwork } from './ActiveNetwork'
import { WalletComponent } from './WalletComponent'
import { RewardsClient } from './RewardsClient'
import { ClaimComponent } from './ClaimComponent'
import { AddAllocationsComponent } from './AddAllocationsComponent'
import { ReclaimAllocationsComponent } from './ReclaimAllocationsComponent'

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

// Add Rewards client and Claim component
const rewardsClient = new RewardsClient(walletManager.wallets[0], walletManager) // Assuming the first wallet is the active one for now
const claimComponent = new ClaimComponent(rewardsClient, walletManager)
appDiv.appendChild(claimComponent.element)

// Add superuser components
const addAllocationsComponent = new AddAllocationsComponent(rewardsClient, walletManager)
appDiv.appendChild(addAllocationsComponent.element)

const reclaimAllocationsComponent = new ReclaimAllocationsComponent(rewardsClient, walletManager)
appDiv.appendChild(reclaimAllocationsComponent.element)

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
