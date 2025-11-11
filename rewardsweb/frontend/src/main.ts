import { WalletManager, WalletId } from '@txnlab/use-wallet'
import { ActiveNetwork } from './ActiveNetwork'
import { WalletComponent } from './WalletComponent'
import { RewardsClient } from './RewardsClient'
import { ClaimComponent } from './ClaimComponent'
import { AddAllocationsComponent } from './AddAllocationsComponent'
import { ReclaimAllocationsComponent } from './ReclaimAllocationsComponent'

/**
 * Main application class that orchestrates the entire frontend application.
 * 
 * This class initializes all components, manages wallet connections, and
 * coordinates between different parts of the application. It handles the
 * complete lifecycle of the application including initialization, component
 * binding, and cleanup.
 * 
 * @example
 * ```typescript
 * // The application auto-initializes on DOMContentLoaded
 * const app = new App()
 * ```
 */
export class App {
  /** The wallet manager instance for handling multiple wallets */
  walletManager: WalletManager | null = null

  // Store component references so Jest tests can verify cleanup
  private activeNetworkComponent: ActiveNetwork | null = null
  private walletComponents: WalletComponent[] = []
  private claimComponent: ClaimComponent | null = null
  private addAllocationsComponent: AddAllocationsComponent | null = null
  private reclaimAllocationsComponent: ReclaimAllocationsComponent | null = null

  /**
   * Creates an instance of App.
   * Sets up the DOMContentLoaded event listener for initialization.
   */
  constructor() {
    document.addEventListener('DOMContentLoaded', this.init.bind(this))
  }

  /**
   * Initializes the application by setting up wallets, components, and event handlers.
   *
   * This method:
   * - Fetches initial wallet and network data from the backend
   * - Initializes the WalletManager with available wallets
   * - Binds all UI components to their respective DOM elements
   * - Sets up cleanup handlers for page unload
   *
   * @throws {Error} When initial data fetching fails
   */
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
        defaultNetwork: 'testnet',
      })

      // Bind network selector
      const activeNetworkEl = document.getElementById('active-network')
      if (activeNetworkEl && this.walletManager) {
        this.activeNetworkComponent = new ActiveNetwork(this.walletManager)
        this.activeNetworkComponent.bind(activeNetworkEl)
      }

      // Create wallet components
      walletsData.forEach((walletData: any) => {
        const wallet = this.walletManager!.getWallet(walletData.id)
        if (wallet) {
          const walletEl = document.getElementById(`wallet-${wallet.id}`)
          if (walletEl) {
            const walletComponent = new WalletComponent(wallet, this.walletManager!)
            walletComponent.bind(walletEl)
            this.walletComponents.push(walletComponent)
          }
        }
      })

      // Rewards client + other UI components
      if (this.walletManager && this.walletManager.wallets.length > 0) {
        const rewardsClient = new RewardsClient(this.walletManager.wallets[0], this.walletManager)

        const claimContainer = document.getElementById('claim-container')
        if (claimContainer) {
          this.claimComponent = new ClaimComponent(rewardsClient, this.walletManager)
          this.claimComponent.bind(claimContainer)
        }

        const addAllocationsContainer = document.getElementById('add-allocations-container')
        if (addAllocationsContainer) {
          this.addAllocationsComponent = new AddAllocationsComponent(rewardsClient, this.walletManager)
          this.addAllocationsComponent.bind(addAllocationsContainer)
        }

        const reclaimAllocationsContainer = document.getElementById('reclaim-allocations-container')
        if (reclaimAllocationsContainer) {
          this.reclaimAllocationsComponent = new ReclaimAllocationsComponent(rewardsClient, this.walletManager)
          this.reclaimAllocationsComponent.bind(reclaimAllocationsContainer)
        }
      }

      await this.walletManager.resumeSessions()

      window.addEventListener('beforeunload', () => {
        this.walletManager?.resumeSessions()
        this.activeNetworkComponent?.destroy?.()
        this.walletComponents.forEach(c => c.destroy?.())
        this.claimComponent?.destroy?.()
        this.addAllocationsComponent?.destroy?.()
        this.reclaimAllocationsComponent?.destroy?.()
      })

    } catch (error) {
      console.error('Error initializing app:', error)
      const errorDiv = document.getElementById('app-error')
      if (errorDiv) {
        errorDiv.style.display = 'block'
      }
    }
  }
}

// Initialize the application
new App()
