"""
Ejemplo mínimo de grafo de escena: un rectángulo (el "brazo") y un círculo colgando
de su extremo. Al girar el brazo, el círculo lo acompaña porque HEREDA su transformación.

Jerarquía:

    mundo
    └── brazo                  (nodo de transformación: aquí rotamos)
        ├── rectangulo         (geometría: cubo achatado)
        └── pivote_circulo     (nodo de transformación: lo lleva al extremo del brazo)
            └── circulo        (geometría: cilindro achatado, visto de frente)

Está basado en el ejemplo del carrusel: mismos shaders, mismas mallas (.off) y mismo
patrón de "nodo de transformación sin geometría + objetos que cuelgan de él".

Ponlo en la MISMA carpeta que vertex_program.glsl y fragment_program.glsl, y ejecútalo
desde la raíz del repositorio (las mallas se buscan en assets/, como en el carrusel).
"""
import os
from pathlib import Path

import numpy as np
import pyglet
import pyglet.gl as GL

import grafica.transformations as tr
from grafica.scenegraph import Scenegraph
from grafica.utils import load_pipeline

ANCHO, ALTO = 900, 700
LARGO_BRAZO = 2.0
ALTO_BRAZO = 0.25
RADIO_CIRCULO = 0.6

COLOR_BRAZO = np.array([0.82, 0.30, 0.28], dtype=np.float32)
COLOR_CIRCULO = np.array([0.30, 0.70, 0.90], dtype=np.float32)

POSICION_CAMARA = np.array([0.0, 0.0, 8.0], dtype=np.float32)

window = pyglet.window.Window(ANCHO, ALTO, caption="Grafo de escena simple")
carpeta = Path(os.path.dirname(__file__))

# ----------------------------------------------------------------------------
# 1) Grafo, mallas y pipeline
# ----------------------------------------------------------------------------
graph = Scenegraph("mundo") #definimos el grafo de escena

# rezero=False y normalize=False: las mallas quedan de -1 a 1 en cada eje, así que los
# argumentos de tr.scale son MEDIAS dimensiones (igual que en el carrusel)
#primero caramos la figura a gpu, para operar sobre ellas. 
graph.load_and_register_mesh("cubo", "assets/cube.off", rezero=False, normalize=False)
graph.load_and_register_mesh("cilindro", "assets/cylinder.off", rezero=False, normalize=False)

graph.register_pipeline(
    "solido",
    load_pipeline(carpeta / "vertex_program.glsl", carpeta / "fragment_program.glsl"),
)

# ----------------------------------------------------------------------------
# 2) La jerarquía, escrita explícitamente: cada add_edge(padre, hijo) es una arista
# ----------------------------------------------------------------------------
# nodo de transformación sin geometría; su transform lo cambiamos en cada cuadro
graph.add_transform("brazo", tr.identity())
graph.add_edge("mundo", "brazo")

# el rectángulo: cubo estirado. Se desplaza LARGO/2 en X para que el brazo "nazca"
# en el origen de su nodo y se extienda hacia +X
graph.add_object(
    "rectangulo", "cubo", "solido", parent="brazo",
    transform=tr.translate(LARGO_BRAZO / 2, 0, 0)
    @ tr.scale(LARGO_BRAZO / 2, ALTO_BRAZO / 2, 0.1),
    color_instancia=COLOR_BRAZO,
    emisivo=0.0,
)

# el pivote lleva al círculo al extremo del brazo. Es un nodo APARTE para que la escala
# del círculo no se herede a nadie
graph.add_transform("pivote_circulo", tr.translate(LARGO_BRAZO, 0, 0))
graph.add_edge("brazo", "pivote_circulo")

# el círculo: cilindro achatado. El cilindro tiene su eje en Y, así que lo giramos 90° en X
# para que su tapa mire a la cámara (que está en +Z)
graph.add_object(
    "circulo", "cilindro", "solido", parent="pivote_circulo",
    transform=tr.rotationX(np.pi / 2) @ tr.scale(RADIO_CIRCULO, 0.1, RADIO_CIRCULO),
    color_instancia=COLOR_CIRCULO,
    emisivo=0.0,
)

# ----------------------------------------------------------------------------
# 3) Cámara y luz (el shader del carrusel necesita estos uniforms)
# ----------------------------------------------------------------------------
graph.register_view_transform(
    tr.lookAt(POSICION_CAMARA, np.array([0.0, 0.0, 0.0], dtype=np.float32),
              np.array([0.0, 1.0, 0.0], dtype=np.float32))
)
graph.set_global_attributes(
    projection=tr.perspective(45, ANCHO / ALTO, 0.1, 40.0),
    posicion_camara=POSICION_CAMARA,
    posicion_ampolleta=np.array([2.0, 4.0, 6.0], dtype=np.float32),   # una luz cualquiera
)

# ----------------------------------------------------------------------------
# 4) Dibujo y animación
# ----------------------------------------------------------------------------
tiempo = {"t": 0.0}


@window.event
def on_draw():
    GL.glClearColor(0.07, 0.08, 0.12, 1.0)
    GL.glEnable(GL.GL_DEPTH_TEST)
    window.clear()
    graph.render()          # recalcula las transformaciones globales recorriendo el grafo


def update_world(dt, _):
    tiempo["t"] += dt
    # basta con mover el nodo "brazo": el rectángulo y el círculo lo heredan
    graph.nodes["brazo"]["transform"] = tr.translate(-1.0, 0, 0) @ tr.rotationZ(0.8 * tiempo["t"])


pyglet.clock.schedule_interval(update_world, 1 / 60.0, window)
pyglet.app.run(1 / 60.0)
