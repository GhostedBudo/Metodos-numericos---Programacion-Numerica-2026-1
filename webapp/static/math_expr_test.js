const assert = require("node:assert/strict");
const { normalizeMathExpr } = require("./math_expr.js");

const cases = [
  ["x^3-3x", "x^3-3*x"],
  ["2(x + 1)", "2*(x+1)"],
  ["(x+1)(x-1)", "(x+1)*(x-1)"],
  ["sqrt(x)/2", "sqrt(x)/2"],
  ["sen(x)", "sin(x)"],
  ["2π", "2*pi"],
  ["2×sin(x)", "2*sin(x)"],
  ["e^x", "e^x"],
];

for (const [input, expected] of cases) {
  assert.equal(normalizeMathExpr(input), expected);
}

console.log("Pruebas de expresión matemática: OK");
