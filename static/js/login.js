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

var LoginView = {
  init: function() {
    document.getElementById("loginForm").addEventListener("submit", function(e) {
      LoginView.handleLogin(e);
    });
  },

  handleLogin: async function(e) {
    e.preventDefault();

    var pinInput = document.getElementById("pin");
    var errorContainer = document.getElementById("errorContainer");
    var errorMessage = document.getElementById("errorMessage");
    var btnText = document.getElementById("btnText");
    var spinner = document.getElementById("loadingSpinner");
    var submitBtn = document.getElementById("submitBtn");

    errorContainer.classList.add("hidden");
    submitBtn.disabled = true;
    btnText.textContent = __("decrypting");
    spinner.classList.remove("hidden");

    try {
      var data = await ApiClient.post("/login", { pin: pinInput.value });

      btnText.textContent = __("access_granted");
      submitBtn.classList.replace("border-cyber-500", "border-green-500");
      submitBtn.classList.replace("text-cyber-500", "text-green-500");

      setTimeout(function() {
        window.location.href = "/";
      }, 800);
    } catch (error) {
      errorMessage.textContent = error.message;
      errorContainer.classList.remove("hidden");

      pinInput.classList.add("translate-x-1", "border-red-500");
      setTimeout(function() { pinInput.classList.remove("translate-x-1"); }, 100);
      setTimeout(function() { pinInput.classList.add("-translate-x-1"); }, 200);
      setTimeout(function() {
        pinInput.classList.remove("-translate-x-1", "border-red-500");
      }, 300);
    } finally {
      submitBtn.disabled = false;
      btnText.textContent = __("init_session");
      spinner.classList.add("hidden");
      pinInput.value = "";
      pinInput.focus();
    }
  }
};

LoginView.init();
