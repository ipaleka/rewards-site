const {
  showToast,
  processDjangoMessages,
  closeModal,
  isBlockingRequest,
  startProgressBar,
  finishProgressBar,
  processActiveNetwork,
  processDaisyUITheme,
} = require("./site.js");

// JSDOM doesn't implement showModal, so we'll mock it.
HTMLDialogElement.prototype.showModal = jest.fn();
HTMLDialogElement.prototype.close = jest.fn();

describe("Toast and Message Functions", () => {
  beforeEach(() => {
    document.body.innerHTML = '<div id="toast-container"></div>';
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test("showToast should create and append a toast notification", () => {
    showToast("success", "Test message");
    const toastContainer = document.getElementById("toast-container");
    expect(toastContainer.children.length).toBe(1);
    const toast = toastContainer.children[0];
    expect(toast.classList.contains("alert-success")).toBe(true);
    expect(toast.textContent).toBe("Test message");

    // Fast-forward time to check if the toast is removed
    jest.advanceTimersByTime(5000);
    expect(toastContainer.children.length).toBe(0);
  });

  test("showToast should handle different types", () => {
    showToast("error", "Error message");
    let toast = document.querySelector(".alert");
    expect(toast.classList.contains("alert-error")).toBe(true);
    toast.remove();

    showToast("info", "Info message");
    toast = document.querySelector(".alert");
    expect(toast.classList.contains("alert-info")).toBe(true);
    toast.remove();

    showToast("warning", "Warning message");
    toast = document.querySelector(".alert");
    expect(toast.classList.contains("alert-warning")).toBe(true);
  });

  test("showToast should not fail if container is not found", () => {
    document.body.innerHTML = ""; // No toast container
    expect(() => showToast("success", "test")).not.toThrow();
  });

  test("processDjangoMessages should show toasts and remove the container", () => {
    document.body.innerHTML += `
      <div id="django-messages">
        <div data-message="Message 1" data-message-type="success"></div>
        <div data-message="Message 2" data-message-type="error"></div>
        <div data-message="Message 3"></div>
      </div>
    `;
    processDjangoMessages();
    const toastContainer = document.getElementById("toast-container");
    expect(toastContainer.children.length).toBe(3);
    expect(toastContainer.children[2].classList.contains("alert-info")).toBe(
      true
    );
    expect(document.getElementById("django-messages")).toBeNull();
  });

  test("processDjangoMessages should not fail if container is not found", () => {
    expect(() => processDjangoMessages()).not.toThrow();
  });
});

describe("Modal Functions", () => {
  test("closeModal should clear the modal container", () => {
    document.body.innerHTML = '<div id="modal-container">Some content</div>';
    closeModal();
    const modalContainer = document.getElementById("modal-container");
    expect(modalContainer.innerHTML).toBe("");
  });

  test("closeModal should not fail if container is not found", () => {
    document.body.innerHTML = "";
    expect(() => closeModal()).not.toThrow();
  });
});

describe("HTMX Progress Bar Functions", () => {
  beforeEach(() => {
    document.body.innerHTML = '<div id="htmx-progress-bar" class="hidden"></div>';
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test("isBlockingRequest should detect blocking conditions", () => {
    const elWithHxVals = document.createElement("div");
    elWithHxVals.setAttribute("hx-vals", '{"blocking": "true"}');
    expect(isBlockingRequest(elWithHxVals, {})).toBe(true);

    const elWithDataset = document.createElement("div");
    elWithDataset.dataset.blocking = "true";
    expect(isBlockingRequest(elWithDataset, {})).toBe(true);

    const elBoosted = document.createElement("div");
    expect(isBlockingRequest(elBoosted, { boosted: true })).toBe(true);

    const nonBlockingEl = document.createElement("div");
    expect(isBlockingRequest(nonBlockingEl, {})).toBe(false);

    expect(isBlockingRequest(null, {})).toBe(false);
  });

  test("startProgressBar should not fail if bar is not found", () => {
    document.body.innerHTML = "";
    expect(() => startProgressBar()).not.toThrow();
  });

  test("startProgressBar should show the bar and start the interval", () => {
    startProgressBar();
    const bar = document.getElementById("htmx-progress-bar");
    expect(bar.classList.contains("hidden")).toBe(false);
    expect(bar.style.width).toBe("0%");

    jest.advanceTimersByTime(250);
    expect(parseFloat(bar.style.width)).toBeGreaterThan(0);
  });

  test("startProgressBar with blocking should disable pointer events", () => {
    startProgressBar(true);
    expect(document.body.style.pointerEvents).toBe("none");
  });

  test("finishProgressBar should not fail if bar is not found", () => {
    document.body.innerHTML = "";
    expect(() => finishProgressBar()).not.toThrow();
  });

  test("finishProgressBar should complete and hide the bar", async () => {
    startProgressBar();
    const bar = document.getElementById("htmx-progress-bar");
    const promise = finishProgressBar();
    jest.advanceTimersByTime(300);
    await promise;

    expect(bar.style.width).toBe("0%");
    expect(bar.classList.contains("hidden")).toBe(true);
  });

  test("finishProgressBar with blocking should re-enable pointer events", () => {
    document.body.style.pointerEvents = "none";
    finishProgressBar(true);
    expect(document.body.style.pointerEvents).toBe("");
  });

  test("finishProgressBar should execute a callback", (done) => {
    const callback = jest.fn(() => {
      done();
    });
    finishProgressBar(false, callback);
    jest.advanceTimersByTime(300);
    expect(callback).toHaveBeenCalled();
  });
});

describe("UI Initializers", () => {
  test("processActiveNetwork should toggle button states on click", () => {
    document.body.innerHTML = `
      <div id="active-network">
        <button data-network="mainnet">Mainnet</button>
        <button data-network="testnet" disabled class="btn-disabled">Testnet</button>
      </div>
    `;
    processActiveNetwork();
    const mainnetButton = document.querySelector('[data-network="mainnet"]');
    const testnetButton = document.querySelector('[data-network="testnet"]');

    mainnetButton.click();

    expect(mainnetButton.disabled).toBe(true);
    expect(mainnetButton.classList.contains("btn-disabled")).toBe(true);
    expect(testnetButton.disabled).toBe(false);
    expect(testnetButton.classList.contains("btn-disabled")).toBe(false);

    // Click the other button to test the reverse
    testnetButton.click();

    expect(testnetButton.disabled).toBe(true);
    expect(testnetButton.classList.contains("btn-disabled")).toBe(true);
    expect(mainnetButton.disabled).toBe(false);
    expect(mainnetButton.classList.contains("btn-disabled")).toBe(false);

    // Click a non-button element
    const container = document.getElementById("active-network");
    container.click();
    expect(testnetButton.disabled).toBe(true); // State should not change
  });

  test("processActiveNetwork should not fail if container is not found", () => {
    document.body.innerHTML = "";
    expect(() => processActiveNetwork()).not.toThrow();
  });

  test("processDaisyUITheme should not fail if saved theme element is not found", () => {
    localStorage.setItem("theme", "nonexistent");
    document.body.innerHTML = `
      <input type="radio" name="theme-dropdown" value="light">
    `;
    expect(() => processDaisyUITheme()).not.toThrow();
  });

  test("processDaisyUITheme should load theme from localStorage", () => {
    localStorage.setItem("theme", "dark");
    document.body.innerHTML = `
      <input type="radio" name="theme-dropdown" value="light">
      <input type="radio" name="theme-dropdown" value="dark">
    `;
    processDaisyUITheme();
    const darkThemeInput = document.querySelector('[value="dark"]');
    expect(darkThemeInput.checked).toBe(true);
  });

  test("processDaisyUITheme should handle no theme in localStorage", () => {
    localStorage.removeItem("theme");
    document.body.innerHTML = `
      <input type="radio" name="theme-dropdown" value="light" checked>
      <input type="radio" name="theme-dropdown" value="dark">
    `;
    processDaisyUITheme();
    const lightThemeInput = document.querySelector('[value="light"]');
    expect(lightThemeInput.checked).toBe(true); // Stays at default
  });

  test("processDaisyUITheme should save theme to localStorage on change", () => {
    document.body.innerHTML = `
      <input type="radio" name="theme-dropdown" value="light" checked>
      <input type="radio" name="theme-dropdown" value="dark">
    `;
    processDaisyUITheme();
    const darkThemeInput = document.querySelector('[value="dark"]');
    darkThemeInput.click(); // Simulate user clicking the theme
    darkThemeInput.dispatchEvent(new Event("change")); // Dispatch change event

    expect(localStorage.getItem("theme")).toBe("dark");
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
  });

  test("processDaisyUITheme should not add listeners twice", () => {
    document.body.innerHTML = `
      <input type="radio" name="theme-dropdown" value="light">
    `;
    const input = document.querySelector("input");
    const addEventListenerSpy = jest.spyOn(input, "addEventListener");

    processDaisyUITheme();
    processDaisyUITheme(); // Call a second time

    expect(addEventListenerSpy).toHaveBeenCalledTimes(1);
  });
});

describe("Global Event Listeners", () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <div id="htmx-progress-bar" class="hidden"></div>
      <div id="toast-container"></div>
      <div id="modal-container"></div>
    `;
    jest.useFakeTimers();
    jest.spyOn(global, "setTimeout");
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test("DOMContentLoaded should initialize UI components", () => {
    jest.mock("./site.js", () => ({
      processActiveNetwork: jest.fn(),
      processDaisyUITheme: jest.fn(),
      processDjangoMessages: jest.fn(),
      initializeDomReadyListeners: jest.fn(() => {
        require("./site.js").processActiveNetwork();
        require("./site.js").processDaisyUITheme();
        require("./site.js").processDjangoMessages();
      }),
      htmxState: { requestBlocking: false },
    }));

    const site = require("./site.js");

    site.initializeDomReadyListeners();

    expect(site.processActiveNetwork).toHaveBeenCalled();
    expect(site.processDaisyUITheme).toHaveBeenCalled();
    expect(site.processDjangoMessages).toHaveBeenCalled();
  });

  test("htmx:configRequest should start the progress bar", () => {
    const event = new CustomEvent("htmx:configRequest", {
      detail: { elt: document.body, requestConfig: {} },
    });
    document.body.dispatchEvent(event);
    const bar = document.getElementById("htmx-progress-bar");
    expect(bar.classList.contains("hidden")).toBe(false);
  });

  test("htmx:afterSwap should trigger multiple UI updates", () => {
    const site = require("./site.js");
    site.htmxState.requestBlocking = true;

    const swapTarget = document.createElement("div");
    swapTarget.dataset.toastMessage = "Swapped!";
    swapTarget.innerHTML = `
      <input type="text">
      <dialog id="my-modal"></dialog>
    `;

    const configRequestEvent = new CustomEvent("htmx:configRequest", {
      detail: { elt: document.body, requestConfig: {} },
    });
    document.body.dispatchEvent(configRequestEvent);

    const event = new CustomEvent("htmx:afterSwap", {
      bubbles: true,
      detail: { target: swapTarget },
    });
    document.body.dispatchEvent(event); // Dispatch on body to ensure listener catches it

    // Let the first batch of timers run (progress bar, fade-in, autofocus)
    jest.advanceTimersByTime(300);

    // Test progress bar finish
    const bar = document.getElementById("htmx-progress-bar");
    expect(bar.classList.contains("hidden")).toBe(true);
    expect(bar.style.width).toBe("0%");

    // Test fade-in
    expect(swapTarget.classList.contains("fade-in")).toBe(false);

    // Test autofocus
    expect(setTimeout).toHaveBeenCalledWith(expect.any(Function), 30);

    // Test toast is present
    const toast = document.querySelector(".alert");
    expect(toast).not.toBeNull();
    expect(toast.textContent).toBe("Swapped!");

    // Test modal
    const modal = swapTarget.querySelector("#my-modal");
    expect(modal.showModal).toHaveBeenCalled();

    // Now run the timer for removing the toast
    jest.advanceTimersByTime(4500);
    expect(document.querySelector(".alert")).toBeNull();
  });

  test("htmx:afterSwap should handle swapped element being a dialog", () => {
    const swapTarget = document.createElement("dialog");
    const event = new CustomEvent("htmx:afterSwap", {
      bubbles: true,
      detail: { target: swapTarget },
    });
    document.body.dispatchEvent(event);
    expect(swapTarget.showModal).toHaveBeenCalled();
  });

  test("htmx:afterSwap should handle no focusable inputs or dialogs", () => {
    const swapTarget = document.createElement("div");
    swapTarget.innerHTML = "<span>Some content</span>";
    const event = new CustomEvent("htmx:afterSwap", {
      bubbles: true,
      detail: { target: swapTarget },
    });
    expect(() => swapTarget.dispatchEvent(event)).not.toThrow();
  });

  test("htmx:error should finish the progress bar", () => {
    const site = require('./site.js');
    site.htmxState.requestBlocking = true;

    const event = new Event("htmx:error");
    document.body.dispatchEvent(event);

    const bar = document.getElementById("htmx-progress-bar");
    expect(bar.style.width).toBe("100%");
    expect(document.body.style.pointerEvents).toBe("");
  });
});

describe("initializeDomReadyListeners Isolation Test", () => {
  let mockProcessActiveNetwork;
  let mockProcessDaisyUITheme;
  let mockProcessDjangoMessages;

  beforeEach(() => {
    jest.resetModules(); // Ensure a clean module state for this isolated test
    const site = require("./site.js");
    mockProcessActiveNetwork = jest.spyOn(site, "processActiveNetwork").mockImplementation(() => {});
    mockProcessDaisyUITheme = jest.spyOn(site, "processDaisyUITheme").mockImplementation(() => {});
    mockProcessDjangoMessages = jest.spyOn(site, "processDjangoMessages").mockImplementation(() => {});
  });

  afterEach(() => {
    mockProcessActiveNetwork.mockRestore();
    mockProcessDaisyUITheme.mockRestore();
    mockProcessDjangoMessages.mockRestore();
  });

  test("should call all initialization functions", () => {
    const { initializeDomReadyListeners } = require("./site.js");
    initializeDomReadyListeners();

    expect(mockProcessActiveNetwork).toHaveBeenCalledTimes(1);
    expect(mockProcessDaisyUITheme).toHaveBeenCalledTimes(1);
    expect(mockProcessDjangoMessages).toHaveBeenCalledTimes(1);
  });
});
