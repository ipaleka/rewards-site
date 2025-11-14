module.exports = {
  testEnvironment: "jsdom",
  testEnvironmentOptions: {
    url: "http://localhost",
    resources: "usable",
  },
  collectCoverageFrom: [
    "**/js/*.js",
    "!**/js/*.min.js",
    "!**/node_modules/**",
    "!**/coverage/**",
  ],
  coverageDirectory: "coverage",
  testMatch: ["**/?(*.)+(spec|test).js"],
  moduleFileExtensions: ["js", "jsx"],
  setupFiles: [],
};