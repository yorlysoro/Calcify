var ConfigView = {
  init: function() {
    this.renderCurrencies();
    this.renderRates();

    var rateSelect = document.getElementById("rate-currency-code");
    rateSelect.innerHTML = "";
    App.state.currencies.forEach(function(cur) {
      var opt = document.createElement("option");
      opt.value = cur.code;
      opt.textContent = cur.code + " - " + cur.name;
      rateSelect.appendChild(opt);
    });

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
