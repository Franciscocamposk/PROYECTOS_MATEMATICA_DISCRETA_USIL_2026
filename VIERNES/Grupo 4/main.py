"""Proyecto final P04 - Aves migratorias: el árbol de humedales que las une sin rodeos.

Lee el Excel (hojas Vuelos y Humedales), arma el grafo no dirigido de tramos
activos, calcula un árbol generador con Kruskal (union-find), comprueba que es
un árbol (conexo y sin ciclos), compara los km contra la red completa y guarda
aves_arbol.png.

Uso:  python main.py
"""

from pathlib import Path

import networkx as nx
import pandas as pd

PROJECT = Path(__file__).resolve().parent
EXCEL = PROJECT / "P04_Aves_humedales.xlsx"
PNG = PROJECT / "aves_arbol.png"
PARQUES = ["PaloVerde", "CanoNegro", "Tortuguero", "Carara"]


# --------------------------------------------------------------------------
# 1. Lectura de datos y grafo
# --------------------------------------------------------------------------
def leer_excel(path):
    """Devuelve (vuelos, humedales) limpios, leídos con pandas."""
    vuelos = pd.read_excel(path, sheet_name="Vuelos")
    humedales = pd.read_excel(path, sheet_name="Humedales")
    for col in ("origen", "destino", "activo"):
        vuelos[col] = vuelos[col].astype(str).str.strip()
    vuelos["activo"] = vuelos["activo"].str.lower()
    humedales["humedal"] = humedales["humedal"].astype(str).str.strip()
    return vuelos, humedales


def construir_grafo(vuelos, humedales):
    """Grafo no dirigido: nodos = hoja Humedales; aristas = vuelos activo == 'si'.

    Como la red es no dirigida, A-B y B-A son el mismo tramo; si el tramo se
    repite se conserva el menor km. Se descartan autolazos.
    """
    nodos = set(humedales["humedal"])
    activos = vuelos[vuelos["activo"] == "si"]
    desconocidos = (set(activos["origen"]) | set(activos["destino"])) - nodos
    if desconocidos:
        raise ValueError("Vuelos menciona humedales que no están en la hoja Humedales: "
                         + ", ".join(sorted(desconocidos)))
    G = nx.Graph()
    G.add_nodes_from(sorted(nodos))
    for fila in activos.itertuples(index=False):
        u, v, km = fila.origen, fila.destino, float(fila.km)
        if u == v:
            continue
        if not G.has_edge(u, v) or km < G[u][v]["km"]:
            G.add_edge(u, v, km=km)
    return G


def leer_grafo(path):
    """Atajo: Excel -> grafo."""
    return construir_grafo(*leer_excel(path))


# --------------------------------------------------------------------------
# 2. Árbol generador: Kruskal con conjuntos disjuntos (union-find)
# --------------------------------------------------------------------------
class ConjuntosDisjuntos:
    def __init__(self, elementos):
        self.padre = {x: x for x in elementos}
        self.rango = {x: 0 for x in elementos}

    def buscar(self, x):
        while self.padre[x] != x:
            self.padre[x] = self.padre[self.padre[x]]  # compresión de camino
            x = self.padre[x]
        return x

    def unir(self, a, b):
        ra, rb = self.buscar(a), self.buscar(b)
        if ra == rb:
            return False  # ya conectados: agregar la arista cerraría un ciclo
        if self.rango[ra] < self.rango[rb]:
            ra, rb = rb, ra
        self.padre[rb] = ra
        if self.rango[ra] == self.rango[rb]:
            self.rango[ra] += 1
        return True


def arbol_generador(G):
    """Kruskal: ordena las aristas por km y agrega la que no forme ciclo."""
    T = nx.Graph()
    T.add_nodes_from(G.nodes())
    conjuntos = ConjuntosDisjuntos(G.nodes())
    for u, v, d in sorted(G.edges(data=True), key=lambda e: (e[2]["km"], e[0], e[1])):
        if conjuntos.unir(u, v):
            T.add_edge(u, v, km=d["km"])
    return T


# --------------------------------------------------------------------------
# 3. Comprobaciones calculadas (no escritas a mano)
# --------------------------------------------------------------------------
def ciclos_independientes(G):
    """Número ciclomático |E| - |V| + C (C = componentes conexas)."""
    return G.number_of_edges() - G.number_of_nodes() + nx.number_connected_components(G)


def km_total(G):
    return sum(d["km"] for _, _, d in G.edges(data=True))


def verificar_arbol(T):
    """Prueba de que T es árbol: conexo, |E| = |V|-1 y 0 ciclos independientes."""
    n, m = T.number_of_nodes(), T.number_of_edges()
    return {
        "vertices": n,
        "aristas": m,
        "conexo": nx.is_connected(T),
        "ciclos": ciclos_independientes(T),
        "es_arbol": nx.is_tree(T),
    }


def validar_linea(n=4):
    """Caso del enunciado: n humedales en línea dan n-1 tramos y 0 ciclos."""
    L = nx.path_graph([f"H{i}" for i in range(1, n + 1)])
    nx.set_edge_attributes(L, 10.0, "km")
    return arbol_generador(L)


# --------------------------------------------------------------------------
# 4. Gráfico
# --------------------------------------------------------------------------
def _punto(pos, u, v, t):
    return (pos[u][0] + t * (pos[v][0] - pos[u][0]),
            pos[u][1] + t * (pos[v][1] - pos[u][1]))


def dibujar_ave_arbol(G, T, png):
    """Red completa en gris, árbol generador en verde grueso, km en las aristas."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    pos = nx.circular_layout(sorted(G.nodes()))
    fig, ax = plt.subplots(figsize=(11, 8))

    # red completa (gris) con km pequeños, cerca del primer extremo para no apilarse
    for i, (u, v, d) in enumerate(G.edges(data=True)):
        if T.has_edge(u, v):
            continue
        ax.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]],
                color="0.78", linewidth=0.9, zorder=1)
        x, y = _punto(pos, u, v, (0.2, 0.3, 0.4)[i % 3])
        ax.text(x, y, f'{d["km"]:.0f}', ha="center", va="center", fontsize=6.5,
                color="0.35", zorder=2,
                bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.9))

    # árbol generador (verde grueso) con km legibles
    for u, v, d in T.edges(data=True):
        ax.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]],
                color="#1f8f3f", linewidth=4.5, solid_capstyle="round", zorder=3)
        x, y = _punto(pos, u, v, 0.5)
        ax.text(x, y, f'{d["km"]:.0f} km', ha="center", va="center", fontsize=9,
                fontweight="bold", color="#0b4d20", zorder=5,
                bbox=dict(boxstyle="round,pad=0.25", fc="#e6f5ea", ec="#1f8f3f", lw=1))

    # nodos y nombres (fuera del punto)
    for n in G.nodes():
        ax.plot(*pos[n], "o", color="#f2a900", mec="black", ms=13, zorder=6)
        x, y = pos[n]
        ha = "left" if x > 0.5 else ("right" if x < -0.5 else "center")
        ax.annotate(n, (x, y), xytext=(x * 1.08 + (0.05 if x > 0.5 else -0.05 if x < -0.5 else 0),
                                       y * 1.12), textcoords="data",
                    ha=ha, va="center", fontsize=10, fontweight="bold", zorder=7)

    ahorro = km_total(G) - km_total(T)
    ax.set_title("Humedales: red completa activa (gris) y árbol generador (verde)\n"
                 f"Árbol: {km_total(T):.0f} km en {T.number_of_edges()} tramos | "
                 f"Red: {km_total(G):.0f} km en {G.number_of_edges()} tramos | "
                 f"Ahorro: {ahorro:.0f} km", fontsize=11)
    ax.set_xlim(-1.6, 1.6)
    ax.set_ylim(-1.3, 1.3)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.savefig(png, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# --------------------------------------------------------------------------
# 5. Decisión para el cliente
# --------------------------------------------------------------------------
def decision(G, T):
    total_t, total_g = km_total(T), km_total(G)
    ahorro = total_g - total_t
    pct = 100 * ahorro / total_g if total_g else 0
    chk = verificar_arbol(T)

    print("=== P04 - Aves migratorias: el árbol de humedales que las une sin rodeos ===")
    print(f"Humedales ({G.number_of_nodes()}): " + ", ".join(sorted(G.nodes())))
    print(f"Red activa: {G.number_of_edges()} tramos únicos, {total_g:.0f} km, "
          f"conexa = {'sí' if nx.is_connected(G) else 'NO'}, "
          f"ciclos independientes = {ciclos_independientes(G)}")
    if not nx.is_connected(G):
        print("AVISO: la red activa no es conexa; solo existe un bosque generador "
              "(un árbol por componente).")

    print(f"\nÁrbol generador (Kruskal): {T.number_of_edges()} tramos, {total_t:.0f} km")
    for u, v, d in sorted(T.edges(data=True), key=lambda e: e[2]["km"]):
        print(f"   {u} - {v}: {d['km']:.0f} km")

    print("\nPrueba de que no hay ciclo:")
    print(f"   aristas = {chk['aristas']} y vértices - 1 = {chk['vertices'] - 1}")
    print(f"   conexo = {chk['conexo']}, ciclos independientes (|E|-|V|+1) = {chk['ciclos']}")
    print(f"   es árbol = {chk['es_arbol']}")

    print(f"\nComparación: árbol {total_t:.0f} km vs red completa {total_g:.0f} km "
          f"-> se ahorran {ahorro:.0f} km ({pct:.1f} %) y se descartan "
          f"{G.number_of_edges() - T.number_of_edges()} tramos.")

    parques = G.subgraph(PARQUES)
    Tp = arbol_generador(parques)
    chk_p = verificar_arbol(Tp)
    print(f"\nValidación - 4 parques ({', '.join(PARQUES)}): "
          f"{Tp.number_of_edges()} tramos y {chk_p['ciclos']} ciclos")
    for u, v, d in sorted(Tp.edges(data=True), key=lambda e: e[2]["km"]):
        print(f"   {u} - {v}: {d['km']:.0f} km")
    L = validar_linea(4)
    print(f"Validación - 4 humedales en línea: {L.number_of_edges()} tramos y "
          f"{verificar_arbol(L)['ciclos']} ciclos")

    print(f"\nDECISIÓN: con {T.number_of_edges()} de los {G.number_of_edges()} tramos activos "
          f"({total_t:.0f} km) se unen los {G.number_of_nodes()} humedales sin rutas de más; "
          f"se ahorran {ahorro:.0f} km frente a la red completa ({total_g:.0f} km).")
    print(f"Gráfico guardado en: {PNG.name}")


def main():
    G = leer_grafo(EXCEL)
    T = arbol_generador(G)
    dibujar_ave_arbol(G, T, PNG)
    decision(G, T)


if __name__ == "__main__":
    main()
