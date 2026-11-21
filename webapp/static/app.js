const state = {
  method: "bisection",
  data: null,
  graphMode: "2d",
  curveMode: "both",
  inputType: "function",
  activeTab: "summary",
  loading: false,
  stepIndex: 0,
};

const methodMeta = {
  bisection: {
    title: "Bisección",
    hint: "Requiere un intervalo [xl, xu] con cambio de signo en f'(x), calculada desde f(x).",
    formulas: [
      "x_r = \\frac{x_l + x_u}{2}",
      "test = f'(x_l) \\cdot f'(x_r)",
      "ea = \\left|\\frac{x_r - x_{r,ant}}{x_r}\\right| 100\\%",
    ],
  },
  newton: {
    title: "Newton",
    hint: "Usa x0. Calcula f'(x) y f''(x) desde f(x) para resolver f'(x)=0.",
    formulas: [
      "x_{k+1} = x_k - \\frac{f'(x_k)}{f''(x_k)}",
      "ea = \\left|\\frac{x_{k+1} - x_k}{x_{k+1}}\\right| 100\\%",
    ],
  },
  secant: {
    title: "Secante",
    hint: "Usa dos puntos iniciales x0 y x1. Calcula f'(x) desde f(x).",
    formulas: [
      "x_{k+1} = x_k - f'(x_k)\\frac{x_k - x_{k-1}}{f'(x_k) - f'(x_{k-1})}",
      "ea = \\left|\\frac{x_{k+1} - x_k}{x_{k+1}}\\right| 100\\%",
    ],
  },
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

function fmt(value, digits = 8) {
  if (value === null || value === undefined) return "---";
  const number = Number(value);
  if (!Number.isFinite(number)) return "---";
  return String(Number(number.toPrecision(digits)));
}

function escapeHtml(text) {
  return String(text ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function setMath(element, latex) {
  if (!element) return;
  element.textContent = latex || "";
  if (typeof element.render === "function") {
    Promise.resolve(element.render()).catch(() => {});
  }
}

function renderLatexText(element, source) {
  if (!element) return;
  const text = source || "No se pudo analizar la función.";
  if (!window.MathLive || typeof MathLive.renderMathInElement !== "function") {
    element.textContent = text.replaceAll("\\(", "").replaceAll("\\)", "");
    return;
  }
  element.innerHTML = escapeHtml(text);
  MathLive.renderMathInElement(element, {
    delimiters: [{ left: "\\(", right: "\\)", display: false }],
  });
}

function renderMethodFormulas(container, method) {
  container.innerHTML = "";
  for (const formula of methodMeta[method].formulas) {
    const math = document.createElement("math-div");
    setMath(math, formula);
    container.append(math);
  }
}

function val(id) {
  return document.getElementById(id).value.trim();
}

function mathValue(id) {
  const field = document.getElementById(id);
  const raw = typeof field.getValue === "function"
    ? field.getValue("ascii-math")
    : (field.value || field.textContent || "");
  return normalizeMathExpr(raw);
}

function setMethod(method) {
  state.method = method;
  state.data = null;
  state.graphMode = "2d";

  $$(".method-btn").forEach((button) => {
    button.classList.toggle("active", button.dataset.method === method);
  });
  $$(".method-form").forEach((form) => {
    form.classList.toggle("active", form.dataset.method === method);
  });

  $("#formTitle").textContent = methodMeta[method].title;
  $("#formHint").textContent = methodMeta[method].hint;
  $("#btn2d").classList.add("active");
  $("#btn3d").classList.remove("active");
  hideError();
  resetOutputs();
}

function setTab(tab) {
  state.activeTab = tab;
  $$(".tab-btn").forEach((button) => {
    button.classList.toggle("active", button.dataset.tab === tab);
  });
  $$(".tab-panel").forEach((panel) => {
    panel.classList.toggle("active", panel.id === `tab-${tab}`);
  });
  if (tab === "graph") {
    requestAnimationFrame(() => renderGraph());
  }
}

function setGraphMode(mode) {
  state.graphMode = mode;
  $("#btn2d").classList.toggle("active", mode === "2d");
  $("#btn3d").classList.toggle("active", mode === "3d");
  renderGraph();
}

function setCurveMode(mode) {
  state.curveMode = mode;
  $("#btnBoth").classList.toggle("active", mode === "both");
  $("#btnOriginal").classList.toggle("active", mode === "original");
  $("#btnDerivative").classList.toggle("active", mode === "derivative");
  renderGraph();
}

function setInputType(type) {
  state.inputType = type;
  $("#btnInputFunction").classList.toggle("active", type === "function");
  $("#btnInputDerivative").classList.toggle("active", type === "derivative");
  $("#inputTypeHint").textContent = type === "function"
    ? "Escribes f(x). El sistema calcula f'(x) y f''(x)."
    : "Escribes f'(x). El sistema calcula f''(x) e integra F(x) con C=0.";
}

function stepTotal() {
  return state.data ? state.data.graph.iterations.length : 0;
}

function updateStepControls() {
  const total = stepTotal();
  $("#stepLabel").textContent = `Paso ${state.stepIndex} / ${total}`;
  $("#btnStepPrev").disabled = !state.data || state.stepIndex <= 0;
  $("#btnStepNext").disabled = !state.data || state.stepIndex >= total;
  $("#btnStepAll").disabled = !state.data || state.stepIndex >= total;
}

function setStep(delta) {
  if (!state.data) return;
  state.stepIndex = Math.max(0, Math.min(stepTotal(), state.stepIndex + delta));
  updateStepControls();
  renderGraph();
}

function setStepAll() {
  if (!state.data) return;
  state.stepIndex = stepTotal();
  updateStepControls();
  renderGraph();
}

function showError(message) {
  renderLatexText($("#errorBox"), message);
  $("#errorBox").classList.remove("hidden");
}

function hideError() {
  const box = $("#errorBox");
  box.textContent = "";
  box.classList.add("hidden");
}

function resetOutputs() {
  $("#summaryContent").innerHTML = `
    <p>Elige un método, llena los datos y presiona <strong>Calcular</strong>.</p>
  `;
  $("#stepsFormulas").innerHTML = "";
  $("#analysisText").textContent = "Presiona Calcular para analizar la función.";
  $("#stepsText").textContent = "Aquí aparecerá el procedimiento con fórmulas y sustituciones.";
  const table = $("#iterTable");
  table.querySelector("thead").innerHTML = "";
  table.querySelector("tbody").innerHTML = "";
  const plot = $("#plot");
  if (window.Plotly) {
    Plotly.purge(plot);
  }
  plot.innerHTML = "";
  updateStepControls();
}

function readPayload() {
  if (state.method === "bisection") {
    return {
      method: "bisection",
      expr: mathValue("b_expr"),
      input_type: state.inputType,
      xl: val("b_xl"),
      xu: val("b_xu"),
      es: val("b_es"),
      imax: val("b_imax"),
    };
  }
  if (state.method === "newton") {
    return {
      method: "newton",
      expr: mathValue("n_expr"),
      input_type: state.inputType,
      x0: val("n_x0"),
      tol: val("n_tol"),
      max_iter: val("n_max"),
      xmin: val("n_xmin"),
      xmax: val("n_xmax"),
    };
  }
  return {
    method: "secant",
    expr: mathValue("s_expr"),
    input_type: state.inputType,
    x0: val("s_x0"),
    x1: val("s_x1"),
    tol: val("s_tol"),
    max_iter: val("s_max"),
    xmin: val("s_xmin"),
    xmax: val("s_xmax"),
  };
}

async function calculate() {
  if (state.loading) return;
  hideError();
  state.data = null;
  state.stepIndex = 0;
  resetOutputs();
  state.loading = true;
  const button = $("#calcBtn");
  button.disabled = true;
  button.textContent = "Calculando...";

  try {
    $("#analysisText").textContent = "Analizando función...";
    const response = await fetch("/api/solve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(readPayload()),
    });
    const data = await response.json();

    if (data.analysis) {
      renderAnalysis(data);
    }
    if (!response.ok || !data.success) {
      state.data = null;
      if (data.analysis) {
        setTab("analysis");
      } else {
        showError(data.error_message || "No se pudo resolver el problema.");
      }
      return;
    }

    state.data = data;
    state.graphMode = "2d";
    $("#btn2d").classList.add("active");
    $("#btn3d").classList.remove("active");
    state.stepIndex = data.graph.iterations.length;
    updateStepControls();

    renderSummary(data);
    renderSteps(data);
    renderTable(data);
    setTab("analysis");
  } catch (error) {
    showError(`Error de conexión: ${error.message}`);
    $("#analysisText").textContent = "No se pudo analizar la función.";
    state.data = null;
  } finally {
    state.loading = false;
    button.disabled = false;
    button.textContent = "Calcular";
  }
}

function renderAnalysis(data) {
  renderLatexText($("#analysisText"), data.analysis?.text);
}

function renderSummary(data) {
  const summary = data.summary;
  const originalName = summary.original_is_antiderivative ? "F" : "f";
  const finalInterval = summary.xl_final !== null && summary.xl_final !== undefined
    ? `${fmt(summary.xl_final)} a ${fmt(summary.xu_final)}`
    : "No aplica";

  const items = [
    ["x* (punto crítico)", fmt(summary.root, 10)],
    ["Iteraciones", summary.iterations],
    ["Error final ea", `${fmt(summary.error, 8)} %`],
    [`${originalName}(x*)`, fmt(summary.original_value, 8)],
    ["f'(x*)", fmt(summary.derivative_value ?? summary.f_value, 8)],
    ["f''(x*)", fmt(summary.second_derivative, 8)],
    ["Clasificación", summary.critical_type || "inconcluso"],
    ["Intervalo final", finalInterval],
    ["Convergió", summary.converged ? "Sí" : "No"],
  ];

  const cards = items.map(([label, value]) => `
    <div class="summary-item">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value)}</strong>
    </div>
  `).join("");

  const message = summary.message
    ? '<p class="summary-message" id="summaryMessage"></p>'
    : "";
  const classification = summary.classification
    ? '<div class="classification" id="summaryClassification"></div>'
    : "";

  const originalLabel = summary.original_is_antiderivative
    ? "F(x) (C=0)"
    : "f(x)";
  const formulas = `
    <div class="summary-formulas">
      <p><math-span id="summaryInputLabel"></math-span></p>
      <p><math-span id="summaryOriginalLabel"></math-span> = <math-span id="summaryOriginal"></math-span></p>
      <p><math-span>f'(x)</math-span> = <math-span id="summaryDerivative"></math-span></p>
      <p><math-span>f''(x)</math-span> = <math-span id="summarySecond"></math-span></p>
    </div>
  `;

  $("#summaryContent").innerHTML = `
    <p class="hint">Método: <strong>${escapeHtml(methodMeta[data.method].title)}</strong></p>
    ${formulas}
    <div class="summary-grid">${cards}</div>
    ${message}
    ${classification}
    <p class="hint">Recuerda: se resuelve f'(x)=0, no f(x)=0.</p>
  `;
  const latex = data.latex || {};
  setMath($("#summaryInputLabel"), summary.input_type === "derivative" ? "f'(x)" : "f(x)");
  setMath($("#summaryOriginalLabel"), latex.original_label || originalLabel);
  setMath($("#summaryOriginal"), latex.original || summary.original_expr);
  setMath($("#summaryDerivative"), latex.derivative || summary.derivative_expr);
  setMath($("#summarySecond"), latex.second_derivative || summary.second_derivative_expr);
  renderLatexText($("#summaryMessage"), summary.message);
  renderLatexText($("#summaryClassification"), summary.classification);
}

function renderSteps(data) {
  renderMethodFormulas($("#stepsFormulas"), data.method);
  renderLatexText($("#stepsText"), data.steps_text || "Sin procedimiento.");
}

function renderTable(data) {
  const table = $("#iterTable");
  const thead = table.querySelector("thead");
  const tbody = table.querySelector("tbody");

  let headers = [];
  let rowBuilder = null;

  if (data.method === "bisection") {
    headers = ["Iter", "xl", "xu", "xr", "fp(xl)", "fp(xr)", "test", "ea (%)"];
    rowBuilder = (row) => [
      row.iter,
      fmt(row.xl),
      fmt(row.xu),
      fmt(row.xr),
      fmt(row.fp_xl),
      fmt(row.fp_xr),
      fmt(row.test),
      fmt(row.ea),
    ];
  } else if (data.method === "newton") {
    headers = ["Iter", "x_i", "fp(x_i)", "fpp(x_i)", "ea (%)"];
    rowBuilder = (row) => [
      row.iter,
      fmt(row.x),
      fmt(row.fp),
      fmt(row.fpp),
      fmt(row.ea),
    ];
  } else {
    headers = ["Iter", "x_i", "fp(x_i)", "ea (%)"];
    rowBuilder = (row) => [
      row.iter,
      fmt(row.x),
      fmt(row.fp),
      fmt(row.ea),
    ];
  }

  thead.innerHTML = `<tr>${headers.map((header) => `<th>${escapeHtml(header)}</th>`).join("")}</tr>`;
  tbody.innerHTML = data.table.map((row) => {
    const cells = rowBuilder(row).map((cell) => `<td>${escapeHtml(cell)}</td>`).join("");
    return `<tr>${cells}</tr>`;
  }).join("");
}

function curveData(graph, key) {
  if (key === "original") {
    return graph.original_curve || { x: [], y: [] };
  }
  return graph.derivative_curve || graph.curve || { x: [], y: [] };
}

function base2DLayout(data, curveMode) {
  const domain = data.graph.domain;
  const shapes = [];
  const showOriginal = curveMode !== "derivative";
  const showDerivative = curveMode !== "original";
  const both = showOriginal && showDerivative;

  if (data.graph.initial_interval) {
    shapes.push({
      type: "rect",
      xref: "x",
      yref: "paper",
      x0: data.graph.initial_interval[0],
      x1: data.graph.initial_interval[1],
      y0: 0,
      y1: 1,
      fillcolor: "rgba(88, 161, 211, 0.12)",
      line: { width: 0 },
      layer: "below",
    });
  }

  const layout = {
    paper_bgcolor: "#0b1220",
    plot_bgcolor: "#0b1220",
    font: { color: "#e8f1ff", family: "Inter, system-ui, sans-serif" },
    margin: { l: 56, r: 18, t: 26, b: 52 },
    hovermode: "closest",
    shapes,
    xaxis: {
      title: "x",
      gridcolor: "#243653",
      zerolinecolor: "#243653",
      range: [domain[0], domain[1]],
    },
    yaxis: {
      title: showOriginal ? "f(x)" : "f'(x)",
      titlefont: { color: showOriginal ? "#2ca02c" : "#58a1d3" },
      gridcolor: "#243653",
      zerolinecolor: "#243653",
    },
    legend: {
      orientation: "h",
      y: -0.2,
      font: { size: 10 },
    },
  };

  if (both) {
    layout.yaxis2 = {
      title: "f'(x)",
      titlefont: { color: "#58a1d3" },
      overlaying: "y",
      side: "right",
      showgrid: false,
      zerolinecolor: "#243653",
    };
  }

  return layout;
}

function plot2D(data) {
  const graph = data.graph;
  const mode = state.curveMode;
  const showOriginal = mode !== "derivative";
  const showDerivative = mode !== "original";
  const both = showOriginal && showDerivative;
  const originalCurve = curveData(graph, "original");
  const derivativeCurve = curveData(graph, "derivative");
  const shown = graph.iterations.slice(0, state.stepIndex);
  const current = shown.length ? shown[shown.length - 1] : null;
  const traces = [];

  if (showOriginal) {
    traces.push({
      x: originalCurve.x,
      y: originalCurve.y,
      mode: "lines",
      name: graph.original_label || "f(x)",
      line: { color: "#2ca02c", width: 3 },
      connectgaps: false,
    });
  }

  if (showDerivative) {
    traces.push({
      x: derivativeCurve.x,
      y: derivativeCurve.y,
      mode: "lines",
      name: graph.derivative_label || "f'(x)",
      yaxis: both ? "y2" : "y",
      line: { color: "#58a1d3", width: 3 },
      connectgaps: false,
    });

    traces.push({
      x: graph.domain,
      y: [0, 0],
      mode: "lines",
      name: "f'(x) = 0",
      yaxis: both ? "y2" : "y",
      line: { color: "#93a6c4", width: 1.4, dash: "dash" },
    });
  }

  if (shown.length) {
    const useOriginal = mode === "original";
    traces.push({
      x: shown.map((point) => point.x),
      y: shown.map((point) => (
        useOriginal ? point.original_y : point.y
      )),
      mode: "lines+markers",
      name: useOriginal ? "Iteraciones sobre f(x)" : "Iteraciones sobre f'(x)",
      yaxis: useOriginal ? "y" : (both ? "y2" : "y"),
      line: { color: "#ff9f43", width: 1.6, dash: "dot" },
      marker: { color: "#ff9f43", size: 7 },
    });

    if (both) {
      traces.push({
        x: shown.map((point) => point.x),
        y: shown.map((point) => point.original_y),
        mode: "markers",
        name: "Iteraciones sobre f(x)",
        yaxis: "y",
        marker: { color: "#2ca02c", size: 5, opacity: 0.55 },
        hoverinfo: "skip",
        showlegend: false,
      });
    }
  }

  if (current && current.segment && showDerivative) {
    traces.push({
      x: [current.segment[0], current.segment[2]],
      y: [current.segment[1], current.segment[3]],
      mode: "lines",
      name: "Recta del paso actual",
      yaxis: both ? "y2" : "y",
      line: { color: "#e74c3c", width: 2.4 },
      hoverinfo: "skip",
      showlegend: false,
    });
  }

  if (graph.final && graph.final.x !== null
      && state.stepIndex >= graph.iterations.length) {
    if (showOriginal) {
      traces.push({
        x: [graph.final.x],
        y: [graph.final.original_y],
        mode: "markers",
        name: `x* ≈ ${fmt(graph.final.x, 6)} sobre f(x)`,
        yaxis: "y",
        marker: { color: "#2ca02c", size: 17, symbol: "star" },
      });
    }
    if (showDerivative) {
      traces.push({
        x: [graph.final.x],
        y: [graph.final.y],
        mode: "markers",
        name: `x* ≈ ${fmt(graph.final.x, 6)} sobre f'(x)`,
        yaxis: both ? "y2" : "y",
        marker: { color: "#2ca02c", size: 17, symbol: "star" },
      });
    }
  }

  const layout = base2DLayout(data, mode);
  if (current && current.bracket) {
    layout.shapes.push({
      type: "rect",
      xref: "x",
      yref: "paper",
      x0: current.bracket[0],
      x1: current.bracket[1],
      y0: 0,
      y1: 1,
      fillcolor: "rgba(255, 159, 67, 0.16)",
      line: { color: "#ff9f43", width: 1.2 },
      layer: "below",
    });
  }

  Plotly.react($("#plot"), traces, layout, {
    responsive: true,
    displaylogo: false,
    scrollZoom: false,
  });
}

function surfacePoints(curve) {
  const xs = [];
  const zs = [];
  for (let index = 0; index < curve.x.length; index += 1) {
    const x = curve.x[index];
    const y = curve.y[index];
    if (x !== null && y !== null) {
      xs.push(x);
      zs.push(y);
    }
  }
  return { xs, zs };
}

function plot3D(data) {
  const graph = data.graph;
  const mode = state.curveMode;
  const showOriginal = mode !== "derivative";
  const showDerivative = mode !== "original";
  const both = showOriginal && showDerivative;
  const originalCurve = curveData(graph, "original");
  const derivativeCurve = curveData(graph, "derivative");
  const originalBand = both ? [-0.9, -0.3] : [-1, 1];
  const derivativeBand = both ? [0.3, 0.9] : [-1, 1];
  const originalY = both ? -0.6 : 0;
  const derivativeY = both ? 0.6 : 0;
  const traces = [];

  if (showOriginal) {
    const original = surfacePoints(originalCurve);
    if (original.xs.length >= 2) {
      traces.push({
        type: "surface",
        x: original.xs,
        y: originalBand,
        z: [original.zs, original.zs],
        colorscale: [[0, "#0f4c2a"], [0.55, "#1f7a3d"], [1, "#2ca02c"]],
        opacity: 0.82,
        showscale: false,
        name: graph.original_label || "f(x)",
        hovertemplate: "x = %{x}<br>f(x) = %{z}<extra></extra>",
      });
    }
  }

  if (showDerivative) {
    const derivative = surfacePoints(derivativeCurve);
    if (derivative.xs.length >= 2) {
      traces.push({
        type: "surface",
        x: derivative.xs,
        y: derivativeBand,
        z: [derivative.zs, derivative.zs],
        colorscale: [[0, "#0f4c81"], [0.55, "#2f7fb8"], [1, "#58a1d3"]],
        opacity: 0.82,
        showscale: false,
        name: graph.derivative_label || "f'(x)",
        hovertemplate: "x = %{x}<br>f'(x) = %{z}<extra></extra>",
      });

      const zeroRow = derivative.xs.map(() => 0);
      traces.push({
        type: "surface",
        x: derivative.xs,
        y: derivativeBand,
        z: [zeroRow, zeroRow],
        colorscale: [[0, "#93a6c4"], [1, "#93a6c4"]],
        opacity: 0.16,
        showscale: false,
        name: "f'(x) = 0",
        hoverinfo: "skip",
      });
    }
  }

  if (graph.iterations.length) {
    const useOriginal = mode === "original";
    traces.push({
      type: "scatter3d",
      x: graph.iterations.map((point) => point.x),
      y: graph.iterations.map(() => (useOriginal ? 0 : derivativeY)),
      z: graph.iterations.map((point) => (
        useOriginal ? point.original_y : point.y
      )),
      mode: "lines+markers",
      name: useOriginal ? "Iteraciones sobre f(x)" : "Iteraciones sobre f'(x)",
      line: { color: "#ff9f43", width: 5 },
      marker: { color: "#ff9f43", size: 3.5 },
    });
  }

  if (graph.final && graph.final.x !== null) {
    if (showOriginal) {
      traces.push({
        type: "scatter3d",
        x: [graph.final.x],
        y: [originalY],
        z: [graph.final.original_y],
        mode: "markers",
        name: "x* sobre f(x)",
        marker: { color: "#2ca02c", size: 7, symbol: "diamond" },
      });
    }
    if (showDerivative) {
      traces.push({
        type: "scatter3d",
        x: [graph.final.x],
        y: [derivativeY],
        z: [graph.final.y],
        mode: "markers",
        name: "x* sobre f'(x)",
        marker: { color: "#2ca02c", size: 7, symbol: "diamond" },
      });
    }
  }

  const axisStyle = {
    gridcolor: "#243653",
    zerolinecolor: "#243653",
    backgroundcolor: "#0b1220",
    tickfont: { color: "#93a6c4", size: 9 },
    titlefont: { color: "#e8f1ff", size: 11 },
  };

  const zTitle = both ? "f(x) / f'(x)" : (showOriginal ? "f(x)" : "f'(x)");
  const layout = {
    paper_bgcolor: "#0b1220",
    plot_bgcolor: "#0b1220",
    font: { color: "#e8f1ff", family: "Inter, system-ui, sans-serif" },
    margin: { l: 0, r: 0, t: 10, b: 0 },
    showlegend: true,
    legend: { orientation: "h", y: 0, font: { size: 10 } },
    scene: {
      bgcolor: "#0b1220",
      xaxis: { ...axisStyle, title: "x" },
      yaxis: {
        ...axisStyle,
        title: both ? "f(x) ↔ f'(x)" : "profundidad",
        range: [-1.2, 1.2],
      },
      zaxis: { ...axisStyle, title: zTitle },
      camera: { eye: { x: 1.55, y: 1.55, z: 1.05 } },
    },
  };

  Plotly.react($("#plot"), traces, layout, {
    responsive: true,
    displaylogo: false,
    scrollZoom: false,
  });
}

function renderGraph() {
  if (!state.data) {
    $("#plot").innerHTML = '<p class="legend">Calcula primero para ver la gráfica.</p>';
    return;
  }
  if (!window.Plotly) {
    $("#plot").innerHTML = '<p class="legend">No se pudo cargar Plotly. Revisa tu conexión a internet.</p>';
    return;
  }

  const legend = $("#graphLegend");
  const modeLabel = state.curveMode === "both"
    ? "Ambas curvas"
    : (state.curveMode === "original" ? "Solo f(x)" : "Solo f'(x)");
  if (state.graphMode === "3d") {
    legend.textContent = `${modeLabel}. Vista 3D: verde = f(x) o F(x), azul = f'(x). `
      + "En Ambas las superficies se separan en bandas. La línea naranja son "
      + "las iteraciones y la estrella verde es x*.";
    plot3D(state.data);
  } else {
    legend.textContent = `${modeLabel}. Eje x = valores de x. `
      + "En Ambas, eje izquierdo = f(x) o F(x) (verde) y eje derecho = f'(x) (azul). "
      + "Línea punteada = f'(x)=0. Puntos naranjas = iteraciones. "
      + "Línea roja = recta del paso actual (tangente en Newton, secante en Secante). "
      + "Rectángulo naranja = intervalo [xl, xu] del paso actual en Bisección. "
      + "Estrella verde = x*. Zona sombreada = intervalo inicial [xl, xu].";
    plot2D(state.data);
  }
}

$$(".method-btn").forEach((button) => {
  button.addEventListener("click", () => setMethod(button.dataset.method));
});

$$(".tab-btn").forEach((button) => {
  button.addEventListener("click", () => setTab(button.dataset.tab));
});

$("#calcBtn").addEventListener("click", calculate);
$("#btn2d").addEventListener("click", () => setGraphMode("2d"));
$("#btn3d").addEventListener("click", () => setGraphMode("3d"));
$("#btnBoth").addEventListener("click", () => setCurveMode("both"));
$("#btnOriginal").addEventListener("click", () => setCurveMode("original"));
$("#btnDerivative").addEventListener("click", () => setCurveMode("derivative"));
$("#btnInputFunction").addEventListener("click", () => setInputType("function"));
$("#btnInputDerivative").addEventListener("click", () => setInputType("derivative"));
$("#btnStepPrev").addEventListener("click", () => setStep(-1));
$("#btnStepNext").addEventListener("click", () => setStep(1));
$("#btnStepAll").addEventListener("click", setStepAll);

window.addEventListener("resize", () => {
  if (state.data && state.activeTab === "graph" && window.Plotly) {
    Plotly.Plots.resize($("#plot"));
  }
});

function init() {
  const mathfieldClass = window.MathfieldElement || window.MathLive?.MathfieldElement;
  if (mathfieldClass) {
    mathfieldClass.soundsDirectory = null;
  }
  setMethod("bisection");
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init, { once: true });
} else {
  init();
}
