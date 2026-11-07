const state = {
  method: "bisection",
  data: null,
  graphMode: "2d",
  activeTab: "summary",
  loading: false,
};

const methodMeta = {
  bisection: {
    title: "Bisección",
    hint: "Requiere un intervalo [xl, xu] con cambio de signo en f'(x).",
  },
  newton: {
    title: "Newton",
    hint: "Usa x0 y calcula f''(x) automáticamente para resolver f'(x)=0.",
  },
  secant: {
    title: "Secante",
    hint: "Usa dos puntos iniciales x0 y x1. No necesita f''(x).",
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

function val(id) {
  return document.getElementById(id).value.trim();
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

function showError(message) {
  const box = $("#errorBox");
  box.textContent = message;
  box.classList.remove("hidden");
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
  $("#stepsText").textContent = "Aquí aparecerá el procedimiento con fórmulas y sustituciones.";
  const table = $("#iterTable");
  table.querySelector("thead").innerHTML = "";
  table.querySelector("tbody").innerHTML = "";
  const plot = $("#plot");
  if (window.Plotly) {
    Plotly.purge(plot);
  }
  plot.innerHTML = "";
}

function readPayload() {
  if (state.method === "bisection") {
    return {
      method: "bisection",
      expr: val("b_expr"),
      xl: val("b_xl"),
      xu: val("b_xu"),
      es: val("b_es"),
      imax: val("b_imax"),
    };
  }
  if (state.method === "newton") {
    return {
      method: "newton",
      expr: val("n_expr"),
      x0: val("n_x0"),
      tol: val("n_tol"),
      max_iter: val("n_max"),
      xmin: val("n_xmin"),
      xmax: val("n_xmax"),
    };
  }
  return {
    method: "secant",
    expr: val("s_expr"),
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
  state.loading = true;
  const button = $("#calcBtn");
  button.disabled = true;
  button.textContent = "Calculando...";

  try {
    const response = await fetch("/api/solve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(readPayload()),
    });
    const data = await response.json();

    if (!response.ok || !data.success) {
      showError(data.error_message || "No se pudo resolver el problema.");
      state.data = null;
      return;
    }

    state.data = data;
    state.graphMode = "2d";
    $("#btn2d").classList.add("active");
    $("#btn3d").classList.remove("active");

    renderSummary(data);
    renderSteps(data);
    renderTable(data);
    setTab("summary");
  } catch (error) {
    showError(`Error de conexión: ${error.message}`);
    state.data = null;
  } finally {
    state.loading = false;
    button.disabled = false;
    button.textContent = "Calcular";
  }
}

function renderSummary(data) {
  const summary = data.summary;
  const finalInterval = summary.xl_final !== null && summary.xl_final !== undefined
    ? `${fmt(summary.xl_final)} a ${fmt(summary.xu_final)}`
    : "No aplica";

  const items = [
    ["x* (punto crítico)", fmt(summary.root, 10)],
    ["Iteraciones", summary.iterations],
    ["Error final ea", `${fmt(summary.error, 8)} %`],
    ["f'(x*)", fmt(summary.f_value, 8)],
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
    ? `<p class="summary-message">${escapeHtml(summary.message)}</p>`
    : "";
  const classification = summary.classification
    ? `<div class="classification">${escapeHtml(summary.classification)}</div>`
    : "";

  $("#summaryContent").innerHTML = `
    <p class="hint">Método: <strong>${escapeHtml(methodMeta[data.method].title)}</strong></p>
    <div class="summary-grid">${cards}</div>
    ${message}
    ${classification}
    <p class="hint">Recuerda: se resuelve f'(x)=0, no f(x)=0.</p>
  `;
}

function renderSteps(data) {
  $("#stepsText").textContent = data.steps_text || "Sin procedimiento.";
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

function base2DLayout(data) {
  const domain = data.graph.domain;
  const shapes = [];

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

  return {
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
      title: "f'(x)",
      gridcolor: "#243653",
      zerolinecolor: "#243653",
    },
    legend: {
      orientation: "h",
      y: -0.2,
      font: { size: 10 },
    },
  };
}

function plot2D(data) {
  const graph = data.graph;
  const traces = [];

  traces.push({
    x: graph.curve.x,
    y: graph.curve.y,
    mode: "lines",
    name: "f'(x)",
    line: { color: "#58a1d3", width: 3 },
    connectgaps: false,
  });

  traces.push({
    x: graph.domain,
    y: [0, 0],
    mode: "lines",
    name: "f'(x) = 0",
    line: { color: "#93a6c4", width: 1.4, dash: "dash" },
  });

  if (graph.iterations.length) {
    traces.push({
      x: graph.iterations.map((point) => point.x),
      y: graph.iterations.map((point) => point.y),
      mode: "lines+markers",
      name: "Iteraciones",
      line: { color: "#ff9f43", width: 1.6, dash: "dot" },
      marker: { color: "#ff9f43", size: 7 },
    });
  }

  if (graph.final && graph.final.x !== null) {
    traces.push({
      x: [graph.final.x],
      y: [graph.final.y],
      mode: "markers",
      name: `x* ≈ ${fmt(graph.final.x, 6)}`,
      marker: { color: "#2ca02c", size: 17, symbol: "star" },
    });
  }

  Plotly.react($("#plot"), traces, base2DLayout(data), {
    responsive: true,
    displaylogo: false,
    scrollZoom: false,
  });
}

function plot3D(data) {
  const graph = data.graph;
  const points = [];

  for (let index = 0; index < graph.curve.x.length; index += 1) {
    const x = graph.curve.x[index];
    const y = graph.curve.y[index];
    if (x !== null && y !== null) {
      points.push({ x, y });
    }
  }

  const xs = points.map((point) => point.x);
  const zs = points.map((point) => point.y);
  const traces = [];

  if (xs.length >= 2) {
    traces.push({
      type: "surface",
      x: xs,
      y: [-1, 1],
      z: [zs, zs],
      colorscale: [[0, "#0f4c81"], [0.55, "#2f7fb8"], [1, "#58a1d3"]],
      opacity: 0.82,
      showscale: false,
      name: "f'(x)",
      hovertemplate: "x = %{x}<br>f'(x) = %{z}<extra></extra>",
    });

    const zeroRow = xs.map(() => 0);
    traces.push({
      type: "surface",
      x: xs,
      y: [-1, 1],
      z: [zeroRow, zeroRow],
      colorscale: [[0, "#93a6c4"], [1, "#93a6c4"]],
      opacity: 0.16,
      showscale: false,
      name: "f'(x) = 0",
      hoverinfo: "skip",
    });
  }

  if (graph.iterations.length) {
    traces.push({
      type: "scatter3d",
      x: graph.iterations.map((point) => point.x),
      y: graph.iterations.map(() => 0),
      z: graph.iterations.map((point) => point.y),
      mode: "lines+markers",
      name: "Iteraciones",
      line: { color: "#ff9f43", width: 5 },
      marker: { color: "#ff9f43", size: 3.5 },
    });
  }

  if (graph.final && graph.final.x !== null) {
    traces.push({
      type: "scatter3d",
      x: [graph.final.x],
      y: [0],
      z: [graph.final.y],
      mode: "markers",
      name: "x*",
      marker: { color: "#2ca02c", size: 7, symbol: "diamond" },
    });
  }

  const axisStyle = {
    gridcolor: "#243653",
    zerolinecolor: "#243653",
    backgroundcolor: "#0b1220",
    tickfont: { color: "#93a6c4", size: 9 },
    titlefont: { color: "#e8f1ff", size: 11 },
  };

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
      yaxis: { ...axisStyle, title: "y (profundidad)", range: [-1.2, 1.2] },
      zaxis: { ...axisStyle, title: "f'(x)" },
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
  if (state.graphMode === "3d") {
    legend.textContent = "Vista 3D: superficie z = f'(x) extendida en y. La línea naranja son las iteraciones sobre y=0. La superficie transparente es f'(x)=0. La estrella verde es x*.";
    plot3D(state.data);
  } else {
    legend.textContent = "Eje x = valores de x. Eje y = f'(x). Curva azul = f'(x). Línea punteada = f'(x)=0. Puntos naranjas = iteraciones. Estrella verde = x*. Zona sombreada = intervalo inicial [xl, xu].";
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

window.addEventListener("resize", () => {
  if (state.data && state.activeTab === "graph" && window.Plotly) {
    Plotly.Plots.resize($("#plot"));
  }
});

setMethod("bisection");
