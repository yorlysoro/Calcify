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

var ConfigView = {
  init: function() {
    this.renderCurrencies();
    this.renderRates();
    this.renderMetrics();
    this._populateRateCurrencySelect();

    document.getElementById("config-currency-form").addEventListener("submit", async function(e) {
      e.preventDefault();
      var btn = document.getElementById("config-currency-btn");
      btn.disabled = true;

      var payload = {
        code: document.getElementById("cur-code").value,
        name: document.getElementById("cur-name").value,
        symbol: document.getElementById("cur-symbol").value,
      };

      try {
        await ApiClient.post("/api/v1/currencies", payload);
        var res = await ApiClient.get("/api/v1/currencies");
        App.state.currencies = res.data;
        ConfigView.renderCurrencies();
        ConfigView._populateRateCurrencySelect();
        document.getElementById("config-currency-form").reset();
        CalculatorView.init();
        InventoryView.initModal();
      } catch (error) {
        alert(__("error_adding_currency") + " " + error.message);
      } finally {
        btn.disabled = false;
      }
    });

    document.getElementById("config-rate-form").addEventListener("submit", async function(e) {
      e.preventDefault();
      var btn = document.getElementById("config-rate-btn");
      btn.disabled = true;

      var payload = {
        currency_code: document.getElementById("rate-currency-code").value,
        rate: document.getElementById("rate-value").value,
      };

      try {
        await ApiClient.post("/api/v1/rates", payload);
        var res = await ApiClient.get("/api/v1/rates/latest");
        App.state.rates = res.data;
        document.getElementById("config-rate-form").reset();
        ConfigView.renderRates();
        CalculatorView.render();
      } catch (error) {
        alert(__("error_adding_rate") + " " + error.message);
      } finally {
        btn.disabled = false;
      }
    });

    document.getElementById("config-export-btn").addEventListener("click", function() {
      window.open("/api/v1/backup/export", "_blank");
    });
  },

  renderCurrencies: function() {
    var container = document.getElementById("config-currency-list");
    container.innerHTML = "";
    App.state.currencies.forEach(function(cur) {
      var card = document.createElement("div");
      card.className = "bg-black border border-zinc-800 rounded-lg p-4 text-center";
      var inner = '<div class="text-2xl mb-1">' + cur.symbol + '</div>' +
        '<div class="font-mono font-bold text-emerald-400 text-sm">' + cur.code + '</div>' +
        '<div class="text-xs text-zinc-500 truncate">' + cur.name + '</div>';
      if (cur.is_main) {
        inner += '<div class="text-[0.6rem] uppercase tracking-widest text-amber-500 mt-1">' + __("main") + '</div>';
      } else {
        inner += '<button onclick="ConfigView.setMainCurrency(\'' + cur.code + '\')" class="text-[0.6rem] uppercase tracking-widest text-emerald-500 hover:text-emerald-400 mt-1">' + __("set_base") + '</button>';
      }
      card.innerHTML = inner;
      container.appendChild(card);
    });
  },

  setMainCurrency: async function(code) {
    try {
      await ApiClient.put("/api/v1/currencies/" + code + "/set_main");
      var res = await ApiClient.get("/api/v1/currencies");
      App.state.currencies = res.data;
      this.renderCurrencies();
      CalculatorView.init();
    } catch (error) {
      alert(__("error_setting_base") + " " + error.message);
    }
  },

  renderRates: function() {
    var container = document.getElementById("config-rates-list");
    container.innerHTML = "";
    if (App.state.rates.length === 0) {
      container.innerHTML = '<div class="text-zinc-600 text-sm text-center py-4">' + __("no_rates") + '</div>';
      return;
    }
    App.state.rates.forEach(function(r) {
      var row = document.createElement("div");
      row.className = "bg-black border border-zinc-800 rounded-lg px-4 py-3 flex items-center justify-between";
      row.innerHTML = '<div><span class="font-mono font-bold text-emerald-400 text-sm">' + r.currency_code + '</span>' +
        '<span class="font-mono text-white text-sm ml-3">' + r.rate + '</span></div>' +
        '<button onclick="ConfigView.deleteRate(\'' + r.id + '\')" class="text-red-500 hover:text-red-400 text-xs font-bold uppercase tracking-wider">' + __("delete_rate") + '</button>';
      container.appendChild(row);
    });
  },

  renderMetrics: function() {
    var today = new Date().toISOString().split("T")[0];
    var dateEl = document.getElementById("report-date");
    if (dateEl) dateEl.textContent = today;

    var todayTx = App.state.transactions.filter(function(tx) {
      return tx.created_at && tx.created_at.slice(0, 10) === today;
    });

    var totalPurchases = 0;
    var totalSales = 0;
    todayTx.forEach(function(tx) {
      var total = parseFloat(tx.unit_price) * tx.quantity;
      if (tx.transaction_type === "IN") {
        totalPurchases += total;
      } else if (tx.transaction_type === "OUT") {
        totalSales += total;
      }
    });
    var profit = totalSales - totalPurchases;
    var baseObj = getBaseCurrency(App.state.currencies);
    var baseCurrency = baseObj ? baseObj.code : "USD";

    var elPurchases = document.getElementById("metric-purchases");
    var elSales = document.getElementById("metric-sales");
    var elProfit = document.getElementById("metric-profit");
    if (elPurchases) elPurchases.textContent = formatMoney(totalPurchases, baseCurrency);
    if (elSales) elSales.textContent = formatMoney(totalSales, baseCurrency);
    if (elProfit) elProfit.textContent = formatMoney(profit, baseCurrency);
  },

  _populateRateCurrencySelect: function() {
    var rateSelect = document.getElementById("rate-currency-code");
    if (!rateSelect) return;
    rateSelect.innerHTML = "";
    App.state.currencies.forEach(function(cur) {
      var opt = document.createElement("option");
      opt.value = cur.code;
      opt.textContent = cur.code + " - " + cur.name;
      rateSelect.appendChild(opt);
    });
  },

  deleteRate: async function(id) {
    if (!confirm(__("delete_confirm"))) return;
    try {
      await ApiClient.delete("/api/v1/rates/" + id);
      var res = await ApiClient.get("/api/v1/rates/latest");
      App.state.rates = res.data;
      this.renderRates();
      CalculatorView.render();
    } catch (error) {
      alert(__("error_deleting_rate") + " " + error.message);
    }
  },
};
