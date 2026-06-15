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
      var results = await Promise.all([
        ApiClient.get("/api/v1/currencies"),
        ApiClient.get("/api/v1/products"),
        ApiClient.get("/api/v1/rates/latest"),
      ]);

      this.state.currencies = results[0].data;
      this.state.products = results[1].data;
      this.state.rates = results[2].data;

      var statusText = document.getElementById("sys-status-text");
      var statusDot = document.getElementById("sys-status-dot");
      if (statusText) statusText.textContent = "Online";
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
