import { WalletManager, WalletId } from '@txnlab/use-wallet'
import { ActiveNetwork } from './ActiveNetwork'
import { WalletComponent } from './WalletComponent'
import { RewardsClient } from './RewardsClient'
import { ClaimComponent } from './ClaimComponent'
import { AddAllocationsComponent } from './AddAllocationsComponent'
import { ReclaimAllocationsComponent } from './ReclaimAllocationsComponent'

class App {
  walletManager: WalletManager | null = null

  constructor() {
    document.addEventListener('DOMContentLoaded', this.init.bind(this))
  }

  async init() {
    try {
      const [walletsResponse, networkResponse] = await Promise.all([
        fetch('/api/wallet/wallets/'),
        fetch('/api/wallet/active-network/')
      ])

      if (!walletsResponse.ok || !networkResponse.ok) {
        throw new Error('Failed to fetch initial data')
      }

      const walletsData = await walletsResponse.json()
      const walletIds = walletsData.map((w: any) => w.id as WalletId)

      this.walletManager = new WalletManager({
        wallets: walletIds,
        defaultNetwork: 'testnet'
      })

      const appDiv = document.querySelector<HTMLDivElement>('#app')!

      // Bind network selector
      const activeNetworkEl = document.getElementById('active-network')
      if (activeNetworkEl && this.walletManager) {
        const activeNetwork = new ActiveNetwork(this.walletManager)
        activeNetwork.bind(activeNetworkEl)
      }

      // Create and bind wallet components
      walletsData.forEach((walletData: any) => {
        const wallet = this.walletManager!.getWallet(walletData.id)
        if (wallet) {
          const walletEl = document.getElementById(`wallet-${wallet.id}`)
          if (walletEl) {
            const walletComponent = new WalletComponent(wallet, this.walletManager!)
            walletComponent.bind(walletEl)
          }
        }
      })

      // Add Rewards client and other components
      if (this.walletManager && this.walletManager.wallets.length > 0) {
        const rewardsClient = new RewardsClient(this.walletManager.wallets[0], this.walletManager)
        const claimComponent = new ClaimComponent(rewardsClient, this.walletManager)
        appDiv.appendChild(claimComponent.element)

        const addAllocationsComponent = new AddAllocationsComponent(rewardsClient, this.walletManager)
        appDiv.appendChild(addAllocationsComponent.element)

        const reclaimAllocationsComponent = new ReclaimAllocationsComponent(rewardsClient, this.walletManager)
        appDiv.appendChild(reclaimAllocationsComponent.element)
      }

      await this.walletManager.resumeSessions()

    } catch (error) {
      console.error('Error initializing app:', error)
      const appDiv = document.querySelector<HTMLDivElement>('#app')!
      appDiv.innerHTML = '<div class="alert alert-error">Could not initialize wallet application. Please try again later.</div>'
    }
  }
}

new App()
