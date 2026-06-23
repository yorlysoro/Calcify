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

var CalculatorView = {
  _eventListenersAttached: false,

  init: function() {
    this.inputEl = document.getElementById("calc-input");
    this.selectEl = document.getElementById("calc-base");
    this.resultsEl = document.getElementById("calc-results");
    this.warningEl = document.getElementById("calc-warning");

    if (!this._eventListenersAttached) {
      this.inputEl.addEventListener("input", function() { this.render(); }.bind(this));
      this.selectEl.addEventListener("change", function() { this.render(); }.bind(this));
      this._eventListenersAttached = true;
    }

    this._populateCurrencySelect();
    this.render();
  },

  _populateCurrencySelect: function() {
    this.selectEl.innerHTML = "";
    App.state.currencies.forEach(function(cur) {
      var opt = document.createElement("option");
      opt.value = cur.code;
      opt.textContent = cur.code + " - " + cur.name;
      this.selectEl.appendChild(opt);
    }.bind(this));
  },

  render: function() {
    var base = getBaseCurrency(App.state.currencies);
    if (!base) {
      this.resultsEl.innerHTML = '<div class="col-span-full text-center py-8 text-zinc-500">⚠️ ' + __("please_set_base") + ' <button onclick="App.switchTab(\'view-config\')" class="text-emerald-500 hover:underline">' + __("settings_link") + '</button> ' + __("to_use_calculator") + '</div>';
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
