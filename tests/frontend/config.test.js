const fs = require("fs");
const path = require("path");

function loadGlobal(file) {
  const code = fs.readFileSync(path.resolve(__dirname, "../../static/js/" + file + ".js"), "utf-8");
  (0, eval)(code);
}

describe("ConfigView", () => {
  function setupDOM() {
    document.body.innerHTML = `
      <div id="config-currency-list"></div>
      <div id="config-rates-list"></div>
      <form id="config-currency-form">
        <input type="text" id="cur-code" value="EUR" />
        <input type="text" id="cur-name" value="Euro" />
        <input type="text" id="cur-symbol" value="€" />
        <button type="submit" id="config-currency-btn">Add Currency</button>
      </form>
      <form id="config-rate-form">
        <select id="rate-currency-code"></select>
        <input type="number" id="rate-value" value="1.25" />
        <button type="submit" id="config-rate-btn">Add Rate</button>
      </form>
      <button id="config-export-btn">Download JSON Backup</button>
    `;
  }

  beforeEach(() => {
    setupDOM();
    loadGlobal("utils");
    loadGlobal("api-client");
    CalculatorView = { init: jest.fn(), render: jest.fn() };
    InventoryView = { initModal: jest.fn() };
    App = {
      state: {
        currencies: [
          { code: "USD", name: "US Dollar", symbol: "$", is_main: true },
          { code: "EUR", name: "Euro", symbol: "€", is_main: false },
        ],
        products: [],
        rates: [{ id: "r1", currency_code: "EUR", rate: "0.850000" }],
        transactions: [],
      }
    };
  });

  it("renders currency cards on init", () => {
    loadGlobal("config");
    ConfigView.init();
    expect(document.getElementById("config-currency-list").children.length).toBe(2);
  });

  it("renders rates list on init", () => {
    loadGlobal("config");
    ConfigView.init();
    expect(document.getElementById("config-rates-list").children.length).toBe(1);
  });

  it("shows main currency badge", () => {
    loadGlobal("config");
    ConfigView.init();
    expect(document.getElementById("config-currency-list").innerHTML).toContain("main");
  });

  it("shows Set Base button for non-main currencies", () => {
    loadGlobal("config");
    ConfigView.init();
    expect(document.getElementById("config-currency-list").innerHTML).toContain("set_base");
  });

  it("populates rate currency select", () => {
    loadGlobal("config");
    ConfigView.init();
    expect(document.getElementById("rate-currency-code").options.length).toBe(2);
  });

  it("handles empty currencies gracefully", () => {
    App.state.currencies = [];
    loadGlobal("config");
    ConfigView.init();
    expect(document.getElementById("config-currency-list").children.length).toBe(0);
  });

  it("shows empty rates message", () => {
    App.state.rates = [];
    loadGlobal("config");
    ConfigView.init();
    expect(document.getElementById("config-rates-list").innerHTML).toContain("no_rates");
  });

  it("uses ApiClient.put for setMainCurrency, not _request", async () => {
    // Arrange
    ApiClient.put = jest.fn().mockResolvedValue({ data: [] });
    ApiClient.get = jest.fn().mockResolvedValue({ data: [] });
    ApiClient._request = jest.fn();
    loadGlobal("config");

    // Act
    await ConfigView.setMainCurrency("EUR");

    // Assert
    expect(ApiClient._request).not.toHaveBeenCalled();
    expect(ApiClient.put).toHaveBeenCalledWith("/api/v1/currencies/EUR/set_main");
  });
});
