/************************************************************
 *  Toast Notifications (DaisyUI)
 ************************************************************/
function showToast(type, text) {
    const toastContainer = document.getElementById("toast-container");
    if (!toastContainer) return;
    const toast = document.createElement("div");

    toast.className = `alert alert-${type === "error" ? "error" : "success"} shadow-lg`;
    toast.innerHTML = `<span>${text}</span>`;

    toastContainer.appendChild(toast);
    setTimeout(() => toast.remove(), 4500);
}

function showDjangoMessages(messages) {
    if (!messages?.length) return;
    messages.forEach(({ tag, text }) => showToast(tag, text));
}


/************************************************************
 *  Modal Close Helpers
 ************************************************************/
function closeModal() {
    const modalContainer = document.getElementById("modal-container");
    if (modalContainer) modalContainer.innerHTML = "";
}


/************************************************************
 *  ✅ GLOBAL HTMX TOP PROGRESS BAR (GitHub-style)
 ************************************************************/
var progressInterval = null;
var htmxRequestBlocking = false;


/**
 * Determine if HTMX request should be blocking
 */
function isBlockingRequest(el, requestConfig) {
    return (
        el?.getAttribute("hx-vals")?.includes('"blocking": "true"') ||
        el?.dataset.blocking === "true" ||
        requestConfig?.boosted === true  // <--- links / boosted navigation are blocking
    );
}

function startProgressBar(blocking = false) {
    const bar = document.getElementById("htmx-progress-bar");
    if (!bar) return;
    bar.classList.remove("hidden");
    bar.style.width = "0%";

    if (blocking) {
        document.body.style.pointerEvents = "none";
    }

    let width = 0;
    progressInterval = setInterval(() => {
        width = Math.min(width + Math.random() * 15, 90);
        bar.style.width = `${width}%`;
    }, 200);
}

function finishProgressBar(blocking = false) {
    const bar = document.getElementById("htmx-progress-bar");
    if (!bar) return;

    clearInterval(progressInterval);
    bar.style.width = "100%";

    if (blocking) {
        document.body.style.pointerEvents = "";
    }

    setTimeout(() => {
        bar.classList.add("hidden");
        bar.style.width = "0%";
    }, 300);
}


/************************************************************
 *  ✅ UNIFIED HTMX EVENT PIPELINE (single afterSwap handler)
 ************************************************************/

/**
 * Request started — progress bar
 */
document.body.addEventListener("htmx:configRequest", (event) => {
    htmxRequestBlocking = isBlockingRequest(event.detail.elt, event.detail.requestConfig);
    startProgressBar(htmxRequestBlocking);
});


/**
 * DOM updated — stop progress, fade animation, autofocus, toast
 */
document.body.addEventListener("htmx:afterSwap", (event) => {
    finishProgressBar(htmxRequestBlocking);

    // fade-in animation
    event.target.classList.add("fade-in");
    setTimeout(() => event.target.classList.remove("fade-in"), 300);

    // autofocus
    const firstInput = event.target.querySelector("input:not([type=hidden]), textarea, select");
    if (firstInput) setTimeout(() => firstInput.focus(), 30);

    // toast notifications
    if (event.target.dataset.toastMessage) {
        showToast(event.target.dataset.toastType || "success", event.target.dataset.toastMessage);
    }
});


/************************************************************
 *  Auto-open modals after HTMX swap
 ************************************************************/
document.body.addEventListener('htmx:afterSwap', function(evt) {
    // Look for any dialog elements in the swapped content
    const dialogs = evt.detail.target.querySelectorAll('dialog');
    dialogs.forEach(dialog => {
        if (!dialog.open) {
            console.log('Auto-opening modal:', dialog.id);
            dialog.showModal();
        }
    });
    // Also check if the target itself is a dialog
    if (evt.detail.target.tagName === 'DIALOG' && !evt.detail.target.open) {
        console.log('Auto-opening dialog target:', evt.detail.target.id);
        evt.detail.target.showModal();
    }
});


// Theme toggle functionality
document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.querySelector('.theme-controller');
    if (themeToggle) {
        // Set initial state from localStorage
        const currentTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', currentTheme);
        themeToggle.checked = currentTheme === 'dark';
        
        themeToggle.addEventListener('change', function() {
            const newTheme = this.checked ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
        });
    }
});

/**
 * Error case — always stop blocking
 */
document.body.addEventListener("htmx:error", () => {
    finishProgressBar(htmxRequestBlocking);
});


/************************************************************
 *  Auto-hide toasts (exists outside HTMX lifecycle)
 ************************************************************/
document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".toast").forEach(toast => {
        setTimeout(() => {
            toast.classList.add("opacity-0", "transition", "duration-300");
            setTimeout(() => toast.remove(), 300);
        }, 4500);
    });
});


/* istanbul ignore next */
if (typeof exports !== 'undefined') {
  module.exports = {
    showToast,
    showDjangoMessages,
    closeModal,
    isBlockingRequest,
    startProgressBar,
    finishProgressBar,
  };
}
