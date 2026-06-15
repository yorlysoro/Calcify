const vm = require("vm");
const fs = require("fs");
const path = require("path");

function loadGlobalScript(filePath) {
  const code = fs.readFileSync(filePath, "utf-8");
  vm.runInThisContext(code, filePath);
}

const jsDir = path.resolve(__dirname, "../../static/js");
loadGlobalScript(path.join(jsDir, "utils.js"));
loadGlobalScript(path.join(jsDir, "api-client.js"));

global.loadViewScript = function(name) {
  const code = fs.readFileSync(path.join(jsDir, name + ".js"), "utf-8");
  vm.runInThisContext(code, name + ".js");
};
