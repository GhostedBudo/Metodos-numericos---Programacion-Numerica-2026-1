import customtkinter as ctk #pyright: ignore
from tkinter import messagebox
import numpy as np #pyright: ignore
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from lib.bisection_method import BisectionMethod
from lib.optimization_utils import (
    build_function_spec, evaluate_curve, evaluate_expression,
)
from gui.components.sidebar import Sidebar
from gui.glossary import GLOSSARY_TEXT
from gui.theme import (
    COLOR_BG, COLOR_PANEL, COLOR_BORDER, COLOR_INTERACTIVE_BORDER,
    COLOR_ACCENT, COLOR_ACCENT_HOVER, COLOR_LIGHT_CYAN, COLOR_TEXT, COLOR_MUTED,
    get_title_font, get_section_font, get_label_font, get_mono_font
)


class BisectionMethodView(ctk.CTkFrame):
    """
    Vista del Método de Bisección aplicado a optimización.

    El usuario ingresa la función original f(x), xl, xu, es
    (tolerancia) e imax. El método calcula f'(x) y resuelve f'(x) = 0
    para encontrar un punto crítico x* (mínimo o máximo). Muestra tres
    tabs: Resultado, Paso a Paso y Gráfica (f(x) y f'(x)).
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.title_font = get_title_font()
        self.section_font = get_section_font()
        self.label_font = get_label_font()
        self.mono_font = get_mono_font()
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.create_layout()
        self.load_preset("cubica")

    def create_layout(self):
        self.sidebar = Sidebar(self, active_method="bisection_method")
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.view_container = ctk.CTkFrame(self, fg_color="transparent")
        self.view_container.grid(row=0, column=1, sticky="nsew", padx=24, pady=24)
        self.view_container.grid_columnconfigure(0, weight=1)
        self.view_container.grid_rowconfigure(1, weight=1)

        header_frame = ctk.CTkFrame(self.view_container, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        header_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            header_frame, text="Optimización: Bisección desde f(x)",
            font=self.title_font, text_color=COLOR_LIGHT_CYAN
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            header_frame,
            text="Calcula f'(x) y encuentra x* donde f'(x) = 0. Requiere que f'(xl) y f'(xu) tengan signos opuestos.",
            font=self.label_font, text_color=COLOR_MUTED
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        content_frame = ctk.CTkFrame(self.view_container, fg_color="transparent")
        content_frame.grid(row=1, column=0, sticky="nsew")
        content_frame.grid_columnconfigure(0, weight=5)
        content_frame.grid_columnconfigure(1, weight=5)
        content_frame.grid_rowconfigure(0, weight=1)

        self._setup_left_panel(content_frame)
        self._setup_right_panel(content_frame)

    def _setup_left_panel(self, parent):
        self.left_panel = ctk.CTkFrame(
            parent, fg_color=COLOR_PANEL, border_color=COLOR_BORDER,
            border_width=1, corner_radius=12
        )
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 12), pady=0)
        self.left_panel.grid_columnconfigure(0, weight=1)

        config_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        config_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        config_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(config_frame, text="Tipo de entrada:", font=self.label_font, text_color=COLOR_TEXT).grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 6))
        self.input_type_switch = ctk.CTkSegmentedButton(
            config_frame, values=["f(x)", "f'(x)"], command=self._on_input_type,
            font=self.label_font,
            selected_color=COLOR_ACCENT, selected_hover_color=COLOR_ACCENT_HOVER,
            unselected_color=COLOR_BG, unselected_hover_color=COLOR_BORDER,
            text_color=COLOR_TEXT, corner_radius=8
        )
        self.input_type_switch.set("f(x)")
        self.input_type_switch.grid(row=0, column=1, sticky="w", pady=(0, 6))
        self.input_type = "function"

        ctk.CTkLabel(config_frame, text="Entrada (f(x) o f'(x)):", font=self.label_font, text_color=COLOR_TEXT).grid(
            row=1, column=0, sticky="w", padx=(0, 8), pady=(0, 6))
        self.entry_func = ctk.CTkEntry(config_frame, font=self.label_font, fg_color=COLOR_BG,
                                       border_color=COLOR_INTERACTIVE_BORDER, text_color=COLOR_TEXT)
        self.entry_func.grid(row=1, column=1, sticky="ew", pady=(0, 6))

        ctk.CTkLabel(config_frame, text="xl:", font=self.label_font, text_color=COLOR_TEXT).grid(
            row=2, column=0, sticky="w", padx=(0, 8), pady=(0, 6))
        self.entry_xl = ctk.CTkEntry(config_frame, font=self.label_font, fg_color=COLOR_BG,
                                     border_color=COLOR_INTERACTIVE_BORDER, text_color=COLOR_TEXT, width=120)
        self.entry_xl.grid(row=2, column=1, sticky="w", pady=(0, 6))

        ctk.CTkLabel(config_frame, text="xu:", font=self.label_font, text_color=COLOR_TEXT).grid(
            row=3, column=0, sticky="w", padx=(0, 8), pady=(0, 6))
        self.entry_xu = ctk.CTkEntry(config_frame, font=self.label_font, fg_color=COLOR_BG,
                                     border_color=COLOR_INTERACTIVE_BORDER, text_color=COLOR_TEXT, width=120)
        self.entry_xu.grid(row=3, column=1, sticky="w", pady=(0, 6))

        ctk.CTkLabel(config_frame, text="es (%):", font=self.label_font, text_color=COLOR_TEXT).grid(
            row=4, column=0, sticky="w", padx=(0, 8), pady=(0, 6))
        self.entry_es = ctk.CTkEntry(config_frame, font=self.label_font, fg_color=COLOR_BG,
                                     border_color=COLOR_INTERACTIVE_BORDER, text_color=COLOR_TEXT, width=120)
        self.entry_es.insert(0, "0.01")
        self.entry_es.grid(row=4, column=1, sticky="w", pady=(0, 6))

        ctk.CTkLabel(config_frame, text="imax:", font=self.label_font, text_color=COLOR_TEXT).grid(
            row=5, column=0, sticky="w", padx=(0, 8), pady=(0, 6))
        self.entry_imax = ctk.CTkEntry(config_frame, font=self.label_font, fg_color=COLOR_BG,
                                       border_color=COLOR_INTERACTIVE_BORDER, text_color=COLOR_TEXT, width=120)
        self.entry_imax.insert(0, "100")
        self.entry_imax.grid(row=5, column=1, sticky="w", pady=(0, 6))

        ctk.CTkLabel(config_frame, text="Ejemplo:", font=self.label_font, text_color=COLOR_TEXT).grid(
            row=6, column=0, sticky="w", padx=(0, 8))
        self.preset_combo = ctk.CTkComboBox(
            config_frame,
            values=["Manual", "x²−4x+1 en [0,3]", "x³−3x en [0,1.5]", "sin(x)+0.5x en [0,4]"],
            command=self.on_preset,
            fg_color=COLOR_BG, border_color=COLOR_INTERACTIVE_BORDER,
            button_color=COLOR_INTERACTIVE_BORDER, button_hover_color=COLOR_ACCENT,
            dropdown_fg_color=COLOR_PANEL, dropdown_hover_color=COLOR_BORDER,
            dropdown_text_color=COLOR_TEXT, text_color=COLOR_TEXT,
            font=self.label_font, corner_radius=8
        )
        self.preset_combo.set("Manual")
        self.preset_combo.grid(row=6, column=1, sticky="ew")

        actions_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        actions_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=20)
        actions_frame.grid_columnconfigure(0, weight=1)
        actions_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            actions_frame, text="Limpiar",
            fg_color="transparent", hover_color=COLOR_BORDER,
            border_color=COLOR_INTERACTIVE_BORDER, border_width=1,
            text_color=COLOR_LIGHT_CYAN, font=self.label_font,
            corner_radius=8, height=38, command=self.clear_inputs
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")

        ctk.CTkButton(
            actions_frame, text="Calcular y Graficar",
            fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
            text_color=COLOR_BG,
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            corner_radius=8, height=38, command=self.solve_bisection
        ).grid(row=0, column=1, padx=(6, 0), sticky="ew")

        info_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        info_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))
        self.lbl_info = ctk.CTkLabel(
            info_frame, text="", font=self.label_font, text_color=COLOR_MUTED, wraplength=320)
        self.lbl_info.grid(row=0, column=0, sticky="w")

    def _setup_right_panel(self, parent):
        self.right_panel = ctk.CTkFrame(
            parent, fg_color=COLOR_PANEL, border_color=COLOR_BORDER,
            border_width=1, corner_radius=12
        )
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(12, 0), pady=0)
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(1, weight=1)

        self.result_tabs = ctk.CTkTabview(
            self.right_panel, fg_color=COLOR_PANEL,
            segmented_button_fg_color=COLOR_BG,
            segmented_button_selected_color=("#58A1D3", "#0F4C81"),
            segmented_button_selected_hover_color=("#3e87b7", "#0b3a63"),
            segmented_button_unselected_color=COLOR_BG,
            segmented_button_unselected_hover_color=COLOR_BORDER,
            text_color=COLOR_TEXT, corner_radius=8
        )
        self.result_tabs.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=12, pady=12)

        self.tab_result = self.result_tabs.add("Resultado")
        self.tab_steps = self.result_tabs.add("Paso a Paso")
        self.tab_table = self.result_tabs.add("Tabla")
        self.tab_graph = self.result_tabs.add("Gráfica")
        self.tab_glossary = self.result_tabs.add("Glosario")
        self._setup_result_tab()
        self._setup_steps_tab()
        self._setup_table_tab()
        self._setup_graph_tab()
        self._setup_glossary_tab()

    def _setup_result_tab(self):
        self.tab_result.grid_columnconfigure(0, weight=1)
        self.tab_result.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(
            self.tab_result, text="Resultado de la Bisección",
            font=self.section_font, text_color=COLOR_LIGHT_CYAN
        ).grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.txt_result = ctk.CTkTextbox(
            self.tab_result, fg_color=COLOR_BG, font=self.mono_font,
            text_color=COLOR_TEXT, border_color=COLOR_BORDER, border_width=1,
            corner_radius=8,
            scrollbar_button_color=COLOR_INTERACTIVE_BORDER,
            scrollbar_button_hover_color=COLOR_ACCENT
        )
        self.txt_result.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.txt_result.insert("1.0", "Ingrese datos y presione 'Calcular y Graficar'.")
        self.txt_result.configure(state="disabled")

    def _setup_steps_tab(self):
        self.tab_steps.grid_columnconfigure(0, weight=1)
        self.tab_steps.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(
            self.tab_steps, text="Iteraciones del Método de Bisección",
            font=self.section_font, text_color=COLOR_LIGHT_CYAN
        ).grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.txt_steps = ctk.CTkTextbox(
            self.tab_steps, fg_color=COLOR_BG, font=self.mono_font,
            text_color=COLOR_TEXT, border_color=COLOR_BORDER, border_width=1,
            corner_radius=8,
            scrollbar_button_color=COLOR_INTERACTIVE_BORDER,
            scrollbar_button_hover_color=COLOR_ACCENT
        )
        self.txt_steps.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.txt_steps.insert(
            "1.0",
            "Paso a paso (buscamos f'(x) = 0):\n"
            "1. Verificar que f'(xl) y f'(xu) tengan signos opuestos.\n"
            "2. xr = (xl + xu)/2 (punto medio)\n"
            "3. ea = |(xr - xrold)/xr| * 100 (error relativo)\n"
            "4. test = f'(xl) * f'(xr):\n"
            "   - < 0 → xu = xr (el punto crítico está abajo)\n"
            "   - > 0 → xl = xr (el punto crítico está arriba)\n"
            "   - = 0 → punto crítico exacto encontrado\n"
            "5. Sale cuando ea < es o iter >= imax\n"
            "6. Al final, f''(x*) clasifica: f''>0 mínimo, f''<0 máximo."
        )
        self.txt_steps.configure(state="disabled")

    def _setup_table_tab(self):
        self.tab_table.grid_columnconfigure(0, weight=1)
        self.tab_table.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            self.tab_table, text="Tabla de iteraciones",
            font=self.section_font, text_color=COLOR_LIGHT_CYAN
        ).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 4))

        leyenda = (
            "LEYENDA\n"
            "  Iter = número de iteración.\n"
            "  xl   = límite inferior del intervalo.\n"
            "  xu   = límite superior del intervalo.\n"
            "  xr   = punto medio; aproximación de x*.\n"
            "  fp(xl), fp(xr) = f'(x) evaluada en esos puntos.\n"
            "  test = f'(xl)*f'(xr); su signo decide qué mitad se conserva.\n"
            "  ea   = error relativo porcentual."
        )
        ctk.CTkLabel(
            self.tab_table, text=leyenda, font=self.label_font,
            text_color=COLOR_MUTED, justify="left", anchor="w", wraplength=560
        ).grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 8))

        self.txt_table = ctk.CTkTextbox(
            self.tab_table, fg_color=COLOR_BG, font=self.mono_font,
            text_color=COLOR_TEXT, border_color=COLOR_BORDER, border_width=1,
            corner_radius=8,
            scrollbar_button_color=COLOR_INTERACTIVE_BORDER,
            scrollbar_button_hover_color=COLOR_ACCENT
        )
        self.txt_table.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.txt_table.insert("1.0", "Presione 'Calcular y Graficar' para llenar la tabla.")
        self.txt_table.configure(state="disabled")

    def _setup_graph_tab(self):
        self.tab_graph.grid_columnconfigure(0, weight=1)
        self.tab_graph.grid_rowconfigure(1, weight=1)

        controls = ctk.CTkFrame(self.tab_graph, fg_color="transparent")
        controls.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 0))
        ctk.CTkLabel(
            controls, text="Vista:", font=self.label_font, text_color=COLOR_MUTED
        ).pack(side="left", padx=(0, 8))
        self.graph_mode_switch = ctk.CTkSegmentedButton(
            controls, values=["2D", "3D"], command=self._on_graph_mode,
            font=self.label_font,
            selected_color=COLOR_ACCENT, selected_hover_color=COLOR_ACCENT_HOVER,
            unselected_color=COLOR_BG, unselected_hover_color=COLOR_BORDER,
            text_color=COLOR_TEXT, corner_radius=8
        )
        self.graph_mode_switch.set("2D")
        self.graph_mode_switch.pack(side="left")
        ctk.CTkLabel(
            controls, text="Curva:", font=self.label_font, text_color=COLOR_MUTED
        ).pack(side="left", padx=(16, 8))
        self.curve_mode_switch = ctk.CTkSegmentedButton(
            controls, values=["Ambas", "f(x)", "f'(x)"],
            command=self._on_curve_mode,
            font=self.label_font,
            selected_color=COLOR_ACCENT, selected_hover_color=COLOR_ACCENT_HOVER,
            unselected_color=COLOR_BG, unselected_hover_color=COLOR_BORDER,
            text_color=COLOR_TEXT, corner_radius=8
        )
        self.curve_mode_switch.set("Ambas")
        self.curve_mode_switch.pack(side="left")
        self.graph_mode = "2D"
        self.curve_mode = "Ambas"
        self._plot_data = None
        self.step_index = 0

        ctk.CTkLabel(
            controls, text="Paso:", font=self.label_font, text_color=COLOR_MUTED
        ).pack(side="left", padx=(16, 8))
        step_button_style = {
            "font": self.label_font,
            "fg_color": COLOR_BG,
            "hover_color": COLOR_BORDER,
            "border_color": COLOR_INTERACTIVE_BORDER,
            "border_width": 1,
            "text_color": COLOR_TEXT,
            "corner_radius": 8,
        }
        self.btn_step_prev = ctk.CTkButton(
            controls, text="◀", width=34,
            command=lambda: self._change_step(-1), **step_button_style)
        self.btn_step_prev.pack(side="left")
        self.btn_step_next = ctk.CTkButton(
            controls, text="▶", width=34,
            command=lambda: self._change_step(1), **step_button_style)
        self.btn_step_next.pack(side="left", padx=(4, 4))
        self.btn_step_all = ctk.CTkButton(
            controls, text="Todo", width=52,
            command=self._step_all, **step_button_style)
        self.btn_step_all.pack(side="left")
        self.lbl_step = ctk.CTkLabel(
            controls, text="Paso 0 / 0", font=self.label_font,
            text_color=COLOR_MUTED)
        self.lbl_step.pack(side="left", padx=(8, 0))
        self._update_step_controls()

        self.graph_frame = ctk.CTkFrame(self.tab_graph, fg_color="transparent")
        self.graph_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.graph_legend = ctk.CTkLabel(
            self.tab_graph, text="",
            font=self.label_font, text_color=COLOR_MUTED,
            justify="left", anchor="w"
        )
        self.graph_legend.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 6))
        self._update_graph_legend()

    def _update_graph_legend(self):
        if self.graph_mode == "3D":
            text = (
                "Eje x = x.  Eje y = separación de curvas.  Eje z = valor.\n"
                "Superficie verde = f(x) o F(x).  Superficie azul = f'(x).\n"
                "Superficie gris = f'(x)=0.  Línea naranja = iterados.\n"
                "Estrella verde = x* final sobre cada curva."
            )
        else:
            text = (
                "Curva verde = f(x) o F(x) (C=0).  Curva azul = f'(x).  Línea negra = f'(x)=0.\n"
                "En 'Ambas' se usa doble eje Y: izquierdo f(x), derecho f'(x).\n"
                "Puntos naranjas = iteraciones (◀ ▶ recorren la construcción paso a paso).\n"
                "Rectángulo naranja = intervalo [xl, xu] del paso actual.\n"
                "Zona azul sombreada = intervalo inicial [xl, xu].\n"
                "Estrella verde = x* final (aparece al llegar al último paso)."
            )
        self.graph_legend.configure(text=text)

    def _iteration_steps(self):
        if self._plot_data is None:
            return []
        return [s for s in self._plot_data[0] if s["type"] == "iteration"]

    def _update_step_controls(self):
        total = len(self._iteration_steps())
        self.lbl_step.configure(text=f"Paso {self.step_index} / {total}")
        sin_datos = self._plot_data is None
        self.btn_step_prev.configure(
            state="disabled" if (sin_datos or self.step_index <= 0) else "normal")
        self.btn_step_next.configure(
            state="disabled" if (sin_datos or self.step_index >= total) else "normal")
        self.btn_step_all.configure(
            state="disabled" if (sin_datos or self.step_index >= total) else "normal")

    def _change_step(self, delta):
        total = len(self._iteration_steps())
        self.step_index = max(0, min(total, self.step_index + delta))
        self._update_step_controls()
        self._render_plot()

    def _step_all(self):
        self.step_index = len(self._iteration_steps())
        self._update_step_controls()
        self._render_plot()

    def _on_graph_mode(self, value):
        self.graph_mode = value
        self._update_graph_legend()
        if self._plot_data is not None:
            self._render_plot()

    def _on_curve_mode(self, value):
        self.curve_mode = value
        self._update_graph_legend()
        if self._plot_data is not None:
            self._render_plot()

    def _setup_glossary_tab(self):
        self.tab_glossary.grid_columnconfigure(0, weight=1)
        self.tab_glossary.grid_rowconfigure(0, weight=1)
        txt_glossary = ctk.CTkTextbox(
            self.tab_glossary, fg_color=COLOR_BG, font=self.mono_font,
            text_color=COLOR_TEXT, border_color=COLOR_BORDER, border_width=1,
            corner_radius=8,
            scrollbar_button_color=COLOR_INTERACTIVE_BORDER,
            scrollbar_button_hover_color=COLOR_ACCENT
        )
        txt_glossary.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        txt_glossary.insert("1.0", GLOSSARY_TEXT)
        txt_glossary.configure(state="disabled")

    def _on_input_type(self, value):
        self.input_type = "function" if value == "f(x)" else "derivative"

    # --- Lógica de presets ---
    def on_preset(self, value):
        if value == "x²−4x+1 en [0,3]":
            self.load_preset("cuadratica")
        elif value == "x³−3x en [0,1.5]":
            self.load_preset("cubica")
        elif value == "sin(x)+0.5x en [0,4]":
            self.load_preset("trigonometrica")
        if value != "Manual":
            self.preset_combo.set("Manual")

    def load_preset(self, name):
        if name == "cuadratica":
            func, xl, xu = "x**2 - 4*x + 1", 0.0, 3.0
        elif name == "cubica":
            func, xl, xu = "x**3 - 3*x", 0.0, 1.5
        elif name == "trigonometrica":
            func, xl, xu = "sin(x) + 0.5*x", 0.0, 4.0
        else:
            return
        self.input_type = "function"
        self.input_type_switch.set("f(x)")
        self.entry_func.delete(0, "end")
        self.entry_func.insert(0, func)
        self.entry_xl.delete(0, "end")
        self.entry_xl.insert(0, str(xl))
        self.entry_xu.delete(0, "end")
        self.entry_xu.insert(0, str(xu))

    def clear_inputs(self):
        for e in [self.entry_func, self.entry_xl, self.entry_xu, self.entry_es, self.entry_imax]:
            e.delete(0, "end")
        self.entry_es.insert(0, "0.01")
        self.entry_imax.insert(0, "100")
        self.lbl_info.configure(text="")

    # --- Resolución ---
    def solve_bisection(self):
        func_str = self.entry_func.get().strip()
        if func_str == "":
            func_str = None
        try:
            xl = float(self.entry_xl.get().strip())
            xu = float(self.entry_xu.get().strip())
            es = float(self.entry_es.get().strip())
            imax = int(self.entry_imax.get().strip())
        except ValueError:
            messagebox.showerror("Error de entrada", "xl, xu, es deben ser numéricos e imax entero.")
            return

        solver = BisectionMethod(
            func_str, xl, xu, es=es, imax=imax,
            input_type=self.input_type)
        result = solver.solve()

        self.txt_result.configure(state="normal")
        self.txt_steps.configure(state="normal")
        self.txt_table.configure(state="normal")
        self.txt_result.delete("1.0", "end")
        self.txt_steps.delete("1.0", "end")
        self.txt_table.delete("1.0", "end")

        if not result["success"]:
            err = f"ERROR\n{result['error_message']}"
            self.txt_result.insert("1.0", err)
            self.txt_steps.insert("1.0", err)
            self.txt_table.insert("1.0", err)
            self.lbl_info.configure(text="")
        else:
            sol = result["solution"]
            original_name = (
                "F(x)" if sol.get("original_is_antiderivative") else "f(x)"
            )
            out = f"{original_name} = {sol.get('original_expr', '---')}\n"
            out += f"f'(x) = {sol.get('derivative_expr', '---')}\n"
            out += f"f''(x) = {sol.get('second_derivative_expr', '---')}\n"
            out += f"\nPunto crítico x* ≈ {sol['root']:.8f}\n"
            out += f"Iteraciones = {sol['iterations']}\n"
            out += f"Error (ea) = {sol['error']:.6g}%\n"
            out += f"Convergió = {'Sí' if sol['converged'] else 'No (máx. iteraciones)'}\n"
            out += f"{original_name}* = {sol.get('original_value', float('nan')):.6g}\n"
            out += f"f'(x*) = {sol['f_value']:.6g}\n"
            if sol.get("second_derivative") is not None:
                out += f"f''(x*) = {sol['second_derivative']:.6g}\n"
            out += f"Clasificación: {sol.get('critical_type', 'inconcluso')}\n"
            out += f"{sol.get('classification', '')}\n"
            out += f"Intervalo final: [{sol['xl_final']:.6g}, {sol['xu_final']:.6g}]\n"
            out += "\nRecuerde: x* es donde f'(x)=0, no una raíz de f(x).\n"
            self.txt_result.insert("1.0", out)

            sep = "─" * 60
            steps_text = (
                "PROCEDIMIENTO — BISECCIÓN SOBRE f'(x)\n"
                f"{original_name} = {sol.get('original_expr', '---')}\n"
                f"f'(x) = {sol.get('derivative_expr', '---')}\n"
                "Objetivo: hallar x* donde f'(x*) = 0.\n\n"
                "Fórmulas:\n"
                "  xr = (xl + xu) / 2\n"
                "  test = f'(xl) * f'(xr)\n"
                "  ea = |(xr - xr_anterior) / xr| * 100%\n\n"
                "Decisión:\n"
                "  test < 0  →  xu = xr  (el punto crítico está a la izquierda)\n"
                "  test > 0  →  xl = xr  (el punto crítico está a la derecha)\n"
                "  test = 0  →  x* exacto\n\n"
            )
            for step in result["steps"]:
                if step["type"] == "initial":
                    steps_text += "DATOS INICIALES\n"
                    steps_text += f"  {original_name} = {sol.get('original_expr', '---')}\n"
                    steps_text += f"  f'(x) = {step['f_expr']}\n"
                    steps_text += f"  Intervalo = [{step['xl']:.8g}, {step['xu']:.8g}]\n"
                    steps_text += f"  f'(xl) = {step['f_xl']:.8g}\n"
                    steps_text += f"  f'(xu) = {step['f_xu']:.8g}\n"
                    steps_text += f"  f'(xl)*f'(xu) = {step['f_xl'] * step['f_xu']:.8g}\n"
                    steps_text += f"  es = {step['es']}%   imax = {step['imax']}\n\n"
                elif step["type"] == "iteration":
                    accion = "x* exacto" if step["action"] == "raiz_exacta" else step["action"]
                    xl_new = step.get("xl_new", step["xl"])
                    xu_new = step.get("xu_new", step["xu"])
                    steps_text += sep + "\n"
                    steps_text += f"ITERACIÓN {step['iter']}\n"
                    steps_text += f"  xr = (xl + xu)/2 = ({step['xl']:.8g} + {step['xu']:.8g})/2 = {step['xr']:.8g}\n"
                    steps_text += f"  xr_anterior = {step['xrold']:.8g}\n"
                    steps_text += f"  f'(xl) = {step['f_xl']:.8g}\n"
                    steps_text += f"  f'(xr) = {step['f_xr']:.8g}\n"
                    steps_text += f"  test = f'(xl)*f'(xr) = ({step['f_xl']:.8g})*({step['f_xr']:.8g}) = {step['test']:.8g}\n"
                    steps_text += f"  Decisión: {accion}\n"
                    steps_text += f"  Nuevo intervalo: [{xl_new:.8g}, {xu_new:.8g}]\n"
                    steps_text += f"  ea = |({step['xr']:.8g} - {step['xrold']:.8g})/{step['xr']:.8g}|*100 = {step['ea']:.8g}%\n\n"
                elif step["type"] == "final":
                    segunda = (f"{sol['second_derivative']:.8g}"
                               if sol.get("second_derivative") is not None
                               else "no evaluable")
                    steps_text += "═" * 60 + "\n"
                    steps_text += "RESULTADO FINAL\n"
                    steps_text += f"  x* ≈ {step['root']:.10g}\n"
                    steps_text += f"  Iteraciones = {step['iterations']}\n"
                    steps_text += f"  ea final = {step['error']:.8g}%\n"
                    steps_text += f"  {original_name}* = {sol.get('original_value', float('nan')):.8g}\n"
                    steps_text += f"  f'(x*) = {sol['f_value']:.8g}\n"
                    steps_text += f"  f''(x*) = {segunda}\n"
                    steps_text += f"  Clasificación: {sol.get('critical_type', 'inconcluso')}\n"
                    steps_text += f"  {sol.get('classification', '')}\n"
            self.txt_steps.insert("1.0", steps_text)

            table_text = (
                "TABLA DE ITERACIONES — BISECCIÓN\n\n"
                f"{'Iter':>4} | {'xl':>10} | {'xu':>10} | {'xr':>10} | "
                f"{'fp(xl)':>12} | {'fp(xr)':>12} | {'test':>12} | {'ea(%)':>10}\n"
            )
            table_text += "-" * 106 + "\n"
            for step in result["steps"]:
                if step["type"] != "iteration":
                    continue
                table_text += (
                    f"{step['iter']:>4} | {step['xl']:>10.6g} | {step['xu']:>10.6g} | "
                    f"{step['xr']:>10.6g} | {step['f_xl']:>12.6g} | {step['f_xr']:>12.6g} | "
                    f"{step['test']:>12.6g} | {step['ea']:>10.6g}\n"
                )
            table_text += "-" * 106 + "\n"
            table_text += (
                f"Final: x* ≈ {sol['root']:.10g}   f'(x*) = {sol['f_value']:.6g}   "
                f"ea = {sol['error']:.6g}%   iter = {sol['iterations']}\n"
            )
            self.txt_table.insert("1.0", table_text)

            self.lbl_info.configure(
                text=f"x* ≈ {sol['root']:.6g} ({sol.get('critical_type', 'inconcluso')}, iter={sol['iterations']}, ea={sol['error']:.4g}%)"
            )

            self._plot(result["steps"], func_str, xl, xu, self.input_type)

        self.txt_result.configure(state="disabled")
        self.txt_steps.configure(state="disabled")
        self.txt_table.configure(state="disabled")

    # --- Gráfica ---
    def _plot(self, steps, func_str, xl_orig, xu_orig,
              input_type="function"):
        self._plot_data = (steps, func_str, xl_orig, xu_orig, input_type)
        self.step_index = len(self._iteration_steps())
        self._update_step_controls()
        self._render_plot()

    def _render_plot(self):
        if self._plot_data is None:
            return
        steps, func_str, xl_orig, xu_orig, input_type = self._plot_data
        for w in self.graph_frame.winfo_children():
            w.destroy()
        if self.graph_mode == "3D":
            self._render_plot_3d(steps, func_str, xl_orig, xu_orig, input_type)
        else:
            self._render_plot_2d(steps, func_str, xl_orig, xu_orig, input_type)

    def _render_plot_2d(self, steps, func_str, xl_orig, xu_orig,
                        input_type="function"):
        fig, ax = plt.subplots(figsize=(5.5, 3.5))
        show_original = self.curve_mode in {"Ambas", "f(x)"}
        show_derivative = self.curve_mode in {"Ambas", "f'(x)"}
        both = show_original and show_derivative
        ax2 = ax.twinx() if both else None
        derivative_axis = ax2 if ax2 is not None else ax

        ax.axvspan(xl_orig, xu_orig, alpha=0.1, color="#58A1D3",
                   label="Intervalo inicial")
        margen = 0.2 * (xu_orig - xl_orig)
        a, b = xl_orig - margen, xu_orig + margen
        spec = None
        try:
            spec = build_function_spec(func_str, input_type=input_type)
        except Exception:
            pass

        if spec is not None:
            original_label = (
                "F(x) (C=0)" if spec["original_is_antiderivative"]
                else "f(x)"
            )
            if show_original:
                xs, ys = evaluate_curve(spec["original"], a, b, 300)
                ax.plot(xs, ys, color="#2ca02c", linewidth=1.8,
                        label=original_label)
            if show_derivative:
                xs, ys = evaluate_curve(spec["derivative"], a, b, 300)
                derivative_axis.plot(xs, ys, color="#58A1D3",
                                     linewidth=1.8, label="f'(x)")
                derivative_axis.axhline(0, color="k", linewidth=0.8)

        all_iter_steps = [s for s in steps if s["type"] == "iteration"]
        iter_steps = all_iter_steps[:self.step_index]
        current_step = iter_steps[-1] if iter_steps else None

        if current_step is not None:
            ax.axvspan(
                current_step["xl"], current_step["xu"], alpha=0.18,
                color="#ff9f43", label="Intervalo del paso", zorder=1)
            for limite in (current_step["xl"], current_step["xu"]):
                derivative_axis.axvline(
                    limite, color="#ff9f43", linestyle="--", linewidth=1)

        x_iters = [s["xr"] for s in iter_steps]
        if x_iters:
            if show_derivative:
                y_iters = [s["f_xr"] for s in iter_steps]
                derivative_axis.scatter(
                    x_iters, y_iters, color="#ff7f0e", marker="o",
                    s=35, label="Iterados", zorder=3)
                derivative_axis.plot(
                    x_iters, y_iters, color="#ff7f0e", linestyle=":",
                    alpha=0.5)
            elif spec is not None:
                y_iters = [evaluate_expression(spec["original"], value)
                           for value in x_iters]
                ax.scatter(x_iters, y_iters, color="#ff7f0e",
                           marker="o", s=35, label="Iterados", zorder=3)

        try:
            final_step = next(s for s in reversed(steps)
                              if s["type"] == "final")
            root_val = final_step["root"]
        except Exception:
            root_val = xl_orig

        if self.step_index >= len(all_iter_steps) and spec is not None:
            if show_original:
                f_root = evaluate_expression(spec["original"], root_val)
                ax.scatter(root_val, f_root, color="#2ca02c", marker="*",
                           s=150, label=f"x* ≈ {root_val:.4g}", zorder=4)
            if show_derivative:
                df_root = evaluate_expression(spec["derivative"], root_val)
                derivative_axis.scatter(
                    root_val, df_root, color="#2ca02c", marker="*",
                    s=150, label=f"x* ≈ {root_val:.4g}", zorder=4)

        ax.set_title("Bisección: f(x) y f'(x)")
        ax.set_xlabel("x")
        if show_original:
            ax.set_ylabel(
                "F(x)" if spec is not None and spec["original_is_antiderivative"]
                else "f(x)")
        else:
            ax.set_ylabel("f'(x)")
        if ax2 is not None:
            ax2.set_ylabel("f'(x)")
        ax.grid(True, linestyle=":", alpha=0.6)
        handles, labels = ax.get_legend_handles_labels()
        if ax2 is not None:
            handles2, labels2 = ax2.get_legend_handles_labels()
            handles += handles2
            labels += labels2
        ax.legend(handles, labels, fontsize=8)

        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _render_plot_3d(self, steps, func_str, xl_orig, xu_orig,
                        input_type="function"):
        fig = plt.figure(figsize=(5.5, 3.5))
        ax = fig.add_subplot(111, projection="3d")
        show_original = self.curve_mode in {"Ambas", "f(x)"}
        show_derivative = self.curve_mode in {"Ambas", "f'(x)"}
        both = show_original and show_derivative
        original_band = [-0.9, -0.3] if both else [-1.0, 1.0]
        derivative_band = [0.3, 0.9] if both else [-1.0, 1.0]
        original_y = -0.6 if both else 0.0
        derivative_y = 0.6 if both else 0.0

        margen = 0.2 * (xu_orig - xl_orig)
        a, b = xl_orig - margen, xu_orig + margen
        spec = None
        try:
            spec = build_function_spec(func_str, input_type=input_type)
        except Exception:
            pass

        if spec is not None:
            if show_original:
                x_range, y_range = evaluate_curve(
                    spec["original"], a, b, 240)
                mask = np.isfinite(y_range)
                x_range, y_range = x_range[mask], y_range[mask]
                if x_range.size > 1:
                    x_mesh, y_mesh = np.meshgrid(
                        x_range, np.array(original_band))
                    z_mesh = np.tile(y_range, (2, 1))
                    ax.plot_surface(
                        x_mesh, y_mesh, z_mesh, color="#2ca02c",
                        alpha=0.72, linewidth=0, antialiased=True)
            if show_derivative:
                x_range, y_range = evaluate_curve(
                    spec["derivative"], a, b, 240)
                mask = np.isfinite(y_range)
                x_range, y_range = x_range[mask], y_range[mask]
                if x_range.size > 1:
                    x_mesh, y_mesh = np.meshgrid(
                        x_range, np.array(derivative_band))
                    z_mesh = np.tile(y_range, (2, 1))
                    ax.plot_surface(
                        x_mesh, y_mesh, z_mesh, color="#58A1D3",
                        alpha=0.72, linewidth=0, antialiased=True)
                    ax.plot_surface(
                        x_mesh, y_mesh, np.zeros_like(z_mesh),
                        color="#93a6c4", alpha=0.14, linewidth=0)

        x_iters = [s["xr"] for s in steps if s["type"] == "iteration"]
        if x_iters:
            if show_derivative:
                y_iters = [s["f_xr"] for s in steps
                           if s["type"] == "iteration"]
                ax.plot(
                    x_iters, np.full(len(x_iters), derivative_y), y_iters,
                    color="#ff7f0e", marker="o", markersize=4,
                    linestyle=":", linewidth=1.4, label="Iterados f'(x)")
            elif spec is not None:
                y_iters = [evaluate_expression(spec["original"], value)
                           for value in x_iters]
                ax.plot(
                    x_iters, np.full(len(x_iters), original_y), y_iters,
                    color="#ff7f0e", marker="o", markersize=4,
                    linestyle=":", linewidth=1.4, label="Iterados f(x)")

        try:
            final_step = next(s for s in reversed(steps)
                              if s["type"] == "final")
            root_val = final_step["root"]
        except Exception:
            root_val = xl_orig

        if spec is not None:
            if show_original:
                f_root = evaluate_expression(spec["original"], root_val)
                ax.scatter(
                    [root_val], [original_y], [f_root], color="#2ca02c",
                    marker="*", s=150, label=f"x* f(x) ≈ {root_val:.4g}")
            if show_derivative:
                df_root = evaluate_expression(spec["derivative"], root_val)
                ax.scatter(
                    [root_val], [derivative_y], [df_root],
                    color="#2ca02c", marker="*", s=150,
                    label=f"x* f'(x) ≈ {root_val:.4g}")

        ax.set_title("Bisección: vista 3D")
        ax.set_xlabel("x")
        ax.set_ylabel("f(x) / f'(x)")
        ax.set_zlabel("valor")
        ax.view_init(elev=22, azim=-62)
        ax.legend(fontsize=8)

        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
