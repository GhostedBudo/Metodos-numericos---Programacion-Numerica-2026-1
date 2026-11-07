import customtkinter as ctk #pyright: ignore
from gui.theme import (
    COLOR_PANEL, COLOR_BORDER, COLOR_INTERACTIVE_BORDER,
    COLOR_ACCENT, COLOR_LIGHT_CYAN, COLOR_TEXT, COLOR_MUTED,
    get_title_font, get_label_font
)


class Sidebar(ctk.CTkFrame):
    """
    Barra lateral reducida a los tres métodos de optimización:
    Bisección, Newton y Secante sobre f'(x).
    """

    def __init__(self, master, active_method="bisection_method", **kwargs):
        super().__init__(
            master,
            width=240,
            corner_radius=0,
            fg_color=COLOR_PANEL,
            border_color=COLOR_BORDER,
            border_width=1,
            **kwargs
        )
        self.active_method = active_method
        self.title_font = get_title_font()
        self.label_font = get_label_font()

        self.grid_rowconfigure(6, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.create_widgets()

    def create_widgets(self):
        title_label = ctk.CTkLabel(
            self,
            text="Optimización\nNumérica",
            font=self.title_font,
            text_color=COLOR_LIGHT_CYAN,
            justify="center",
            anchor="center"
        )
        title_label.grid(row=0, column=0, padx=24, pady=(10, 3), sticky="ew")

        sep = ctk.CTkFrame(self, height=1, fg_color=COLOR_BORDER)
        sep.grid(row=1, column=0, sticky="ew", padx=24, pady=0)

        section = ctk.CTkLabel(
            self,
            text="Puntos críticos: f'(x) = 0",
            font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
            text_color=COLOR_MUTED
        )
        section.grid(row=2, column=0, padx=24, pady=(14, 4), sticky="w")

        sidebar_font = ctk.CTkFont(family="Inter", size=13, weight="bold")

        self.btn_bisection = self._make_button(
            row=3,
            text="      📐   Bisección",
            method="bisection_method",
            font=sidebar_font
        )
        self.btn_newton_roots = self._make_button(
            row=4,
            text="      📐   Newton",
            method="newton_roots",
            font=sidebar_font
        )
        self.btn_secant_roots = self._make_button(
            row=5,
            text="      📐   Secante",
            method="secant_roots",
            font=sidebar_font
        )

        theme_frame = ctk.CTkFrame(self, fg_color="transparent")
        theme_frame.grid(row=6, column=0, padx=24, pady=(0, 20), sticky="sew")

        theme_lbl = ctk.CTkLabel(
            theme_frame,
            text="🎨  Tema",
            font=sidebar_font,
            text_color=COLOR_TEXT
        )
        theme_lbl.pack(anchor="w", pady=(0, 4))

        self.theme_menu = ctk.CTkOptionMenu(
            theme_frame,
            values=["Oscuro", "Claro", "Sistema"],
            command=self.change_appearance_mode,
            fg_color=COLOR_PANEL,
            button_color=COLOR_INTERACTIVE_BORDER,
            button_hover_color=COLOR_ACCENT,
            dropdown_fg_color=COLOR_PANEL,
            dropdown_hover_color=COLOR_BORDER,
            dropdown_text_color=COLOR_TEXT,
            text_color=COLOR_TEXT,
            font=self.label_font,
            corner_radius=8,
            height=36
        )
        self.theme_menu.pack(fill="x")

        current_mode = ctk.get_appearance_mode()
        if current_mode == "Dark":
            self.theme_menu.set("Oscuro")
        elif current_mode == "Light":
            self.theme_menu.set("Claro")
        else:
            self.theme_menu.set("Sistema")

    def _make_button(self, row, text, method, font):
        is_active = self.active_method == method
        btn = ctk.CTkButton(
            self,
            text=text,
            fg_color=COLOR_INTERACTIVE_BORDER if is_active else "transparent",
            text_color=COLOR_LIGHT_CYAN if is_active else COLOR_TEXT,
            hover_color=COLOR_INTERACTIVE_BORDER,
            font=font,
            corner_radius=0,
            height=44,
            anchor="w",
            command=lambda: self._navigate(method)
        )
        btn.grid(row=row, column=0, padx=0, pady=0, sticky="ew")
        return btn

    def _navigate(self, method):
        if self.active_method == method:
            return
        app = self.winfo_toplevel()
        if hasattr(app, "switch_to_view"):
            app.switch_to_view(method)

    def change_appearance_mode(self, mode):
        if mode == "Claro":
            ctk.set_appearance_mode("light")
        elif mode == "Oscuro":
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("system")
