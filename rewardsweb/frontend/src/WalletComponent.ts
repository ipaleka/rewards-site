import {
  BaseWallet,
  WalletId,
  WalletManager
} from '@txnlab/use-wallet'
import { AtomicTransactionComposer, makePaymentTxnWithSuggestedParamsFromObject, encodeUnsignedTransaction, isValidAddress } from 'algosdk'
import validator from 'validator';

export class WalletComponent {
  wallet: BaseWallet
  manager: WalletManager
  element: HTMLElement
  private unsubscribe?: () => void
  private magicEmail: string = ''

  constructor(wallet: BaseWallet, manager: WalletManager) {
    this.wallet = wallet
    this.manager = manager
    this.element = document.createElement('div')
    this.unsubscribe = wallet.subscribe((state) => {
      console.info('[App] State change:', state)
      this.render()
    })
    this.render()
    this.addEventListeners()
  }

  connect = (args?: Record<string, any>) => this.wallet.connect(args)
  disconnect = () => this.wallet.disconnect()
  setActive = () => this.wallet.setActive()

  sendTransaction = async () => {
    const txnButton = this.element.querySelector('#transaction-button') as HTMLButtonElement
    if (!txnButton) return

    try {
      const activeAddress = this.wallet.activeAccount?.address
      if (!activeAddress) {
        throw new Error('[App] No active account')
      }

      const atc = new AtomicTransactionComposer()
      const suggestedParams = await this.manager.algodClient.getTransactionParams().do()
      const transaction = makePaymentTxnWithSuggestedParamsFromObject({
        sender: activeAddress,
        receiver: activeAddress,
        amount: 0,
        suggestedParams
      })

      atc.addTransaction({ txn: transaction, signer: this.wallet.transactionSigner })
      console.info(`[App] Sending transaction...`, transaction)

      txnButton.disabled = true
      txnButton.textContent = 'Sending Transaction...'

      const result = await atc.execute(this.manager.algodClient, 4)
      console.info(`[App] ✅ Successfully sent transaction!`, {
        confirmedRound: result.confirmedRound,
        txIDs: result.txIDs
      })
    } catch (error) {
      console.error('[App] Error signing transaction:', error)
    } finally {
      txnButton.disabled = false
      txnButton.textContent = 'Send Transaction'
    }
  }

  auth = async () => {
    const activeAddress = this.wallet.activeAccount?.address
    if (!activeAddress || !isValidAddress(activeAddress)) {
      throw new Error(`[App] Invalid or missing address: ${activeAddress || 'undefined'}`)
    }
    console.info(`[App] Authenticating with address: ${activeAddress}`)
    try {
      // Get CSRF token
      const getCsrfToken = () => {
        const name = 'csrftoken'
        const cookieValue = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)')?.pop() || ''
        return cookieValue || (document.querySelector('input[name="csrfmiddlewaretoken"]') as HTMLInputElement)?.value || ''
      }
      const headers = {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken()
      }

      // Fetch nonce
      console.info('[App] Fetching nonce for address:', activeAddress)
      const nonceResponse = await fetch('/api/wallet/nonce/', {
        method: 'POST',
        headers,
        body: JSON.stringify({ address: activeAddress })
      })
      const nonceData = await nonceResponse.json()
      if (nonceData.error) {
        throw new Error(`[App] Failed to fetch nonce: ${nonceData.error}`)
      }
      const nonce = nonceData.nonce
      const prefix = nonceData.prefix
      console.info('[App] Received nonce:', nonce)

      // Create a transaction with a note
      const message = `${prefix}${nonce}`
      const note = new TextEncoder().encode(message)
      const suggestedParams = await this.manager.algodClient.getTransactionParams().do()
      const transaction = makePaymentTxnWithSuggestedParamsFromObject({
        sender: activeAddress,
        receiver: activeAddress,
        amount: 0,
        note,
        suggestedParams
      })
      const encodedTx = encodeUnsignedTransaction(transaction)
      console.info('[App] Client encodedTx:', Array.from(encodedTx))
      console.info('[App] Signing transaction with note:', message)
      const signedTxs = await this.wallet.signTransactions([encodedTx])

      // Extract signed transaction bytes
      if (!signedTxs[0]) {
        throw new Error('[App] No signed transaction returned')
      }
      const signedTxBytes = signedTxs[0] // Already bytes from signTransactions
      const signedTxBase64 = btoa(String.fromCharCode(...signedTxBytes)) // Convert to base64 for JSON
      console.info('[App] Signed transaction base64 length:', signedTxBase64.length)

      // Send to verify
      const verifyResponse = await fetch('/api/wallet/verify/', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          address: activeAddress,
          signedTransaction: signedTxBase64, // Send full signed txn as base64
          nonce
        })
      })
      const verifyData = await verifyResponse.json()
      if (!verifyData.success) {
        throw new Error(`[App] Verification failed: ${verifyData.error}`)
      }

      console.info(`[App] ✅ Successfully authenticated with ${this.wallet.metadata.name}!`)
      // Use backend redirect URL if provided, fallback to root
      window.location.href = verifyData.redirect_url || '/'
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : String(error)
      console.error('[App] Error signing data:', error)
      // Display error to user
      const errorDiv = document.createElement('div')
      errorDiv.className = 'error-message'
      errorDiv.style.color = 'red'
      errorDiv.textContent = errorMessage
      this.element.appendChild(errorDiv)
      setTimeout(() => errorDiv.remove(), 5000)
    }
  }

  setActiveAccount = (event: Event) => {
    const target = event.target as HTMLSelectElement
    this.wallet.setActiveAccount(target.value)
  }

  isMagicLink = () => this.wallet.id === WalletId.MAGIC

  isEmailValid = () => validator.isEmail(this.magicEmail);
  isConnectDisabled = () => this.wallet.isConnected || (this.isMagicLink() && !this.isEmailValid())
  getConnectArgs = () => (this.isMagicLink() ? { email: this.magicEmail } : undefined)

  sanitizeText(text: string): string {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML; // Escapes HTML
  }
  render() {
    console.log(`[WalletComponent] ${this.wallet.metadata.name}: id = ${this.wallet.id}, isActive = ${this.wallet.isActive}, canSignData = ${this.wallet.canSignData}, metadata =`, JSON.stringify(this.wallet.metadata, null, 2));
    const walletName = this.sanitizeText(this.wallet.metadata.name); // Sanitize wallet name
    const sanitizedEmail = this.sanitizeText(this.magicEmail); // Sanitize email
    this.element.innerHTML = `
    <div class="wallet-group">
      <h4>
        ${walletName} ${this.wallet.isActive ? '[active]' : ''}
      </h4>
      <div class="wallet-buttons">
        <button id="connect-button" type="button" ${this.isConnectDisabled() ? 'disabled' : ''}>
          Connect
        </button>
        <button id="disconnect-button" type="button" ${!this.wallet.isConnected ? 'disabled' : ''}>
          Disconnect
        </button>
        ${this.wallet.isActive
        ? `<button id="transaction-button" type="button">Send Transaction</button>
               <button id="auth-button" type="button">Authenticate</button>`
        : `<button id="set-active-button" type="button" ${!this.wallet.isConnected ? 'disabled' : ''
        }>Set Active</button>`
      }
      </div>
      ${this.isMagicLink()
        ? `
        <div class="input-group">
          <label for="magic-email">Email:</label>
          <input
            id="magic-email"
            type="email"
            value="${sanitizedEmail}"
            placeholder="Enter email to connect..."
            ${this.wallet.isConnected ? 'disabled' : ''}
          />
        </div>
      `
        : ''
      }
      ${this.wallet.isActive && this.wallet.accounts.length
        ? `
        <div>
          <select>
            ${this.wallet.accounts
          .map(
            (account) => `
              <option value="${this.sanitizeText(account.address)}" ${account.address === this.wallet.activeAccount?.address ? 'selected' : ''
              }>
                ${this.sanitizeText(account.address)}
              </option>
            `
          )
          .join('')}
          </select>
        </div>
      `
        : ''
      }
    </div>
  `
  }

  updateEmailInput = () => {
    const emailInput = this.element.querySelector('#magic-email') as HTMLInputElement
    if (emailInput) {
      emailInput.value = this.magicEmail
    }

    const connectButton = this.element.querySelector('#connect-button') as HTMLButtonElement
    if (connectButton) {
      connectButton.disabled = this.isConnectDisabled()
    }
  }

  addEventListeners() {
    this.element.addEventListener('click', (e: Event) => {
      const target = e.target as HTMLElement
      if (target.id === 'connect-button') {
        const args = this.getConnectArgs()
        this.connect(args)
      } else if (target.id === 'disconnect-button') {
        this.disconnect()
      } else if (target.id === 'set-active-button') {
        this.setActive()
      } else if (target.id === 'transaction-button') {
        this.sendTransaction()
      } else if (target.id === 'auth-button') {
        this.auth()
      }
    })

    this.element.addEventListener('change', (e: Event) => {
      const target = e.target as HTMLElement
      if (target.tagName.toLowerCase() === 'select') {
        this.setActiveAccount(e)
      }
    })

    this.element.addEventListener('input', (e: Event) => {
      const target = e.target as HTMLInputElement
      if (target.id === 'magic-email') {
        this.magicEmail = target.value
        this.updateEmailInput()
      }
    })
  }

  destroy() {
    if (this.unsubscribe) {
      this.unsubscribe()
    }
    this.element.removeEventListener('click', this.addEventListeners)
    this.element.removeEventListener('change', this.addEventListeners)
    this.element.removeEventListener('input', this.addEventListeners)
  }
}