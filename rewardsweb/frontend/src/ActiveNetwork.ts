import { NetworkId, WalletManager } from '@txnlab/use-wallet'

export class ActiveNetwork {
  private element: HTMLElement | null = null
  private unsubscribe: (() => void) | null = null

  constructor(private manager: WalletManager) { }

  bind(element: HTMLElement) {
    this.element = element
    this.unsubscribe = this.manager.subscribe((state) => {
      this.render(state.activeNetwork)
    })
    this.element.addEventListener('click', this.handleClick)
    this.render(this.manager.activeNetwork)
  }

  private handleClick = async (e: Event) => {
    const btn = e.target as HTMLElement
    const network = btn.dataset.network as NetworkId

    if (!network) return

    this.manager.setActiveNetwork(network)

    try {
      const csrfToken = this.getCsrfToken()
      await fetch('/api/wallet/active-network/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ network })
      })
    } catch (error) {
      console.error('Error setting active network:', error)
    }
  }

  private render(activeNetwork: string | null) {
    if (!this.element) return

    const networkSpan = this.element.querySelector('span')
    if (networkSpan) {
      networkSpan.textContent = activeNetwork || 'none'
    }

    const buttons = this.element.querySelectorAll('button')
    buttons.forEach((btn) => {
      if (btn.dataset.network === activeNetwork) {
        btn.classList.add('disabled')
      } else {
        btn.classList.remove('disabled')
      }
    })
  }

  private getCsrfToken(): string {
    const csrfCookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='))
    return csrfCookie ? csrfCookie.split('=')[1] : ''
  }

  destroy() {
    if (this.unsubscribe) {
      this.unsubscribe()
      this.unsubscribe = null // Prevent multiple calls
    }
    if (this.element) {
      this.element.removeEventListener('click', this.handleClick)
      // Don't nullify element as it might be needed for other cleanup
    }
  }
}
