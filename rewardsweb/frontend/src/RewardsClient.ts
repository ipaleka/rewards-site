import {
  AtomicTransactionComposer,
  ABIContract,
  makeAssetTransferTxnWithSuggestedParamsFromObject,
  Algodv2
} from 'algosdk'
import { BaseWallet, WalletManager, NetworkId } from '@txnlab/use-wallet'
import rewardsABI from '../../contract/artifacts/Rewards.arc56.json'

/**
 * Client for interacting with the Rewards smart contract and backend API.
 * 
 * This class provides methods to interact with the Algorand blockchain
 * for reward-related operations including adding allocations, reclaiming
 * allocations, and claiming rewards. It handles transaction composition,
 * signing, and submission.
 * 
 * @example
 * ```typescript
 * const rewardsClient = new RewardsClient(wallet, walletManager)
 * await rewardsClient.addAllocations(addresses, amounts)
 * ```
 */
export class RewardsClient {
  private wallet: BaseWallet
  private manager: WalletManager
  private algodClient: Algodv2
  private contract: ABIContract
  private rewardsAppIds: { [key in NetworkId]?: number }

  /**
   * Creates an instance of RewardsClient.
   *
   * @param wallet - The wallet instance for transaction signing
   * @param manager - The wallet manager for network and account management
   */
  constructor(wallet: BaseWallet, manager: WalletManager) {
    this.wallet = wallet
    this.manager = manager
    this.algodClient = this.manager.algodClient
    this.contract = new ABIContract(rewardsABI as any)

    // Hardcoded App IDs for different networks
    this.rewardsAppIds = {
      [NetworkId.MAINNET]: 0, // TODO: Replace with your Mainnet App ID
      [NetworkId.TESTNET]: 749240272, // TODO: Replace with your Testnet App ID
    }
  }

  /**
   * Retrieves the CSRF token from cookies or form input for API requests.
   *
   * @returns The CSRF token as a string
   * @private
   */
  private getCsrfToken = () => {
    const cookieValue = document.cookie.match(/(^|;)\s*csrftoken\s*=\s*([^;]+)/)?.pop() || ''
    return cookieValue || (document.querySelector('input[name="csrfmiddlewaretoken"]') as HTMLInputElement)?.value || ''
  }

  /**
   * Gets the headers for API requests including CSRF token.
   *
   * @returns Headers object for fetch requests
   * @private
   */
  private getHeaders = () => ({
    'Content-Type': 'application/json',
    'X-CSRFToken': this.getCsrfToken()
  })

  /**
   * Adds allocations to multiple addresses with specified amounts.
   *
   * Creates and submits an atomic transaction to the rewards contract
   * to allocate rewards to the provided addresses.
   *
   * @param addresses - Array of recipient addresses
   * @param amounts - Array of amounts to allocate (must match addresses length)
   * @returns The transaction result
   * @throws {Error} When no active account, arrays are empty, or arrays length mismatch
   */
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
      const currentNetwork = this.manager.activeNetwork as NetworkId
      const appId = this.rewardsAppIds[currentNetwork]

      if (!appId) {
        throw new Error(`App ID not configured for network: ${currentNetwork}`)
      }

      atc.addMethodCall({
        appID: appId,
        method: this.contract.getMethodByName('add_allocations'),
        methodArgs: [addresses, amounts],
        sender: this.wallet.activeAccount.address,
        signer: this.wallet.transactionSigner,
        suggestedParams
      })

      const result = await atc.execute(this.algodClient, 4)
      console.info(`[RewardsClient] ✅ Successfully sent add_allocations transaction!`, {
        confirmedRound: result.confirmedRound,
        txIDs: result.txIDs
      })
      return result
    } catch (error) {
      console.error('[RewardsClient] Error adding allocations:', error)
      throw error
    }
  }

  /**
   * Reclaims an allocation from a specific user address.
   *
   * Submits a transaction to reclaim previously allocated rewards from
   * the specified address back to the contract owner.
   *
   * @param userAddress - The address to reclaim allocation from
   * @returns The transaction result
   * @throws {Error} When no active account or app ID not configured
   */
  public async reclaimAllocation(userAddress: string) {
    if (!this.wallet.activeAccount?.address) {
      throw new Error('No active account selected.')
    }

    try {
      const suggestedParams = await this.algodClient.getTransactionParams().do()
      const atc = new AtomicTransactionComposer()
      const currentNetwork = this.manager.activeNetwork as NetworkId
      const appId = this.rewardsAppIds[currentNetwork]

      if (!appId) {
        throw new Error(`App ID not configured for network: ${currentNetwork}`)
      }

      atc.addMethodCall({
        appID: appId,
        method: this.contract.getMethodByName('reclaim_allocation'),
        methodArgs: [userAddress],
        sender: this.wallet.activeAccount.address,
        signer: this.wallet.transactionSigner,
        suggestedParams
      })

      const result = await atc.execute(this.algodClient, 4)
      console.info(`[RewardsClient] ✅ Successfully sent reclaim_allocation transaction!`, {
        confirmedRound: result.confirmedRound,
        txIDs: result.txIDs
      })
      return result
    } catch (error) {
      console.error('[RewardsClient] Error reclaiming allocation:', error)
      throw error
    }
  }

  /**
   * Claims available rewards for the active account.
   *
   * Performs an atomic transaction group that includes:
   * 1. Asset opt-in transaction for the reward token
   * 2. Claim method call to the rewards contract
   *
   * @returns The transaction result
   * @throws {Error} When no active account, app ID not configured, or token_id not found
   */
  public async claim() {
    if (!this.wallet.activeAccount?.address) {
      throw new Error('No active account selected.')
    }

    try {
      const suggestedParams = await this.algodClient.getTransactionParams().do()
      const atc = new AtomicTransactionComposer()
      const sender = this.wallet.activeAccount.address
      const signer = this.wallet.transactionSigner
      const currentNetwork = this.manager.activeNetwork as NetworkId
      const appId = this.rewardsAppIds[currentNetwork]

      if (!appId) {
        throw new Error(`App ID not configured for network: ${currentNetwork}`)
      }

      // Fetch the token_id from the contract's global state
      const appInfo = await this.algodClient.getApplicationByID(appId).do();
      const globalState = appInfo.params.globalState;
      if (!globalState || globalState.length === 0) {
        throw new Error("Contract global state is empty or not found");
      }
      const tokenIdEncoded = btoa('token_id');
      const tokenIdValue = globalState.find((state: any) => state['key'] === tokenIdEncoded);
      if (!tokenIdValue) {
        throw new Error("token_id not found in contract's global state");
      }
      const tokenId = tokenIdValue['value']['uint'];

      // 1. Create the asset opt-in transaction
      const optInTxn = makeAssetTransferTxnWithSuggestedParamsFromObject({
        sender: sender,
        receiver: sender,
        amount: 0,
        assetIndex: tokenId,
        suggestedParams: suggestedParams,
      });

      // Wrap it in a TransactionWithSigner
      const tws = { txn: optInTxn, signer: signer };

      // 2. Add the opt-in transaction to our atomic group
      atc.addTransaction(tws);

      // 3. Add the method call to 'claim' to our atomic group
      atc.addMethodCall({
        appID: appId,
        method: this.contract.getMethodByName('claim'),
        methodArgs: [],
        sender: sender,
        signer: signer,
        suggestedParams,
        appForeignAssets: [tokenId]
      });

      const result = await atc.execute(this.algodClient, 4)
      console.info(`[RewardsClient] ✅ Successfully sent claim transaction!`, {
        confirmedRound: result.confirmedRound,
        txIDs: result.txIDs
      })
      return result
    } catch (error) {
      console.error('[RewardsClient] Error claiming allocation:', error)
      throw error
    }
  }

  /**
   * Fetches the claimable status for an address from the backend API.
   *
   * @param address - The address to check claimable status for
   * @returns Object indicating whether rewards are claimable
   * @throws {Error} When the API request fails
   */
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
      console.error('[RewardsClient] Error fetching claimable status:', error)
      throw error
    }
  }

  /**
   * Fetches add allocations data for an address from the backend API.
   *
   * @param address - The address to fetch allocation data for
   * @returns Object containing addresses and amounts for allocations
   * @throws {Error} When the API request fails
   */
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
      console.error('[RewardsClient] Error fetching add allocations data:', error)
      throw error
    }
  }

  /**
   * Fetches reclaimable allocations data for an address from the backend API.
   *
   * @param address - The address to fetch reclaimable data for
   * @returns Object containing addresses with reclaimable allocations
   * @throws {Error} When the API request fails
   */
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
      console.error('[RewardsClient] Error fetching reclaim allocations data:', error)
      throw error
    }
  }
}
