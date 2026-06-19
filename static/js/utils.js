if (typeof __locale === "undefined") var __locale = "en";

function formatMoney(value, currency) {
  var locale = __locale === "es" ? "es-" + __locale.toUpperCase() : "en-US";
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency: currency || "USD",
  }).format(value);
}

function truncate(value, decimals) {
  if (decimals === undefined) decimals = 4;
  var factor = Math.pow(10, decimals);
  return Math.round((value + Number.EPSILON) * factor) / factor;
}

function escapeHtml(str) {
  var div = document.createElement("div");
  div.appendChild(document.createTextNode(str));
  return div.innerHTML;
}

function formatDate(date) {
  return date.toISOString().split("T")[0];
}

function getBaseCurrency(currencies) {
  return currencies.find(function(c) { return c.is_main === true; });
}

function getInverseRate(rates, baseCurrency, code) {
  if (baseCurrency && code === baseCurrency.code) return 1.0;
  var r = rates.find(function(x) { return x.currency_code === code; });
  return r ? parseFloat(r.inverse_rate) : 1.0;
}
