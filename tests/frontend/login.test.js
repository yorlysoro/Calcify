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
    eval(loginJs);
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
