# desenho.py
import cv2

class DesenhadorLinhas:
    def __init__(self, imagem):
        self.img = imagem

    def desenhar_linha(self, coords, cor=(255, 0, 0), espessura=1):
        """
        Desenha uma linha na imagem.

        Parâmetros:
        - coords: (x1, y1, x2, y2)
        - cor: (B, G, R)
        - espessura: espessura da linha
        """
        x1, y1, x2, y2 = coords
        cv2.line(self.img, (x1, y1), (x2, y2), cor, espessura)

    def desenhar_varias_linhas(self, lista_linhas):
        """
        Desenha várias linhas. Cada item da lista deve ser uma tupla:
        (x1, y1, x2, y2, (B, G, R))
        """
        for linha in lista_linhas:
            coords = linha[:4]
            cor = linha[4]
            self.desenhar_linha(coords, cor)