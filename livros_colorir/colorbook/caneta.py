"""Caneta: uma camada fina sobre o canvas do ReportLab para desenhar traço.

Os desenhos são escritos numa grade de 0 a 100 com o eixo Y para BAIXO
(como num papel), o que facilita criar e revisar desenhos à mão ou com o
Claude. A caneta converte essa grade para a área real da página.

Regra de ouro para livro de colorir: toda forma tem contorno preto grosso e
preenchimento branco. Como as formas são desenhadas em ordem, a de cima
"tampa" a de baixo, o que permite compor figuras sem apagar linhas.
"""
from __future__ import annotations

import math
from contextlib import contextmanager

from reportlab.lib.colors import Color, black, white
from reportlab.pdfgen.canvas import Canvas

from .fonts import FONTE_NEGRITO


class Caneta:
    def __init__(self, c: Canvas, x: float, y: float, largura: float, altura: float,
                 espessura: float = 3.2, preenchimento: Color = white,
                 paleta: list[Color] | None = None, cor_traco: Color = black,
                 tracejado: tuple[float, float] | None = None):
        """Cria uma caneta que mapeia a grade 100x100 para um quadrado centrado
        na área (x, y, largura, altura) em pontos PDF.

        paleta:    se informada, cada forma é pintada com a próxima cor da lista
                   (usado na capa, para mostrar o desenho "já colorido").
        cor_traco: cor do contorno (cinza nas páginas de "cubra o pontilhado").
        tracejado: (traço, espaço) em pontos para contorno pontilhado."""
        self.c = c
        lado = min(largura, altura)
        self.escala = lado / 100.0
        self.x0 = x + (largura - lado) / 2
        self.y_topo = y + (altura - lado) / 2 + lado
        self.espessura_base = espessura
        self.preenchimento = preenchimento
        self.paleta = paleta or []
        self._cor_i = 0
        self.cor_traco = cor_traco
        self.tracejado = tracejado
        c.setLineCap(1)
        c.setLineJoin(1)

    # --- conversão de coordenadas -------------------------------------------------
    def X(self, x: float) -> float:
        return self.x0 + x * self.escala

    def Y(self, y: float) -> float:
        return self.y_topo - y * self.escala

    def s(self, v: float) -> float:
        return v * self.escala

    # --- estilo -------------------------------------------------------------------
    def _estilo(self, espessura: float | None, cheio: bool | Color):
        c = self.c
        c.setStrokeColor(self.cor_traco)
        c.setLineWidth(self.espessura_base if espessura is None else espessura)
        if self.tracejado:
            c.setDash(*self.tracejado)
        if cheio is True:
            if self.paleta:
                c.setFillColor(self.paleta[self._cor_i % len(self.paleta)])
                self._cor_i += 1
            else:
                c.setFillColor(self.preenchimento)
        elif isinstance(cheio, Color):
            c.setFillColor(cheio)
        return 1 if cheio is not False else 0

    @contextmanager
    def girar(self, cx: float, cy: float, graus: float):
        """Gira o que for desenhado dentro do bloco em torno de (cx, cy).
        Ângulo positivo = sentido horário na grade (Y para baixo)."""
        c = self.c
        c.saveState()
        c.translate(self.X(cx), self.Y(cy))
        c.rotate(-graus)
        c.translate(-self.X(cx), -self.Y(cy))
        try:
            yield
        finally:
            c.restoreState()

    # --- primitivas -----------------------------------------------------------------
    def linha(self, x1, y1, x2, y2, espessura=None):
        self._estilo(espessura, False)
        self.c.line(self.X(x1), self.Y(y1), self.X(x2), self.Y(y2))

    def polilinha(self, pontos, espessura=None):
        p = self.c.beginPath()
        p.moveTo(self.X(pontos[0][0]), self.Y(pontos[0][1]))
        for x, y in pontos[1:]:
            p.lineTo(self.X(x), self.Y(y))
        self._estilo(espessura, False)
        self.c.drawPath(p, stroke=1, fill=0)

    def poligono(self, pontos, cheio=True, espessura=None):
        p = self.c.beginPath()
        p.moveTo(self.X(pontos[0][0]), self.Y(pontos[0][1]))
        for x, y in pontos[1:]:
            p.lineTo(self.X(x), self.Y(y))
        p.close()
        f = self._estilo(espessura, cheio)
        self.c.drawPath(p, stroke=1, fill=f)

    def circulo(self, cx, cy, r, cheio=True, espessura=None):
        f = self._estilo(espessura, cheio)
        self.c.circle(self.X(cx), self.Y(cy), self.s(r), stroke=1, fill=f)

    def ponto(self, cx, cy, r=1.6):
        """Bolinha sólida (olhos, narizes...) na cor do traço."""
        self.c.setFillColor(self.cor_traco)
        self.c.circle(self.X(cx), self.Y(cy), self.s(r), stroke=0, fill=1)

    def elipse(self, cx, cy, rx, ry, angulo=0.0, cheio=True, espessura=None):
        with self.girar(cx, cy, angulo):
            f = self._estilo(espessura, cheio)
            self.c.ellipse(self.X(cx - rx), self.Y(cy - ry), self.X(cx + rx), self.Y(cy + ry),
                           stroke=1, fill=f)

    def retangulo(self, x1, y1, x2, y2, raio=0.0, cheio=True, espessura=None):
        f = self._estilo(espessura, cheio)
        x, y = self.X(min(x1, x2)), self.Y(max(y1, y2))
        w, h = self.s(abs(x2 - x1)), self.s(abs(y2 - y1))
        if raio:
            self.c.roundRect(x, y, w, h, self.s(raio), stroke=1, fill=f)
        else:
            self.c.rect(x, y, w, h, stroke=1, fill=f)

    def arco(self, cx, cy, r, inicio, fim, espessura=None):
        """Arco aberto. Ângulos em graus, 0 = direita, 90 = para CIMA (como no relógio
        matemático), para ficar natural ao desenhar sorrisos e ondas."""
        self._estilo(espessura, False)
        self.c.arc(self.X(cx - r), self.Y(cy + r), self.X(cx + r), self.Y(cy - r),
                   startAng=inicio, extent=fim - inicio)

    def caminho(self, comandos, cheio=True, fechar=True, espessura=None):
        """Desenha um caminho livre. `comandos` é uma lista de tuplas:
        ("M", x, y)  mover;  ("L", x, y)  reta;
        ("C", x1, y1, x2, y2, x, y)  curva de Bézier cúbica;
        ("Q", x1, y1, x, y)  curva quadrática (convertida em cúbica)."""
        p = self.c.beginPath()
        atual = (0.0, 0.0)
        for cmd in comandos:
            tipo = cmd[0]
            if tipo == "M":
                p.moveTo(self.X(cmd[1]), self.Y(cmd[2]))
                atual = (cmd[1], cmd[2])
            elif tipo == "L":
                p.lineTo(self.X(cmd[1]), self.Y(cmd[2]))
                atual = (cmd[1], cmd[2])
            elif tipo == "C":
                _, x1, y1, x2, y2, x, y = cmd
                p.curveTo(self.X(x1), self.Y(y1), self.X(x2), self.Y(y2), self.X(x), self.Y(y))
                atual = (x, y)
            elif tipo == "Q":
                _, qx, qy, x, y = cmd
                x0, y0 = atual
                c1 = (x0 + 2 / 3 * (qx - x0), y0 + 2 / 3 * (qy - y0))
                c2 = (x + 2 / 3 * (qx - x), y + 2 / 3 * (qy - y))
                p.curveTo(self.X(c1[0]), self.Y(c1[1]), self.X(c2[0]), self.Y(c2[1]),
                          self.X(x), self.Y(y))
                atual = (x, y)
            else:
                raise ValueError(f"Comando de caminho desconhecido: {tipo}")
        if fechar:
            p.close()
        f = self._estilo(espessura, cheio if fechar else False)
        self.c.drawPath(p, stroke=1, fill=f)

    def tubo(self, comandos, largura=6.0):
        """Traço "oco": desenha uma faixa com contorno (rabo de gato, cabo de balão
        grosso, arco-íris...). A faixa fica pintável por dentro."""
        externo = self.s(largura) + self.espessura_base
        interno = max(self.s(largura) - self.espessura_base, 0.5)
        miolo = self.preenchimento
        if self.paleta:
            miolo = self.paleta[self._cor_i % len(self.paleta)]
            self._cor_i += 1
        for esp, cor in ((externo, self.cor_traco), (interno, miolo)):
            if self.tracejado and cor is self.cor_traco:
                self.c.setDash(*self.tracejado)
            else:
                self.c.setDash()
            p = self.c.beginPath()
            for cmd in comandos:
                if cmd[0] == "M":
                    p.moveTo(self.X(cmd[1]), self.Y(cmd[2]))
                elif cmd[0] == "L":
                    p.lineTo(self.X(cmd[1]), self.Y(cmd[2]))
                elif cmd[0] == "C":
                    _, x1, y1, x2, y2, x, y = cmd
                    p.curveTo(self.X(x1), self.Y(y1), self.X(x2), self.Y(y2),
                              self.X(x), self.Y(y))
            self.c.setStrokeColor(cor)
            self.c.setLineWidth(esp)
            self.c.drawPath(p, stroke=1, fill=0)
        self.c.setStrokeColor(self.cor_traco)

    def estrela(self, cx, cy, r_ext, r_int=None, pontas=5, giro=-90.0, cheio=True,
                espessura=None):
        r_int = r_ext * 0.45 if r_int is None else r_int
        pts = []
        for i in range(pontas * 2):
            r = r_ext if i % 2 == 0 else r_int
            a = math.radians(giro + i * 180.0 / pontas)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        self.poligono(pts, cheio=cheio, espessura=espessura)

    def sorriso(self, cx, cy, r, espessura=None):
        self.arco(cx, cy, r, 200, 340, espessura)

    def texto_contorno(self, texto, cx, base_y, tamanho, espessura=2.5):
        """Texto vazado (só contorno) para pintar — usado nas letras do alfabeto."""
        c = self.c
        tam = self.s(tamanho)
        largura = c.stringWidth(texto, FONTE_NEGRITO, tam)
        t = c.beginText()
        t.setTextRenderMode(1)  # 1 = só contorno
        t.setFont(FONTE_NEGRITO, tam)
        c.setStrokeColor(black)
        c.setLineWidth(espessura)
        t.setTextOrigin(self.X(cx) - largura / 2, self.Y(base_y))
        t.textOut(texto)
        # Isola o modo de texto (contorno/preenchido): no PDF ele vale até ser trocado.
        c.saveState()
        c.drawText(t)
        c.restoreState()
