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

  it("calls ReportView.fetchAndRender after successful sale", async () => {
    ReportView = { fetchAndRender: jest.fn() };
    ConfigView = { renderMetrics: jest.fn() };
    global.fetch = jest.fn()
      .mockResolvedValueOnce({ ok: true, status: 201, headers: new Map(), json: async () => ({}) })
      .mockResolvedValueOnce({ ok: true, status: 200, headers: new Map([["content-type", "application/json"]]), json: async () => ({ data: [] }) })
      .mockResolvedValueOnce({ ok: true, status: 200, headers: new Map([["content-type", "application/json"]]), json: async () => ({ data: [] }) });
    loadGlobal("sales");
    SalesView.init();
    const event = new Event("submit", { bubbles: true, cancelable: true });
    await SalesView.handleSubmit(event);
    expect(ReportView.fetchAndRender).toHaveBeenCalled();
    expect(ConfigView.renderMetrics).toHaveBeenCalled();
  });

  it("calls InventoryView.render and ReportView.fetchAndRender after sale", async () => {
    ReportView = { fetchAndRender: jest.fn() };
    ConfigView = { renderMetrics: jest.fn() };
    global.fetch = jest.fn()
      .mockResolvedValueOnce({ ok: true, status: 201, headers: new Map(), json: async () => ({}) })
      .mockResolvedValueOnce({ ok: true, status: 200, headers: new Map([["content-type", "application/json"]]), json: async () => ({ data: [{ id: "p1", name: "Laptop", stock_quantity: 9 }] }) })
      .mockResolvedValueOnce({ ok: true, status: 200, headers: new Map([["content-type", "application/json"]]), json: async () => ({ data: [{ id: "tx1", product_id: "p1", transaction_type: "OUT", quantity: 1 }] }) });
    loadGlobal("sales");
    SalesView.init();
    const event = new Event("submit", { bubbles: true, cancelable: true });
    await SalesView.handleSubmit(event);
    expect(InventoryView.render).toHaveBeenCalled();
    expect(ReportView.fetchAndRender).toHaveBeenCalled();
    expect(ConfigView.renderMetrics).toHaveBeenCalled();
    expect(App.state.products[0].stock_quantity).toBe(9);
    expect(App.state.transactions.length).toBe(1);
  });
});
