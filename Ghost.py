import pygame
from pygame.locals import *

# Cargamos las bibliotecas de OpenGL
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

import math
import os
import numpy as np
import pandas as pd
import random
import heapq

class Ghost:
    def __init__(self, mapa, mc, x_mc, y_mc, xmc, ymc, xini, yini, tipo): #xini y yini deben de ser coordenadas de un elemento >= 0 del MC

        self.corners = {
            0: (1, 3),
            1: (0, 2),
            10: (0, 1),
            21: (0, 1, 3),
            11: (0, 3),
            12: (1, 2),
            13: (2, 3),
            22: (0, 2, 3),
            23: (1, 2, 3),
            24: (0, 1, 2),
            25: (0, 1, 2, 3),
            26: (1,),
            27: (3,)
        }

        #Matriz de control que almacena los IDs de las intersecciones
        self.MC = mc
        #Vectores que almacenan las coordenadas 
        self.XPxToMC = x_mc
        self.YPxToMC = y_mc

        self.xMC = xmc
        self.yMC = ymc
        #se resplanda el mapa en terminos de pixeles
        self.mapa = mapa

        #Variables de control
        self.x = xini
        self.y = yini
        self.size = 16
        self.dir_id = random.choice(self.corners[self.MC[self.YPxToMC[int(self.y)]][self.XPxToMC[int(self.x)]]])
        self.speed = 1
        self.x_delta = 0
        self.y_delta = 0

        self.directions = {
        0: (0, 1),   # abajo
        1: (1, 0),   # derecha
        2: (0, -1),  # arriba
        3: (-1, 0),  # izquierda
        4: (0, 0)    # stop
        }

        self.dir_ids = {v: k for k, v in self.directions.items()}

    class Node:
        def __init__(self, ix, iy, cr, parent):
            self.idx_x = ix
            self.idx_y = iy
            self.corner = cr
            self.g = 0
            self.h = 0
            self.f = 0
            self.pc_proximity = 0
            self.pc_prox_offset = 0
            self.parent = parent

        def __eq__(self, other):
            if not isinstance(other, Ghost.Node):
                return NotImplemented
            return self.idx_x == other.idx_x and self.idx_y == other.idx_y
        
        def __hash__(self):
            return hash((self.idx_x, self.idx_y))
        
        def __lt__(self, other):
            if not isinstance(other, Ghost.Node):
                return NotImplemented
            return self.f < other.f
        
        def __le__(self, other):
            if not isinstance(other, Ghost.Node):
                return NotImplemented
            return self.f <= other.f
        
        def __gt__(self, other):
            if not isinstance(other, Ghost.Node):
                return NotImplemented
            return self.f > other.f
        
        def __ge__(self, other):
            if not isinstance(other, Ghost.Node):
                return NotImplemented
            return self.f >= other.f

        # def calculate_prox_offset(self):

        # def estimate_with_proximity(self):
        
    def loadTextures(self, texturas, id):
        self.texturas = texturas
        self.Id = id

    def update_dir_random(self):
        idx_1 = self.XPxToMC[int(self.x)]
        idx_2 = self.YPxToMC[int(self.y)]
        corner = self.MC[idx_2][idx_1]

        if corner >= 0:
            options = list(self.corners[corner])

            if self.dir_id < 2:
                reverse = self.dir_id + 2
            else:
                reverse = self.dir_id - 2

            weights = []

            for d in options:
                if d == reverse:
                    weights.append(0.1)
                else:
                    weights.append(1.0)

            # Safety check
            if options:
                self.dir_id = random.choices(options, weights=weights, k=1)[0]

    def update_dir_seeker(self, pacmanXY):
        idx_1 = self.XPxToMC[int(self.x)]
        idx_2 = self.YPxToMC[int(self.y)]
        corner = self.MC[idx_2][idx_1]

        if corner >= 0:
            next = self.astar(pacmanXY, 3)
            dv = (next.idx_x - idx_1, next.idx_y - idx_2)
            self.dir_id = self.dir_ids[dv]

    def update_delta(self):
        dx, dy = self.directions[self.dir_id]

        self.x_delta = self.speed * dx
        self.y_delta = self.speed * dy
    
    def update_move(self):
        self.x += self.x_delta
        self.y += self.y_delta

    def get_neighbors(self, node): # TODO: Change idx_corner to neighbor type
        dirs = self.corners[node.corner]

        # print(dirs)

        neighbors = []

        for d in dirs:
            xo, yo = self.directions[d]
            neighbors.append(Ghost.Node(node.idx_x + xo, node.idx_y + yo, self.MC[node.idx_y + yo][node.idx_x + xo], node))

        return neighbors
    
    def ponder_neighbor(self, parent, neighbor, pcx, pcy):
        parent_coord_x = self.xMC[parent.idx_x]
        parent_coord_y = self.yMC[parent.idx_y]
        neighbor_coord_x = self.xMC[neighbor.idx_x]
        neighbor_coord_y = self.yMC[neighbor.idx_y]

        neighbor.g = parent.g + abs(neighbor_coord_x - parent_coord_x) + abs(neighbor_coord_y - parent_coord_y)
        neighbor.h = abs(neighbor_coord_x - pcx) + abs(neighbor_coord_y - pcy)
        neighbor.f = neighbor.g + neighbor.h

    def update_open(self, neighbors, open_heap: list, closed: dict):
        open_dict = {}

        for i, node in enumerate(open_heap):
            open_dict[(node.idx_x, node.idx_y)] = (node, i)

        for n in neighbors:
            key = (n.idx_x, n.idx_y)

            if key in closed:
                if n.g < closed[key].g:
                    closed.pop(key)
                    heapq.heappush(open_heap, n)
                continue

            if key in open_dict:
                old_node, old_index = open_dict[key]

                if n.g < old_node.g:
                    open_heap[old_index].g = n.g
                    open_heap[old_index].h = n.h
                    open_heap[old_index].f = n.f

                    heapq.heapify(open_heap)
                continue

            heapq.heappush(open_heap, n)
                    

    def evaluate_node(self, pcx, pcy, open_heap: list, closed: dict):
        current = heapq.heappop(open_heap)
        neighbors = self.get_neighbors(current)
        for n in neighbors:
            self.ponder_neighbor(current, n, pcx, pcy)
        self.update_open(neighbors, open_heap, closed)
        closed = closed | {(current.idx_x, current.idx_y): current}

    def get_next(self, node, n0):
        recall = node
        print(f"{n0.corner} -> Reconstruct:")
        print(recall.corner)
        while recall.parent != n0:
            recall = recall.parent
            print(recall.corner)
        return recall
        


    def astar(self, pcxy, n):
        pcx, pcy = pcxy
        idx_1 = self.XPxToMC[int(self.x)]
        idx_2 = self.YPxToMC[int(self.y)]
        corner = self.MC[idx_2][idx_1]

        n0 = Ghost.Node(idx_1, idx_2, corner, None)

        open_heap = [n0]
        closed = {}

        while n > 0 and open_heap:
            self.evaluate_node(pcx, pcy, open_heap, closed)
            n -= 1
        
        # print("Closed:")
        # print(closed)

        return self.get_next(heapq.heappop(open_heap), n0)
        

    def test_neighbors(self):
        idx_1 = self.XPxToMC[int(self.x)]
        idx_2 = self.YPxToMC[int(self.y)]
        corner = self.MC[idx_2][idx_1]

        if corner >= 0:
            node = Ghost.Node(idx_1, idx_2, corner)
            neighbors = self.get_neighbors(node)
            str = f"Parent: {corner} Childs: "
            for n in neighbors:
                str += f"{n.corner} | "
            print(str)


    def test_neighbors2(self, pacmanXY):
        idx_1 = self.XPxToMC[int(self.x)]
        idx_2 = self.YPxToMC[int(self.y)]
        corner = self.MC[idx_2][idx_1]

        if corner >= 0:
            next = self.astar(pacmanXY, 3)
            # print(next.corner)


    def update(self):
        self.test_neighbors()
        self.update_dir_random()
        self.update_delta()
        self.update_move()

    def update2(self, pacmanXY):
        self.test_neighbors2(pacmanXY)
        self.update_dir_seeker(pacmanXY)
        self.update_delta()
        self.update_move()
        
    def draw(self):
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texturas[self.Id])

        glPushMatrix()

        glTranslatef(14, 11, 0)

        glBegin(GL_QUADS)
        glTexCoord2f(0, 0)
        glVertex2f(self.x, self.y)

        glTexCoord2f(1, 0)
        glVertex2f(self.x + self.size, self.y)

        glTexCoord2f(1, 1)
        glVertex2f(self.x + self.size, self.y + self.size)

        glTexCoord2f(0, 1)
        glVertex2f(self.x, self.y + self.size)
        glEnd()

        glPopMatrix()

        glDisable(GL_TEXTURE_2D)
 