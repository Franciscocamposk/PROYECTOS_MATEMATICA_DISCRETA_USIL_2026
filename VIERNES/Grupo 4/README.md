# P04 - Aves migratorias: el árbol de humedales que las une sin rodeos

- Grupo 4 - Viernes - Exposición: 4 de diciembre de 2026, 7:30 p.m.
- Integrantes: Navarro Barboza Max Alejandro, Picado Godínez Fiorella Ximena, Vaca Rojas Leonel Andrés
- Plataforma oficial: UISIL (escrito + diapositivas). Repositorio del curso: github.com/Franciscocamposk/PROYECTOS_MATEMATICA_DISCRETA_USIL_2026

## Datos

`P04_Aves_humedales.xlsx` (1637 registros simulados): hoja `Humedales` (8 humedales, nodos) y
hoja `Vuelos` (origen, destino, km, activo). Solo se usan los vuelos con `activo = si`;
A-B y B-A son el mismo tramo (grafo no dirigido) y, si se repite, se conserva el menor km.

## Modelo

Grafo no dirigido ponderado por km. Árbol generador con Kruskal (conjuntos disjuntos / union-find).
El programa comprueba que el resultado es un árbol (|E| = |V|-1, conexo, 0 ciclos),
compara los km contra la red completa y valida el caso de 4 humedales en línea (3 tramos, 0 ciclos).

## Ejecutar (Python 3.10+)

```
pip install -r requirements.txt
python main.py
python pruebas/test_arbol.py
```

Genera `aves_arbol.png` (red completa en gris, árbol en verde grueso, km en las aristas).

## Salida esperada (resumen)

```
Árbol generador (Kruskal): 7 tramos, 249 km
Prueba de que no hay ciclo: aristas = 7 = vértices - 1, ciclos = 0, es árbol = True
Comparación: árbol 249 km vs red completa 1752 km -> se ahorran 1503 km (85.8 %)
DECISIÓN: con 7 de los 28 tramos activos (249 km) se unen los 8 humedales sin rutas de más ...
```
