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

var App = {
  state: {
    currentTab: "view-calculator",
    currencies: [],
    products: [],
    rates: [],
    transactions: [],
  },

  init: async function() {
    try {
      var today = new Date().toISOString().split("T")[0];
      var results = await Promise.all([
        ApiClient.get("/api/v1/currencies"),
        ApiClient.get("/api/v1/products"),
        ApiClient.get("/api/v1/rates/latest"),
        ApiClient.get("/api/v1/transactions?date=" + today),
      ]);

      this.state.currencies = results[0].data;
      this.state.products = results[1].data;
      this.state.rates = results[2].data;
      this.state.transactions = results[3].data;

      var statusText = document.getElementById("sys-status-text");
      var statusDot = document.getElementById("sys-status-dot");
      if (statusText) statusText.textContent = __("online");
      if (statusDot) statusDot.classList.replace("bg-zinc-500", "bg-emerald-500");
    } catch (error) {
      console.error("Failed to bootstrap application data:", error);
    }

    CalculatorView.init();
    InventoryView.init();
    ConfigView.init();
    ReportView.init();
    SalesView.init();

    document.querySelectorAll(".tab-btn").forEach(function(btn) {
      btn.addEventListener("click", function(e) {
        App.switchTab(e.currentTarget.dataset.target);
      });
    });
  },

  switchTab: function(targetId) {
    this.state.currentTab = targetId;
    document.querySelectorAll("main > section").forEach(function(sec) {
      sec.classList.toggle("hidden", sec.id !== targetId);
    });
    document.querySelectorAll(".tab-btn").forEach(function(btn) {
      var isActive = btn.dataset.target === targetId;
      btn.classList.toggle("text-emerald-500", isActive);
      btn.classList.toggle("border-emerald-500", isActive);
      btn.classList.toggle("text-zinc-500", !isActive);
      btn.classList.toggle("border-transparent", !isActive);
    });
  },

  refreshProducts: async function() {
    var res = await ApiClient.get("/api/v1/products");
    this.state.products = res.data;
    return this.state.products;
  },

  refreshCurrencies: async function() {
    var res = await ApiClient.get("/api/v1/currencies");
    this.state.currencies = res.data;
    return this.state.currencies;
  },

  refreshRates: async function() {
    var res = await ApiClient.get("/api/v1/rates/latest");
    this.state.rates = res.data;
    return this.state.rates;
  },
};
