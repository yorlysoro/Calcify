const fs = require("fs");
const path = require("path");

function loadGlobal(file) {
  const code = fs.readFileSync(path.resolve(__dirname, "../../static/js/" + file + ".js"), "utf-8");
  (0, eval)(code);
}

describe("App Controller", () => {
  function setupDOM() {
    document.body.innerHTML = `
      <span id="sys-status-text">Offline</span>
      <span id="sys-status-dot" class="bg-zinc-500"></span>
      <nav>
        <button data-target="view-calculator" class="tab-btn text-emerald-500 border-emerald-500">🧮 Calculadora</button>
        <button data-target="view-inventory" class="tab-btn text-zinc-500 border-transparent">📦 Inventario</button>
        <button data-target="view-config" class="tab-btn text-zinc-500 border-transparent">⚙️ Config</button>
      </nav>
      <main>
        <section id="view-calculator" class="w-full">Calculator Content</section>
        <section id="view-inventory" class="hidden">Inventory Content</section>
        <section id="view-config" class="hidden">Config Content</section>
      </main>
    `;
  }

  beforeEach(() => {
    setupDOM();
    loadGlobal("utils");
    loadGlobal("api-client");
    CalculatorView = { init: jest.fn() };
    InventoryView = { init: jest.fn() };
    ConfigView = { init: jest.fn() };
    ReportView = { init: jest.fn() };
    SalesView = { init: jest.fn() };
    loadGlobal("app");
  });

  afterEach(() => { jest.restoreAllMocks(); delete global.fetch; });

  it("initializes with calculator as default tab", () => {
    expect(App.state.currentTab).toBe("view-calculator");
  });

  it("switches tabs correctly", () => {
    App.switchTab("view-config");
    expect(App.state.currentTab).toBe("view-config");
    expect(document.getElementById("view-calculator").classList.contains("hidden")).toBe(true);
    expect(document.getElementById("view-config").classList.contains("hidden")).toBe(false);
  });

  it("updates tab button styling on switch", () => {
    App.switchTab("view-inventory");
    expect(document.querySelector('[data-target="view-calculator"]').classList.contains("text-zinc-500")).toBe(true);
    expect(document.querySelector('[data-target="view-inventory"]').classList.contains("text-emerald-500")).toBe(true);
  });

  it("fetches data on init and updates status", async () => {
    global.fetch = jest.fn()
      .mockResolvedValueOnce({ ok: true, status: 200, headers: new Map([["content-type", "application/json"]]), json: async () => ({ data: [{ code: "USD", is_main: true }] }) })
      .mockResolvedValueOnce({ ok: true, status: 200, headers: new Map([["content-type", "application/json"]]), json: async () => ({ data: [] }) })
      .mockResolvedValueOnce({ ok: true, status: 200, headers: new Map([["content-type", "application/json"]]), json: async () => ({ data: [] }) });

    await App.init();
    expect(App.state.currencies).toEqual([{ code: "USD", is_main: true }]);
    expect(document.getElementById("sys-status-text").textContent).toBe("Online");
  });

  it("handles API failure gracefully on init", async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error("Network failure"));
    await App.init();
    expect(document.getElementById("sys-status-text").textContent).toBe("Offline");
  });

  it("handles switch to non-existent tab", () => {
    App.switchTab("view-nonexistent");
    document.querySelectorAll("main > section").forEach(function(sec) {
      expect(sec.classList.contains("hidden")).toBe(true);
    });
  });

  it("fails gracefully when status elements are missing", async () => {
    document.getElementById("sys-status-text").remove();
    document.getElementById("sys-status-dot").remove();
    global.fetch = jest.fn().mockResolvedValue({ ok: true, status: 200, headers: new Map([["content-type", "application/json"]]), json: async () => ({ data: [] }) });
    await expect(App.init()).resolves.toBeUndefined();
  });

  it("refreshProducts updates state", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true, status: 200,
      headers: new Map([["content-type", "application/json"]]),
      json: async () => ({ data: [{ id: "new1", name: "New Product" }] }),
    });
    await App.refreshProducts();
    expect(App.state.products).toEqual([{ id: "new1", name: "New Product" }]);
  });

  it("handles missing tab buttons", () => {
    document.querySelectorAll(".tab-btn").forEach(function(btn) { btn.remove(); });
    expect(function() { App.switchTab("view-calculator"); }).not.toThrow();
  });
});
