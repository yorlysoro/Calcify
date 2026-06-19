var SalesView = {
  init: function() {
    this.productSelect = document.getElementById("sales-product");
    this.currencySelect = document.getElementById("sales-currency");
    this.quantityInput = document.getElementById("sales-quantity");
    this.priceInput = document.getElementById("sales-unit-price");
    this.commentInput = document.getElementById("sales-comment");
    this.messageEl = document.getElementById("sales-message");
    this.submitBtn = document.getElementById("sales-submit-btn");
    this.searchInput = document.getElementById("sales-product-search");

    this.populateSelects();
    this.searchInput.addEventListener("input", function() { this.filterProducts(); }.bind(this));
    document.getElementById("sales-form").addEventListener("submit", function(e) { this.handleSubmit(e); }.bind(this));
  },

  populateSelects: function() {
    this.productSelect.innerHTML = "";
    App.state.products.forEach(function(p) {
      var opt = document.createElement("option");
      opt.value = p.id;
      opt.textContent = p.name + " (Stock: " + p.stock_quantity + ")";
      opt.dataset.stock = p.stock_quantity;
      this.productSelect.appendChild(opt);
    }.bind(this));

    this.currencySelect.innerHTML = "";
    App.state.currencies.forEach(function(c) {
      var opt = document.createElement("option");
      opt.value = c.code;
      opt.textContent = c.code + " - " + c.name;
      this.currencySelect.appendChild(opt);
    }.bind(this));

    this.searchInput.value = "";
    this.filterProducts();
  },

  filterProducts: function() {
    var searchTerm = this.searchInput.value.toLowerCase();
    var options = this.productSelect.querySelectorAll("option");

    var visibleCount = 0;
    options.forEach(function(opt) {
      if (opt.dataset.placeholder) {
        opt.remove();
        return;
      }
      var match = opt.textContent.toLowerCase().includes(searchTerm);
      opt.style.display = match ? "" : "none";
      if (match) visibleCount++;
    });

    if (visibleCount === 0) {
      var placeholder = document.createElement("option");
      placeholder.disabled = true;
      placeholder.selected = true;
      placeholder.dataset.placeholder = "true";
      placeholder.textContent = __("no_results");
      this.productSelect.appendChild(placeholder);
    }
  },

  handleSubmit: async function(e) {
    e.preventDefault();
    this.submitBtn.disabled = true;
    this.submitBtn.textContent = __("registering");
    this.messageEl.innerHTML = "";

    var productId = this.productSelect.value;
    var quantity = parseInt(this.quantityInput.value) || 0;
    var unitPrice = this.priceInput.value;
    var currencyCode = this.currencySelect.value;
    var comment = this.commentInput.value;

    try {
      var payload = {
        product_id: productId,
        quantity: quantity,
        unit_price: unitPrice,
        currency_code: currencyCode,
        comment: comment,
      };
      await ApiClient.post("/api/v1/sales", payload);

      var results = await Promise.all([
        ApiClient.get("/api/v1/products"),
        ApiClient.get("/api/v1/transactions"),
      ]);
      App.state.products = results[0].data;
      App.state.transactions = results[1].data;

      if (typeof InventoryView !== "undefined") {
        InventoryView.render();
      }

      this.messageEl.innerHTML = '<div class="text-emerald-500 text-sm font-bold">' + __("sale_registered") + '</div>';
      document.getElementById("sales-form").reset();
      this.populateSelects();
    } catch (error) {
      this.messageEl.innerHTML = '<div class="text-red-500 text-sm">' + error.message + '</div>';
    } finally {
      this.submitBtn.disabled = false;
      this.submitBtn.textContent = __("register_sale");
    }
  },
};
