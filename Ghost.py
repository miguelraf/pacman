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
        self.range = 10

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

            if options:
                self.dir_id = random.choices(options, weights=weights, k=1)[0]

    def update_dir_seeker(self, pacmanXY):
        idx_1 = self.XPxToMC[int(self.x)]
        idx_2 = self.YPxToMC[int(self.y)]
        corner = self.MC[idx_2][idx_1]

        if corner >= 0:
            if self.dir_id < 2:
                reverse = self.dir_id + 2
            else:
                reverse = self.dir_id - 2

            xo, yo = self.directions[reverse]
            next = self.astar(pacmanXY, 3, Ghost.Node(idx_1, idx_2, corner, Ghost.Node(idx_1 + xo, idx_2 + yo, self.MC[idx_2 + yo][idx_1 + xo], None)))
            # print(f"next: {next.corner}")
            dv = (next.idx_x - idx_1, next.idx_y - idx_2)
            # print(dv)
            self.dir_id = self.dir_ids[dv]
            # print(self.directions[self.dir_id])

    def update_delta(self):
        dx, dy = self.directions[self.dir_id]

        self.x_delta = self.speed * dx
        self.y_delta = self.speed * dy
    
    def update_move(self):
        self.x += self.x_delta
        self.y += self.y_delta

    def get_neighbors(self, node): # TODO: Change idx_corner to neighbor type
        dirs = self.corners[node.corner]

        neighbors = []

        for d in dirs:
            xo, yo = self.directions[d]
            if node.corner != 27 and node.corner != 26 and Ghost.Node(node.idx_x + xo, node.idx_y + yo, self.MC[node.idx_y + yo][node.idx_x + xo], None) == node.parent:
                continue
            neighbors.append(Ghost.Node(node.idx_x + xo, node.idx_y + yo, self.MC[node.idx_y + yo][node.idx_x + xo], node))

        return neighbors
    
    def ponder_neighbors(self, parent, neighbors, pcx, pcy):
        for neighbor in neighbors:
            parent_coord_x = self.xMC[parent.idx_x]
            parent_coord_y = self.yMC[parent.idx_y]
            neighbor_coord_x = self.xMC[neighbor.idx_x]
            neighbor_coord_y = self.yMC[neighbor.idx_y]

            neighbor.g = parent.g + abs(neighbor_coord_x - parent_coord_x) + abs(neighbor_coord_y - parent_coord_y)
            neighbor.h = abs(neighbor_coord_x - pcx) + abs(neighbor_coord_y - pcy)
            neighbor.f = neighbor.g + neighbor.h

    def evaluate_node(self, pcx, pcy, open_heap: list, closed: list):
        current = heapq.heappop(open_heap)
        neighbors = self.get_neighbors(current)
        # str = f"Neighbors of current: {current.corner} -> "
        # for n in neighbors:
        #     str = str + f"{n.corner} | "

        # print(str)
        self.ponder_neighbors(current, neighbors, pcx, pcy)
        for n in neighbors:
            # if n in closed or n in open_heap:
            #     continue
            heapq.heappush(open_heap, n)

        dist = 1000
        if open_heap:
            p = open_heap[0]
            best_coord_x = self.xMC[p.idx_x]
            best_coord_y = self.yMC[p.idx_y]

            dist = math.sqrt(math.pow((pcx - best_coord_x), 2) + math.pow((pcy - best_coord_y), 2))

        closed.append(current)

        if dist < self.range:
            return True
        else:
            return False

    def astar(self, pacmanXY, depth, n0):
        pcx, pcy = pacmanXY
        open_heap = [n0]
        closed = []

        while depth > 0 and open_heap:
            if self.evaluate_node(pcx, pcy, open_heap, closed):
                break
            depth -= 1
        
        # print("Open:")
        # for n in open_heap:
        #     print(f"{n.corner} - {n.idx_x} - {n.idx_y}")
        # print("Closed:")
        # for n in closed:
        #     print(f"{n.corner} - {n.idx_x} - {n.idx_y}")

        return self.get_next(heapq.heappop(open_heap), n0)

    def get_next(self, node, n0):

        recall = node
        # print(f"{n0.corner} -> Reconstruct:")
        # print(recall.corner)
        while recall.parent != n0:
            recall = recall.parent
            # print(recall.corner)
        # print("-----")
        return recall
    
    def test_astar(self, pacmanXY):
        idx_1 = self.XPxToMC[int(self.x)]
        idx_2 = self.YPxToMC[int(self.y)]
        corner = self.MC[idx_2][idx_1]

        if corner >= 0:
            if self.dir_id < 2:
                reverse = self.dir_id + 2
            else:
                reverse = self.dir_id - 2

            xo, yo = self.directions[reverse]
            next = self.astar(pacmanXY, 3, Ghost.Node(idx_1, idx_2, corner, Ghost.Node(idx_1 + xo, idx_2 + yo, self.MC[idx_2 + yo][idx_1 + xo], None)))
            # print(f"next: {next.corner}")

    def update(self):
        self.update_dir_random()
        self.update_delta()
        self.update_move()

    def update2(self, pacmanXY):
        # self.test_astar(pacmanXY)
        self.update_dir_seeker(pacmanXY)
        # self.update_dir_random()
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
 