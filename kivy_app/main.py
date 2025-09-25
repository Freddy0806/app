from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRectangleFlatButton
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.tab import MDTabsBase
from kivymd.uix.tabs import MDTabs

from core_simulador import (
    simulate_entregas,
    rng_congruencial_mixto,
    rng_congruencial_multiplicativo,
    generar_variable,
    parse_rangos,
    simulate_colas,
)


# Estado compartido entre pestañas
class AppState:
    def __init__(self):
        self.numeros: list[float] = []
        self.variables: dict[str, list[float]] = {}
        self.variables_meta: dict[str, dict] = {}


class TabEntregas(MDBoxLayout, MDTabsBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = (10, 10, 10, 10)
        self.spacing = 10

        # Inputs area
        inputs = GridLayout(cols=6, spacing=10, size_hint_y=None)
        inputs.bind(minimum_height=inputs.setter('height'))

        # Campos
        self.tf_demanda = MDTextField(
            hint_text="Demanda (lista, ej: 10,12,9,11)",
            helper_text="Valores separados por coma",
            helper_text_mode="on_focus",
            size_hint_x=None, width=dp(280)
        )
        self.tf_demanda.text = "10,12,9,11,10,8,12,9,10,11"

        self.tf_inv_ini = MDTextField(hint_text="Inventario inicial", text="50", size_hint_x=None, width=dp(170))
        self.tf_entrega = MDTextField(hint_text="Pedido (cantidad)", text="50", size_hint_x=None, width=dp(170))
        self.tf_frec = MDTextField(hint_text="Frecuencia (días)", text="7", size_hint_x=None, width=dp(170))
        self.tf_cap = MDTextField(hint_text="Capacidad máx.", text="100", size_hint_x=None, width=dp(170))

        self.tf_c_orden = MDTextField(hint_text="Costo ordenar", text="10", size_hint_x=None, width=dp(150))
        self.tf_c_inv = MDTextField(hint_text="Costo inventario/u", text="2", size_hint_x=None, width=dp(170))
        self.tf_c_falt = MDTextField(hint_text="Costo faltante/u", text="5", size_hint_x=None, width=dp(170))

        # Organizar en la grilla (dos filas lógicas)
        inputs.add_widget(MDLabel(text="Demanda", halign="left"))
        inputs.add_widget(self.tf_demanda)
        inputs.add_widget(MDLabel(text="Inv. inicial", halign="left"))
        inputs.add_widget(self.tf_inv_ini)
        inputs.add_widget(MDLabel(text="Pedido", halign="left"))
        inputs.add_widget(self.tf_entrega)

        inputs.add_widget(MDLabel(text="Frecuencia", halign="left"))
        inputs.add_widget(self.tf_frec)
        inputs.add_widget(MDLabel(text="Cap. máx.", halign="left"))
        inputs.add_widget(self.tf_cap)
        inputs.add_widget(MDLabel(text="Costo ordenar", halign="left"))
        inputs.add_widget(self.tf_c_orden)

        inputs.add_widget(MDLabel(text="Costo inventario/u", halign="left"))
        inputs.add_widget(self.tf_c_inv)
        inputs.add_widget(MDLabel(text="Costo faltante/u", halign="left"))
        inputs.add_widget(self.tf_c_falt)
        # Espaciadores para completar columnas
        inputs.add_widget(Widget())
        inputs.add_widget(Widget())

        self.add_widget(inputs)

        # Botón generar
        self.btn_generar = MDRectangleFlatButton(text="Generar tabla", on_release=self.on_generar)
        self.add_widget(AnchorLayout(anchor_x="left", anchor_y="top", size_hint_y=None, height=dp(48)))
        self.children[0].add_widget(self.btn_generar)

        # Contenedor para tabla
        self.table_container = MDBoxLayout(orientation="vertical", size_hint=(1, 1))
        self.add_widget(self.table_container)

        self.table = None

    def parse_demanda(self) -> list:
        raw = self.tf_demanda.text.strip()
        if not raw:
            return []
        out = []
        for part in raw.split(','):
            part = part.strip()
            if not part:
                continue
            try:
                out.append(float(part))
            except:
                pass
        return out

    def on_generar(self, *_):
        demanda = self.parse_demanda()
        if not demanda:
            self.show_error("Demanda inválida. Ingrese números separados por coma.")
            return
        try:
            inv_inicial = int(float(self.tf_inv_ini.text))
            entrega_q = int(float(self.tf_entrega.text))
            frec = int(float(self.tf_frec.text))
            cap = int(float(self.tf_cap.text))
            c_orden = float(self.tf_c_orden.text)
            c_inv = float(self.tf_c_inv.text)
            c_falt = float(self.tf_c_falt.text)
        except Exception:
            self.show_error("Parámetros inválidos. Revise los campos numéricos.")
            return

        rows = simulate_entregas(
            demanda, inv_inicial, entrega_q, frec, cap, c_orden, c_inv, c_falt
        )
        self.render_table(rows)

    def render_table(self, rows):
        # Limpiar tabla anterior
        self.table_container.clear_widgets()
        if self.table:
            self.table = None

        column_data = [
            ("Día", dp(40)),
            ("Pedido", dp(70)),
            ("Entrega", dp(70)),
            ("Inv. inicial", dp(90)),
            ("Demanda", dp(80)),
            ("Ventas", dp(70)),
            ("Inv. final", dp(90)),
            ("Costo ordenar", dp(120)),
            ("Costo inventario", dp(130)),
            ("Costo faltante", dp(120)),
            ("Costo total", dp(110)),
            ("Costo prom.", dp(110)),
        ]
        row_data = [
            [*map(str, r)] for r in rows
        ]

        # MDDataTable ya tiene scroll; para móviles añadimos un ScrollView externo horizontal
        scroll = ScrollView(do_scroll_x=True, do_scroll_y=True, bar_width=dp(6))
        self.table = MDDataTable(
            size_hint=(None, None),
            size=(max(dp(1000), Window.width - dp(20)), Window.height - dp(260)),
            use_pagination=False,
            check=False,
            rows_num=min(20, max(10, len(row_data))),
            column_data=column_data,
            row_data=row_data,
        )
        # Ajuste de ancho total para permitir scroll horizontal si columnas exceden
        total_width = sum(w for _, w in column_data) + dp(40)
        self.table.size = (max(total_width, Window.width - dp(20)), self.table.size[1])

        scroll.add_widget(self.table)
        self.table_container.add_widget(scroll)

    def show_error(self, msg: str):
        from kivymd.uix.snackbar import Snackbar
        Snackbar(text=msg, duration=2).open()


# -------------- Pestaña RNG --------------
class TabRNG(MDBoxLayout, MDTabsBase):
    def __init__(self, state: AppState, **kwargs):
        super().__init__(**kwargs)
        self.state = state
        self.orientation = "vertical"
        self.spacing = 10
        self.padding = (10, 10, 10, 10)

        grid = GridLayout(cols=6, spacing=10, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        # Controles
        self.method = MDTextField(hint_text="Método (mixto/multiplicativo)", text="mixto", size_hint_x=None, width=dp(220))
        self.tx0 = MDTextField(hint_text="X0", text="17", size_hint_x=None, width=dp(120))
        self.ta = MDTextField(hint_text="a", text="101", size_hint_x=None, width=dp(120))
        self.tc = MDTextField(hint_text="c (solo mixto)", text="53", size_hint_x=None, width=dp(150))
        self.tm = MDTextField(hint_text="m", text="997", size_hint_x=None, width=dp(120))
        self.tn = MDTextField(hint_text="N cantidad", text="200", size_hint_x=None, width=dp(140))

        grid.add_widget(MDLabel(text="Método")); grid.add_widget(self.method)
        grid.add_widget(MDLabel(text="X0")); grid.add_widget(self.tx0)
        grid.add_widget(MDLabel(text="a")); grid.add_widget(self.ta)
        grid.add_widget(MDLabel(text="c")); grid.add_widget(self.tc)
        grid.add_widget(MDLabel(text="m")); grid.add_widget(self.tm)
        grid.add_widget(MDLabel(text="N")); grid.add_widget(self.tn)

        self.add_widget(grid)
        self.btn_gen = MDRectangleFlatButton(text="Generar números", on_release=self.on_generar)
        self.add_widget(AnchorLayout(anchor_x="left", anchor_y="top", size_hint_y=None, height=dp(48)))
        self.children[0].add_widget(self.btn_gen)

        self.lbl_info = MDLabel(text="", halign="left")
        self.add_widget(self.lbl_info)

    def on_generar(self, *_):
        try:
            x0 = int(float(self.tx0.text)); a = int(float(self.ta.text)); m = int(float(self.tm.text)); n = int(float(self.tn.text))
            metodo = (self.method.text or "").strip().lower()
            if metodo.startswith("mixt"):
                c = int(float(self.tc.text))
                nums = rng_congruencial_mixto(x0, a, c, m, n)
            else:
                nums = rng_congruencial_multiplicativo(x0, a, m, n)
            self.state.numeros = nums
            self.lbl_info.text = f"Generados {len(nums)} números."
        except Exception:
            self.lbl_info.text = "Error en parámetros."


# -------------- Pestaña Números --------------
class TabNumeros(MDBoxLayout, MDTabsBase):
    def __init__(self, state: AppState, **kwargs):
        super().__init__(**kwargs)
        self.state = state
        self.orientation = "vertical"
        self.padding = (10, 10, 10, 10)
        self.spacing = 10

        self.table_container = MDBoxLayout(orientation="vertical")
        self.add_widget(self.table_container)
        self.render_table()

    def on_pre_enter(self):
        self.render_table()

    def render_table(self):
        self.table_container.clear_widgets()
        nums = self.state.numeros
        column_data = [("#", dp(60)), ("Número", dp(160))]
        row_data = [[str(i+1), f"{v:.6f}"] for i, v in enumerate(nums)]
        scroll = ScrollView(do_scroll_x=True, do_scroll_y=True, bar_width=dp(6))
        table = MDDataTable(size_hint=(None, None), size=(max(dp(360), Window.width - dp(20)), Window.height - dp(200)),
                            use_pagination=False, check=False, rows_num=min(20, max(10, len(row_data))),
                            column_data=column_data, row_data=row_data)
        total_width = sum(w for _, w in column_data) + dp(40)
        table.size = (max(total_width, Window.width - dp(20)), table.size[1])
        scroll.add_widget(table)
        self.table_container.add_widget(scroll)


# -------------- Pestaña Variables --------------
class TabVariables(MDBoxLayout, MDTabsBase):
    def __init__(self, state: AppState, **kwargs):
        super().__init__(**kwargs)
        self.state = state
        self.orientation = "vertical"
        self.spacing = 10
        self.padding = (10, 10, 10, 10)

        grid = GridLayout(cols=6, spacing=10, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        self.tipo = MDTextField(hint_text="Distribución (Exponencial/Normal/Poisson/Geométrica/Binomial)", size_hint_x=None, width=dp(420))
        self.nombre = MDTextField(hint_text="Nombre variable", size_hint_x=None, width=dp(220))
        self.p1 = MDTextField(hint_text="p1 (λ/μ/n)", size_hint_x=None, width=dp(150))
        self.p2 = MDTextField(hint_text="p2 (σ/p)", size_hint_x=None, width=dp(150))
        self.rU = MDTextField(hint_text="Rangos U (ej 1-10,12)", size_hint_x=None, width=dp(260))
        self.rU1 = MDTextField(hint_text="Rangos U1 (Normal)", size_hint_x=None, width=dp(260))
        self.rU2 = MDTextField(hint_text="Rangos U2 (Normal)", size_hint_x=None, width=dp(260))

        grid.add_widget(MDLabel(text="Dist.")); grid.add_widget(self.tipo)
        grid.add_widget(MDLabel(text="Nombre")); grid.add_widget(self.nombre)
        grid.add_widget(MDLabel(text="p1")); grid.add_widget(self.p1)
        grid.add_widget(MDLabel(text="p2")); grid.add_widget(self.p2)
        grid.add_widget(MDLabel(text="U")); grid.add_widget(self.rU)
        grid.add_widget(MDLabel(text="U1")); grid.add_widget(self.rU1)
        grid.add_widget(MDLabel(text="U2")); grid.add_widget(self.rU2)
        self.add_widget(grid)

        self.btn = MDRectangleFlatButton(text="Generar Variable", on_release=self.on_generar)
        self.add_widget(AnchorLayout(anchor_x="left", anchor_y="top", size_hint_y=None, height=dp(48)))
        self.children[0].add_widget(self.btn)

        self.lbl = MDLabel(text="", halign="left")
        self.add_widget(self.lbl)

    def on_generar(self, *_):
        if not self.state.numeros:
            self.lbl.text = "Primero genere números en RNG."
            return
        tipo = (self.tipo.text or '').strip().capitalize()
        nombre = (self.nombre.text or '').strip()
        if not nombre:
            self.lbl.text = "Ingrese nombre."
            return

        params = {}
        indices = {}
        try:
            if tipo == 'Exponencial':
                params['lam'] = float(self.p1.text)
                indices['U'] = self.rU.text
            elif tipo == 'Normal':
                params['mu'] = float(self.p1.text)
                params['sigma'] = float(self.p2.text)
                indices['U1'] = self.rU1.text
                indices['U2'] = self.rU2.text
            elif tipo == 'Poisson':
                params['lam'] = float(self.p1.text)
                indices['U'] = self.rU.text
            elif tipo == 'Geométrica':
                params['p'] = float(self.p1.text)
                indices['U'] = self.rU.text
            elif tipo == 'Binomial':
                params['n'] = int(float(self.p1.text))
                params['p'] = float(self.p2.text)
                indices['U'] = self.rU.text
            else:
                self.lbl.text = "Distribución inválida."
                return
        except Exception:
            self.lbl.text = "Parámetros inválidos."
            return

        valores, meta = generar_variable(tipo, self.state.numeros, nombre, params, indices)
        if not valores:
            self.lbl.text = "No se generaron valores (revisar rangos U)."
            return
        self.state.variables[nombre] = valores
        self.state.variables_meta[nombre] = meta
        self.lbl.text = f"Variable '{nombre}' generada ({len(valores)})."


# -------------- Pestaña Variables Generadas --------------
class TabVarGen(MDBoxLayout, MDTabsBase):
    def __init__(self, state: AppState, **kwargs):
        super().__init__(**kwargs)
        self.state = state
        self.orientation = "vertical"
        self.padding = (10, 10, 10, 10)
        self.spacing = 10
        self.table_container = MDBoxLayout(orientation="vertical")
        self.add_widget(self.table_container)
        self.render_table()

    def on_pre_enter(self):
        self.render_table()

    def render_table(self):
        self.table_container.clear_widgets()
        cols = [("Nombre", dp(160)), ("Dist.", dp(120)), ("Parámetros", dp(240)), ("Índices", dp(260)), ("Cantidad", dp(100))]
        row_data = []
        for nombre, vals in self.state.variables.items():
            meta = self.state.variables_meta.get(nombre, {})
            row_data.append([
                nombre,
                meta.get('dist',''),
                meta.get('params',''),
                meta.get('indices',''),
                str(len(vals))
            ])
        scroll = ScrollView(do_scroll_x=True, do_scroll_y=True, bar_width=dp(6))
        table = MDDataTable(size_hint=(None, None), size=(max(dp(1000), Window.width - dp(20)), Window.height - dp(220)),
                            use_pagination=False, check=False, rows_num=min(20, max(10, len(row_data))),
                            column_data=cols, row_data=row_data)
        total_width = sum(w for _, w in cols) + dp(40)
        table.size = (max(total_width, Window.width - dp(20)), table.size[1])
        scroll.add_widget(table)
        self.table_container.add_widget(scroll)


# -------------- Pestaña Colas --------------
class TabColas(MDBoxLayout, MDTabsBase):
    def __init__(self, state: AppState, **kwargs):
        super().__init__(**kwargs)
        self.state = state
        self.orientation = "vertical"
        self.spacing = 10
        self.padding = (10, 10, 10, 10)

        grid = GridLayout(cols=6, spacing=10, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))
        self.tf_lleg = MDTextField(hint_text="Nombre var llegada", size_hint_x=None, width=dp(240))
        self.tf_aten = MDTextField(hint_text="Nombre var atención", size_hint_x=None, width=dp(240))
        self.lbl_vars = MDLabel(text="Disponibles: (se actualiza al abrir)", halign="left")
        grid.add_widget(MDLabel(text="Llegada")); grid.add_widget(self.tf_lleg)
        grid.add_widget(MDLabel(text="Atención")); grid.add_widget(self.tf_aten)
        grid.add_widget(MDLabel(text="")); grid.add_widget(MDLabel(text=""))
        self.add_widget(grid)

        self.btn = MDRectangleFlatButton(text="Generar tabla de colas", on_release=self.on_generar)
        self.add_widget(AnchorLayout(anchor_x="left", anchor_y="top", size_hint_y=None, height=dp(48)))
        self.children[0].add_widget(self.btn)
        self.add_widget(self.lbl_vars)

        self.table_container = MDBoxLayout(orientation="vertical")
        self.add_widget(self.table_container)

    def on_pre_enter(self):
        nombres = list(self.state.variables.keys())
        self.lbl_vars.text = "Disponibles: " + ", ".join(nombres) if nombres else "No hay variables."

    def on_generar(self, *_):
        llegada = self.state.variables.get((self.tf_lleg.text or '').strip(), [])
        atencion = self.state.variables.get((self.tf_aten.text or '').strip(), [])
        rows = simulate_colas(llegada, atencion)
        self.render_table(rows)

    def render_table(self, rows):
        self.table_container.clear_widgets()
        cols = [
            ("Cliente", dp(90)), ("Tiempo llegada", dp(130)), ("Tiempo arribo", dp(130)),
            ("Inicio atención", dp(130)), ("Tiempo atención", dp(130)), ("Fin atención", dp(130)),
            ("Tiempo inspección", dp(150)), ("Tiempo espera", dp(130)), ("Prom. inspección", dp(150))
        ]
        row_data = [[*map(str, r)] for r in rows]
        scroll = ScrollView(do_scroll_x=True, do_scroll_y=True, bar_width=dp(6))
        table = MDDataTable(size_hint=(None, None), size=(max(dp(1200), Window.width - dp(20)), Window.height - dp(260)),
                            use_pagination=False, check=False, rows_num=min(20, max(10, len(row_data))),
                            column_data=cols, row_data=row_data)
        total_width = sum(w for _, w in cols) + dp(40)
        table.size = (max(total_width, Window.width - dp(20)), table.size[1])
        scroll.add_widget(table)
        self.table_container.add_widget(scroll)


class SimuladorApp(MDApp):
    def build(self):
        self.title = "Simulador (KivyMD)"
        self.theme_cls.primary_palette = "Green"
        root = MDBoxLayout(orientation="vertical")

        self.state = AppState()

        tabs = MDTabs()
        tabs.add_widget(TabRNG(self.state, title="RNG"))
        tabs.add_widget(TabNumeros(self.state, title="Números"))
        tabs.add_widget(TabVariables(self.state, title="Variables"))
        tabs.add_widget(TabVarGen(self.state, title="Var. Generadas"))
        tabs.add_widget(TabColas(self.state, title="Colas"))
        tabs.add_widget(TabEntregas(title="Entregas"))
        root.add_widget(tabs)
        return root


if __name__ == "__main__":
    SimuladorApp().run()
