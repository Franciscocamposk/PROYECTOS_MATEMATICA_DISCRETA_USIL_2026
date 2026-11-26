"""Pruebas del modelo P04.

Ejecutar desde la raíz del proyecto:  python pruebas/test_arbol.py
"""

import sys
import tempfile
import unittest
from pathlib import Path

import networkx as nx

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

import main as proyecto  # noqa: E402

EXCEL = PROJECT / "P04_Aves_humedales.xlsx"


def grafo(aristas):
    G = nx.Graph()
    for u, v, km in aristas:
        G.add_edge(u, v, km=km)
    return G


class TestSinteticas(unittest.TestCase):
    def test_cuatro_en_linea_dan_3_tramos_y_0_ciclos(self):
        T = proyecto.arbol_generador(proyecto.validar_linea(4))
        self.assertEqual(T.number_of_edges(), 3)
        self.assertEqual(proyecto.ciclos_independientes(T), 0)
        self.assertTrue(nx.is_tree(T))

    def test_triangulo_descarta_la_arista_mas_larga(self):
        G = grafo([("A", "B", 1), ("B", "C", 2), ("A", "C", 9)])
        T = proyecto.arbol_generador(G)
        self.assertEqual(T.number_of_edges(), 2)
        self.assertFalse(T.has_edge("A", "C"))
        self.assertEqual(proyecto.km_total(T), 3)

    def test_ciclo_de_4_tiene_1_ciclo_independiente(self):
        G = grafo([("A", "B", 1), ("B", "C", 1), ("C", "D", 1), ("D", "A", 1)])
        self.assertEqual(proyecto.ciclos_independientes(G), 1)
        self.assertEqual(proyecto.arbol_generador(G).number_of_edges(), 3)

    def test_union_find_detecta_ciclo(self):
        c = proyecto.ConjuntosDisjuntos("ABC")
        self.assertTrue(c.unir("A", "B"))
        self.assertTrue(c.unir("B", "C"))
        self.assertFalse(c.unir("A", "C"))

    def test_grafo_desconectado_da_bosque(self):
        G = grafo([("A", "B", 1), ("C", "D", 1)])
        T = proyecto.arbol_generador(G)
        self.assertEqual(T.number_of_edges(), 2)
        self.assertFalse(nx.is_connected(T))


class TestDatosReales(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.G = proyecto.leer_grafo(EXCEL)
        cls.T = proyecto.arbol_generador(cls.G)

    def test_lee_los_8_humedales_y_28_tramos(self):
        self.assertEqual(self.G.number_of_nodes(), 8)
        self.assertEqual(self.G.number_of_edges(), 28)

    def test_grafo_conectado(self):
        self.assertTrue(nx.is_connected(self.G))

    def test_arbol_es_arbol_y_cubre_todo(self):
        self.assertTrue(nx.is_tree(self.T))
        self.assertEqual(set(self.T.nodes()), set(self.G.nodes()))
        self.assertEqual(self.T.number_of_edges(), 7)
        self.assertEqual(proyecto.verificar_arbol(self.T)["ciclos"], 0)

    def test_km_arbol_vs_red(self):
        self.assertEqual(proyecto.km_total(self.T), 249)
        self.assertEqual(proyecto.km_total(self.G), 1752)
        self.assertEqual(proyecto.km_total(self.G) - proyecto.km_total(self.T), 1503)

    def test_arbol_coincide_con_networkx(self):
        ref = nx.minimum_spanning_tree(self.G, weight="km")
        self.assertEqual(proyecto.km_total(self.T), proyecto.km_total(ref))

    def test_cuatro_parques(self):
        Tp = proyecto.arbol_generador(self.G.subgraph(proyecto.PARQUES))
        self.assertEqual(Tp.number_of_edges(), 3)
        self.assertEqual(proyecto.ciclos_independientes(Tp), 0)

    def test_genera_png(self):
        with tempfile.TemporaryDirectory() as d:
            png = Path(d) / "aves_arbol.png"
            proyecto.dibujar_ave_arbol(self.G, self.T, png)
            self.assertTrue(png.exists() and png.stat().st_size > 10_000)

    def test_humedal_desconocido_en_vuelos_da_error(self):
        vuelos, humedales = proyecto.leer_excel(EXCEL)
        humedales = humedales[humedales["humedal"] != "Ostional"]
        with self.assertRaises(ValueError):
            proyecto.construir_grafo(vuelos, humedales)


if __name__ == "__main__":
    unittest.main(verbosity=2)
