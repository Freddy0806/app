import math
from typing import List, Tuple, Dict

Row = Tuple[int, float, float, float, float, float, float, float, float, float, float, float]


def simulate_entregas(
    demanda: List[float],
    inv_inicial: int,
    entrega_q: int,
    frec_entrega: int,
    cap_max: int,
    c_orden: float,
    c_inv_u: float,
    c_falt_u: float,
) -> List[Row]:
    """
    Simula el inventario con reabastecimiento periódico con capacidad máxima.

    Retorna una lista de filas con las columnas:
    (dia, pedido, entrega, inv_inicial, demanda, ventas, inv_final,
     costo_orden, costo_inv, costo_falt, costo_total, costo_prom)
    """
    rows: List[Row] = []

    inv_actual = float(inv_inicial)
    suma_costos = 0.0

    for i, dem in enumerate(demanda, start=1):
        pedido = 0.0
        entrega_recibida = 0.0
        costo_ord = 0.0

        # Recepción al inicio del día si corresponde (no en el día 1)
        if i > 1 and frec_entrega > 0 and (i % frec_entrega == 0):
            pedido = max(0.0, float(entrega_q))
            espacio = max(0.0, float(cap_max) - inv_actual)
            entrega_recibida = min(pedido, espacio)
            if entrega_recibida > 0:
                inv_actual += entrega_recibida
                costo_ord = c_orden

        inv_ini = inv_actual

        ventas = min(inv_ini, float(dem))
        inv_final = inv_ini - ventas

        # Costos
        costo_inv = ((inv_ini + inv_final) / 2.0) * c_inv_u
        costo_falt = max(0.0, float(dem) - ventas) * c_falt_u
        costo_total = costo_ord + costo_inv + costo_falt
        suma_costos += costo_total
        costo_prom = suma_costos / i

        rows.append(
            (
                i,
                round(pedido, 2),
                round(entrega_recibida, 2),
                round(inv_ini, 2),
                round(float(dem), 2),
                round(ventas, 2),
                round(inv_final, 2),
                round(costo_ord, 2),
                round(costo_inv, 2),
                round(costo_falt, 2),
                round(costo_total, 2),
                round(costo_prom, 2),
            )
        )

        inv_actual = inv_final

    return rows

# ---------------- RNG & helpers ----------------
def rng_congruencial_mixto(x0: int, a: int, c: int, m: int, n: int) -> List[float]:
    if m <= 0 or n <= 0:
        return []
    x = x0
    out = []
    for _ in range(n):
        x = (a * x + c) % m
        out.append(x / m)
    return out

def rng_congruencial_multiplicativo(x0: int, a: int, m: int, n: int) -> List[float]:
    if m <= 0 or n <= 0:
        return []
    x = x0
    out = []
    for _ in range(n):
        x = (a * x) % m
        out.append(x / m)
    return out

def parse_rangos(txt: str) -> List[int]:
    if not txt or not txt.strip():
        return []
    parts = [p.strip() for p in txt.split(',')]
    idxs = set()
    for p in parts:
        if not p:
            continue
        if '-' in p:
            try:
                a, b = p.split('-')
                a = int(a); b = int(b)
                if a > b:
                    a, b = b, a
                for i in range(a, b + 1):
                    if i >= 1:
                        idxs.add(i - 1)
            except:
                continue
        else:
            try:
                i = int(p)
                if i >= 1:
                    idxs.add(i - 1)
            except:
                continue
    return sorted(idxs)

# ---------------- Distributions ----------------
def inv_poisson_u(u: float, lam: float) -> int:
    if lam < 0:
        lam = 0.0
    k = 0
    p = math.exp(-lam)
    F = p
    while u > F:
        k += 1
        if k == 0:
            p = math.exp(-lam)
        else:
            p *= lam / k
        F += p
    return k

def inv_geometrica_u(u: float, p: float) -> int:
    if p <= 0:
        p = 1e-9
    if p >= 1:
        p = 1 - 1e-9
    return int(math.ceil(math.log(1 - u) / math.log(1 - p)))

def inv_binomial_u(u: float, n: int, p: float) -> int:
    if n < 0:
        n = 0
    if p < 0:
        p = 0.0
    if p > 1:
        p = 1.0
    q = 1 - p
    pmf = (q ** n)
    F = pmf
    k = 0
    while u > F and k < n:
        k += 1
        if q == 0:
            pmf = 0.0 if k < n else 1.0
        else:
            pmf = pmf * (n - k + 1) / k * (p / q)
        F += pmf
    return k

def generar_variable(
    tipo: str,
    numeros: List[float],
    nombre: str,
    params: Dict[str, float],
    indices: Dict[str, str],
) -> Tuple[List[float], Dict[str, str]]:
    """Genera una variable a partir de números uniformes y devuelve (valores, meta)."""
    tipo = (tipo or '').strip()
    meta: Dict[str, str] = {"dist": tipo}
    if tipo == 'Exponencial':
        lam = float(params.get('lam', 1.0))
        idx = parse_rangos(indices.get('U', ''))
        U = [numeros[i] for i in idx if i < len(numeros)]
        valores = [lam * (-math.log(1 - u)) for u in U]
        meta['params'] = f"λ={lam}"
        meta['indices'] = f"U={indices.get('U','')}"
        return valores, meta
    elif tipo == 'Normal':
        mu = float(params.get('mu', 0.0))
        sigma = float(params.get('sigma', 1.0))
        idx1 = parse_rangos(indices.get('U1', ''))
        idx2 = parse_rangos(indices.get('U2', ''))
        U1 = [numeros[i] for i in idx1 if i < len(numeros)]
        U2 = [numeros[i] for i in idx2 if i < len(numeros)]
        n = min(len(U1), len(U2))
        valores = []
        for i in range(n):
            u1, u2 = U1[i], U2[i]
            Z = math.sqrt(-2.0 * math.log(1.0 - u1)) * math.cos(2.0 * math.pi * u2)
            X = mu + sigma * Z
            valores.append(X)
        meta['params'] = f"μ={mu}, σ={sigma}"
        meta['indices'] = f"U1={indices.get('U1','')}; U2={indices.get('U2','')}"
        return valores, meta
    elif tipo == 'Poisson':
        lam = float(params.get('lam', 1.0))
        idx = parse_rangos(indices.get('U', ''))
        U = [numeros[i] for i in idx if i < len(numeros)]
        valores = [float(inv_poisson_u(u, lam)) for u in U]
        meta['params'] = f"λ={lam}"
        meta['indices'] = f"U={indices.get('U','')}"
        return valores, meta
    elif tipo == 'Geométrica':
        p = float(params.get('p', 0.5))
        idx = parse_rangos(indices.get('U', ''))
        U = [numeros[i] for i in idx if i < len(numeros)]
        valores = [float(inv_geometrica_u(u, p)) for u in U]
        meta['params'] = f"p={p}"
        meta['indices'] = f"U={indices.get('U','')}"
        return valores, meta
    elif tipo == 'Binomial':
        n = int(params.get('n', 1))
        p = float(params.get('p', 0.5))
        idx = parse_rangos(indices.get('U', ''))
        U = [numeros[i] for i in idx if i < len(numeros)]
        valores = [float(inv_binomial_u(u, n, p)) for u in U]
        meta['params'] = f"n={n}, p={p}"
        meta['indices'] = f"U={indices.get('U','')}"
        return valores, meta
    else:
        return [], {"dist": tipo, "params": "", "indices": ""}

# ---------------- Colas ----------------
def simulate_colas(llegada: List[float], atencion: List[float]) -> List[Tuple]:
    n = min(len(llegada), len(atencion))
    if n <= 0:
        return []
    rows = []
    tiempo_arribo = 0.0
    fin_atencion_prev = 0.0
    prom = 0.0
    for i in range(n):
        cliente = i + 1
        A = float(llegada[i])
        if i == 0:
            B = A
        else:
            B = tiempo_arribo + A
        C = max(B, fin_atencion_prev)
        D = float(atencion[i])
        E = C + D
        F = E - B
        G = C - B
        prom = F if i == 0 else (prom * i + F) / (i + 1)
        tiempo_arribo = B
        fin_atencion_prev = E
        rows.append((
            cliente, round(A, 2), round(B, 2), round(C, 2), round(D, 2), round(E, 2), round(F, 2), round(G, 2), round(prom, 2)
        ))
    return rows
