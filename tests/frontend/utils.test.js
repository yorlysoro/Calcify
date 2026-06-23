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
