"""
Implementación de esqueleto con 3 posturas distintas y diferentes perspecticas de cámara
utiliza funciones de gráfica.
"""

import os
from pathlib import Path

import numpy as np
import pyglet
import pyglet.gl as GL

import grafica.transformations as tr
from grafica.scenegraph import Scenegraph
from grafica.utils import load_pipeline

import click
from pyglet.window import key


wAn, wLa = 900, 700 
troncoL = .50 
troncoAncho = .30
troncoProf  = .15
brazoL  = .7 
brazoA  = .2
brazoP  = .5
piernaL = .9
cabezax = 0.15
cabezay = 0.2
cabezaz = .2
manox   = .3
manoy   =.4
manoz   =.4

# Dimensiones de los muslos
musloL = piernaL*2/3
musloA = brazoA*3/2
musloP = brazoP *2/3

#dim Pie
piex    = .3
piey    = .15
piez    = 3

#colores 
c1  =np.array((0.80, 0.30, 0.30), dtype= np.float32)
c2  = np.array((0.10, 0.20, 0.80), dtype= np.float32)
c3  = np.array((0.20, 0.5, 0.10), dtype= np.float32)
c4  = np.array((0.8, 0.2, 0.70), dtype= np.float32)

#camPos = np.array([0.0, 0.0, 8.0], dtype=np.float32)

window = pyglet.window.Window(wAn, wLa, caption= "Escena")
carpeta = Path(os.path.dirname(__file__))


# ----------------------------------------------------------------------------
# 1) Grafo, mallas y pipeline
# ----------------------------------------------------------------------------

graph = Scenegraph("esqueleto") # estructura de grafo de escena

# cargamos los elementos a utilizar
graph.load_and_register_mesh("cubo", "assets/cube.off", rezero=False, normalize=False)
graph.load_and_register_mesh("cono", "assets/cone.off", rezero=False, normalize=False)

#cargamos pipeline
graph.register_pipeline(
    "esqueleto",
    load_pipeline(carpeta / "vertex_program.glsl", carpeta / "fragment_program.glsl"),
)

# ----------------------------------------------------------------------------
# 2) La jerarquía, escrita explícitamente: cada add_edge(padre, hijo) es una arista
# ----------------------------------------------------------------------------
# nodo de transformación sin geometría
graph.add_transform("tronco", tr.identity())
#le asignamos su jerarquía
graph.add_edge("esqueleto", "tronco")

graph.add_object(
    "tronco", "cubo", "esqueleto", parent="tronco",
    transform=tr.translate(0,0,0)
    @ tr.scale(troncoAncho, troncoL, troncoProf),
    color_instancia=c1,
    emisivo=0.0,
)

graph.add_object("cabeza", "cono", "esqueleto", parent= "esqueleto", 
                 transform= tr.translate(0, troncoL + cabezay*.5, 0) 
                 @ tr.rotationX(np.array((np.pi))) 
                 @ tr.scale(cabezax, cabezay, cabezaz),
                 color_instancia=c1,
                 emisivo=0
)

#añadimos  nodo 
graph.add_transform("brazoDer", tr.identity())   #tr.translate(-troncoAncho/2, troncoL/2,0))
graph.add_transform("brazoIzq", tr.identity())

graph.add_transform("piernaDer", tr.identity())
graph.add_transform("piernaIzq", tr.identity())

graph.add_transform("antebrazoDer", tr.identity())
graph.add_transform("antebrazoIzq", tr.identity())

graph.add_transform("manoDer", tr.identity())
graph.add_transform("manoIzq", tr.identity())

# Cadera y sus tres partes
graph.add_transform("cadera", tr.identity())
graph.add_transform("caderaCentro", tr.identity())
graph.add_transform("caderaDer", tr.identity())
graph.add_transform("caderaIzq", tr.identity())


#asignamos gerarquía de brazos y piernas
graph.add_edge("tronco","brazoDer")
graph.add_edge("tronco","brazoIzq")


graph.add_edge("brazoDer", "antebrazoDer")
graph.add_edge("brazoIzq", "antebrazoIzq")

graph.add_edge("antebrazoDer", "manoDer")
graph.add_edge("antebrazoIzq", "manoIzq")

# Nuevos nodos cadera
graph.add_transform("cadera", tr.identity())
graph.add_transform("caderaCentro", tr.identity())
graph.add_transform("caderaDer", tr.identity())
graph.add_transform("caderaIzq", tr.identity())

#Pie
graph.add_transform("pieDer", tr.identity())
graph.add_transform("pieIzq", tr.identity())

# Jerarquía cadera

graph.add_edge("tronco", "cadera")

graph.add_edge("cadera", "caderaCentro")
graph.add_edge("cadera", "caderaDer")
graph.add_edge("cadera", "caderaIzq")

graph.add_edge("caderaDer", "piernaDer")
graph.add_edge("caderaIzq", "piernaIzq")

#pie 
graph.add_edge("pantorrillaDer", "PieDer")
graph.add_edge("pantorrillaIzq", "PieIzq")


graph.add_object("brazoDer", "cubo", "esqueleto", parent= "tronco",
                  transform= tr.translate(-(troncoAncho + brazoL*2) ,troncoL + brazoA, 0)
                  @ tr.scale(brazoL, brazoA, brazoP),
                  color_instancia = c2,
                  emisivo = 0
)


graph.add_object("brazoIzq", "cubo", "esqueleto", parent= "tronco",
                  transform= tr.translate((troncoAncho + brazoL*2) ,troncoL + brazoA, 0)
                  @ tr.scale(brazoL, brazoA, brazoP),
                  color_instancia = c2,
                  emisivo = 0
)

graph.add_object("antebrazoDer", "cubo", "esqueleto", "brazoDer", 
                transform= tr.translate(-(troncoAncho + brazoL*3) ,troncoL - brazoA*2 , brazoP/2)
                @ tr.scale(brazoL*2, brazoA*2, brazoP*2),
                color_instancia = c2,
                emisivo=0
                )

graph.add_object("antebrazoIzq", "cubo", "esqueleto", "brazoIzq", 
                transform= tr.translate((troncoAncho + brazoL*3) ,troncoL - brazoA*2 , brazoP/2)
                @ tr.scale(brazoL*2, brazoA*2, brazoP*2),
                color_instancia = c2,
                emisivo=0
                )

graph.add_object("manoDer", "cono", "esqueleto", "antebrazoDer", 
                transform= tr.translate(-(troncoAncho+ brazoL*2) ,troncoL - brazoA*2 , brazoP/4)
                @ tr.rotationZ(np.array(np.pi/2, dtype=np.float32))
                @ tr.scale(manox, manoy, manoz),
                color_instancia = c2,
                emisivo=0
                )



graph.add_object("manoIzq", "cono", "esqueleto", "antebrazoIzq", 
                transform= tr.translate((troncoAncho+ brazoL*2) ,troncoL - brazoA*2 , brazoP/4)
                @ tr.rotationZ(np.array(-np.pi/2, dtype=np.float32))
                @ tr.scale(manox, manoy, manoz),
                color_instancia = c2,
                emisivo=0
                )


# Muslo derecho
graph.add_object(
    "musloDer", "cubo", "esqueleto",
    parent="caderaDer",
    transform=tr.translate(
        -troncoAncho, -troncoL*2 - musloL, 0
    ) @ tr.scale(musloA, musloL, musloP),
    color_instancia=c3,
    emisivo=0
)

# Muslo Izq
graph.add_object(
    "musloIzq", "cubo", "esqueleto",
    parent="caderaIzq",
    transform=tr.translate(
        troncoAncho, -troncoL*2 - musloL, 0
    ) @ tr.scale(musloA, musloL, musloP),
    color_instancia=c3,
    emisivo=0
)

# Pantorrilla derecha
graph.add_object(
    "pantorrillaDer", "cubo", "esqueleto",
    parent="musloDer",
    transform=tr.translate(
        0, -(musloL*2 + troncoL*2), 0
    ) @ tr.scale(musloA*2, musloL*2, musloP*2),
    color_instancia=c3,
    emisivo=0
)

# Pantorrilla Izq
graph.add_object(
    "pantorrillaIzq", "cubo", "esqueleto",
    parent="musloIzq",
    transform=tr.translate(
        0, -musloL*2 - troncoL*2, 0
    ) @ tr.scale(musloA*2, musloL*2, musloP*2),
    color_instancia=c3,
    emisivo=0
)

graph.add_object("PieDer", "cubo", "esqueleto", "pantorrillaDer", 
                transform= tr.translate(-musloA/4, -(musloL*2), piez/2)
                @ tr.scale(piex, piey, piez),
                color_instancia = c3,
                emisivo=0
                 )


graph.add_object("PieIzq", "cubo", "esqueleto", "pantorrillaIzq", 
                transform= tr.translate(musloA/4, -(musloL*2), piez/2)
                @ tr.scale(piex, piey, piez),
                color_instancia = c3,
                emisivo=0
                 )

# ----------------------------------------------------------------------------
# 3) Cámara y luz (el shader del carrusel necesita estos uniforms)
# ----------------------------------------------------------------------------
# posición de la cámara: 
# eye: donde está, target: donde mira, up: cenit
#angulo cr ver, angulo cr horiz, frustrum with
camPos = np.array([.0, .0, 8], dtype=np.float32)
campos1 = np.array([5.0, .0, .2], dtype=np.float32)
campos2 = np.array([5.0, .9, 1], dtype=np.float32)
campos3 = np.array([5.0, .4, 8], dtype=np.float32)

@window.event

def on_key_press(symbol, modifier):
    window.clear()

    if symbol == key._1:
        camPos = campos1

    if symbol == key._2:
        camPos = campos2


    if symbol == key._3:
        camPos = campos3

        
    graph.register_view_transform(
        tr.lookAt(camPos, np.array([0.0, 0.0, 0.5], dtype=np.float32),
                np.array([0.0, 1.0, 0.0], dtype=np.float32))
    )


graph.register_view_transform(
    tr.lookAt(camPos, np.array([0.0, 0.0, 0.5], dtype=np.float32),
              np.array([0.0, 1.0, 0.0], dtype=np.float32))
)
graph.set_global_attributes(
    projection=tr.perspective(45, wAn / wLa, 0.1, 40.0),
    
    
    #posicion_camara=campos
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


#def update_world(dt, _):
    #tiempo["t"] += dt
    # basta con mover el nodo "brazo": el rectángulo y el círculo lo heredan
    #graph.nodes["brazo"]["transform"] = tr.translate(-1.0, 0, 0) @ tr.rotationZ(0.8 * tiempo["t"])


#pyglet.clock.schedule_interval(update_world, 1 / 60.0, window)
pyglet.app.run(1 / 60.0)
