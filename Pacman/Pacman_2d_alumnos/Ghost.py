class Ghost:
    def __init__(self, mapa, mc, x_mc, y_mc, xini, yini, dir, tipo):
        self.MC = mc
        self.XPxToMC = x_mc
        self.YPxToMC = y_mc
        self.mapa = mapa

        # Posición inicial
        self.x = xini
        self.y = yini
        self.dir = dir
        self.tipo = tipo

    def loadTextures(self, texturas, id):
        self.texturas = texturas
        self.Id = id

    def sigue_adelante(self):
        # Movimiento simple en la dirección actual
        if self.dir == "UP":
            self.y -= 1
        elif self.dir == "DOWN":
            self.y += 1
        elif self.dir == "LEFT":
            self.x -= 1
        elif self.dir == "RIGHT":
            self.x += 1

    def interseccion_random(self):
        # Cambia dirección aleatoriamente
        self.dir = random.choice(["UP", "DOWN", "LEFT", "RIGHT"])

    def update2(self, pacmanXY):
        # Lógica básica: moverse y cambiar dirección aleatoria
        if random.random() < 0.1:
            self.interseccion_random()
        self.sigue_adelante()

    def draw(self):
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texturas[self.Id])

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

        glDisable(GL_TEXTURE_2D)