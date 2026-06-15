module.exports = {
  testEnvironment: "jsdom",
  rootDir: "../../",
  testMatch: ["<rootDir>/tests/frontend/**/*.test.js"],
  setupFiles: ["<rootDir>/tests/frontend/setup.js"],
  moduleNameMapper: {
    "\\.css$": "<rootDir>/tests/frontend/__mocks__/styleMock.js",
  },
};
