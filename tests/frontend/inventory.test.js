const fs = require("fs");
const path = require("path");

function loadGlobal(file) {
  const code = fs.readFileSync(path.resolve(__dirname, "../../static/js/" + file + ".js"), "utf-8");
  (0, eval)(code);
}

describe("InventoryView", () => {
  function setupDOM() {
    document.body.innerHTML = `
      <input type="text" id="inv-search" />
      <table><tbody id="inv-table-body"></tbody></table>
      <div id="inv-cards-container"></div>
      <button id="add-product-btn">+ Add Product</button>
      <div id="product-modal" class="hidden">
        <div id="modal-loading" class="hidden"></div>
        <h3 id="modal-title">Add Product</h3>
        <form id="product-form">
          <input type="text" id="prod-name" />
          <input type="text" id="prod-category" />
          <input type="number" id="prod-cost" />
          <select id="prod-currency"></select>
          <input type="number" id="prod-margin" value="30" />
          <input type="number" id="prod-stock" value="0" />
          <div id="live-price-preview">0.00</div>
          <button type="button" id="close-modal-btn">Cancel</button>
          <button type="submit" id="save-modal-btn">Save</button>
        </form>
      </div>
    `;
  }

  function setupAppState() {
    App = {
      state: {
        currencies: [{ code: "USD", name: "US Dollar", symbol: "$", is_main: true }],
        products: [
          { id: "1", name: "Laptop", category: "Electronics", cost_price: "800.00", cost_currency_code: "USD", margin_percentage: "25.00", stock_quantity: 10 },
          { id: "2", name: "Mouse", category: "Accessories", cost_price: "20.00", cost_currency_code: "USD", margin_percentage: "50.00", stock_quantity: 100 },
        ],
        rates: [],
        transactions: [],
      }
    };
  }

  function initAppState() {
    App = { state: { currencies: [], products: [], rates: [], transactions: [] } };
  }

  beforeEach(() => {
    setupDOM();
    initAppState();
    loadGlobal("utils");
    loadGlobal("api-client");
  });

  it("renders products in table and cards on init", () => {
    setupAppState();
    loadGlobal("inventory");
    InventoryView.init();
    expect(document.getElementById("inv-table-body").children.length).toBe(2);
    expect(document.getElementById("inv-cards-container").children.length).toBe(2);
  });

  it("filters products by search term", () => {
    setupAppState();
    loadGlobal("inventory");
    InventoryView.init();
    InventoryView.render("Mouse");
    expect(document.getElementById("inv-table-body").innerHTML).toContain("Mouse");
    expect(document.getElementById("inv-table-body").innerHTML).not.toContain("Laptop");
  });

  it("shows empty state when no products", () => {
    loadGlobal("inventory");
    InventoryView.init();
    expect(document.getElementById("inv-table-body").innerHTML).toContain("no_products");
  });

  it("shows empty state when search matches nothing", () => {
    setupAppState();
    loadGlobal("inventory");
    InventoryView.init();
    InventoryView.render("NonExistentProductXYZ");
    expect(document.getElementById("inv-table-body").innerHTML).toContain("no_products");
  });

  it("renders product with missing optional fields", () => {
    App.state.products = [{ id: "3", name: "Service", cost_price: "100.00", cost_currency_code: "USD", margin_percentage: "10.00" }];
    App.state.currencies = [{ code: "USD", is_main: true }];
    loadGlobal("inventory");
    InventoryView.init();
    expect(document.getElementById("inv-table-body").innerHTML).toContain("Service");
  });

  it("renders product with zero stock quantity", () => {
    App.state.products = [{ id: "4", name: "Digital Item", category: "Software", cost_price: "0.00", cost_currency_code: "USD", margin_percentage: "0.00", stock_quantity: 0 }];
    App.state.currencies = [{ code: "USD", is_main: true }];
    loadGlobal("inventory");
    InventoryView.init();
    expect(document.getElementById("inv-table-body").innerHTML).toContain("Digital Item");
  });

  it("handles search with special characters", () => {
    setupAppState();
    loadGlobal("inventory");
    InventoryView.init();
    InventoryView.render(".*+?^${}()|[]\\");
    expect(() => { InventoryView.render(".*+?^${}()|[]\\"); }).not.toThrow();
    expect(document.getElementById("inv-table-body").innerHTML).toContain("no_products");
  });

  it("uses ApiClient.put for product update, not _request", () => {
    // Arrange
    ApiClient.put = jest.fn().mockResolvedValue({ data: [] });
    ApiClient._request = jest.fn();
    setupAppState();
    loadGlobal("inventory");
    InventoryView.init();
    InventoryView.editingId = "prod-123";

    document.getElementById("prod-name").value = "Updated Product";
    document.getElementById("prod-cost").value = "150.00";
    document.getElementById("prod-margin").value = "30";
    document.getElementById("prod-currency").value = "USD";
    document.getElementById("prod-stock").value = "10";

    // Act
    document.getElementById("product-form").dispatchEvent(new Event("submit"));

    // Assert
    expect(ApiClient._request).not.toHaveBeenCalled();
    expect(ApiClient.put).toHaveBeenCalled();
  });
});
