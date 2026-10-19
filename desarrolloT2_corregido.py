"""
Esqueleto articulado con grafo de escena (versión corregida de desarrolloT2.py).

Regla central: ESCALAS SOLO EN NODOS HOJA.
  - cada parte tiene un nodo de ARTICULACIÓN (solo traslación + rotación) del que cuelgan
    las articulaciones siguientes,
  - y un nodo de FORMA <articulacion>Vis (offset + escala de la malla) que no tiene hijos.

Jerarquía (el nivel cuenta desde la raíz "esqueleto"):

    esqueleto
    └── tronco                                   nivel 1
        ├── cuello                               nivel 2   (cabeza)
        ├── hombroDer / hombroIzq                nivel 2
        │   └── codoDer / codoIzq                nivel 3
        │       └── muñecaDer / muñecaIzq        nivel 4   (mano)
        └── caderaDer / caderaIzq                nivel 2
            └── rodillaDer / rodillaIzq          nivel 3
                └── tobilloDer / tobilloIzq      nivel 4   (pie)

Todas las medidas son MEDIAS dimensiones (las mallas .off van de -1 a 1 con
rezero=False y normalize=False), igual que en el ejemplo del carrusel.

Teclas: ESPACIO = siguiente pose (y su cámara) | 1, 2, 3 = ir directo a una pose.
"""
import colorsys
import os
from pathlib import Path

import numpy as np
import pyglet
import pyglet.gl as GL
from pyglet.window import key

import grafica.transformations as tr
from grafica.scenegraph import Scenegraph
from grafica.utils import load_pipeline

ANCHO_VENTANA, ALTO_VENTANA = 900, 700

# ----------------------------------------------------------------------------
# Medidas (medias dimensiones x, y, z). Ajústalas a gusto: las uniones se calculan
# a partir de ellas, así que el personaje no se descuadra al cambiarlas.
# ----------------------------------------------------------------------------
TRONCO = (0.30, 0.50, 0.15)
CABEZA = (0.15, 0.20, 0.20)        # cono
BRAZO = (0.35, 0.10, 0.10)         # largo en X
ANTEBRAZO = (0.30, 0.09, 0.09)     # largo en X
MANO = (0.12, 0.16, 0.16)          # cono; su eje (Y local) queda a lo largo del brazo
MUSLO = (0.12, 0.35, 0.12)         # largo en Y
PANTORRILLA = (0.10, 0.35, 0.10)   # largo en Y
PIE = (0.10, 0.06, 0.22)           # largo en Z (apunta hacia la cámara)


def color(hue):
    """Un color distinto por nivel/parte: dos partes conectadas nunca comparten hue."""
    return np.array(colorsys.hsv_to_rgb(hue % 1.0, 0.75, 0.9), dtype=np.float32)


window = pyglet.window.Window(ANCHO_VENTANA, ALTO_VENTANA, caption="Esqueleto")
carpeta = Path(os.path.dirname(__file__))

# ----------------------------------------------------------------------------
# 1) Grafo, mallas y pipeline
# ----------------------------------------------------------------------------
graph = Scenegraph("esqueleto")

graph.load_and_register_mesh("cubo", "assets/cube.off", rezero=False, normalize=False)
graph.load_and_register_mesh("cono", "assets/cone.off", rezero=False, normalize=False)

graph.register_pipeline(
    "solido",
    load_pipeline(carpeta / "vertex_program.glsl", carpeta / "fragment_program.glsl"),
)

# ----------------------------------------------------------------------------
# 2) Jerarquía
# ----------------------------------------------------------------------------
OFFSETS = {}   # nombre de articulación -> su posición respecto al padre 
#(no cambia entre poses), y así nos ahorramos antitransformadas


def articulacion(nombre, padre, offset):
    """
    Agrega nodo sin geomeria a modo de punto de pivote. 
    solo se aplican traslaciones para hubicar el nodo
    offset es el un vector para hubicar el futro objeto que se colgará de este pivote
    Nodo sin geometría: solo traslación (la rotación de cada pose se agrega después).
    """
    graph.add_transform(nombre, tr.translate(*offset))
    graph.add_edge(padre, nombre)
    OFFSETS[nombre] = offset


def pieza(nombre_articulacion, malla, offset, escala, color_pieza, rotacion=None):
    """
    Nodo hoja con la forma. Cuelga de su articulación y no tiene hijos.
    De esta forma no se aplican escalamientos indeseados
    El objeto a agregar se llamará <nombre_articulación>vis
    """
    if rotacion is None:
        rotacion = tr.identity()
    graph.add_object(
        f"{nombre_articulacion}Vis", malla, "solido", parent=nombre_articulacion,
        transform=tr.matmul([tr.translate(*offset), rotacion, tr.scale(*escala)]),
        color_instancia=color_pieza,
        emisivo=0.0,
    )

#------------------------------------------------------------------------------------------------
#construcción del grafo de escena
#------------------------------------------------------------------------------------------------
# Tronco (nivel 1): su articulación está en el centro del torso
articulacion("tronco", "esqueleto", (0, 0, 0))
pieza("tronco", "cubo", (0, 0, 0), TRONCO, color(0.00))

# Cabeza (nivel 2): el cuello está en la parte alta del torso; el cono se apoya sobre él
articulacion("cuello", "tronco", (0, TRONCO[1], 0))
pieza("cuello", "cono", (0, CABEZA[1], 0), CABEZA, color(0.12), rotacion=tr.rotationX(np.pi))

# Derecha = -x, izquierda = +x (como en tu versión). s es el signo del lado.
for lado, s in (("Der", -1), ("Izq", 1)):
    # Brazo: hombro (2) -> codo (3) -> muñeca (4)
    articulacion(f"hombro{lado}", "tronco", (s * TRONCO[0], TRONCO[1] - 0.10, 0))
    pieza(f"hombro{lado}", "cubo", (s * BRAZO[0], 0, 0), BRAZO, color(0.30))

    articulacion(f"codo{lado}", f"hombro{lado}", (s * 2 * BRAZO[0], 0, 0))
    pieza(f"codo{lado}", "cubo", (s * ANTEBRAZO[0], 0, 0), ANTEBRAZO, color(0.45))

    articulacion(f"muneca{lado}", f"codo{lado}", (s * 2 * ANTEBRAZO[0], 0, 0))
    pieza(f"muneca{lado}", "cono", (s * MANO[1], 0, 0), MANO, color(0.58),
          rotacion=tr.rotationZ(-s * np.pi / 2))

    # Pierna: cadera (2) -> rodilla (3) -> tobillo (4)
    articulacion(f"cadera{lado}", "tronco", (s * TRONCO[0] / 2, -TRONCO[1], 0))
    pieza(f"cadera{lado}", "cubo", (0, -MUSLO[1], 0), MUSLO, color(0.70))

    articulacion(f"rodilla{lado}", f"cadera{lado}", (0, -2 * MUSLO[1], 0))
    pieza(f"rodilla{lado}", "cubo", (0, -PANTORRILLA[1], 0), PANTORRILLA, color(0.82))

    articulacion(f"tobillo{lado}", f"rodilla{lado}", (0, -2 * PANTORRILLA[1], 0))
    pieza(f"tobillo{lado}", "cubo", (0, -PIE[1], PIE[2] / 2), PIE, color(0.92))

# ----------------------------------------------------------------------------
# 3) Poses (ángulos en GRADOS: rx, ry, rz) y una cámara por pose
# ----------------------------------------------------------------------------
# Lo que no aparece en "joints" queda en reposo (0, 0, 0).
POSES = [
    {
        "nombre": "Pose 1",
        "joints": {
            "cuello":       (45, 0, 0),
            "hombroDer":    (-20, 90, 0),
            "codoDer":      (0, 90, 0),
            "codoIzq":      (0, 0, 60),      # nivel 3
            "caderaDer":    (-30, 0, 0),
            "rodillaDer":   (50, 0, 0),      # nivel 3
        },
        "camara": {"eye": (3, 4, 9.0), "at": (0.0, -0.5, 0.0), "up": (0.0, 1.0, 0.0), "fov": 45},
    },
    # TODO Pose 2: cambia >= 4 articulaciones respecto a la otra pose.
    #              La cámara de abajo está provisoria: ojo bajo la cintura (y < -0.5), fov 70.
    {
        "nombre": "Pose 2",
        "joints": {
            "caderaDer" :   (-90, 0, 0),
            "caderaIzq":    (-90, 0, 0),
            "rodillaDer":   (90, 0, 0),
            "rodillaIzq":   (90, 0, 0),
            "hombroDer" :   (0, 90, 0),
            "hombroIzq":    (0, -90, 0),
            "codoDer":      (0, 20, 0),
            "codoIzq":      (0, -20, 0)

        },
        "camara": {"eye": (4.0, -2.5, 4.0), "at": (0.0, -0.5, 0.0), "up": (0.0, 1.0, 0.0), "fov": 70},
    },
    # TODO Pose 3: cámara provisoria con fov 30 (más del doble que 70 -> perspectiva comprimida)
    {
        "nombre": "Pose 3",
        "joints": {
            "hombroDer":    (0, 90, 0),
            "hombroIzq":    (0, 90, 0),
            "codoIzq":      (0, 0, -90),
            "codoDer":      (0, 0, -90),
            "munecaDer":    (0, 0, 90),

            "caderaDer" :   (-0, 0, 0),
            "caderaIzq":    (-90, 0, 0),
            "rodillaDer":   (0, 0, 0),
            "rodillaIzq":   (90, 0, 0), 
            "munecaIzq":    (0, 0, 90)

        },
        "camara": {"eye": (-8.0, 0.5, 1.0), "at": (0.0, -0.5, 0.0), "up": (0.0, 1.0, 0.0), "fov": 30},
    },
]
pose_actual = 0


def aplicar_pose(indice):
    global pose_actual
    pose_actual = indice
    pose = POSES[indice]

    # postura: cada articulación = traslación fija @ rotación de la pose
    for nombre, offset in OFFSETS.items():
        rx, ry, rz = np.radians(pose["joints"].get(nombre, (0, 0, 0)))
        graph.nodes[nombre]["transform"] = tr.matmul([
            tr.translate(*offset),
            tr.rotationZ(rz), tr.rotationY(ry), tr.rotationX(rx),
        ])

    # cámara, proyección y luz: cambian junto con la postura
    cam = pose["camara"]
    eye = np.array(cam["eye"], dtype=np.float32)
    at = np.array(cam["at"], dtype=np.float32)
    up = np.array(cam["up"], dtype=np.float32)
    graph.register_view_transform(tr.lookAt(eye, at, up), name="vista", set_as_current=True)
    graph.set_global_attributes(
        projection=tr.perspective(cam["fov"], ANCHO_VENTANA / ALTO_VENTANA, 0.1, 60.0),
        posicion_camara=eye,
        posicion_ampolleta=np.array([2.0, 4.0, 6.0], dtype=np.float32),
    )
    window.set_caption(f"Esqueleto - {pose['nombre']} ({indice + 1}/{len(POSES)})  [espacio: siguiente]")


@window.event
def on_key_press(symbol, modifiers):
    teclas = {key._1: 0, key._2: 1, key._3: 2}
    if symbol == key.SPACE:
        aplicar_pose((pose_actual + 1) % len(POSES))      # tras la última vuelve a la primera
    elif symbol in teclas and teclas[symbol] < len(POSES):
        aplicar_pose(teclas[symbol])


# ----------------------------------------------------------------------------
# 4) Dibujo
# ----------------------------------------------------------------------------
@window.event
def on_draw():
    GL.glClearColor(0.07, 0.08, 0.12, 1.0)
    GL.glEnable(GL.GL_DEPTH_TEST)
    window.clear()
    graph.render()


aplicar_pose(0)
pyglet.app.run(1 / 60.0)
