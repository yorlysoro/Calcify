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

var ReportView = {
  transactions: [],

  init: function() {
    this.dateInput = document.getElementById("report-date-filter");
    this.exportBtn = document.getElementById("export-csv-btn");
    this.tbody = document.getElementById("report-table-body");

    this.dateInput.value = new Date().toISOString().split("T")[0];

    this.dateInput.addEventListener("change", function() { this.fetchAndRender(); }.bind(this));
    this.exportBtn.addEventListener("click", function() { this.exportCSV(); }.bind(this));

    this.fetchAndRender();
  },

  fetchAndRender: async function() {
    var date = this.dateInput.value;
    if (!date) return;

    try {
      var res = await ApiClient.get("/api/v1/transactions?date=" + date);
      this.transactions = res.data;
      this.render();
    } catch (error) {
      console.error("Failed to fetch transactions:", error.message);
      this.tbody.innerHTML = '<tr><td colspan="6" class="p-8 text-center text-zinc-500">' + __("failed_load_transactions") + '</td></tr>';
      document.getElementById("report-cards-container").innerHTML = '<div class="p-8 text-center text-zinc-500 bg-zinc-900/30 rounded-lg">' + __("failed_load_transactions") + '</div>';
    }
  },

  render: function() {
    var cardsContainer = document.getElementById("report-cards-container");
    this.tbody.innerHTML = "";
    cardsContainer.innerHTML = "";

    if (this.transactions.length === 0) {
      this.tbody.innerHTML = '<tr><td colspan="6" class="p-8 text-center text-zinc-500">' + __("no_transactions") + '</td></tr>';
      cardsContainer.innerHTML = '<div class="p-8 text-center text-zinc-500 bg-zinc-900/30 rounded-lg">' + __("no_transactions") + '</div>';
      return;
    }

    var base = getBaseCurrency(App.state.currencies);

    this.transactions.forEach(function(tx) {
      var product = App.state.products.find(function(p) { return p.id === tx.product_id; });
      var productName = product ? product.name : tx.product_id;
      var time = new Date(tx.created_at).toLocaleTimeString();

      var sourceInverse = getInverseRate(App.state.rates, base, tx.currency_code);

      var convertedCol = "";
      var convertedCards = "";
      App.state.currencies.forEach(function(cur) {
        if (cur.code === tx.currency_code) return;
        var targetInverse = getInverseRate(App.state.rates, base, cur.code);
        var converted = truncate((parseFloat(tx.unit_price) * targetInverse) / sourceInverse, 2);
        convertedCol += '<span class="block text-xs font-mono">' + cur.code + ': ' + converted.toFixed(2) + '</span>';
        convertedCards += '<span class="text-xs font-mono">' + cur.code + ': ' + converted.toFixed(2) + '</span>';
      });

      this.tbody.innerHTML += '<tr class="hover:bg-zinc-900/50 transition-colors">' +
        '<td class="px-4 py-3 font-mono text-xs text-zinc-400">' + time + '</td>' +
        '<td class="px-4 py-3 text-white">' + productName + '</td>' +
        '<td class="px-4 py-3"><span class="' + (tx.transaction_type === 'IN' ? 'text-emerald-500' : 'text-red-500') + ' font-bold">' + tx.transaction_type + '</span></td>' +
        '<td class="px-4 py-3 font-mono">' + tx.quantity + '</td>' +
        '<td class="px-4 py-3 font-mono">' + formatMoney(parseFloat(tx.unit_price), tx.currency_code) + '</td>' +
        '<td class="px-4 py-3 text-xs">' + convertedCol + '</td></tr>';

      var typeBadge = tx.transaction_type === 'IN'
        ? '<span class="text-emerald-500 font-bold">IN</span>'
        : '<span class="text-red-500 font-bold">OUT</span>';

      cardsContainer.innerHTML += '<div class="bg-zinc-900/80 border border-zinc-800 rounded-xl p-4 flex flex-col gap-2">' +
        '<div class="flex justify-between items-start">' +
        '<h4 class="font-bold text-white">' + productName + '</h4>' +
        '<span class="font-mono text-xs text-zinc-400">' + time + '</span></div>' +
        '<div class="grid grid-cols-2 gap-2 text-sm text-zinc-400">' +
        '<div><span class="text-[0.65rem] uppercase tracking-widest text-zinc-500">Type</span><br/>' + typeBadge + '</div>' +
        '<div><span class="text-[0.65rem] uppercase tracking-widest text-zinc-500">Qty</span><br/><span class="font-mono">' + tx.quantity + '</span></div>' +
        '<div><span class="text-[0.65rem] uppercase tracking-widest text-zinc-500">Unit Price</span><br/><span class="font-mono">' + formatMoney(parseFloat(tx.unit_price), tx.currency_code) + '</span></div>' +
        '<div><span class="text-[0.65rem] uppercase tracking-widest text-zinc-500">Converted</span><br/>' + convertedCards + '</div></div></div>';
    }.bind(this));
  },

  exportCSV: function() {
    var date = this.dateInput.value;
    if (this.transactions.length === 0) {
      alert(__("no_data_export"));
      return;
    }

    var base = getBaseCurrency(App.state.currencies);
    var currencyCodes = App.state.currencies.map(function(c) { return c.code; });
    var headers = ["Time", "Product Name", "Type", "Qty", "Unit Price"].concat(currencyCodes);

    var rows = this.transactions.map(function(tx) {
      var product = App.state.products.find(function(p) { return p.id === tx.product_id; });
      var productName = product ? product.name : tx.product_id;
      var time = new Date(tx.created_at).toLocaleTimeString();
      var sourceInverse = getInverseRate(App.state.rates, base, tx.currency_code);

      var converted = currencyCodes.map(function(code) {
        var targetInverse = getInverseRate(App.state.rates, base, code);
        return truncate((parseFloat(tx.unit_price) * targetInverse) / sourceInverse, 2).toFixed(2);
      });

      return [time, productName, tx.transaction_type, tx.quantity, tx.unit_price].concat(converted);
    });

    var csvString = headers.join(",") + "\n" + rows.map(function(row) {
      return row.map(function(cell) { return '"' + cell + '"'; }).join(",");
    }).join("\n");

    var blob = new Blob([csvString], { type: "text/csv;charset=utf-8;" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = "report-" + date + ".csv";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  },
};
