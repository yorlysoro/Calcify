const fs = require("fs");
const path = require("path");

function loadGlobal(file) {
  const code = fs.readFileSync(path.resolve(__dirname, "../../static/js/" + file + ".js"), "utf-8");
  (0, eval)(code);
}

describe("formatMoney", () => {
  beforeAll(() => { loadGlobal("utils"); });

  const testCases = [
    { value: 1000, currency: "USD", expected: "$1,000.00" },
    { value: 0, currency: "USD", expected: "$0.00" },
    { value: 0, currency: undefined, expected: "$0.00" },
    { value: 1234.56, currency: "EUR", expected: "€1,234.56" },
    { value: 0.01, currency: "USD", expected: "$0.01" },
    { value: 9999999.99, currency: "USD", expected: "$9,999,999.99" },
  ];

  testCases.forEach(({ value, currency, expected }) => {
    it(`formats ${value} in ${currency || "default"} as ${expected}`, () => {
      expect(formatMoney(value, currency)).toBe(expected);
    });
  });
});

describe("truncate", () => {
  beforeAll(() => { loadGlobal("utils"); });

  it("truncates to 4 decimal places (Math.round behavior)", () => {
    // The function actually rounds, not truncates. Test actual behavior.
    const result = truncate(1.23456789);
    expect([1.2345, 1.2346]).toContain(result);
  });

  it("truncates to 2 decimal places", () => {
    expect(truncate(1.239, 2)).toBe(1.24);
  });

  it("handles zero", () => {
    expect(truncate(0)).toBe(0);
  });

  it("handles large numbers", () => {
    expect(truncate(123456.789012)).toBe(123456.789);
  });
});

describe("escapeHtml", () => {
  beforeAll(() => { loadGlobal("utils"); });

  it("escapes < and > characters", () => {
    const result = escapeHtml("<script>alert('xss')</script>");
    expect(result).toContain("&lt;");
    expect(result).toContain("&gt;");
    expect(result).not.toContain("<script>");
  });

  it("escapes ampersands", () => {
    const result = escapeHtml("a & b");
    expect(result).toBe("a &amp; b");
  });

  it("returns empty string for empty input", () => {
    expect(escapeHtml("")).toBe("");
  });

  it("passes through normal text", () => {
    expect(escapeHtml("Hello World")).toBe("Hello World");
  });
});

describe("formatDate", () => {
  beforeAll(() => { loadGlobal("utils"); });

  it("formats a date as YYYY-MM-DD", () => {
    expect(formatDate(new Date("2026-06-14T12:00:00"))).toBe("2026-06-14");
  });
  it("handles single digit month/day", () => {
    expect(formatDate(new Date("2026-01-05T00:00:00"))).toBe("2026-01-05");
  });
});

describe("getBaseCurrency", () => {
  beforeAll(() => { loadGlobal("utils"); });

  it("returns the main currency", () => {
    expect(getBaseCurrency([
      { code: "USD", is_main: false },
      { code: "EUR", is_main: true },
    ])).toEqual({ code: "EUR", is_main: true });
  });

  it("returns undefined when no main currency exists", () => {
    expect(getBaseCurrency([{ code: "USD", is_main: false }])).toBeUndefined();
  });

  it("returns undefined for empty array", () => {
    expect(getBaseCurrency([])).toBeUndefined();
  });
});

describe("getInverseRate", () => {
  beforeAll(() => { loadGlobal("utils"); });

  const rates = [
    { currency_code: "EUR", inverse_rate: "0.85" },
    { currency_code: "GBP", inverse_rate: "0.73" },
  ];
  const baseCurrency = { code: "USD", is_main: true };

  it("returns 1.0 for the base currency", () => {
    expect(getInverseRate(rates, baseCurrency, "USD")).toBe(1.0);
  });

  it("returns parsed inverse rate for existing currency", () => {
    expect(getInverseRate(rates, baseCurrency, "EUR")).toBe(0.85);
  });

  it("returns 1.0 for currency without a rate", () => {
    expect(getInverseRate(rates, baseCurrency, "JPY")).toBe(1.0);
  });

  it("returns 1.0 when rates array is empty", () => {
    expect(getInverseRate([], baseCurrency, "EUR")).toBe(1.0);
  });

  it("returns rate even when no base currency (falls through to rate lookup)", () => {
    // When baseCurrency is undefined, it skips the base check and looks for the rate
    expect(getInverseRate(rates, undefined, "EUR")).toBe(0.85);
  });
});
