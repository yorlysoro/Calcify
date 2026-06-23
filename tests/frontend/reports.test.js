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

describe("ReportView", () => {
  function setupDOM() {
    document.body.innerHTML = `
      <input type="date" id="report-date-filter" />
      <button id="export-csv-btn">Export CSV</button>
      <table><tbody id="report-table-body"></tbody></table>
      <div id="report-cards-container"></div>
    `;
  }

  function setupApp() {
    App = {
      state: {
        currencies: [
          { code: "USD", name: "US Dollar", symbol: "$", is_main: true },
          { code: "EUR", name: "Euro", symbol: "€", is_main: false },
        ],
        products: [{ id: "p1", name: "Laptop" }],
        rates: [{ currency_code: "EUR", rate: "0.850000", inverse_rate: "0.85" }],
        transactions: [],
      }
    };
  }

  beforeEach(() => {
    setupDOM();
    loadGlobal("utils");
    loadGlobal("api-client");
    setupApp();
  });

  afterEach(() => { jest.restoreAllMocks(); delete global.fetch; });

  it("sets date input to today on init", () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true, status: 200,
      headers: new Map([["content-type", "application/json"]]),
      json: async () => ({ data: [] }),
    });
    loadGlobal("reports");
    ReportView.init();
    const today = new Date().toISOString().split("T")[0];
    expect(document.getElementById("report-date-filter").value).toBe(today);
  });

  it("shows no transactions message when none exist", () => {
    loadGlobal("reports");
    ReportView.tbody = document.getElementById("report-table-body");
    ReportView.transactions = [];
    ReportView.render();
    expect(document.getElementById("report-table-body").innerHTML).toContain("no_transactions");
  });

  it("renders transactions with converted values", () => {
    loadGlobal("reports");
    CalculatorView = { formatMoney: formatMoney };
    ReportView.tbody = document.getElementById("report-table-body");
    ReportView.transactions = [{
      id: "tx1", product_id: "p1", transaction_type: "IN",
      quantity: 2, unit_price: "500.00", currency_code: "USD",
      created_at: "2026-06-14T10:30:00Z",
    }];
    ReportView.render();
    expect(document.getElementById("report-table-body").innerHTML).toContain("Laptop");
  });

  it("renders IN type badge correctly", () => {
    loadGlobal("reports");
    CalculatorView = { formatMoney: formatMoney };
    ReportView.tbody = document.getElementById("report-table-body");
    ReportView.transactions = [{
      id: "tx1", product_id: "p1", transaction_type: "OUT",
      quantity: 1, unit_price: "100.00", currency_code: "USD",
      created_at: "2026-06-14T10:00:00Z",
    }];
    ReportView.render();
    expect(document.getElementById("report-table-body").innerHTML).toContain("OUT");
  });

  it("handles transaction with unknown product ID", () => {
    loadGlobal("reports");
    CalculatorView = { formatMoney: formatMoney };
    ReportView.tbody = document.getElementById("report-table-body");
    ReportView.transactions = [{
      id: "tx1", product_id: "nonexistent", transaction_type: "IN",
      quantity: 1, unit_price: "50.00", currency_code: "USD",
      created_at: "2026-06-14T12:00:00Z",
    }];
    ReportView.render();
    expect(document.getElementById("report-table-body").innerHTML).toContain("nonexistent");
  });

  it("shows alert when exporting empty data", () => {
    global.alert = jest.fn();
    loadGlobal("reports");
    CalculatorView = { formatMoney: formatMoney };
    ReportView.transactions = [];
    ReportView.dateInput = document.getElementById("report-date-filter");
    ReportView.exportCSV();
    expect(global.alert).toHaveBeenCalledWith("no_data_export");
  });

  it("shows error state on API failure", async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error("API Error"));
    loadGlobal("reports");
    CalculatorView = { formatMoney: formatMoney };
    ReportView.tbody = document.getElementById("report-table-body");
    ReportView.dateInput = document.getElementById("report-date-filter");
    ReportView.dateInput.value = "2026-06-14";
    await ReportView.fetchAndRender();
    expect(document.getElementById("report-table-body").innerHTML).toContain("failed_load_transactions");
  });

  it("refreshes transactions after fetchAndRender", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true, status: 200,
      headers: new Map([["content-type", "application/json"]]),
      json: async () => ({ data: [{ id: "tx1", product_id: "p1", transaction_type: "OUT", quantity: 1, unit_price: "100.00", currency_code: "USD", created_at: "2026-06-14T10:00:00Z" }] }),
    });
    loadGlobal("reports");
    CalculatorView = { formatMoney: formatMoney };
    ReportView.tbody = document.getElementById("report-table-body");
    ReportView.dateInput = document.getElementById("report-date-filter");
    ReportView.dateInput.value = "2026-06-14";
    expect(ReportView.transactions.length).toBe(0);
    await ReportView.fetchAndRender();
    expect(ReportView.transactions.length).toBe(1);
    expect(ReportView.transactions[0].id).toBe("tx1");
  });
});
