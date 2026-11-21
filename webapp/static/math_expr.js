(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.normalizeMathExpr = api.normalizeMathExpr;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const aliases = { sen: "sin", abs: "Abs" };
  const functions = new Set([
    "sqrt", "sin", "cos", "tan", "ln", "log", "exp", "Abs",
    ...Object.keys(aliases),
  ]);

  function tokenize(text) {
    const tokens = [];
    let index = 0;

    while (index < text.length) {
      const char = text[index];

      if (/\s/.test(char)) {
        index += 1;
        continue;
      }

      if (/[0-9.]/.test(char)) {
        const match = text.slice(index).match(/^(?:\d+(?:\.\d*)?|\.\d+)/);
        if (match) {
          tokens.push({ kind: "value", text: match[0] });
          index += match[0].length;
          continue;
        }
      }

      if (/[A-Za-z]/.test(char)) {
        const word = text.slice(index).match(/^[A-Za-z]+/)[0];
        const key = word.toLowerCase();
        if (functions.has(key)) {
          tokens.push({ kind: "function", text: aliases[key] || key });
        } else if (word.length === 1 || ["e", "E", "pi"].includes(word)) {
          tokens.push({ kind: "value", text: word });
        } else {
          for (const letter of word) {
            tokens.push({ kind: "value", text: letter });
          }
        }
        index += word.length;
        continue;
      }

      if ("([{".includes(char)) {
        tokens.push({ kind: "open", text: char });
      } else if (")]}".includes(char)) {
        tokens.push({ kind: "close", text: char });
      } else {
        tokens.push({ kind: "operator", text: char });
      }
      index += 1;
    }

    return tokens;
  }

  function endsValue(token) {
    return token.kind === "value" || token.kind === "close";
  }

  function startsValue(token) {
    return token.kind === "value" || token.kind === "function" || token.kind === "open";
  }

  function needsMultiply(previous, current) {
    return endsValue(previous) && startsValue(current);
  }

  function normalizeMathExpr(text) {
    const cleaned = String(text ?? "")
      .replace(/−/g, "-")
      .replace(/×|·/g, "*")
      .replace(/÷/g, "/")
      .replace(/π/g, "pi")
      .replace(/√\s*\(/g, "sqrt(")
      .replace(/√\s*([A-Za-z])/g, "sqrt($1)");
    const tokens = tokenize(cleaned);
    let result = "";

    for (let index = 0; index < tokens.length; index += 1) {
      if (index && needsMultiply(tokens[index - 1], tokens[index])) {
        result += "*";
      }
      result += tokens[index].text;
    }

    return result.trim();
  }

  return { normalizeMathExpr };
});
