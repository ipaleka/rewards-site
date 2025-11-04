import {
  AtomicTransactionComposer,
  ABIContract
} from 'algosdk'
import { BaseWallet, WalletManager, NetworkId } from '@txnlab/use-wallet'
import { getAlgodClient } from './ActiveNetwork'
import airdropABI from '../../contract/Airdrop.arc56.json'

// ARC-56 Contract
const contract = new ABIContract(airdropABI)

// TODO: Replace with your actual app ID
const appId = 123456789

export class AirdropClient {
  private wallet: BaseWallet
  private manager: WalletManager
  private algodClient: ReturnType<typeof getAlgodClient>

  constructor(wallet: BaseWallet, manager: WalletManager) {
    this.wallet = wallet
    this.manager = manager
    this.algodClient = getAlgodClient(this.manager.activeNetwork as NetworkId)
  }

  private getCsrfToken = () => {
    const name = 'csrftoken'
    const cookieValue = document.cookie.match('(^|;)\s*' + name + '\s*=\s*([^;]+)')?.pop() || ''
    return cookieValue || (document.querySelector('input[name="csrfmiddlewaretoken"]') as HTMLInputElement)?.value || ''
  }

  private getHeaders = () => ({
    'Content-Type': 'application/json',
    'X-CSRFToken': this.getCsrfToken()
  })

  public async addAllocations(addresses: string[], amounts: number[]) {
    if (!this.wallet.activeAccount?.address) {
      throw new Error('No active account selected.')
    }
    if (!addresses.length || addresses.length !== amounts.length) {
      throw new Error('Addresses and amounts arrays must have the same non-zero length.')
    }

    try {
      const suggestedParams = await this.algodClient.getTransactionParams().do()
      const atc = new AtomicTransactionComposer()

      atc.addMethodCall({
        appID: appId,
        method: contract.getMethodByName('add_allocations'),
        methodArgs: [addresses, amounts],
        sender: this.wallet.activeAccount.address,
        signer: this.wallet.transactionSigner,
        suggestedParams
      })

      const result = await atc.execute(this.algodClient, 4)
      console.info(`[AirdropClient] ✅ Successfully sent add_allocations transaction!`, {
        confirmedRound: result.confirmedRound,
        txIDs: result.txIDs
      })
      return result
    } catch (error) {
      console.error('[AirdropClient] Error adding allocations:', error)
      throw error
    }
  }

  public async reclaimAllocation(userAddress: string) {
    if (!this.wallet.activeAccount?.address) {
      throw new Error('No active account selected.')
    }

    try {
      const suggestedParams = await this.algodClient.getTransactionParams().do()
      const atc = new AtomicTransactionComposer()

      atc.addMethodCall({
        appID: appId,
        method: contract.getMethodByName('reclaim_allocation'),
        methodArgs: [userAddress],
        sender: this.wallet.activeAccount.address,
        signer: this.wallet.transactionSigner,
        suggestedParams
      })

      const result = await atc.execute(this.algodClient, 4)
      console.info(`[AirdropClient] ✅ Successfully sent reclaim_allocation transaction!`, {
        confirmedRound: result.confirmedRound,
        txIDs: result.txIDs
      })
      return result
    } catch (error) {
      console.error('[AirdropClient] Error reclaiming allocation:', error)
      throw error
    }
  }

  public async claim() {
    if (!this.wallet.activeAccount?.address) {
      throw new Error('No active account selected.')
    }

    try {
      const suggestedParams = await this.algodClient.getTransactionParams().do()
      const atc = new AtomicTransactionComposer()

      // The claim method might require a foreign asset, let's assume token_id is 1 for now
      // You might need to fetch this dynamically
      const tokenId = 1;

      atc.addMethodCall({
        appID: appId,
        method: contract.getMethodByName('claim'),
        methodArgs: [],
        sender: this.wallet.activeAccount.address,
        signer: this.wallet.transactionSigner,
        suggestedParams,
        appForeignAssets: [tokenId]
      })

      const result = await atc.execute(this.algodClient, 4)
      console.info(`[AirdropClient] ✅ Successfully sent claim transaction!`, {
        confirmedRound: result.confirmedRound,
        txIDs: result.txIDs
      })
      return result
    } catch (error) {
      console.error('[AirdropClient] Error claiming allocation:', error)
      throw error
    }
  }

  public async fetchClaimableStatus(address: string): Promise<{ claimable: boolean }> {
    try {
      const response = await fetch('/api/wallet/claim-allocation/', {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ address })
      })
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      return data
    } catch (error) {
      console.error('[AirdropClient] Error fetching claimable status:', error)
      throw error
    }
  }

  public async fetchAddAllocationsData(address: string): Promise<{ addresses: string[], amounts: number[] }> {
    try {
      const response = await fetch('/api/wallet/add-allocations/', {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ address })
      })
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      return data
    } catch (error) {
      console.error('[AirdropClient] Error fetching add allocations data:', error)
      throw error
    }
  }

  public async fetchReclaimAllocationsData(address: string): Promise<{ addresses: string[] }> {
    try {
      const response = await fetch('/api/wallet/reclaim-allocations/', {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ address })
      })
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      return data
    } catch (error) {
      console.error('[AirdropClient] Error fetching reclaim allocations data:', error)
      throw error
    }
  }
}
