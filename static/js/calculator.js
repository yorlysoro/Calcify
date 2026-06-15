var CalculatorView = {
  init: function() {
    this.inputEl = document.getElementById("calc-input");
    this.selectEl = document.getElementById("calc-base");
    this.resultsEl = document.getElementById("calc-results");
    this.warningEl = document.getElementById("calc-warning");

    this.selectEl.innerHTML = "";
    App.state.currencies.forEach(function(cur) {
      var opt = document.createElement("option");
      opt.value = cur.code;
      opt.textContent = cur.code + " - " + cur.name;
      this.selectEl.appendChild(opt);
    }.bind(this));

    this.inputEl.addEventListener("input", function() { this.render(); }.bind(this));
    this.selectEl.addEventListener("change", function() { this.render(); }.bind(this));

    this.render();
  },

  render: function() {
    var base = getBaseCurrency(App.state.currencies);
    if (!base) {
      this.resultsEl.innerHTML = '<div class="col-span-full text-center py-8 text-zinc-500">⚠️ Please set a base currency in <button onclick="App.switchTab(\'view-config\')" class="text-emerald-500 hover:underline">Settings</button> to use the calculator.</div>';
      return;
    }

    var amount = parseFloat(this.inputEl.value) || 0;
    var baseCur = this.selectEl.value || base.code;
    var sourceInverse = getInverseRate(App.state.rates, base, baseCur);

    this.resultsEl.innerHTML = "";
    if (!baseCur) return;

    App.state.currencies.forEach(function(cur) {
      if (cur.code === baseCur) return;

      var targetInverse = getInverseRate(App.state.rates, base, cur.code);
      var finalVal = truncate((amount * targetInverse) / sourceInverse);
      var exchangeRate = truncate(targetInverse / sourceInverse).toFixed(4);

      this.resultsEl.innerHTML += '<div class="bg-black border border-zinc-800 rounded-xl p-5 flex flex-col justify-between shadow-lg">' +
        '<div class="flex justify-between items-center mb-4">' +
        '<span class="text-zinc-400 text-sm font-medium tracking-widest uppercase">' + cur.code + '</span>' +
        '<span class="px-2 py-1 bg-zinc-900 rounded text-[0.65rem] text-zinc-500 font-mono border border-zinc-800">Rate: ' + exchangeRate + '</span>' +
        '</div>' +
        '<div class="text-2xl font-mono text-white truncate">' + formatMoney(finalVal, cur.code) + '</div>' +
        '</div>';
    }.bind(this));
  },
};
