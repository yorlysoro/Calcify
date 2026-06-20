document
  .getElementById("loginForm")
  .addEventListener("submit", async (e) => {
    e.preventDefault();

    const pinInput = document.getElementById("pin");
    const errorContainer = document.getElementById("errorContainer");
    const errorMessage = document.getElementById("errorMessage");
    const btnText = document.getElementById("btnText");
    const spinner = document.getElementById("loadingSpinner");
    const submitBtn = document.getElementById("submitBtn");

    errorContainer.classList.add("hidden");
    submitBtn.disabled = true;
    btnText.textContent = __("decrypting");
    spinner.classList.remove("hidden");

    try {
      const data = await ApiClient.post("/login", { pin: pinInput.value });

      btnText.textContent = __("access_granted");
      submitBtn.classList.replace("border-cyber-500", "border-green-500");
      submitBtn.classList.replace("text-cyber-500", "text-green-500");

      setTimeout(() => {
        window.location.href = "/";
      }, 800);
    } catch (error) {
      errorMessage.textContent = error.message;
      errorContainer.classList.remove("hidden");

      pinInput.classList.add("translate-x-1", "border-red-500");
      setTimeout(() => pinInput.classList.remove("translate-x-1"), 100);
      setTimeout(() => pinInput.classList.add("-translate-x-1"), 200);
      setTimeout(
        () => pinInput.classList.remove("-translate-x-1", "border-red-500"),
        300,
      );
    } finally {
      submitBtn.disabled = false;
      btnText.textContent = __("init_session");
      spinner.classList.add("hidden");
      pinInput.value = "";
      pinInput.focus();
    }
  });
