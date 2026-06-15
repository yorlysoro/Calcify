var InventoryView = {
  editingId: null,

  init: function() {
    this.tbodyEl = document.getElementById("inv-table-body");
    this.cardsContainer = document.getElementById("inv-cards-container");
    this.searchInput = document.getElementById("inv-search");

    this.searchInput.addEventListener("input", function(e) {
      this.render(e.target.value);
    }.bind(this));

    this.initModal();
    this.render();
  },

  initModal: function() {
    var modal = document.getElementById("product-modal");
    var form = document.getElementById("product-form");
    var currencySelect = document.getElementById("prod-currency");
    var costInput = document.getElementById("prod-cost");
    var marginInput = document.getElementById("prod-margin");
    var previewEl = document.getElementById("live-price-preview");

    currencySelect.innerHTML = "";
    App.state.currencies.forEach(function(cur) {
      var opt = document.createElement("option");
      opt.value = cur.code;
      opt.textContent = cur.code;
      currencySelect.appendChild(opt);
    });

    function updatePreview() {
      var cost = parseFloat(costInput.value) || 0;
      var margin = parseFloat(marginInput.value) || 0;
      var salePrice = cost * (1 + margin / 100);
      previewEl.textContent = formatMoney(salePrice, currencySelect.value || "USD");
    }

    costInput.addEventListener("input", updatePreview);
    marginInput.addEventListener("input", updatePreview);
    currencySelect.addEventListener("change", updatePreview);

    document.getElementById("add-product-btn").addEventListener("click", function() {
      InventoryView.editingId = null;
      document.getElementById("modal-title").innerHTML = 'Add <strong class="font-bold text-emerald-500">Product</strong>';
      document.getElementById("save-modal-btn").textContent = "Save";
      form.reset();
      updatePreview();
      modal.classList.remove("hidden");
    });

    document.getElementById("close-modal-btn").addEventListener("click", function() {
      InventoryView.editingId = null;
      modal.classList.add("hidden");
      form.reset();
      updatePreview();
    });

    form.addEventListener("submit", async function(e) {
      e.preventDefault();
      var loader = document.getElementById("modal-loading");
      loader.classList.remove("hidden");

      var payload = {
        name: document.getElementById("prod-name").value,
        category: document.getElementById("prod-category").value.trim() || "Uncategorized",
        cost_price: costInput.value,
        cost_currency_code: currencySelect.value,
        margin_percentage: marginInput.value,
        stock_quantity: parseInt(document.getElementById("prod-stock").value) || 0,
      };

      try {
        if (InventoryView.editingId) {
          await ApiClient._request("/api/v1/products/" + InventoryView.editingId, {
            method: "PUT",
            body: JSON.stringify(payload),
          });
        } else {
          payload.id = crypto.randomUUID();
          await ApiClient.post("/api/v1/products", payload);
        }

        var res = await ApiClient.get("/api/v1/products");
        App.state.products = res.data;
        InventoryView.render();

        InventoryView.editingId = null;
        modal.classList.add("hidden");
        form.reset();
        updatePreview();
      } catch (error) {
        alert("Error saving product: " + error.message);
      } finally {
        loader.classList.add("hidden");
      }
    });
  },

  editProduct: function(id) {
    var product = App.state.products.find(function(p) { return p.id === id; });
    if (!product) return;

    this.editingId = id;
    document.getElementById("modal-title").innerHTML = 'Edit <strong class="font-bold text-emerald-500">Product</strong>';
    document.getElementById("save-modal-btn").textContent = "Update";
    document.getElementById("prod-name").value = product.name;
    document.getElementById("prod-category").value = product.category || "";
    document.getElementById("prod-cost").value = product.cost_price;
    document.getElementById("prod-currency").value = product.cost_currency_code;
    document.getElementById("prod-margin").value = product.margin_percentage;
    document.getElementById("prod-stock").value = product.stock_quantity ?? 0;

    var cost = parseFloat(product.cost_price) || 0;
    var margin = parseFloat(product.margin_percentage) || 0;
    document.getElementById("live-price-preview").textContent = formatMoney(cost * (1 + margin / 100), product.cost_currency_code);

    document.getElementById("product-modal").classList.remove("hidden");
  },

  deleteProduct: async function(id) {
    if (!confirm("Are you sure you want to delete this product?")) return;

    try {
      await ApiClient.delete("/api/v1/products/" + id);
      App.state.products = App.state.products.filter(function(p) { return p.id !== id; });
      this.render();
    } catch (error) {
      alert("Error deleting: " + error.message);
    }
  },

  render: function(filterText) {
    if (filterText === undefined) filterText = "";
    this.tbodyEl.innerHTML = "";
    this.cardsContainer.innerHTML = "";

    var filtered = App.state.products.filter(function(p) {
      return p.name.toLowerCase().includes(filterText.toLowerCase());
    });

    if (filtered.length === 0) {
      this.tbodyEl.innerHTML = '<tr><td colspan="7" class="p-8 text-center text-zinc-500">No products found.</td></tr>';
      this.cardsContainer.innerHTML = '<div class="p-8 text-center text-zinc-500 bg-zinc-900/30 rounded-lg">No products found.</div>';
      return;
    }

    filtered.forEach(function(p) {
      var cost = parseFloat(p.cost_price);
      var margin = parseFloat(p.margin_percentage);
      var salePrice = cost * (1 + margin / 100);
      var formattedCost = formatMoney(cost, p.cost_currency_code);
      var formattedSale = formatMoney(salePrice, p.cost_currency_code);

      this.tbodyEl.innerHTML += '<tr class="hover:bg-zinc-900/50 transition-colors group">' +
        '<td class="px-6 py-4 font-medium text-white">' + p.name + '</td>' +
        '<td class="px-6 py-4 text-zinc-500 text-xs">' + (p.category || "-") + '</td>' +
        '<td class="px-6 py-4 font-mono text-zinc-400">' + (p.stock_quantity ?? 0) + '</td>' +
        '<td class="px-6 py-4 font-mono text-zinc-400">' + formattedCost + '</td>' +
        '<td class="px-6 py-4 font-mono text-emerald-500">+' + p.margin_percentage + '%</td>' +
        '<td class="px-6 py-4 font-mono text-white font-bold">' + formattedSale + '</td>' +
        '<td class="px-6 py-4 text-right opacity-0 group-hover:opacity-100 transition-opacity">' +
        '<button onclick="InventoryView.editProduct(\'' + p.id + '\')" class="text-emerald-500 hover:text-emerald-400 font-bold text-xs uppercase tracking-wider mr-3">Edit</button>' +
        '<button onclick="InventoryView.deleteProduct(\'' + p.id + '\')" class="text-red-500 hover:text-red-400 font-bold text-xs uppercase tracking-wider">Delete</button>' +
        '</td></tr>';

      this.cardsContainer.innerHTML += '<div class="bg-zinc-900/80 border border-zinc-800 rounded-xl p-5 flex flex-col gap-3">' +
        '<div class="flex justify-between items-start">' +
        '<div><h4 class="text-lg font-bold text-white leading-tight">' + p.name + '</h4>' +
        '<span class="text-[0.65rem] uppercase tracking-widest text-zinc-500">' + (p.category || "-") + '</span></div>' +
        '<div class="text-right"><span class="block text-[0.65rem] text-zinc-500 uppercase tracking-widest">Sale Price</span>' +
        '<span class="font-mono font-bold text-emerald-400">' + formattedSale + '</span></div></div>' +
        '<div class="flex justify-between items-center bg-black rounded p-2 border border-zinc-800/50">' +
        '<span class="text-xs text-zinc-400 font-mono">Stock: ' + (p.stock_quantity ?? 0) + '</span>' +
        '<span class="text-xs text-zinc-400 font-mono">Cost: ' + formattedCost + '</span>' +
        '<span class="text-xs text-emerald-500 font-mono">+' + p.margin_percentage + '%</span></div>' +
        '<div class="grid grid-cols-2 gap-2 mt-2">' +
        '<button onclick="InventoryView.editProduct(\'' + p.id + '\')" class="bg-zinc-800 text-zinc-300 py-2 rounded text-xs font-bold uppercase tracking-wider">Edit</button>' +
        '<button onclick="InventoryView.deleteProduct(\'' + p.id + '\')" class="bg-red-900/20 text-red-500 border border-red-900/30 py-2 rounded text-xs font-bold uppercase tracking-wider">Delete</button>' +
        '</div></div>';
    }.bind(this));
  },
};
