import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import math

# ------------------- Aplicar estilos modernos -------------------
def aplicar_estilos(root):
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure("TButton",
                    padding=6,
                    relief="flat",
                    background="#4CAF50",
                    foreground="white",
                    font=("Segoe UI", 10, "bold"),
                    borderwidth=0)
    style.map("TButton",
              background=[("active", "#45a049")])

    style.configure("TEntry",
                    padding=5,
                    relief="flat",
                    borderwidth=1,
                    font=("Segoe UI", 10))

    style.configure("TNotebook.Tab",
                    padding=[10, 6],
                    font=("Segoe UI", 10, "bold"))
    style.map("TNotebook.Tab",
              background=[("selected", "#4CAF50")],
              foreground=[("selected", "white")])

    style.configure("Treeview",
                    font=("Segoe UI", 10),
                    rowheight=26,
                    borderwidth=0,
                    relief="flat")
    style.configure("Treeview.Heading",
                    font=("Segoe UI", 10, "bold"),
                    background="#4CAF50",
                    foreground="white",
                    relief="flat")
    style.map("Treeview",
              background=[("selected", "#cce5ff")],
              foreground=[("selected", "black")])

# ---------- utilidades ----------
def parse_rangos(txt):
    if not txt or not txt.strip():
        return []
    parts = [p.strip() for p in txt.split(",")]
    idxs = set()
    for p in parts:
        if "-" in p:
            a, b = p.split("-")
            a = int(a); b = int(b)
            if a > b: a, b = b, a
            for i in range(a, b+1):
                if i >= 1:
                    idxs.add(i-1)
        else:
            i = int(p)
            if i >= 1:
                idxs.add(i-1)
    return sorted(idxs)

def compactar_indices_1based(indices0):
    if not indices0:
        return ""
    arr = sorted([i+1 for i in indices0])
    grupos = []
    ini = arr[0]
    prev = arr[0]
    for x in arr[1:]:
        if x == prev + 1:
            prev = x
        else:
            grupos.append((ini, prev))
            ini = x
            prev = x
    grupos.append((ini, prev))
    partes = []
    for a, b in grupos:
        if a == b:
            partes.append(f"{a}")
        else:
            partes.append(f"{a}-{b}")
    return ", ".join(partes)

def inv_poisson_u(u, lam):
    # Inversión por CDF con un solo U
    # F(k) = sum_{i=0}^k e^{-lam} lam^i / i!
    # iteramos hasta que F >= u
    if lam < 0:
        lam = 0.0
    k = 0
    p = math.exp(-lam)   # P(X=0)
    F = p
    while u > F:
        k += 1
        p *= lam / k     # Recurrencia para PMF
        F += p
    return k

def inv_geometrica_u(u, p):
    # Definición de número de ensayos hasta el primer éxito, valores 1,2,3,...
    if p <= 0: p = 1e-9
    if p >= 1: p = 1 - 1e-9
    return int(math.ceil(math.log(1 - u) / math.log(1 - p)))

def inv_binomial_u(u, n, p):
    # Inversión de CDF con un solo U (n entero razonable)
    if n < 0: n = 0
    if p < 0: p = 0.0
    if p > 1: p = 1.0
    # PMF inicial k=0
    q = 1 - p
    pmf = (q ** n)
    F = pmf
    k = 0
    while u > F and k < n:
        k += 1
        # pmf(k) = pmf(k-1) * (n-k+1)/k * p/q
        if q == 0:
            pmf = 0.0 if k < n else 1.0
        else:
            pmf = pmf * (n - k + 1) / k * (p / q)
        F += pmf
    return k

# ------------------- Clase principal -------------------
class SimuladorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulador de Colas y Entregas")
        self.root.geometry("1200x720")

        aplicar_estilos(root)

        # Guardar números y variables
        self.numeros_generados = []                 # lista de floats [0,1)
        self.variables_generadas = []               # [(nombre, dist, params_str, indices_str, cantidad)]
        self.variables_dict = {}                    # nombre -> np.array valores
        self.variables_meta = {}                    # nombre -> dict(meta)

        # Crear pestañas
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True)

        self.tab_rng = ttk.Frame(self.notebook)
        self.tab_numeros = ttk.Frame(self.notebook)
        self.tab_variables = ttk.Frame(self.notebook)
        self.tab_var_generadas = ttk.Frame(self.notebook)
        self.tab_colas = ttk.Frame(self.notebook)
        self.tab_entregas = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_rng, text="Generador Aleatorio")
        self.notebook.add(self.tab_numeros, text="Números Generados")
        self.notebook.add(self.tab_variables, text="Variables")
        self.notebook.add(self.tab_var_generadas, text="Variables Generadas")
        self.notebook.add(self.tab_colas, text="Tabla de Colas")
        self.notebook.add(self.tab_entregas, text="Tabla de Entregas")

        # Inicializar cada pestaña
        self.init_tab_rng()
        self.init_tab_numeros()
        self.init_tab_variables()
        self.init_tab_var_generadas()
        self.init_tab_colas()
        self.init_tab_entregas()

    # ------------------- Pestaña Generador -------------------
    def init_tab_rng(self):
        frame = ttk.Frame(self.tab_rng, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Seleccione el método:", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=5)

        self.metodo = tk.StringVar(value="mixto")
        rb1 = ttk.Radiobutton(frame, text="Congruencial Mixto", variable=self.metodo, value="mixto",
                        command=self.toggle_c)
        rb2 = ttk.Radiobutton(frame, text="Congruencial Multiplicativo", variable=self.metodo, value="multiplicativo",
                        command=self.toggle_c)
        rb1.pack(anchor="w")
        rb2.pack(anchor="w")

        self.param_frame = ttk.LabelFrame(frame, text="Parámetros", padding=10)
        self.param_frame.pack(fill="x", pady=10)

        ttk.Label(self.param_frame, text="Semilla (X₀):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.entry_x0 = ttk.Entry(self.param_frame, width=18)
        self.entry_x0.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.param_frame, text="Multiplicador (a):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.entry_a = ttk.Entry(self.param_frame, width=18)
        self.entry_a.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(self.param_frame, text="Incremento (c):").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.entry_c = ttk.Entry(self.param_frame, width=18)
        self.entry_c.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(self.param_frame, text="Módulo (m):").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.entry_m = ttk.Entry(self.param_frame, width=18)
        self.entry_m.grid(row=3, column=1, padx=5, pady=5)

        cwrap = ttk.Frame(frame)
        cwrap.pack(fill="x", pady=6)
        ttk.Label(cwrap, text="Cantidad de números a generar:").pack(side="left")
        self.entry_n = ttk.Entry(cwrap, width=12)
        self.entry_n.pack(side="left", padx=6)

        ttk.Button(frame, text="Generar", command=self.generar_numeros).pack(pady=10)

    def toggle_c(self):
        if self.metodo.get() == "multiplicativo":
            self.entry_c.delete(0, tk.END)
            self.entry_c.config(state="disabled")
        else:
            self.entry_c.config(state="normal")

    def generar_numeros(self):
        try:
            x = int(self.entry_x0.get())
            a = int(self.entry_a.get())
            m = int(self.entry_m.get())
            n = int(self.entry_n.get())
            if m <= 0:
                raise ValueError("El módulo m debe ser > 0")
            if n <= 0:
                raise ValueError("La cantidad debe ser > 0")
            c = int(self.entry_c.get()) if self.metodo.get() == "mixto" else 0

            self.numeros_generados.clear()
            for _ in range(n):
                if self.metodo.get() == "mixto":
                    x = (a * x + c) % m
                else:
                    x = (a * x) % m
                self.numeros_generados.append(x / m)

            self.update_numeros_table()
            messagebox.showinfo("Éxito", "Números generados correctamente")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ------------------- Pestaña Números -------------------
    def init_tab_numeros(self):
        cols = ("idx", "valor")
        self.tree_nums = ttk.Treeview(self.tab_numeros, columns=cols, show="headings", height=22)
        self.tree_nums.heading("idx", text="Índice")
        self.tree_nums.heading("valor", text="Número Pseudoaleatorio")
        self.tree_nums.column("idx", width=80, anchor="center")
        self.tree_nums.column("valor", width=220, anchor="center")
        self.tree_nums.pack(fill="both", expand=True, padx=20, pady=20)

    def update_numeros_table(self):
        for i in self.tree_nums.get_children():
            self.tree_nums.delete(i)
        for k, val in enumerate(self.numeros_generados, start=1):
            self.tree_nums.insert("", "end", values=(k, f"{val:.6f}"))

    # ------------------- Pestaña Variables -------------------
    def init_tab_variables(self):
        frame = ttk.Frame(self.tab_variables, padding=18)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Generación de Variables", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w", pady=(0,10), columnspan=4)

        # Tipo
        ttk.Label(frame, text="Distribución:").grid(row=1, column=0, sticky="w", padx=(0,6))
        self.var_tipo = tk.StringVar()
        self.cb_tipo = ttk.Combobox(frame, textvariable=self.var_tipo, state="readonly",
                          values=["Exponencial", "Normal", "Poisson", "Geométrica", "Binomial"], width=18)
        self.cb_tipo.grid(row=1, column=1, sticky="w")
        self.cb_tipo.bind("<<ComboboxSelected>>", self.on_tipo_change)

        # Nombre
        ttk.Label(frame, text="Nombre variable:").grid(row=1, column=2, sticky="e", padx=(20,6))
        self.entry_nombre_var = ttk.Entry(frame, width=20)
        self.entry_nombre_var.grid(row=1, column=3, sticky="w")

        # Parámetros dinámicos
        self.param_frame = ttk.LabelFrame(frame, text="Parámetros", padding=10)
        self.param_frame.grid(row=2, column=0, columnspan=4, sticky="we", pady=8)

        # Rangos U
        self.rangos_frame = ttk.LabelFrame(frame, text="Selección de U (índices 1..N)", padding=10)
        self.rangos_frame.grid(row=3, column=0, columnspan=4, sticky="we")

        # Botón generar
        ttk.Button(frame, text="Generar Variable", command=self.generar_variable).grid(row=4, column=0, columnspan=4, pady=12)

        # Preview de U seleccionadas
        self.preview_u = tk.Text(frame, height=6, width=90, relief="flat", borderwidth=1)
        self.preview_u.grid(row=5, column=0, columnspan=4, sticky="we", pady=(4,0))
        self.preview_u.configure(state="disabled")

        # Expansión
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_columnconfigure(3, weight=1)

        # Inicial
        self.on_tipo_change()

    def clear_param_frame(self):
        for w in self.param_frame.winfo_children():
            w.destroy()

    def clear_rangos_frame(self):
        for w in self.rangos_frame.winfo_children():
            w.destroy()

    def on_tipo_change(self, event=None):
        self.clear_param_frame()
        self.clear_rangos_frame()

        tipo = self.var_tipo.get()

        # Parámetros según distribución
        if tipo == "Exponencial":
            ttk.Label(self.param_frame, text="λ (lambda):").grid(row=0, column=0, sticky="w")
            self.p1 = ttk.Entry(self.param_frame, width=12)
            self.p1.grid(row=0, column=1, sticky="w")
        elif tipo == "Normal":
            ttk.Label(self.param_frame, text="μ (media):").grid(row=0, column=0, sticky="w")
            self.p1 = ttk.Entry(self.param_frame, width=12)
            self.p1.grid(row=0, column=1, sticky="w")
            ttk.Label(self.param_frame, text="σ (desv. est.):").grid(row=0, column=2, sticky="e", padx=(16,6))
            self.p2 = ttk.Entry(self.param_frame, width=12)
            self.p2.grid(row=0, column=3, sticky="w")
        elif tipo == "Poisson":
            ttk.Label(self.param_frame, text="λ (lambda):").grid(row=0, column=0, sticky="w")
            self.p1 = ttk.Entry(self.param_frame, width=12)
            self.p1.grid(row=0, column=1, sticky="w")
        elif tipo == "Geométrica":
            ttk.Label(self.param_frame, text="p (0-1):").grid(row=0, column=0, sticky="w")
            self.p1 = ttk.Entry(self.param_frame, width=12)
            self.p1.grid(row=0, column=1, sticky="w")
        elif tipo == "Binomial":
            ttk.Label(self.param_frame, text="n (entero):").grid(row=0, column=0, sticky="w")
            self.p1 = ttk.Entry(self.param_frame, width=12)
            self.p1.grid(row=0, column=1, sticky="w")
            ttk.Label(self.param_frame, text="p (0-1):").grid(row=0, column=2, sticky="e", padx=(16,6))
            self.p2 = ttk.Entry(self.param_frame, width=12)
            self.p2.grid(row=0, column=3, sticky="w")

        # Rangos de U
        if tipo == "Normal":
            ttk.Label(self.rangos_frame, text="Rangos U1 (ej: 1-5, 8, 10-12):").grid(row=0, column=0, sticky="w")
            self.entry_rangos_u1 = ttk.Entry(self.rangos_frame, width=50)
            self.entry_rangos_u1.grid(row=0, column=1, sticky="w", padx=(6,0))

            ttk.Label(self.rangos_frame, text="Rangos U2 (mismo total que U1):").grid(row=1, column=0, sticky="w")
            self.entry_rangos_u2 = ttk.Entry(self.rangos_frame, width=50)
            self.entry_rangos_u2.grid(row=1, column=1, sticky="w", padx=(6,0))
        else:
            ttk.Label(self.rangos_frame, text="Rangos U (ej: 1-10, 15-20):").grid(row=0, column=0, sticky="w")
            self.entry_rangos = ttk.Entry(self.rangos_frame, width=50)
            self.entry_rangos.grid(row=0, column=1, sticky="w", padx=(6,0))

        # Botón para previsualizar U
        ttk.Button(self.rangos_frame, text="Previsualizar U seleccionados", command=self.preview_u_seleccionados).grid(row=2, column=0, columnspan=2, pady=(8,0))

    def preview_u_seleccionados(self):
        tipo = self.var_tipo.get()
        txt = ""
        if not self.numeros_generados:
            messagebox.showwarning("Aviso", "Primero genera números pseudoaleatorios en la pestaña inicial.")
            return

        if tipo == "Normal":
            idx1 = parse_rangos(self.entry_rangos_u1.get())
            idx2 = parse_rangos(self.entry_rangos_u2.get())
            if len(idx1) != len(idx2):
                messagebox.showerror("Error", "U1 y U2 deben tener la misma cantidad de índices.")
                return
            u1 = [self.numeros_generados[i] for i in idx1 if i < len(self.numeros_generados)]
            u2 = [self.numeros_generados[i] for i in idx2 if i < len(self.numeros_generados)]
            txt += f"Índices U1: {compactar_indices_1based(idx1)}\n"
            txt += f"Índices U2: {compactar_indices_1based(idx2)}\n"
            txt += "Primeros valores U1:\n" + ", ".join(f"{x:.5f}" for x in u1[:12]) + ("\n" if len(u1) else "\n")
            txt += "Primeros valores U2:\n" + ", ".join(f"{x:.5f}" for x in u2[:12])
        else:
            idx = parse_rangos(self.entry_rangos.get())
            u = [self.numeros_generados[i] for i in idx if i < len(self.numeros_generados)]
            txt += f"Índices U: {compactar_indices_1based(idx)}\n"
            txt += "Primeros valores U:\n" + ", ".join(f"{x:.5f}" for x in u[:20])

        self.preview_u.configure(state="normal")
        self.preview_u.delete("1.0", tk.END)
        self.preview_u.insert("1.0", txt)
        self.preview_u.configure(state="disabled")

    def generar_variable(self):
        tipo = self.var_tipo.get()
        nombre = self.entry_nombre_var.get().strip()
        if not nombre:
            messagebox.showwarning("Aviso", "Ingrese un nombre para la variable.")
            return
        if not self.numeros_generados:
            messagebox.showwarning("Aviso", "Primero genera números pseudoaleatorios.")
            return

        try:
            # Obtener parámetros y U según distribución
            if tipo == "Exponencial":
                lam = float(self.p1.get())
                idx = parse_rangos(self.entry_rangos.get())
                if not idx:
                    messagebox.showerror("Error", "Especifique rangos de U.")
                    return
                U = np.array([self.numeros_generados[i] for i in idx if i < len(self.numeros_generados)])
                if lam <= 0:
                    raise ValueError("λ debe ser > 0")
                valores = -lam * np.log(1.0 - U)
                params_str = f"λ={lam}"

            elif tipo == "Normal":
                mu = float(self.p1.get())
                sigma = float(self.p2.get())
                if sigma <= 0:
                    raise ValueError("σ debe ser > 0")
                idx1 = parse_rangos(self.entry_rangos_u1.get())
                idx2 = parse_rangos(self.entry_rangos_u2.get())
                if len(idx1) == 0 or len(idx2) == 0:
                    messagebox.showerror("Error", "Indique rangos para U1 y U2.")
                    return
                if len(idx1) != len(idx2):
                    messagebox.showerror("Error", "U1 y U2 deben tener la misma cantidad de índices.")
                    return
                U1 = np.array([self.numeros_generados[i] for i in idx1 if i < len(self.numeros_generados)])
                U2 = np.array([self.numeros_generados[i] for i in idx2 if i < len(self.numeros_generados)])
                # Transformación de Box-Muller modificada
                # Z = sqrt(-2 * ln(1 - U1)) * cos(2π * U2)
                Z = np.sqrt(-2.0 * np.log(1.0 - U1)) * np.cos(2.0 * np.pi * U2)
                # Aplicar media y desviación estándar
                valores = mu + sigma * Z
                params_str = f"μ={mu}, σ={sigma}"

            elif tipo == "Poisson":
                lam = float(self.p1.get())
                if lam < 0:
                    raise ValueError("λ debe ser ≥ 0")
                idx = parse_rangos(self.entry_rangos.get())
                if not idx:
                    messagebox.showerror("Error", "Especifique rangos de U.")
                    return
                U = [self.numeros_generados[i] for i in idx if i < len(self.numeros_generados)]
                out = [inv_poisson_u(u, lam) for u in U]
                valores = np.array(out, dtype=int)
                params_str = f"λ={lam}"

            elif tipo == "Geométrica":
                p = float(self.p1.get())
                if not (0 < p < 1):
                    raise ValueError("p debe estar en (0,1)")
                idx = parse_rangos(self.entry_rangos.get())
                if not idx:
                    messagebox.showerror("Error", "Especifique rangos de U.")
                    return
                U = [self.numeros_generados[i] for i in idx if i < len(self.numeros_generados)]
                out = [inv_geometrica_u(u, p) for u in U]
                valores = np.array(out, dtype=int)
                params_str = f"p={p}"

            elif tipo == "Binomial":
                n = int(float(self.p1.get()))
                p = float(self.p2.get())
                if n < 0:
                    raise ValueError("n debe ser ≥ 0")
                if not (0 <= p <= 1):
                    raise ValueError("p debe estar en [0,1]")
                idx = parse_rangos(self.entry_rangos.get())
                if not idx:
                    messagebox.showerror("Error", "Especifique rangos de U.")
                    return
                U = [self.numeros_generados[i] for i in idx if i < len(self.numeros_generados)]
                out = [inv_binomial_u(u, n, p) for u in U]
                valores = np.array(out, dtype=int)
                params_str = f"n={n}, p={p}"
            else:
                messagebox.showerror("Error", "Seleccione una distribución.")
                return

            # Guardar
            self.variables_dict[nombre] = valores
            meta = {
                "dist": tipo,
                "params": params_str,
            }
            if tipo == "Normal":
                meta["indices"] = f"U1={compactar_indices_1based(parse_rangos(self.entry_rangos_u1.get()))}; " \
                                  f"U2={compactar_indices_1based(parse_rangos(self.entry_rangos_u2.get()))}"
            else:
                meta["indices"] = f"U={compactar_indices_1based(parse_rangos(self.entry_rangos.get()))}"
            self.variables_meta[nombre] = meta

            self.add_variable_row(nombre, tipo, params_str, meta["indices"], len(valores))
            messagebox.showinfo("Éxito", f"Variable '{nombre}' generada ({len(valores)} valores).")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ------------------- Pestaña Variables Generadas -------------------
    def init_tab_var_generadas(self):
        cols = ("nombre", "dist", "params", "indices", "cant")
        self.tree_vars = ttk.Treeview(self.tab_var_generadas,
                                      columns=cols,
                                      show="headings", height=18)
        headers = {
            "nombre": "Nombre",
            "dist": "Distribución",
            "params": "Parámetros",
            "indices": "Índices U usados",
            "cant": "Cantidad"
        }
        for c in cols:
            self.tree_vars.heading(c, text=headers[c])
        self.tree_vars.column("nombre", width=160, anchor="center")
        self.tree_vars.column("dist", width=140, anchor="center")
        self.tree_vars.column("params", width=260, anchor="w")
        self.tree_vars.column("indices", width=280, anchor="w")
        self.tree_vars.column("cant", width=100, anchor="center")
        self.tree_vars.pack(fill="both", expand=True, padx=20, pady=20)

        # Doble clic para ver valores
        self.tree_vars.bind("<Double-1>", self.ver_valores_variable)

    def add_variable_row(self, nombre, dist, params, indices, cant):
        # agregar o reemplazar si ya existe
        # primero borrar línea previa con mismo nombre (si existe)
        for item in self.tree_vars.get_children():
            vals = self.tree_vars.item(item, "values")
            if vals and vals[0] == nombre:
                self.tree_vars.delete(item)
                break
        self.tree_vars.insert("", "end", values=(nombre, dist, params, indices, cant))
        # refrescar combos en tablas
        self.refresh_combos_tablas()

    def ver_valores_variable(self, event):
        item = self.tree_vars.identify_row(event.y)
        if not item:
            return
        vals = self.tree_vars.item(item, "values")
        if not vals:
            return
        nombre = vals[0]
        data = self.variables_dict.get(nombre, None)
        if data is None:
            return
            
        # Obtener metadatos de la variable
        meta = self.variables_meta.get(nombre, {})
        dist = meta.get("dist", "")
        
        # Crear ventana con pestañas
        top = tk.Toplevel(self.root)
        top.title(f"Detalles de '{nombre}' - {dist}")
        top.geometry("750x600")
        
        notebook = ttk.Notebook(top)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Pestaña de valores
        tab_valores = ttk.Frame(notebook)
        notebook.add(tab_valores, text="Valores")
        
        # Área de texto con scroll para los valores
        scroll = ttk.Scrollbar(tab_valores)
        scroll.pack(side="right", fill="y")
        
        txt = tk.Text(tab_valores, wrap="none", yscrollcommand=scroll.set)
        txt.pack(fill="both", expand=True)
        scroll.config(command=txt.yview)
        
        # Mostrar valores
        txt.insert(tk.END, f"Variable: {nombre}\n")
        txt.insert(tk.END, f"Distribución: {dist}\n")
        txt.insert(tk.END, f"Parámetros: {meta.get('params', '')}\n")
        txt.insert(tk.END, f"Índices U: {meta.get('indices', '')}\n\n")
        txt.insert(tk.END, "Índice\tValor\n" + "-"*50 + "\n")
        
        for i, v in enumerate(data, start=1):
            txt.insert(tk.END, f"{i}\t{v:.6f}\n")
        
        # Pestaña de cálculos para todas las distribuciones
        tab_calculos = ttk.Frame(notebook)
        notebook.add(tab_calculos, text="Cálculos")
        
        # Crear área de texto con scroll
        scroll_calc = ttk.Scrollbar(tab_calculos)
        scroll_calc.pack(side="right", fill="y")
        
        txt_calc = tk.Text(tab_calculos, wrap="none", yscrollcommand=scroll_calc.set)
        txt_calc.pack(fill="both", expand=True)
        scroll_calc.config(command=txt_calc.yview)
        
        # Obtener índices U
        indices_text = meta.get("indices", "")
        
        if dist == "Normal":
            # Cálculos para distribución Normal
            u1_part = u2_part = ""
            if "U1=" in indices_text and "U2=" in indices_text:
                u1_part = indices_text.split("U1=")[1].split(";")[0].strip()
                u2_part = indices_text.split("U2=")[1].strip()
            
            idx1 = parse_rangos(u1_part.replace("U1=", "").strip())
            idx2 = parse_rangos(u2_part.replace("U2=", "").strip())
            
            if idx1 and idx2 and len(idx1) == len(idx2):
                U1 = [self.numeros_generados[i] for i in idx1 if i < len(self.numeros_generados)]
                U2 = [self.numeros_generados[i] for i in idx2 if i < len(self.numeros_generados)]
                
                # Obtener parámetros
                mu = float(meta["params"].split("μ=")[1].split(",")[0])
                sigma = float(meta["params"].split("σ=")[1])
                
                # Encabezado
                txt_calc.insert(tk.END, "Cálculos para Distribución Normal\n" + "="*80 + "\n\n")
                txt_calc.insert(tk.END, f"μ (media) = {mu}\n")
                txt_calc.insert(tk.END, f"σ (desviación estándar) = {sigma}\n\n")
                
                # Encabezado de la tabla
                txt_calc.insert(tk.END, f"{'i':<8} {'U1':<12} {'U2':<10} {'-2*ln(1-U1)':<12} "
                                      f"{'√(-2*ln(1-U1))':<12} {'2π*U2':<14} "
                                      f"{'cos(2πU2)':<11} {'Z':<12} {'X = μ + σZ':<12}\n")
                txt_calc.insert(tk.END, "-"*120 + "\n")
                
                # Mostrar cálculos para cada par (U1, U2)
                for i in range(min(len(U1), len(U2))):
                    u1 = U1[i]
                    u2 = U2[i]
                    
                    # Cálculos intermedios
                    log_term = -2 * math.log(1 - u1)
                    sqrt_term = math.sqrt(log_term)
                    two_pi_u2 = 2 * math.pi * u2
                    cos_term = math.cos(two_pi_u2)
                    Z = sqrt_term * cos_term
                    X = mu + sigma * Z
                    
                    # Formatear valores para mostrar
                    txt_calc.insert(tk.END, 
                        f"{i+1:<5} {u1:.6f}   {u2:.6f}   {log_term:>12.6f}   "
                        f"{sqrt_term:>15.6f}   {two_pi_u2:>10.6f}   "
                        f"{cos_term:>10.6f}   {Z:>10.6f}   {X:>10.6f}\n"
                    )
                
                # Explicación del cálculo
                txt_calc.insert(tk.END, "\n" + "="*80 + "\n")
                txt_calc.insert(tk.END, "Fórmula de transformación de Box-Muller:\n\n")
                txt_calc.insert(tk.END, "Z = √(-2·ln(1-U₁)) · cos(2π·U₂)\n")
                txt_calc.insert(tk.END, "X = μ + σ·Z\n\n")
                txt_calc.insert(tk.END, "Donde:\n")
                txt_calc.insert(tk.END, "- U₁, U₂ son números aleatorios ~U(0,1)\n")
                txt_calc.insert(tk.END, "- Z es una variable normal estándar (media=0, desv.est.=1)\n")
                txt_calc.insert(tk.END, "- X es la variable normal con media μ y desviación estándar σ\n")
        
        elif dist == "Exponencial":
            # Cálculos para distribución Exponencial
            idx = parse_rangos(indices_text.replace("U=", "").strip())
            U = [self.numeros_generados[i] for i in idx if i < len(self.numeros_generados)]
            
            # Obtener parámetro lambda
            lam = float(meta["params"].split("λ=")[1])
            
            # Encabezado
            txt_calc.insert(tk.END, "Cálculos para Distribución Exponencial\n" + "="*80 + "\n\n")
            txt_calc.insert(tk.END, f"λ (tasa) = {lam}\n\n")
            
            # Encabezado de la tabla
            txt_calc.insert(tk.END, f"{'i':<5} {'U':<15} {'1-U':<15} {'-ln(1-U)':<20} "
                                  f"{'X = -λ * ln(1-U)':<15}\n")
            txt_calc.insert(tk.END, "-"*80 + "\n")
            
            # Mostrar cálculos para cada U
            for i, u in enumerate(U):
                if i >= len(data):
                    break
                one_minus_u = 1 - u
                ln_term = -math.log(one_minus_u)
                X = (lam) * ln_term if lam != 0 else 0
                
                txt_calc.insert(tk.END, 
                    f"{i+1:<5} {u:.6f}   {one_minus_u:>10.6f}   "
                    f"{ln_term:>15.6f}   {X:>15.6f}\n"
                )
            
            # Explicación del cálculo
            txt_calc.insert(tk.END, "\n" + "="*80 + "\n")
            txt_calc.insert(tk.END, "Fórmula de transformación inversa para distribución exponencial:\n\n")
            txt_calc.insert(tk.END, "X = -1/λ * ln(1-U)\n\n")
            txt_calc.insert(tk.END, "Donde:\n")
            txt_calc.insert(tk.END, "- U es un número aleatorio ~U(0,1)\n")
            txt_calc.insert(tk.END, "- λ es el parámetro de tasa (λ > 0)\n")
            txt_calc.insert(tk.END, "- X es la variable exponencial generada\n")
        
        elif dist == "Poisson":
            # Cálculos para distribución Poisson
            idx = parse_rangos(indices_text.replace("U=", "").strip())
            U = [self.numeros_generados[i] for i in idx if i < len(self.numeros_generados)]
            
            # Obtener parámetro lambda
            lam = float(meta["params"].split("λ=")[1])
            
            # Encabezado
            txt_calc.insert(tk.END, "Cálculos para Distribución de Poisson\n" + "="*80 + "\n\n")
            txt_calc.insert(tk.END, f"λ (tasa) = {lam}\n\n")
            
            # Encabezado de la tabla
            txt_calc.insert(tk.END, f"{'i':<5} {'U':<15} {'k':<5} {'P(X=k)':<15} "
                                  f"{'Acumulado':<15} {'¿P ≤ U?':<10} {'X':<5}\n")
            txt_calc.insert(tk.END, "-"*80 + "\n")
            
            # Mostrar cálculos para cada U
            for i, u in enumerate(U):
                if i >= len(data):
                    break
                
                # Algoritmo de transformación inversa para Poisson
                k = 0
                p = math.exp(-lam)  # P(X=0)
                F = p
                
                # Mostrar cada paso hasta que F >= U
                txt_calc.insert(tk.END, f"{i+1:<5} {u:.6f}   ")
                
                while u > F:
                    txt_calc.insert(tk.END, f"{k:<5} {p:>10.6f}   {F:>10.6f}   "
                                         f"{'No':<10} {k}\n")
                    k += 1
                    p *= lam / k  # P(X=k) = (λ/k) * P(X=k-1)
                    F += p
                
                # Última iteración (cuando se acepta)
                txt_calc.insert(tk.END, f"{k:<5} {p:>10.6f}   {F:>10.6f}   "
                                     f"{'Sí':<10} {k}\n")
                
                txt_calc.insert(tk.END, "-"*80 + "\n")
            
            # Explicación del cálculo
            txt_calc.insert(tk.END, "\n" + "="*80 + "\n")
            txt_calc.insert(tk.END, "Algoritmo de transformación inversa para distribución de Poisson:\n\n")
            txt_calc.insert(tk.END, "1. Inicializar: k = 0, p = e^(-λ), F = p\n")
            txt_calc.insert(tk.END, "2. Mientras U > F:\n")
            txt_calc.insert(tk.END, "   a. k = k + 1\n")
            txt_calc.insert(tk.END, "   b. p = p * (λ / k)\n")
            txt_calc.insert(tk.END, "   c. F = F + p\n")
            txt_calc.insert(tk.END, "3. Retornar k\n\n")
            txt_calc.insert(tk.END, "Donde:\n")
            txt_calc.insert(tk.END, "- U es un número aleatorio ~U(0,1)\n")
            txt_calc.insert(tk.END, "- λ es el parámetro de tasa (λ > 0)\n")
            txt_calc.insert(tk.END, "- X es la variable de Poisson generada\n")
        
        elif dist == "Geométrica":
            # Cálculos para distribución Geométrica
            idx = parse_rangos(indices_text.replace("U=", "").strip())
            U = [self.numeros_generados[i] for i in idx if i < len(self.numeros_generados)]
            
            # Obtener parámetro p
            p = float(meta["params"].split("p=")[1])
            
            # Encabezado
            txt_calc.insert(tk.END, "Cálculos para Distribución Geométrica\n" + "="*80 + "\n\n")
            txt_calc.insert(tk.END, f"p (probabilidad de éxito) = {p}\n\n")
            
            # Encabezado de la tabla
            txt_calc.insert(tk.END, f"{'i':<5} {'U':<15} {'ln(1-U)':<15} "
                                  f"{'ln(1-p)':<15} {'X = ⌈ln(1-U)/ln(1-p)⌉':<20}\n")
            txt_calc.insert(tk.END, "-"*80 + "\n")
            
            # Mostrar cálculos para cada U
            for i, u in enumerate(U):
                if i >= len(data):
                    break
                
                if p == 1:  # Evitar división por cero
                    X = 1
                else:
                    ln_1_minus_u = math.log(1 - u)
                    ln_1_minus_p = math.log(1 - p)
                    X = math.ceil(ln_1_minus_u / ln_1_minus_p)
                    
                    txt_calc.insert(tk.END, 
                        f"{i+1:<5} {u:.6f}   {ln_1_minus_u:>10.6f}   "
                        f"{ln_1_minus_p:>10.6f}   {X:>10d}\n"
                    )
            
            # Explicación del cálculo
            txt_calc.insert(tk.END, "\n" + "="*80 + "\n")
            txt_calc.insert(tk.END, "Fórmula de transformación inversa para distribución geométrica:\n\n")
            txt_calc.insert(tk.END, "X = ⌈ln(1-U) / ln(1-p)⌉\n\n")
            txt_calc.insert(tk.END, "Donde:\n")
            txt_calc.insert(tk.END, "- U es un número aleatorio ~U(0,1)\n")
            txt_calc.insert(tk.END, "- p es la probabilidad de éxito en un ensayo (0 < p < 1)\n")
            txt_calc.insert(tk.END, "- X es el número de ensayos hasta el primer éxito\n")
        
        elif dist == "Binomial":
            # Cálculos para distribución Binomial
            idx = parse_rangos(indices_text.replace("U=", "").strip())
            U = [self.numeros_generados[i] for i in idx if i < len(self.numeros_generados)]
            
            # Obtener parámetros n y p
            n = int(meta["params"].split("n=")[1].split(",")[0])
            p = float(meta["params"].split("p=")[1])
            
            # Encabezado
            txt_calc.insert(tk.END, "Cálculos para Distribución Binomial\n" + "="*80 + "\n\n")
            txt_calc.insert(tk.END, f"n (número de ensayos) = {n}\n")
            txt_calc.insert(tk.END, f"p (probabilidad de éxito) = {p}\n\n")
            
            # Encabezado de la tabla
            txt_calc.insert(tk.END, f"{'i':<5} {'U':<15} {'k':<5} {'P(X=k)':<15} "
                                  f"{'Acumulado':<15} {'¿P ≤ U?':<10} {'X':<5}\n")
            txt_calc.insert(tk.END, "-"*80 + "\n")
            
            # Mostrar cálculos para cada U
            for i, u in enumerate(U):
                if i >= len(data):
                    break
                
                # Algoritmo de transformación inversa para Binomial
                k = 0
                q = 1 - p
                p_k = (q) ** n  # P(X=0) = (1-p)^n
                F = p_k
                
                # Mostrar cada paso hasta que F >= U o k = n
                txt_calc.insert(tk.END, f"{i+1:<5} {u:.6f}   ")
                
                while u > F and k < n:
                    txt_calc.insert(tk.END, f"{k:<5} {p_k:>10.6f}   {F:>10.6f}   "
                                         f"{'No':<10} {k}\n")
                    k += 1
                    # P(X=k) = C(n,k) * p^k * (1-p)^(n-k)
                    # Usamos la relación recursiva: P(X=k) = P(X=k-1) * (n-k+1)/k * p/(1-p)
                    p_k *= (n - k + 1) / k * (p / q) if k > 0 and q != 0 else 0
                    F += p_k
                
                # Última iteración (cuando se acepta o se llega a n)
                txt_calc.insert(tk.END, f"{k:<5} {p_k:>10.6f}   {F:>10.6f}   "
                                     f"{'Sí':<10} {k}\n")
                
                txt_calc.insert(tk.END, "-"*80 + "\n")
            
            # Explicación del cálculo
            txt_calc.insert(tk.END, "\n" + "="*80 + "\n")
            txt_calc.insert(tk.END, "Algoritmo de transformación inversa para distribución binomial:\n\n")
            txt_calc.insert(tk.END, f"1. Inicializar: k = 0, p_k = (1-p)^{n}, F = p_k\n")
            txt_calc.insert(tk.END, f"2. Mientras U > F y k < {n}:\n")
            txt_calc.insert(tk.END, "   a. k = k + 1\n")
            txt_calc.insert(tk.END, "   b. p_k = p_k * (n-k+1)/k * p/(1-p)\n")
            txt_calc.insert(tk.END, "   c. F = F + p_k\n")
            txt_calc.insert(tk.END, "3. Retornar k\n\n")
            txt_calc.insert(tk.END, "Donde:\n")
            txt_calc.insert(tk.END, "- U es un número aleatorio ~U(0,1)\n")
            txt_calc.insert(tk.END, f"- n es el número de ensayos (n = {n})\n")
            txt_calc.insert(tk.END, f"- p es la probabilidad de éxito en cada ensayo (p = {p})\n")
            txt_calc.insert(tk.END, "- X es el número de éxitos en n ensayos\n")

    # ------------------- Pestaña Colas -------------------
    def init_tab_colas(self):
        cont = ttk.Frame(self.tab_colas, padding=14)
        cont.pack(fill="both", expand=True)

        sel = ttk.Frame(cont)
        sel.pack(fill="x", pady=(0,10))

        ttk.Label(sel, text="Variable - Tiempo de llegada:").pack(side="left")
        self.cb_llegada = ttk.Combobox(sel, state="readonly", width=24, values=[])
        self.cb_llegada.pack(side="left", padx=(6,20))

        ttk.Label(sel, text="Variable - Tiempo de atención:").pack(side="left")
        self.cb_atencion = ttk.Combobox(sel, state="readonly", width=24, values=[])
        self.cb_atencion.pack(side="left", padx=(6,20))

        ttk.Button(sel, text="Generar Tabla de Colas", command=self.generar_tabla_colas).pack(side="left")

        cols = ("cliente","tiempo_llegada","tiempo_arribo","inicio_atencion",
                "tiempo_atencion","fin_atencion","tiempo_inspeccion",
                "tiempo_espera","tiempo_prom_inspeccion")

        self.tree_colas = ttk.Treeview(cont, columns=cols, show="headings", height=20)
        headers = {
            "cliente":"Cliente",
            "tiempo_llegada":"Tiempo de llegada",
            "tiempo_arribo":"Tiempo de arribo",
            "inicio_atencion":"Inicio de atención",
            "tiempo_atencion":"Tiempo de atención",
            "fin_atencion":"Fin de atención",
            "tiempo_inspeccion":"Tiempo en inspección",
            "tiempo_espera":"Tiempo en espera",
            "tiempo_prom_inspeccion":"Tiempo promedio inspección"
        }
        for c in cols:
            self.tree_colas.heading(c, text=headers[c])
        # Anchos / alineación
        self.tree_colas.column("cliente", width=80, anchor="center")
        for c in cols[1:]:
            self.tree_colas.column(c, width=140, anchor="center")

        self.tree_colas.pack(fill="both", expand=True, pady=6)

    def generar_tabla_colas(self):
        nombre_lleg = self.cb_llegada.get()
        nombre_aten = self.cb_atencion.get()
        if not nombre_lleg or not nombre_aten:
            messagebox.showerror("Error", "Seleccione las dos variables (llegada y atención).")
            return
        llegada = np.array(self.variables_dict.get(nombre_lleg, []), dtype=float)
        atencion = np.array(self.variables_dict.get(nombre_aten, []), dtype=float)
        if llegada.size == 0 or atencion.size == 0:
            messagebox.showerror("Error", "Alguna variable no tiene datos.")
            return

        n = int(min(len(llegada), len(atencion)))
        for i in self.tree_colas.get_children():
            self.tree_colas.delete(i)

        tiempo_arribo = 0.0
        fin_atencion_prev = 0.0
        prom = 0.0
        for i in range(n):
            cliente = i + 1
            A = float(llegada[i])  # Tiempo de llegada (inter-arribo)
            if i == 0:
                B = A  # tiempo de arribo
            else:
                B = tiempo_arribo + A
            C = max(B, fin_atencion_prev)        # inicio atención
            D = float(atencion[i])               # tiempo atención
            E = C + D                             # fin atención
            F = E - B                             # tiempo en inspección
            G = C - B                             # tiempo en espera
            prom = F if i == 0 else (prom * i + F) / (i + 1)  # promedio
            # guardar para siguiente iteración
            tiempo_arribo = B
            fin_atencion_prev = E

            self.tree_colas.insert("", "end",
                values=(cliente, round(A,2), round(B,2), round(C,2),
                        round(D,2), round(E,2), round(F,2), round(G,2), round(prom,2)))

    # ------------------- Pestaña Entregas -------------------
    def init_tab_entregas(self):
        cont = ttk.Frame(self.tab_entregas, padding=14)
        cont.pack(fill="both", expand=True)

        top = ttk.Frame(cont)
        top.pack(fill="x", pady=(0, 10))

        ttk.Label(top, text="Variable Demanda:").grid(row=0, column=0, sticky="w")
        self.cb_demanda = ttk.Combobox(top, state="readonly", width=24, values=[])
        self.cb_demanda.grid(row=0, column=1, padx=(6, 16))

        ttk.Label(top, text="Inventario inicial:").grid(row=0, column=2, sticky="e")
        self.e_inv_ini = ttk.Entry(top, width=10)
        self.e_inv_ini.grid(row=0, column=3, padx=(6, 16))
        self.e_inv_ini.insert(0, "50")

        ttk.Label(top, text="Entrega (reabastecimiento):").grid(row=0, column=4, sticky="e")
        self.e_entrega = ttk.Entry(top, width=10)
        self.e_entrega.grid(row=0, column=5, padx=(6, 16))
        self.e_entrega.insert(0, "50")

        ttk.Label(top, text="Frecuencia de entrega (días):").grid(row=0, column=6, sticky="e")
        self.e_frec_entrega = ttk.Entry(top, width=10)
        self.e_frec_entrega.grid(row=0, column=7, padx=(6, 16))
        self.e_frec_entrega.insert(0, "7")  # por defecto cada 7 días

        # Nueva: capacidad máxima de inventario (segunda fila para que sea visible)
        ttk.Label(top, text="Capacidad máx. inventario:").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.e_cap_max = ttk.Entry(top, width=10)
        self.e_cap_max.grid(row=1, column=1, padx=(6, 16), pady=(6, 0))
        self.e_cap_max.insert(0, "100")

        ttk.Label(top, text="Costo de ordenar (por pedido):").grid(row=2, column=0, sticky="w", pady=(6, 0))
        self.e_costo_orden = ttk.Entry(top, width=10)
        self.e_costo_orden.grid(row=2, column=1, padx=(6, 16), pady=(6, 0))
        self.e_costo_orden.insert(0, "10")

        ttk.Label(top, text="Costo inventario (por unidad):").grid(row=2, column=2, sticky="e", pady=(6, 0))
        self.e_costo_inv = ttk.Entry(top, width=10)
        self.e_costo_inv.grid(row=2, column=3, padx=(6, 16), pady=(6, 0))
        self.e_costo_inv.insert(0, "2")

        ttk.Label(top, text="Costo faltante (por unidad):").grid(row=2, column=4, sticky="e", pady=(6, 0))
        self.e_costo_falt = ttk.Entry(top, width=10)
        self.e_costo_falt.grid(row=2, column=5, padx=(6, 16), pady=(6, 0))
        self.e_costo_falt.insert(0, "5")

        # Mover botón a la segunda fila para que sea visible
        ttk.Button(top, text="Generar Tabla de Entregas", command=self.generar_tabla_entregas).grid(row=1, column=4,
                                                                                                     columnspan=2,
                                                                                                     padx=(10, 0),
                                                                                                     pady=(6, 0),
                                                                                                     sticky="w")

        cols = ("dia", "pedido", "entrega", "inv_inicial", "demanda", "ventas", "inv_final",
                "costo_orden", "costo_inv", "costo_falt", "costo_total", "costo_prom")

        self.tree_entregas = ttk.Treeview(cont, columns=cols, show="headings", height=20)
        headers = {
            "dia": "Día",
            "pedido": "Pedido solicitado",
            "entrega": "Entrega recibida",
            "inv_inicial": "Inventario inicial",
            "demanda": "Demanda",
            "ventas": "Ventas",
            "inv_final": "Inventario final",
            "costo_orden": "Costo de ordenar",
            "costo_inv": "Costo de inventario",
            "costo_falt": "Costo faltante",
            "costo_total": "Costo total",
            "costo_prom": "Costo promedio"
        }
        for c in cols:
            self.tree_entregas.heading(c, text=headers[c])

        self.tree_entregas.column("dia", width=70, anchor="center")
        self.tree_entregas.column("pedido", width=150, anchor="center")
        self.tree_entregas.column("entrega", width=150, anchor="center")
        self.tree_entregas.column("inv_inicial", width=140, anchor="center")
        self.tree_entregas.column("demanda", width=110, anchor="center")
        self.tree_entregas.column("ventas", width=100, anchor="center")
        self.tree_entregas.column("inv_final", width=120, anchor="center")
        self.tree_entregas.column("costo_orden", width=140, anchor="center")
        self.tree_entregas.column("costo_inv", width=140, anchor="center")
        self.tree_entregas.column("costo_falt", width=130, anchor="center")
        self.tree_entregas.column("costo_total", width=130, anchor="center")
        self.tree_entregas.column("costo_prom", width=130, anchor="center")

        self.tree_entregas.pack(fill="both", expand=True, pady=6)

    def generar_tabla_entregas(self):
        nombre = self.cb_demanda.get()
        if not nombre:
            messagebox.showerror("Error", "Seleccione la variable de demanda.")
            return
        demanda = np.array(self.variables_dict.get(nombre, []), dtype=float)
        if demanda.size == 0:
            messagebox.showerror("Error", "La variable de demanda no tiene datos.")
            return

        try:
            inv = int(float(self.e_inv_ini.get()))
            entrega_q = int(float(self.e_entrega.get()))
            frec_entrega = int(float(self.e_frec_entrega.get()))
            c_orden = float(self.e_costo_orden.get())
            c_inv_u = float(self.e_costo_inv.get())
            c_falt_u = float(self.e_costo_falt.get())
            cap_max = int(float(self.e_cap_max.get()))
        except:
            messagebox.showerror("Error", "Parámetros numéricos inválidos.")
            return

        # Limpiar tabla
        for i in self.tree_entregas.get_children():
            self.tree_entregas.delete(i)

        suma_costos = 0.0
        inv_actual = inv

        for i, dem in enumerate(demanda, start=1):
            pedido = 0
            entrega_recibida = 0
            costo_ord = 0.0

            # Recepción al inicio del día si corresponde
            if i > 1 and frec_entrega > 0 and (i % frec_entrega == 0):
                pedido = max(0, entrega_q)
                espacio = max(0, cap_max - inv_actual)
                entrega_recibida = min(pedido, espacio)
                if entrega_recibida > 0:
                    inv_actual += entrega_recibida
                    costo_ord = c_orden

            inv_inicial = inv_actual

            ventas = min(inv_inicial, dem)
            inv_final = inv_inicial - ventas

            # Cálculo de costos
            costo_inv = ((inv_inicial + inv_final) / 2.0) * c_inv_u
            costo_falt = max(0.0, dem - ventas) * c_falt_u
            costo_total = costo_ord + costo_inv + costo_falt
            suma_costos += costo_total
            costo_prom = suma_costos / i

            # Insertar fila en Treeview
            self.tree_entregas.insert("", "end",
                                      values=(i, round(pedido, 2), round(entrega_recibida, 2), round(inv_inicial, 2), round(dem, 2),
                                              round(ventas, 2), round(inv_final, 2), round(costo_ord, 2),
                                              round(costo_inv, 2), round(costo_falt, 2),
                                              round(costo_total, 2), round(costo_prom, 2)))

            inv_actual = inv_final

    # -------- util --------
    def refresh_combos_tablas(self):
        nombres = list(self.variables_dict.keys())
        self.cb_llegada["values"] = nombres
        self.cb_atencion["values"] = nombres
        self.cb_demanda["values"] = nombres

# ------------------- Main -------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = SimuladorApp(root)
    root.mainloop()
