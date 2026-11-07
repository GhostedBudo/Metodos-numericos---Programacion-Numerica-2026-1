import customtkinter as ctk #pyright: ignore
from tkinter import messagebox
import numpy as np #pyright: ignore
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from lib.bisection_method import BisectionMethod
from lib.optimization_utils import parse_expression
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

    El usuario ingresa la primera derivada f'(x), xl, xu, es
    (tolerancia) e imax. El método resuelve f'(x) = 0 para encontrar
    un punto crítico x* (mínimo o máximo). Muestra tres tabs:
    Resultado, Paso a Paso y Gráfica (curva f'(x) + x* marcado).
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
            header_frame, text="Optimización: Bisección sobre f'(x)",
            font=self.title_font, text_color=COLOR_LIGHT_CYAN
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            header_frame,
            text="Encuentra x* donde f'(x) = 0. Requiere que f'(xl) y f'(xu) tengan signos opuestos.",
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

        ctk.CTkLabel(config_frame, text="f'(x):", font=self.label_font, text_color=COLOR_TEXT).grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 6))
        self.entry_func = ctk.CTkEntry(config_frame, font=self.label_font, fg_color=COLOR_BG,
                                       border_color=COLOR_INTERACTIVE_BORDER, text_color=COLOR_TEXT)
        self.entry_func.grid(row=0, column=1, sticky="ew", pady=(0, 6))

        ctk.CTkLabel(config_frame, text="xl:", font=self.label_font, text_color=COLOR_TEXT).grid(
            row=1, column=0, sticky="w", padx=(0, 8), pady=(0, 6))
        self.entry_xl = ctk.CTkEntry(config_frame, font=self.label_font, fg_color=COLOR_BG,
                                     border_color=COLOR_INTERACTIVE_BORDER, text_color=COLOR_TEXT, width=120)
        self.entry_xl.grid(row=1, column=1, sticky="w", pady=(0, 6))

        ctk.CTkLabel(config_frame, text="xu:", font=self.label_font, text_color=COLOR_TEXT).grid(
            row=2, column=0, sticky="w", padx=(0, 8), pady=(0, 6))
        self.entry_xu = ctk.CTkEntry(config_frame, font=self.label_font, fg_color=COLOR_BG,
                                     border_color=COLOR_INTERACTIVE_BORDER, text_color=COLOR_TEXT, width=120)
        self.entry_xu.grid(row=2, column=1, sticky="w", pady=(0, 6))

        ctk.CTkLabel(config_frame, text="es (%):", font=self.label_font, text_color=COLOR_TEXT).grid(
            row=3, column=0, sticky="w", padx=(0, 8), pady=(0, 6))
        self.entry_es = ctk.CTkEntry(config_frame, font=self.label_font, fg_color=COLOR_BG,
                                     border_color=COLOR_INTERACTIVE_BORDER, text_color=COLOR_TEXT, width=120)
        self.entry_es.insert(0, "0.01")
        self.entry_es.grid(row=3, column=1, sticky="w", pady=(0, 6))

        ctk.CTkLabel(config_frame, text="imax:", font=self.label_font, text_color=COLOR_TEXT).grid(
            row=4, column=0, sticky="w", padx=(0, 8), pady=(0, 6))
        self.entry_imax = ctk.CTkEntry(config_frame, font=self.label_font, fg_color=COLOR_BG,
                                       border_color=COLOR_INTERACTIVE_BORDER, text_color=COLOR_TEXT, width=120)
        self.entry_imax.insert(0, "100")
        self.entry_imax.grid(row=4, column=1, sticky="w", pady=(0, 6))

        ctk.CTkLabel(config_frame, text="Ejemplo:", font=self.label_font, text_color=COLOR_TEXT).grid(
            row=5, column=0, sticky="w", padx=(0, 8))
        self.preset_combo = ctk.CTkComboBox(
            config_frame,
            values=["Manual", "2x−4 en [0,4]", "3x²−3 en [0,1.5]", "cos(x)+0.5 en [0,4]"],
            command=self.on_preset,
            fg_color=COLOR_BG, border_color=COLOR_INTERACTIVE_BORDER,
            button_color=COLOR_INTERACTIVE_BORDER, button_hover_color=COLOR_ACCENT,
            dropdown_fg_color=COLOR_PANEL, dropdown_hover_color=COLOR_BORDER,
            dropdown_text_color=COLOR_TEXT, text_color=COLOR_TEXT,
            font=self.label_font, corner_radius=8
        )
        self.preset_combo.set("Manual")
        self.preset_combo.grid(row=5, column=1, sticky="ew")

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
        self.graph_mode = "2D"
        self._plot_data = None

        self.graph_frame = ctk.CTkFrame(self.tab_graph, fg_color="transparent")
        self.graph_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.graph_legend = ctk.CTkLabel(
            self.tab_graph,
            text=("Eje x = valores de x.  Eje y = f'(x).\n"
                  "Curva azul = f'(x).  Línea negra = y=0 (allí buscamos el corte).\n"
                  "Puntos naranjas = xr de cada iteración.  Estrella verde = x* final.\n"
                  "Zona azul sombreada = intervalo inicial [xl, xu]."),
            font=self.label_font, text_color=COLOR_MUTED,
            justify="left", anchor="w"
        )
        self.graph_legend.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 6))

    def _on_graph_mode(self, value):
        self.graph_mode = value
        if value == "3D":
            self.graph_legend.configure(
                text=("Eje x = x.  Eje y = profundidad.  Eje z = f'(x).\n"
                      "Superficie azul = f'(x) extendida.  Superficie gris = f'(x)=0.\n"
                      "Línea naranja = iterados.  Estrella verde = x* final.")
            )
        else:
            self.graph_legend.configure(
                text=("Eje x = valores de x.  Eje y = f'(x).\n"
                      "Curva azul = f'(x).  Línea negra = y=0 (allí buscamos el corte).\n"
                      "Puntos naranjas = xr de cada iteración.  Estrella verde = x* final.\n"
                      "Zona azul sombreada = intervalo inicial [xl, xu].")
            )
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

    # --- Lógica de presets ---
    def on_preset(self, value):
        if value == "2x−4 en [0,4]":
            self.load_preset("cuadratica")
        elif value == "3x²−3 en [0,1.5]":
            self.load_preset("cubica")
        elif value == "cos(x)+0.5 en [0,4]":
            self.load_preset("trigonometrica")
        if value != "Manual":
            self.preset_combo.set("Manual")

    def load_preset(self, name):
        if name == "cuadratica":
            func, xl, xu = "2*x - 4", 0.0, 4.0
        elif name == "cubica":
            func, xl, xu = "3*x**2 - 3", 0.0, 1.5
        elif name == "trigonometrica":
            func, xl, xu = "cos(x) + 0.5", 0.0, 4.0
        else:
            return
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

        solver = BisectionMethod(func_str, xl, xu, es=es, imax=imax)
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
            out = f"Punto crítico x* ≈ {sol['root']:.8f}\n"
            out += f"Iteraciones = {sol['iterations']}\n"
            out += f"Error (ea) = {sol['error']:.6g}%\n"
            out += f"Convergió = {'Sí' if sol['converged'] else 'No (máx. iteraciones)'}\n"
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

            self._plot(result["steps"], func_str, xl, xu)

        self.txt_result.configure(state="disabled")
        self.txt_steps.configure(state="disabled")
        self.txt_table.configure(state="disabled")

    # --- Gráfica ---
    def _plot(self, steps, func_str, xl_orig, xu_orig):
        self._plot_data = (steps, func_str, xl_orig, xu_orig)
        self._render_plot()

    def _render_plot(self):
        if self._plot_data is None:
            return
        steps, func_str, xl_orig, xu_orig = self._plot_data
        for w in self.graph_frame.winfo_children():
            w.destroy()
        if self.graph_mode == "3D":
            self._render_plot_3d(steps, func_str, xl_orig, xu_orig)
        else:
            self._render_plot_2d(steps, func_str, xl_orig, xu_orig)

    def _render_plot_2d(self, steps, func_str, xl_orig, xu_orig):
        fig, ax = plt.subplots(figsize=(5.5, 3.5))

        ax.axvspan(xl_orig, xu_orig, alpha=0.1, color="#58A1D3",
                   label="Intervalo inicial")
        ax.axhline(0, color="k", linewidth=0.8)

        if func_str:
            try:
                import sympy
                x_sym = sympy.Symbol('x')
                f_expr = parse_expression(func_str)
                f_callable = sympy.lambdify(x_sym, f_expr, "numpy")
                margen = 0.2 * (xu_orig - xl_orig)
                a, b = xl_orig - margen, xu_orig + margen
                x_range = np.linspace(a, b, 300)
                y_range = f_callable(x_range)
                if np.isscalar(y_range):
                    y_range = np.full_like(x_range, float(y_range))
                ax.plot(x_range, y_range, "b-", linewidth=1.5,
                        label="f'(x)")
                ax.plot([xl_orig, xu_orig],
                        [float(f_expr.subs(x_sym, xl_orig)),
                         float(f_expr.subs(x_sym, xu_orig))],
                        "or", markersize=7, label="Extremos [xl,xu]")
            except Exception:
                pass

        x_iters = [s["xr"] for s in steps if s["type"] == "iteration"]
        y_iters = [s["f_xr"] for s in steps if s["type"] == "iteration"]
        if len(x_iters) > 0:
            ax.scatter(x_iters, y_iters, color="#ff7f0e", marker="o", s=35, label="Iterados", zorder=3)
            ax.plot(x_iters, y_iters, color="#ff7f0e", linestyle=":", alpha=0.5)

        try:
            final_step = next(s for s in reversed(steps) if s["type"] == "final")
            root_val = final_step["root"]
            import sympy
            x_sym = sympy.Symbol('x')
            f_expr = parse_expression(func_str)
            f_root = float(f_expr.subs(x_sym, root_val))
        except Exception:
            f_root = 0.0
            root_val = xl_orig

        ax.scatter(root_val, f_root, color="#2ca02c", marker="*", s=130, label=f"x* ≈ {root_val:.4g}", zorder=4)

        ax.set_title("Bisección sobre f'(x): punto crítico")
        ax.set_xlabel("x")
        ax.set_ylabel("f'(x)")
        ax.grid(True, linestyle=":", alpha=0.6)
        ax.legend(fontsize=8)

        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _render_plot_3d(self, steps, func_str, xl_orig, xu_orig):
        fig = plt.figure(figsize=(5.5, 3.5))
        ax = fig.add_subplot(111, projection="3d")

        margen = 0.2 * (xu_orig - xl_orig)
        a, b = xl_orig - margen, xu_orig + margen
        if func_str:
            try:
                import sympy
                x_sym = sympy.Symbol('x')
                f_expr = parse_expression(func_str)
                f_callable = sympy.lambdify(x_sym, f_expr, "numpy")
                x_range = np.linspace(a, b, 240)
                y_range = np.asarray(f_callable(x_range), dtype=float)
                if y_range.ndim == 0:
                    y_range = np.full_like(x_range, float(y_range))
                mask = np.isfinite(y_range)
                x_range = x_range[mask]
                y_range = y_range[mask]
                if x_range.size > 1:
                    y_grid = np.array([-1.0, 1.0])
                    x_mesh, y_mesh = np.meshgrid(x_range, y_grid)
                    z_mesh = np.tile(y_range, (2, 1))
                    ax.plot_surface(
                        x_mesh, y_mesh, z_mesh, color="#58A1D3",
                        alpha=0.72, linewidth=0, antialiased=True
                    )
                    ax.plot_surface(
                        x_mesh, y_mesh, np.zeros_like(z_mesh),
                        color="#93a6c4", alpha=0.14, linewidth=0
                    )
            except Exception:
                pass

        x_iters = [s["xr"] for s in steps if s["type"] == "iteration"]
        y_iters = [s["f_xr"] for s in steps if s["type"] == "iteration"]
        if x_iters:
            ax.plot(
                x_iters, np.zeros(len(x_iters)), y_iters,
                color="#ff7f0e", marker="o", markersize=4,
                linestyle=":", linewidth=1.4, label="Iterados"
            )

        try:
            final_step = next(s for s in reversed(steps) if s["type"] == "final")
            root_val = final_step["root"]
            import sympy
            x_sym = sympy.Symbol('x')
            f_expr = parse_expression(func_str)
            f_root = float(f_expr.subs(x_sym, root_val))
        except Exception:
            f_root = 0.0
            root_val = xl_orig

        ax.scatter(
            [root_val], [0], [f_root], color="#2ca02c", marker="*",
            s=150, label=f"x* ≈ {root_val:.4g}"
        )
        ax.set_title("Bisección sobre f'(x): vista 3D")
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_zlabel("f'(x)")
        ax.view_init(elev=22, azim=-62)
        ax.legend(fontsize=8)

        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
