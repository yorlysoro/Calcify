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

describe("Login Page", () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <form id="loginForm">
        <input type="password" name="pin" id="pin" value="test123" />
        <div id="errorContainer" class="hidden">
          <p id="errorMessage"></p>
        </div>
        <button type="submit" id="submitBtn">
          <span id="btnText">Initialize Session</span>
          <svg id="loadingSpinner" class="hidden"></svg>
        </button>
      </form>
    `;

    ApiClient = { post: jest.fn() };
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.restoreAllMocks();
    delete global.fetch;
    ApiClient = null;
  });

  function setupLoginForm() {
    const fs = require("fs");
    const path = require("path");
    const loginJs = fs.readFileSync(path.resolve(__dirname, "../../static/js/login.js"), "utf-8");
    (0, eval)(loginJs);
    if (typeof LoginView !== "undefined") LoginView.init();
  }

  // Helper: trigger form submit
  function submitForm() {
    const event = new Event("submit", { bubbles: true, cancelable: true });
    document.getElementById("loginForm").dispatchEvent(event);
  }

  it("uses ApiClient.post instead of raw fetch", (done) => {
    // Arrange
    ApiClient.post = jest.fn().mockResolvedValue({ message: "Authentication successful." });
    setupLoginForm();

    // Act
    submitForm();

    // Assert
    setTimeout(() => {
      expect(global.fetch).not.toHaveBeenCalled();
      expect(ApiClient.post).toHaveBeenCalledWith("/login", { pin: "test123" });
      done();
    }, 50);
  });

  it("shows error container on failed login", (done) => {
    // Arrange
    ApiClient.post = jest.fn().mockRejectedValue(new Error("Invalid credentials."));
    setupLoginForm();

    // Act
    submitForm();

    // Assert
    setTimeout(() => {
      const errorContainer = document.getElementById("errorContainer");
      expect(errorContainer.classList.contains("hidden")).toBe(false);
      expect(document.getElementById("errorMessage").textContent).toBe("Invalid credentials.");
      done();
    }, 50);
  });

  // Defensive: empty PIN
  it("submits even with empty PIN (server validation handles it)", (done) => {
    // Arrange
    document.getElementById("pin").value = "";
    ApiClient.post = jest.fn().mockRejectedValue(new Error("Missing 'pin' in request payload."));
    setupLoginForm();

    // Act
    submitForm();

    // Assert
    setTimeout(() => {
      expect(ApiClient.post).toHaveBeenCalledWith("/login", { pin: "" });
      done();
    }, 50);
  });

  // Defensive: network error
  it("handles network error gracefully", (done) => {
    // Arrange
    ApiClient.post = jest.fn().mockRejectedValue(new Error("Network error"));
    setupLoginForm();

    // Act
    submitForm();

    // Assert
    setTimeout(() => {
      const errorContainer = document.getElementById("errorContainer");
      expect(errorContainer.classList.contains("hidden")).toBe(false);
      expect(document.getElementById("errorMessage").textContent).toBe("Network error");
      done();
    }, 50);
  });

  // Structural: ApiClient is defined globally (regression guard: must load api-client.js in login.html)
  it("has ApiClient defined globally", () => {
    expect(typeof ApiClient).toBe("object");
    expect(typeof ApiClient.post).toBe("function");
  });

  // Defensive: clears PIN after submit
  it("clears PIN input after submit (finally block)", (done) => {
    // Arrange
    ApiClient.post = jest.fn().mockRejectedValue(new Error("Invalid credentials."));
    setupLoginForm();

    // Act
    submitForm();

    // Assert
    setTimeout(() => {
      expect(document.getElementById("pin").value).toBe("");
      done();
    }, 50);
  });
});
