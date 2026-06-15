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
    btnText.textContent = "Decrypting...";
    spinner.classList.remove("hidden");

    try {
      const response = await fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pin: pinInput.value }),
      });

      const data = await response.json();

      if (response.ok) {
        btnText.textContent = "Access Granted";
        submitBtn.classList.replace("border-cyber-500", "border-green-500");
        submitBtn.classList.replace("text-cyber-500", "text-green-500");

        setTimeout(() => {
          window.location.href = "/";
        }, 800);
      } else {
        throw new Error(data.error || "Authentication Failed");
      }
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
      btnText.textContent = "Initialize Session";
      spinner.classList.add("hidden");
      pinInput.value = "";
      pinInput.focus();
    }
  });
