import customtkinter as ctk
import numpy as np
import sympy as sp
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from gui.components.sidebar import Sidebar
from gui.glossary import GLOSSARY_TEXT
from gui.theme import (
    COLOR_BG, COLOR_PANEL, COLOR_BORDER, COLOR_INTERACTIVE_BORDER,
    COLOR_ACCENT, COLOR_ACCENT_HOVER, COLOR_LIGHT_CYAN, COLOR_TEXT, COLOR_MUTED,
    get_title_font, get_section_font, get_label_font
)
from lib.secante import SecantRoots
from lib.optimization_utils import (
    build_function_spec, evaluate_curve, evaluate_expression,
)

class SecantRootsView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.sidebar = Sidebar(self, active_method="secant_roots")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
        self.content_frame.grid_columnconfigure(0, weight=1, minsize=340)
        self.content_frame.grid_columnconfigure(1, weight=2)
        self.content_frame.grid_rowconfigure(1, weight=1)
        
        self.title_font = get_title_font()
        self.section_font = get_section_font()
        self.label_font = get_label_font()
        
        self.title_label = ctk.CTkLabel(
            self.content_frame, 
            text="📐 Optimización: Secante desde f(x)",
            font=self.title_font, 
            text_color=COLOR_LIGHT_CYAN
        )
        self.title_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 20))
        
        self.input_card = ctk.CTkScrollableFrame(
            self.content_frame,
            fg_color=COLOR_PANEL,
            border_color=COLOR_BORDER,
            border_width=1,
            corner_radius=12,
            scrollbar_button_color=COLOR_INTERACTIVE_BORDER,
            scrollbar_button_hover_color=COLOR_ACCENT
        )
        self.input_card.grid(row=1, column=0, sticky="nsew", padx=(0, 15), pady=0)
        self.setup_inputs()
        
        self.right_panel = ctk.CTkFrame(
            self.content_frame,
            fg_color=COLOR_PANEL,
            border_color=COLOR_BORDER,
            border_width=1,
            corner_radius=12
        )
        self.right_panel.grid(row=1, column=1, sticky="nsew", padx=(15, 0), pady=0)
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(0, weight=1)
        
        self.output_panel = ctk.CTkTabview(
            self.right_panel,
            fg_color=COLOR_PANEL,
            segmented_button_fg_color=COLOR_BG,
            segmented_button_selected_color=("#58A1D3", "#0F4C81"),
            segmented_button_selected_hover_color=("#3e87b7", "#0b3a63"),
            segmented_button_unselected_color=COLOR_BG,
            segmented_button_unselected_hover_color=COLOR_BORDER,
            text_color=COLOR_TEXT,
            corner_radius=8
        )
        self.output_panel.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        
        self.tab_res = self.output_panel.add("Resultado")
        self.tab_steps = self.output_panel.add("Paso a Paso")
        self.tab_table = self.output_panel.add("Tabla")
        self.tab_graph = self.output_panel.add("Evolución Gráfica")
        self.tab_glossary = self.output_panel.add("Glosario")
        
        self.setup_outputs()

    def setup_inputs(self):
        card_title = ctk.CTkLabel(
            self.input_card,
            text="PARÁMETROS DE ENTRADA",
            font=self.section_font,
            text_color=COLOR_LIGHT_CYAN
        )
        card_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        fields = [
            ("Función original f(x):", "entry_func", "x**3 - 3*x"),
            ("Aproximación Inicial x0:", "entry_x0", "0.5"),
            ("Aproximación Inicial x1:", "entry_x1", "1.5"),
            ("Tolerancia (Tol):", "entry_tol", "1e-5"),
            ("Máx. Iteraciones:", "entry_max", "150"),
            ("Dominio Mín (X min):", "entry_xmin", "-2.0"),
            ("Dominio Máx (X max):", "entry_xmax", "2.0")
        ]

        nota = ctk.CTkLabel(
            self.input_card,
            text=("La Secante calcula f'(x) desde f(x) y resuelve f'(x)=0\n"
                  "sin usar f'' en las iteraciones:\n"
                  "x(k+1) = x(k) - f'(x(k))*(x(k)-x(k-1)) /\n"
                  "                (f'(x(k))-f'(x(k-1)))"),
            font=self.label_font,
            text_color=COLOR_MUTED,
            justify="left"
        )
        nota.pack(anchor="w", padx=15, pady=(0, 5))
        
        for label_text, attr_name, default_val in fields:
            lbl = ctk.CTkLabel(self.input_card, text=label_text, font=self.label_font, text_color=COLOR_TEXT)
            lbl.pack(anchor="w", padx=15, pady=(8, 2))
            
            entry = ctk.CTkEntry(
                self.input_card,
                placeholder_text=default_val,
                fg_color=COLOR_BG,
                border_color=COLOR_BORDER,
                text_color=COLOR_TEXT,
                placeholder_text_color=COLOR_MUTED,
                corner_radius=8,
                height=35
            )
            entry.insert(0, default_val)
            entry.pack(fill="x", padx=15, pady=(0, 5))
            setattr(self, attr_name, entry)
            
        self.btn_calc = ctk.CTkButton(
            self.input_card, 
            text="Calcular Punto Crítico",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            text_color=COLOR_BG,
            corner_radius=8,
            height=40,
            command=self.solve_secant
        )
        self.btn_calc.pack(fill="x", padx=15, pady=20)

    def setup_outputs(self):
        self.txt_res = ctk.CTkTextbox(
            self.tab_res, font=self.label_font, fg_color=COLOR_BG,
            border_color=COLOR_BORDER, border_width=1, text_color=COLOR_TEXT, corner_radius=8,
            scrollbar_button_color=COLOR_INTERACTIVE_BORDER,
            scrollbar_button_hover_color=COLOR_ACCENT
        )
        self.txt_res.pack(fill="both", expand=True, padx=15, pady=15)
        self.txt_res.insert("0.0", "Ingrese f(x) y presione 'Calcular Punto Crítico' para ver el diagnóstico.")
        self.txt_res.configure(state="disabled") # Corregido: Bloqueo inicial
        
        self.txt_steps = ctk.CTkTextbox(
            self.tab_steps, font=ctk.CTkFont(family="Consolas", size=12), fg_color=COLOR_BG,
            border_color=COLOR_BORDER, border_width=1, text_color=COLOR_TEXT, corner_radius=8,
            scrollbar_button_color=COLOR_INTERACTIVE_BORDER,
            scrollbar_button_hover_color=COLOR_ACCENT
        )
        self.txt_steps.pack(fill="both", expand=True, padx=15, pady=15)
        self.txt_steps.insert(
            "1.0",
            "PROCEDIMIENTO — SECANTE SOBRE f'(x)\n"
            "Objetivo: resolver f'(x) = 0 sin calcular f''(x).\n\n"
            "1. Elegir dos puntos iniciales x0 y x1.\n"
            "2. Calcular f'(x0) y f'(x1).\n"
            "3. Aplicar:\n"
            "   x(k+1) = x(k) - f'(x(k))·(x(k)-x(k-1))\n"
            "                     / (f'(x(k))-f'(x(k-1)))\n"
            "4. Calcular el error:\n"
            "   ea = |(x(k+1) - x(k)) / x(k+1)| * 100%\n"
            "5. Repetir hasta que |f'| sea pequeño o ea <= tolerancia.\n\n"
            "f'(x) se calcula automáticamente desde f(x).\n"
            "La secante aproxima f''(x) con los dos puntos anteriores.\n\n"
            "Para clasificar x*:\n"
            "  f''(x*) > 0 → mínimo\n"
            "  f''(x*) < 0 → máximo\n"
            "  f''(x*) ≈ 0 → inconcluso"
        )
        self.txt_steps.configure(state="disabled") # Corregido: Bloqueo inicial

        table_leyenda = (
            "LEYENDA\n"
            "  Iter = número de iteración.\n"
            "  x_i  = aproximación actual de x*.\n"
            "  fp(x_i) = f'(x) evaluada en x_i.\n"
            "  ea = error relativo porcentual.\n"
            "  x0 y x1 son los dos puntos iniciales de la secante."
        )
        ctk.CTkLabel(
            self.tab_table, text=table_leyenda, font=self.label_font,
            text_color=COLOR_MUTED, justify="left", anchor="w"
        ).pack(anchor="w", padx=15, pady=(8, 0))

        self.txt_table = ctk.CTkTextbox(
            self.tab_table, font=ctk.CTkFont(family="Consolas", size=12), fg_color=COLOR_BG,
            border_color=COLOR_BORDER, border_width=1, text_color=COLOR_TEXT, corner_radius=8,
            scrollbar_button_color=COLOR_INTERACTIVE_BORDER,
            scrollbar_button_hover_color=COLOR_ACCENT
        )
        self.txt_table.pack(fill="both", expand=True, padx=15, pady=(8, 8))
        self.txt_table.insert(
            "1.0",
            "Presione 'Calcular Punto Crítico' para llenar la tabla."
        )
        self.txt_table.configure(state="disabled")

        self.graph_mode = "2D"
        self._plot_payload = None
        controls = ctk.CTkFrame(self.tab_graph, fg_color="transparent")
        controls.pack(fill="x", padx=15, pady=(10, 0))
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
        self.curve_mode = "Ambas"

        self.fig, self.ax = plt.subplots(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.tab_graph)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=(8, 0))
        self.graph_legend = ctk.CTkLabel(
            self.tab_graph, text="",
            font=self.label_font, text_color=COLOR_MUTED,
            justify="left", anchor="w"
        )
        self.graph_legend.pack(fill="x", padx=15, pady=(0, 10))
        self._update_graph_legend()
        self.apply_graph_theme()

        txt_glossary = ctk.CTkTextbox(
            self.tab_glossary, font=ctk.CTkFont(family="Consolas", size=12), fg_color=COLOR_BG,
            border_color=COLOR_BORDER, border_width=1, text_color=COLOR_TEXT, corner_radius=8,
            scrollbar_button_color=COLOR_INTERACTIVE_BORDER,
            scrollbar_button_hover_color=COLOR_ACCENT
        )
        txt_glossary.pack(fill="both", expand=True, padx=15, pady=15)
        txt_glossary.insert("1.0", GLOSSARY_TEXT)
        txt_glossary.configure(state="disabled")

    def apply_graph_theme(self):
        is_dark = (ctk.get_appearance_mode() == "Dark")
        bg_color = COLOR_PANEL[1] if is_dark else COLOR_PANEL[0]
        fg_color = COLOR_TEXT[1] if is_dark else COLOR_TEXT[0]
        grid_color = COLOR_BORDER[1] if is_dark else COLOR_BORDER[0]
        axis_bg = COLOR_BG[1] if is_dark else COLOR_BG[0]
        
        self.fig.patch.set_facecolor(bg_color)
        try:
            self.ax.set_facecolor(axis_bg)
        except Exception:
            pass
        self.ax.title.set_color(fg_color)
        self.ax.xaxis.label.set_color(fg_color)
        self.ax.yaxis.label.set_color(fg_color)
        self.ax.tick_params(colors=fg_color, which='both')
        spines = getattr(self.ax, "spines", None)
        if hasattr(spines, "values"):
            for spine in spines.values():
                spine.set_color(grid_color)
        self.ax.grid(True, linestyle=":", alpha=0.5, color=grid_color)

    def _update_graph_legend(self):
        if self.graph_mode == "3D":
            text = (
                "Eje x = x.  Eje y = separación de curvas.  Eje z = valor.\n"
                "Superficie verde = f(x).  Superficie azul = f'(x).\n"
                "Superficie gris = f'(x)=0.  Línea naranja = iterados.\n"
                "Estrella verde = x* final sobre cada curva."
            )
        else:
            text = (
                "Curva verde = f(x).  Curva azul = f'(x).  Línea punteada = f'(x)=0.\n"
                "En 'Ambas' se usa doble eje Y: izquierdo f(x), derecho f'(x).\n"
                "Puntos naranjas = aproximaciones de cada iteración.\n"
                "Estrella verde = x* final."
            )
        self.graph_legend.configure(text=text)

    def _on_graph_mode(self, value):
        self.graph_mode = value
        self._update_graph_legend()
        self._render_graph()

    def _on_curve_mode(self, value):
        self.curve_mode = value
        self._update_graph_legend()
        self._render_graph()

    def _plot_result(self, result, func_str, xmin, xmax):
        self._plot_payload = (result, func_str, xmin, xmax)
        self._render_graph()

    def _render_graph(self):
        if self._plot_payload is None:
            return
        result, func_str, xmin, xmax = self._plot_payload

        self.fig.clear()
        if self.graph_mode == "3D":
            self.ax = self.fig.add_subplot(111, projection="3d")
        else:
            self.ax = self.fig.add_subplot(111)
        self.apply_graph_theme()

        if self.graph_mode == "3D":
            self._render_graph_3d(result, func_str, xmin, xmax)
        else:
            self._render_graph_2d(result, func_str, xmin, xmax)
        self.canvas.draw()

    def _render_graph_2d(self, result, func_str, xmin, xmax):
        try:
            self.ax.clear()
            self.apply_graph_theme()
            show_original = self.curve_mode in {"Ambas", "f(x)"}
            show_derivative = self.curve_mode in {"Ambas", "f'(x)"}
            both = show_original and show_derivative
            ax2 = self.ax.twinx() if both else None
            derivative_axis = ax2 if ax2 is not None else self.ax
            spec = build_function_spec(func_str)

            if show_original:
                xs, ys = evaluate_curve(spec["original"], xmin, xmax, 500)
                self.ax.plot(xs, ys, color="#2ca02c", lw=2, label="f(x)")
            if show_derivative:
                xs, ys = evaluate_curve(spec["derivative"], xmin, xmax, 500)
                derivative_axis.plot(
                    xs, ys, color="#58A1D3", lw=2, label="f'(x)")
                derivative_axis.axhline(
                    0,
                    color=(COLOR_BORDER[1] if ctk.get_appearance_mode() == "Dark"
                           else COLOR_BORDER[0]),
                    linestyle="--", linewidth=1)

            steps_data = result["steps"]
            if len(steps_data) > 1:
                x_iters = [s["x"] for s in steps_data[:-1]]
                if show_derivative:
                    y_iters = [s["fx"] for s in steps_data[:-1]]
                    derivative_axis.scatter(
                        x_iters, y_iters, color="#ff7f0e", marker="o",
                        s=35, label="Iterados", zorder=3)
                    derivative_axis.plot(
                        x_iters, y_iters, color="#ff7f0e",
                        linestyle=":", alpha=0.5)
                elif show_original:
                    y_iters = [evaluate_expression(spec["original"], value)
                               for value in x_iters]
                    self.ax.scatter(
                        x_iters, y_iters, color="#ff7f0e", marker="o",
                        s=35, label="Iterados", zorder=3)

            final_root = steps_data[-1]["x"]
            if show_original:
                final_original = evaluate_expression(
                    spec["original"], final_root)
                self.ax.scatter(
                    final_root, final_original, color="#2ca02c",
                    marker="*", s=150, label=f"x* ({final_root:.4f})",
                    zorder=4)
            if show_derivative:
                final_derivative = evaluate_expression(
                    spec["derivative"], final_root)
                derivative_axis.scatter(
                    final_root, final_derivative, color="#2ca02c",
                    marker="*", s=150, label=f"x* ({final_root:.4f})",
                    zorder=4)

            is_dark = (ctk.get_appearance_mode() == "Dark")
            handles, labels = self.ax.get_legend_handles_labels()
            if ax2 is not None:
                handles2, labels2 = ax2.get_legend_handles_labels()
                handles += handles2
                labels += labels2
            legend = self.ax.legend(handles, labels, loc="best")
            if legend:
                legend.get_frame().set_facecolor(
                    COLOR_BG[1] if is_dark else COLOR_BG[0])
                legend.get_frame().set_edgecolor(
                    COLOR_BORDER[1] if is_dark else COLOR_BORDER[0])
                for text in legend.get_texts():
                    text.set_color(COLOR_TEXT[1] if is_dark else COLOR_TEXT[0])
            self.ax.set_title(
                "Secante: f(x) y f'(x)",
                fontdict={"size": 11, "weight": "bold"})
            self.ax.set_xlabel("x")
            self.ax.set_ylabel("f(x)" if show_original else "f'(x)")
            if ax2 is not None:
                ax2.set_ylabel("f'(x)")

        except Exception as ex:
            is_dark = (ctk.get_appearance_mode() == "Dark")
            txt_color = COLOR_TEXT[1] if is_dark else COLOR_TEXT[0]
            self.ax.text(0.5, 0.5, f"⚠ Gráfica no disponible:\n{str(ex)}",
                         ha="center", va="center", transform=self.ax.transAxes,
                         color=txt_color, weight="bold")

    def _render_graph_3d(self, result, func_str, xmin, xmax):
        try:
            self.ax.clear()
            self.apply_graph_theme()
            show_original = self.curve_mode in {"Ambas", "f(x)"}
            show_derivative = self.curve_mode in {"Ambas", "f'(x)"}
            both = show_original and show_derivative
            original_band = [-0.9, -0.3] if both else [-1.0, 1.0]
            derivative_band = [0.3, 0.9] if both else [-1.0, 1.0]
            original_y = -0.6 if both else 0.0
            derivative_y = 0.6 if both else 0.0
            spec = build_function_spec(func_str)

            if show_original:
                xs, ys = evaluate_curve(spec["original"], xmin, xmax, 240)
                mask = np.isfinite(ys)
                xs, ys = xs[mask], ys[mask]
                if xs.size > 1:
                    x_mesh, y_mesh = np.meshgrid(
                        xs, np.array(original_band))
                    z_mesh = np.tile(ys, (2, 1))
                    self.ax.plot_surface(
                        x_mesh, y_mesh, z_mesh, color="#2ca02c",
                        alpha=0.72, linewidth=0, antialiased=True)
            if show_derivative:
                xs, ys = evaluate_curve(spec["derivative"], xmin, xmax, 240)
                mask = np.isfinite(ys)
                xs, ys = xs[mask], ys[mask]
                if xs.size > 1:
                    x_mesh, y_mesh = np.meshgrid(
                        xs, np.array(derivative_band))
                    z_mesh = np.tile(ys, (2, 1))
                    self.ax.plot_surface(
                        x_mesh, y_mesh, z_mesh, color="#58A1D3",
                        alpha=0.72, linewidth=0, antialiased=True)
                    self.ax.plot_surface(
                        x_mesh, y_mesh, np.zeros_like(z_mesh),
                        color="#93a6c4", alpha=0.14, linewidth=0)

            steps_data = result["steps"]
            if steps_data:
                x_iters = [s["x"] for s in steps_data]
                if show_derivative:
                    y_iters = [s["fx"] for s in steps_data]
                    self.ax.plot(
                        x_iters, np.full(len(x_iters), derivative_y),
                        y_iters, color="#ff7f0e", marker="o",
                        markersize=4, linestyle=":", linewidth=1.4,
                        label="Iterados f'(x)")
                elif show_original:
                    y_iters = [evaluate_expression(
                        spec["original"], value) for value in x_iters]
                    self.ax.plot(
                        x_iters, np.full(len(x_iters), original_y),
                        y_iters, color="#ff7f0e", marker="o",
                        markersize=4, linestyle=":", linewidth=1.4,
                        label="Iterados f(x)")

                final = steps_data[-1]
                if show_original:
                    final_original = evaluate_expression(
                        spec["original"], final["x"])
                    self.ax.scatter(
                        [final["x"]], [original_y], [final_original],
                        color="#2ca02c", marker="*", s=150,
                        label=f"x* f(x) ≈ {final['x']:.4f}")
                if show_derivative:
                    final_derivative = evaluate_expression(
                        spec["derivative"], final["x"])
                    self.ax.scatter(
                        [final["x"]], [derivative_y], [final_derivative],
                        color="#2ca02c", marker="*", s=150,
                        label=f"x* f'(x) ≈ {final['x']:.4f}")

            self.ax.set_title(
                "Secante: vista 3D",
                fontdict={"size": 11, "weight": "bold"})
            self.ax.set_xlabel("x")
            self.ax.set_ylabel("f(x) / f'(x)")
            self.ax.set_zlabel("valor")
            self.ax.view_init(elev=22, azim=-62)
            is_dark = (ctk.get_appearance_mode() == "Dark")
            legend = self.ax.legend(loc="best")
            if legend:
                legend.get_frame().set_facecolor(
                    COLOR_BG[1] if is_dark else COLOR_BG[0])
                legend.get_frame().set_edgecolor(
                    COLOR_BORDER[1] if is_dark else COLOR_BORDER[0])
                for text in legend.get_texts():
                    text.set_color(COLOR_TEXT[1] if is_dark else COLOR_TEXT[0])

        except Exception as ex:
            is_dark = (ctk.get_appearance_mode() == "Dark")
            txt_color = COLOR_TEXT[1] if is_dark else COLOR_TEXT[0]
            self.ax.text2D(
                0.5, 0.5, f"⚠ Gráfica 3D no disponible:\n{str(ex)}",
                ha="center", va="center", transform=self.ax.transAxes,
                color=txt_color, weight="bold")

    def solve_secant(self):
        func_str = self.entry_func.get()

        try:
            x0 = float(self.entry_x0.get())
            x1 = float(self.entry_x1.get())
            tol = float(self.entry_tol.get())
            max_i = int(self.entry_max.get())
            xmin = float(self.entry_xmin.get())
            xmax = float(self.entry_xmax.get())
            
            if max_i <= 0:
                raise ValueError("Las iteraciones máximas deben ser un entero positivo mayor a 0.")
            if tol <= 0:
                raise ValueError("La tolerancia debe ser un valor positivo (ej. 1e-5).")
            if x0 == x1:
                raise ValueError("Las aproximaciones iniciales x0 y x1 no pueden ser iguales para iniciar la Secante.")
            if xmin >= xmax:
                raise ValueError("El dominio de la gráfica es inválido (X min debe ser estrictamente menor a X max).")
                
        except ValueError as e:
            err_msg = str(e)
            if "could not convert" in err_msg or "invalid literal" in err_msg:
                err_msg = "Asegúrese de que los puntos, Tolerancia, Iteraciones y el Dominio contengan únicamente números."

            self.txt_res.configure(state="normal")
            self.txt_res.delete("0.0", "end")
            self.txt_res.insert("0.0", f"❌ Error de Entrada:\n{err_msg}")
            self.txt_res.configure(state="disabled")
            self.txt_table.configure(state="normal")
            self.txt_table.delete("0.0", "end")
            self.txt_table.insert("0.0", f"ERROR DE ENTRADA\n{err_msg}")
            self.txt_table.configure(state="disabled")
            return

        solver = SecantRoots(func_str, x0, x1, tol, max_i)
        result = solver.solve()

        self.txt_res.configure(state="normal")
        self.txt_steps.configure(state="normal")
        self.txt_table.configure(state="normal")

        self.txt_res.delete("0.0", "end")
        self.txt_steps.delete("0.0", "end")
        self.txt_table.delete("0.0", "end")
        self._plot_payload = None
        self.ax.clear()
        self.apply_graph_theme()

        if not result["success"]:
            err_msg = result["error_message"]
            self.txt_res.insert("0.0", f"❌ Error:\n{err_msg}")
            self.txt_steps.insert("0.0", f"ERROR\n{err_msg}")

            if result["steps"]:
                table_text = "TABLA DE ITERACIONES — SECANTE\n\n"
                table_text += (
                    f"{'Iter':>4} | {'x_i':>14} | {'fp(x_i)':>15} | {'ea(%)':>10}\n"
                )
                table_text += "-" * 54 + "\n"
                for step in result["steps"]:
                    err_txt = f"{step['error']:.6g}" if step["error"] is not None else "---"
                    table_text += (
                        f"{step['iter']:>4} | {step['x']:>14.8g} | "
                        f"{step['fx']:>15.6g} | {err_txt:>10}\n"
                    )
                self.txt_table.insert("1.0", table_text)
            else:
                self.txt_table.insert("1.0", f"ERROR\n{err_msg}")

            self.txt_res.configure(state="disabled")
            self.txt_steps.configure(state="disabled")
            self.txt_table.configure(state="disabled")
            self.canvas.draw()
            return
            
        resumen = f"📊 Resumen de Ejecución:\n\n{result['message']}\n\n"
        resumen += f"f(x) = {result.get('original_expr', '---')}\n"
        resumen += f"f'(x) = {result.get('derivative_expr', '---')}\n"
        resumen += f"f''(x) = {result.get('second_derivative_expr', '---')}\n"
        resumen += f"Punto crítico x* ≈ {result['solution']:.8f}\n"
        resumen += f"f(x*) = {result.get('original_value', float('nan')):.6g}\n"
        resumen += f"f'(x*) = {result.get('derivative_value', float('nan')):.6g}\n"
        if result.get("second_derivative") is not None:
            resumen += f"f''(x*) = {result['second_derivative']:.6g}\n"
        resumen += f"Clasificación: {result.get('critical_type', 'inconcluso')}\n"
        resumen += f"{result.get('classification', '')}\n"
        resumen += "\nRecuerde: se resolvió f'(x)=0, no f(x)=0."
        self.txt_res.insert("0.0", resumen)

        sep = "─" * 60
        steps_text = (
            "PROCEDIMIENTO — SECANTE SOBRE f'(x)\n"
            f"f(x) = {result.get('original_expr', '---')}\n"
            f"f'(x) = {result.get('derivative_expr', '---')}\n"
            f"f''(x) = {result.get('second_derivative_expr', '---')}\n"
            "Objetivo: resolver f'(x) = 0 sin calcular f''(x).\n\n"
            "Fórmula:\n"
            "  x(k+1) = x(k) - f'(x(k))·(x(k) - x(k-1)) / (f'(x(k)) - f'(x(k-1)))\n\n"
            "Error relativo:\n"
            "  ea = |(x(k+1) - x(k)) / x(k+1)| * 100%\n\n"
        )

        history = result["steps"]
        if len(history) >= 3:
            for i in range(1, len(history) - 1):
                prev = history[i - 1]
                curr = history[i]
                nxt = history[i + 1]

                x_prev = prev["x"]
                f_prev = prev["fx"]
                x_curr = curr["x"]
                f_curr = curr["fx"]
                x_next = nxt["x"]
                denominador = f_curr - f_prev

                steps_text += sep + "\n"
                steps_text += f"ITERACIÓN {nxt['iter']}\n"
                steps_text += f"  x(k-1) = {x_prev:.10g}   f'(x(k-1)) = {f_prev:.10g}\n"
                steps_text += f"  x(k)   = {x_curr:.10g}   f'(x(k))   = {f_curr:.10g}\n"
                steps_text += "  x(k+1) = x(k) - f'(x(k))·(x(k) - x(k-1)) / (f'(x(k)) - f'(x(k-1)))\n"
                steps_text += (f"         = {x_curr:.10g} - ({f_curr:.10g})·"
                               f"({x_curr:.10g} - {x_prev:.10g}) / "
                               f"({f_curr:.10g} - {f_prev:.10g})\n")
                steps_text += f"         = {x_curr:.10g} - ({f_curr:.10g})·"
                steps_text += f"({x_curr - x_prev:.10g}) / ({denominador:.10g})\n"
                steps_text += f"         = {x_next:.10g}\n"
                if nxt["error"] is not None:
                    steps_text += f"  ea = {nxt['error']:.8g}%\n\n"
                else:
                    steps_text += "\n"

        final = history[-1]
        segunda_final = result.get("second_derivative")
        segunda_final_txt = (f"{segunda_final:.10g}" if segunda_final is not None
                             else "no evaluable")
        steps_text += "═" * 60 + "\n"
        steps_text += "RESULTADO FINAL\n"
        steps_text += f"  x* ≈ {final['x']:.10g}\n"
        steps_text += f"  f(x*) = {result.get('original_value', float('nan')):.8g}\n"
        steps_text += f"  f'(x*) = {final['fx']:.8g}\n"
        steps_text += f"  f''(x*) = {segunda_final_txt}\n"
        steps_text += f"  Clasificación: {result.get('critical_type', 'inconcluso')}\n"
        steps_text += f"  {result.get('classification', '')}\n"

        self.txt_steps.insert("1.0", steps_text)

        table_text = "TABLA DE ITERACIONES — SECANTE\n\n"
        table_text += (
            f"{'Iter':>4} | {'x_i':>14} | {'fp(x_i)':>14} | {'ea(%)':>10}\n"
        )
        table_text += "-" * 54 + "\n"
        for point in history:
            err_txt = f"{point['error']:.6g}" if point["error"] is not None else "---"
            table_text += (
                f"{point['iter']:>4} | {point['x']:>14.8g} | "
                f"{point['fx']:>14.6g} | {err_txt:>10}\n"
            )
        table_text += "-" * 54 + "\n"
        table_text += (
            f"Final: x* ≈ {final['x']:.10g}   f'(x*) = {final['fx']:.6g}   "
            f"f''(x*) = {segunda_final_txt}   iter = {len(history)}\n"
        )
        self.txt_table.insert("1.0", table_text)

        self.txt_res.configure(state="disabled")
        self.txt_steps.configure(state="disabled")
        self.txt_table.configure(state="disabled")
        
        self._plot_result(result, func_str, xmin, xmax)
