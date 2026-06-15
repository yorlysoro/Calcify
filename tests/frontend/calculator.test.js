const fs = require("fs");
const path = require("path");

function loadGlobal(file) {
  const code = fs.readFileSync(path.resolve(__dirname, "../../static/js/" + file + ".js"), "utf-8");
  (0, eval)(code);
}

describe("CalculatorView", () => {
  function setupDOM() {
    document.body.innerHTML = `
      <input type="number" id="calc-input" value="100.00" />
      <select id="calc-base"></select>
      <div id="calc-warning" class="hidden"></div>
      <div id="calc-results"></div>
    `;
  }

  function setupApp() {
    App = {
      state: {
        currencies: [
          { code: "USD", name: "US Dollar", symbol: "$", is_main: true },
          { code: "EUR", name: "Euro", symbol: "€", is_main: false },
          { code: "GBP", name: "British Pound", symbol: "£", is_main: false },
        ],
        products: [],
        rates: [
          { currency_code: "EUR", rate: "0.850000", inverse_rate: "0.85" },
          { currency_code: "GBP", rate: "0.730000", inverse_rate: "0.73" },
        ],
        transactions: [],
      }
    };
  }

  beforeEach(() => {
    setupDOM();
    loadGlobal("utils");
    loadGlobal("api-client");
  });

  it("populates currency select on init", () => {
    setupApp();
    loadGlobal("calculator");
    CalculatorView.init();
    expect(document.getElementById("calc-base").options.length).toBe(3);
    expect(document.getElementById("calc-base").options[0].value).toBe("USD");
  });

  it("renders conversion results for all target currencies", () => {
    setupApp();
    loadGlobal("calculator");
    CalculatorView.init();
    const results = document.getElementById("calc-results");
    expect(results.children.length).toBe(2);
  });

  it("shows warning when no base currency is set", () => {
    App = { state: { currencies: [{ code: "USD", is_main: false }], products: [], rates: [], transactions: [] } };
    loadGlobal("calculator");
    CalculatorView.init();
    expect(document.getElementById("calc-results").innerHTML).toContain("Please set a base currency");
  });

  it("handles empty currencies array", () => {
    App = { state: { currencies: [], products: [], rates: [], transactions: [] } };
    loadGlobal("calculator");
    CalculatorView.init();
    expect(document.getElementById("calc-results").innerHTML).toContain("Please set a base currency");
  });

  it("renders zero amount with correct currency symbols", () => {
    setupApp();
    document.getElementById("calc-input").value = "0";
    loadGlobal("calculator");
    CalculatorView.init();
    const html = document.getElementById("calc-results").innerHTML;
    expect(html).toContain("€0.00");
    expect(html).toContain("£0.00");
  });

  it("handles missing exchange rates (uses fallback 1.0)", () => {
    App = {
      state: {
        currencies: [{ code: "USD", is_main: true }, { code: "EUR", is_main: false }],
        products: [], rates: [], transactions: [],
      }
    };
    loadGlobal("calculator");
    CalculatorView.init();
    expect(document.getElementById("calc-results").innerHTML).toContain("EUR");
  });
});
