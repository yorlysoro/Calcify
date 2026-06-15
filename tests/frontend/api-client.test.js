const fs = require("fs");
const path = require("path");

function loadGlobal(file) {
  const code = fs.readFileSync(path.resolve(__dirname, "../../static/js/" + file + ".js"), "utf-8");
  (0, eval)(code);
}

describe("ApiClient", () => {
  beforeAll(() => { loadGlobal("utils"); loadGlobal("api-client"); });

  beforeEach(() => { global.fetch = jest.fn(); });
  afterEach(() => { jest.restoreAllMocks(); delete global.fetch; });

  describe("get()", () => {
    it("performs a successful GET request and returns JSON", async () => {
      global.fetch = jest.fn().mockResolvedValue({
        status: 200, ok: true,
        headers: new Map([["content-type", "application/json"]]),
        json: async () => ({ data: [] }),
      });
      const result = await ApiClient.get("/api/v1/products");
      expect(result).toEqual({ data: [] });
    });

    it("throws on non-OK response", async () => {
      global.fetch = jest.fn().mockResolvedValue({
        status: 500, ok: false,
        headers: new Map([["content-type", "application/json"]]),
        json: async () => ({ error: "Server Error" }),
      });
      await expect(ApiClient.get("/api/v1/error")).rejects.toThrow("Server Error");
    });

    it("throws on network error", async () => {
      global.fetch = jest.fn().mockRejectedValue(new Error("Network failed"));
      await expect(ApiClient.get("/api/v1/test")).rejects.toThrow("Network failed");
    });

    it("handles empty JSON response", async () => {
      global.fetch = jest.fn().mockResolvedValue({
        status: 200, ok: true,
        headers: new Map([["content-type", "application/json"]]),
        json: async () => ({}),
      });
      const result = await ApiClient.get("/api/v1/empty");
      expect(result).toEqual({});
    });
  });

  describe("post()", () => {
    it("performs a POST request with JSON body", async () => {
      const payload = { name: "Test" };
      global.fetch = jest.fn().mockResolvedValue({
        status: 201, ok: true,
        headers: new Map([["content-type", "application/json"]]),
        json: async () => ({ message: "Created" }),
      });
      const result = await ApiClient.post("/api/v1/products", payload);
      expect(result).toEqual({ message: "Created" });
    });

    it("sends POST with empty object", async () => {
      global.fetch = jest.fn().mockResolvedValue({
        status: 200, ok: true,
        headers: new Map([["content-type", "application/json"]]),
        json: async () => ({}),
      });
      const result = await ApiClient.post("/api/v1/empty", {});
      expect(result).toEqual({});
    });
  });

  describe("delete()", () => {
    it("performs a DELETE request", async () => {
      global.fetch = jest.fn().mockResolvedValue({
        status: 200, ok: true,
        headers: new Map([["content-type", "application/json"]]),
        json: async () => ({ message: "Deleted" }),
      });
      const result = await ApiClient.delete("/api/v1/products/123");
      expect(result).toEqual({ message: "Deleted" });
    });
  });

  describe("put()", () => {
    it("performs a PUT request with JSON body", async () => {
      global.fetch = jest.fn().mockResolvedValue({
        status: 200, ok: true,
        headers: new Map([["content-type", "application/json"]]),
        json: async () => ({ message: "Updated" }),
      });
      const result = await ApiClient.put("/api/v1/products/123", { name: "Updated" });
      expect(result).toEqual({ message: "Updated" });
    });
  });
});
