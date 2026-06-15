function showToast(message, type) {
  if (!type) type = "success";
  var colors = {
    success: "bg-emerald-600",
    error: "bg-red-600",
    warning: "bg-amber-600",
    info: "bg-blue-600",
  };
  var toast = document.createElement("div");
  toast.className = "fixed bottom-4 right-4 z-50 " + (colors[type] || colors.info) + " text-white px-4 py-2 rounded-lg shadow-2xl text-sm font-bold transition-all duration-300";
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(function() {
    toast.style.opacity = "0";
    setTimeout(function() { toast.remove(); }, 300);
  }, 3000);
}
