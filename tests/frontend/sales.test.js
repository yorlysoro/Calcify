const fs = require("fs");
const path = require("path");

function loadGlobal(file) {
  const code = fs.readFileSync(path.resolve(__dirname, "../../static/js/" + file + ".js"), "utf-8");
  (0, eval)(code);
}

describe("SalesView", () => {
  function setupDOM() {
    document.body.innerHTML = `
      <input type="text" id="sales-product-search" />
      <select id="sales-product"></select>
      <input type="number" id="sales-quantity" value="1" />
      <input type="number" id="sales-unit-price" value="100.00" />
      <select id="sales-currency"></select>
      <textarea id="sales-comment"></textarea>
      <div id="sales-message"></div>
      <button type="submit" id="sales-submit-btn">Registrar Venta</button>
      <form id="sales-form"></form>
    `;
  }

  function setupAppState() {
    App = {
      state: {
        currencies: [
          { code: "USD", name: "US Dollar", symbol: "$", is_main: true },
          { code: "EUR", name: "Euro", symbol: "€", is_main: false },
        ],
        products: [
          { id: "p1", name: "Laptop", stock_quantity: 10 },
          { id: "p2", name: "Mouse", stock_quantity: 100 },
        ],
        rates: [],
        transactions: [],
      }
    };
  }

  beforeEach(() => {
    setupDOM();
    loadGlobal("utils");
    loadGlobal("api-client");
    setupAppState();
    InventoryView = { render: jest.fn() };
  });

  it("populates product and currency selects on init", () => {
    loadGlobal("sales");
    SalesView.init();
    expect(document.getElementById("sales-product").options.length).toBe(2);
    expect(document.getElementById("sales-currency").options.length).toBe(2);
  });

  it("filters products by search term", () => {
    loadGlobal("sales");
    SalesView.init();
    SalesView.filterProducts();
    let visible = 0;
    document.getElementById("sales-product").querySelectorAll("option").forEach(function(opt) {
      if (opt.style.display !== "none") visible++;
    });
    expect(visible).toBe(2);
  });

  it("shows no results placeholder when filter matches nothing", () => {
    loadGlobal("sales");
    SalesView.init();
    SalesView.searchInput.value = "NonExistentProduct";
    SalesView.filterProducts();
    let hasPlaceholder = false;
    document.getElementById("sales-product").querySelectorAll("option").forEach(function(opt) {
      if (opt.dataset.placeholder) hasPlaceholder = true;
    });
    expect(hasPlaceholder).toBe(true);
  });

  it("creates a placeholder option when no products match", () => {
    App.state.products = [];
    loadGlobal("sales");
    SalesView.init();
    // filterProducts adds "Sin resultados" placeholder when visibleCount === 0
    const options = document.getElementById("sales-product").querySelectorAll("option");
    expect(options.length).toBe(1);
    expect(options[0].dataset.placeholder).toBe("true");
  });

  it("shows error message on submit failure", async () => {
    loadGlobal("sales");
    SalesView.init();
    global.fetch = jest.fn().mockRejectedValue(new Error("Validation error"));
    const event = new Event("submit", { bubbles: true, cancelable: true });
    await SalesView.handleSubmit(event);
    expect(document.getElementById("sales-message").innerHTML).toContain("Validation error");
  });
});
