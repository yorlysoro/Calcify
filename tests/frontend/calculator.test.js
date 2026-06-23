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
    expect(document.getElementById("calc-results").innerHTML).toContain("please_set_base");
  });

  it("handles empty currencies array", () => {
    App = { state: { currencies: [], products: [], rates: [], transactions: [] } };
    loadGlobal("calculator");
    CalculatorView.init();
    expect(document.getElementById("calc-results").innerHTML).toContain("please_set_base");
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

  it("does not duplicate event listeners when init called twice", () => {
    setupApp();
    loadGlobal("calculator");
    CalculatorView.init();
    CalculatorView.init();

    CalculatorView.render = jest.fn();

    document.getElementById("calc-input").dispatchEvent(new Event("input"));

    expect(CalculatorView.render).toHaveBeenCalledTimes(1);
  });
});
