// BSD 3-Clause License
//
// Copyright (c) 2026, yorlysoro
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are met:
//
// 1. Redistributions of source code must retain the above copyright notice, this
//    list of conditions and the following disclaimer.
//
// 2. Redistributions in binary form must reproduce the above copyright notice,
//    this list of conditions and the following disclaimer in the documentation
//    and/or other materials provided with the distribution.
//
// 3. Neither the name of the copyright holder nor the names of its
//    contributors may be used to endorse or promote products derived from
//    this software without specific prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
// AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
// IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
// DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
// FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
// DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
// SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
// CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
// OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
// OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

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
      <span id="report-date"></span>
      <span id="metric-purchases"></span>
      <span id="metric-sales"></span>
      <span id="metric-profit"></span>
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

  it("repopulates rate currency select after currency creation", async () => {
    ApiClient.post = jest.fn().mockResolvedValue({});
    ApiClient.get = jest.fn()
      .mockResolvedValue({ data: [{ code: "USD", name: "US Dollar", symbol: "$", is_main: true }, { code: "EUR", name: "Euro", symbol: "€", is_main: false }, { code: "GBP", name: "Pound", symbol: "£", is_main: false }] });
    ApiClient._request = jest.fn();
    loadGlobal("config");

    ConfigView._populateRateCurrencySelect();
    var select = document.getElementById("rate-currency-code");
    expect(select.options.length).toBe(2);

    var res = await ApiClient.get("/api/v1/currencies");
    App.state.currencies = res.data;
    ConfigView._populateRateCurrencySelect();

    expect(select.options.length).toBe(3);
    expect(select.innerHTML).toContain("GBP");
  });

  it("renders metrics from today's transactions", () => {
    var today = new Date().toISOString().split("T")[0];
    App.state.transactions = [
      { id: "t1", product_id: "p1", transaction_type: "IN", quantity: 2, unit_price: "100.00", currency_code: "USD", created_at: today + "T10:00:00Z" },
      { id: "t2", product_id: "p1", transaction_type: "OUT", quantity: 1, unit_price: "250.00", currency_code: "USD", created_at: today + "T11:00:00Z" },
    ];
    loadGlobal("config");
    ConfigView.renderMetrics();

    expect(document.getElementById("report-date").textContent).toBe(today);
    expect(document.getElementById("metric-sales").textContent).toContain("250");
    expect(document.getElementById("metric-purchases").textContent).toContain("200");
  });

  it("renders zero metrics when no transactions", () => {
    App.state.transactions = [];
    loadGlobal("config");
    ConfigView.renderMetrics();

    var today = new Date().toISOString().split("T")[0];
    expect(document.getElementById("report-date").textContent).toBe(today);
    expect(document.getElementById("metric-sales").textContent).toBe("$0.00");
    expect(document.getElementById("metric-purchases").textContent).toBe("$0.00");
  });

  it("renderMetrics subtracts purchases from profit", () => {
    var today = new Date().toISOString().split("T")[0];
    App.state.transactions = [
      { id: "t1", product_id: "p1", transaction_type: "IN", quantity: 5, unit_price: "100.00", currency_code: "USD", created_at: today + "T10:00:00Z" },
      { id: "t2", product_id: "p1", transaction_type: "OUT", quantity: 2, unit_price: "300.00", currency_code: "USD", created_at: today + "T11:00:00Z" },
    ];
    loadGlobal("config");
    ConfigView.renderMetrics();

    expect(document.getElementById("metric-purchases").textContent).toBe("$500.00");
    expect(document.getElementById("metric-sales").textContent).toBe("$600.00");
    expect(document.getElementById("metric-profit").textContent).toBe("$100.00");
  });
});
