import customtkinter as ctk #pyright: ignore
from gui.bisection_method.bisection_method_view import BisectionMethodView
from gui.newton_raphson.newton_rapshon_view import NewtonRootsView
from gui.secante.secante_view import SecantRootsView
from gui.theme import COLOR_BG


class GaussSimpleApp(ctk.CTk):
    """
    Contenedor principal de la aplicación de optimización.
    Solo contiene los métodos de Bisección, Newton y Secante sobre f'(x).
    """

    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")

        self.title("Optimización Numérica — f'(x) = 0")

        width = 1300
        height = 800

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)

        self.geometry(f"{width}x{height}+{x}+{y}")
        self.minsize(1000, 650)
        self.configure(fg_color=COLOR_BG)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_main_container()

    def create_main_container(self):
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        self.current_view = BisectionMethodView(self.main_container)
        self.current_view.grid(row=0, column=0, sticky="nsew")

    def switch_to_view(self, view_name):
        """Alterna entre las tres vistas de optimización."""
        views = {
            "bisection_method": BisectionMethodView,
            "newton_roots": NewtonRootsView,
            "secant_roots": SecantRootsView,
        }

        view_class = views.get(view_name)
        if view_class is None:
            return
        if isinstance(self.current_view, view_class):
            return

        self.current_view.destroy()
        self.current_view = view_class(self.main_container)
        self.current_view.grid(row=0, column=0, sticky="nsew")

    def _on_close(self):
        self.quit()
        self.destroy()
