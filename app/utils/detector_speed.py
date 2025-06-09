import time
import cv2
from collections import Counter, defaultdict
import numpy as np
import csv
import math

class VelocidadeDetector:
    def __init__(self):
        self.x2_anterior = None
        self.tempo_anterior = None
        self.contador_classes = Counter()  # Contador para armazenar as quantidades
        self.dados = {}  # Dicionário para armazenar ID -> Classe
        self.contagem_classes = defaultdict(int)  # Dicionário para contar cada classe
        self.dados_objetos = {}  # Armazena posição e tempo de cada objeto por ID

    def calcular_velocidade(self, x2, y2, obj_id):
        """
        Calcula a velocidade do objeto baseado na posição (x2, y2) e retorna a velocidade em km/h.

        Parâmetros:
            x2 (int): Coordenada x do objeto detectado.
            y2 (int): Coordenada y do objeto detectado.
            obj_id (int): ID do objeto.

        Retorna:
            int: Velocidade calculada em km/h ou 0 se não puder ser calculada.
        """
        
        # Se o objeto ainda não foi registrado, inicializa seus dados
        if obj_id not in self.dados_objetos:
            self.dados_objetos[obj_id] = {"x2_anterior": x2, "y2_anterior": y2, "tempo_anterior": time.time()}
            #print(f"Inicializando dados para ID {obj_id}")
            return 0  # Retorna 0 na primeira vez
        
        
        dados = self.dados_objetos[obj_id]
        x2_anterior = dados["x2_anterior"]
        y2_anterior = dados["y2_anterior"]
        tempo_anterior = dados["tempo_anterior"]

        # Se não houve deslocamento, retorna 0
        if x2 == x2_anterior and y2 == y2_anterior:
            return 0

        # Calcula deslocamento total usando distância euclidiana
        distancia_pixels = math.sqrt((x2 - x2_anterior) ** 2 + (y2 - y2_anterior) ** 2)

        # Calcula tempo decorrido
        tempo_atual = time.time()
        delta_tempo = tempo_atual - tempo_anterior

        if delta_tempo <= 0.05:  # Evita cálculos muito rápidos que podem gerar erros
            return 0

        # Conversão de pixels para metros (fator baseado na escala da imagem)
        fator_conversao = 5.12 / 53  
        distancia_metros = distancia_pixels * fator_conversao

        # Calcula velocidade em m/s e converte para km/h
        velocidade_m_s = distancia_metros / delta_tempo
        velocidade_km_h = velocidade_m_s * 3.6

        # Atualiza os dados do objeto
        #self.dados_objetos[obj_id] = {"x2_anterior": x2, "y2_anterior": y2, "tempo_anterior": tempo_atual}

        # Verifica se a velocidade está dentro de um intervalo razoável
        if 1 <= velocidade_km_h <= 300:
            vel = int(velocidade_km_h)
            #print(f"Velocidade do ID {obj_id}: {vel} Km/h")
            return vel  

        return 0  # Retorna 0 se a velocidade estiver fora dos limites

    def exibir_texto_na_imagem(self, img, textos, posicao_inicial, espacamento=10, fonte=cv2.FONT_HERSHEY_SIMPLEX, escala=0.3, cor=(255, 255, 255), espessura=1):
        """
        Exibe textos em uma lista vertical, com posições calculadas automaticamente.

        Parâmetros:
            img (numpy.ndarray): A imagem onde o texto será desenhado.
            textos (list): Lista de strings contendo os textos a serem exibidos.
            posicao_inicial (tuple): Tupla (x, y) com a posição inicial do primeiro texto.
            espacamento (int): Espaçamento vertical entre as linhas de texto (padrão é 30 pixels).
            fonte (int): Fonte do texto (padrão é cv2.FONT_HERSHEY_SIMPLEX).
            escala (float): Escala do texto (padrão é 0.7).
            cor (tuple): Cor do texto no formato BGR (padrão é branco (255, 255, 255)).
            espessura (int): Espessura do texto (padrão é 2).

        Retorna:
            numpy.ndarray: A imagem com os textos desenhados.
        """
        #print(textos, posicao_inicial)
        x, y = posicao_inicial  # Desempacota a posição inicial

        for texto in textos:
            # Desenha o texto na posição atual
            cv2.putText(img, texto, (x, y), fonte, escala, cor, espessura)
            # Atualiza a coordenada y para a próxima linha
            y += espacamento

        return img
    
    '''
    def contar_classes(self, ids, classes):
        """
        Conta a quantidade de cada classe detectada com base no dicionário ID -> Classe.
        """
        self.dados = dict(zip(ids, classes))  # Cria o dicionário mapeando ID -> Classe
        self.contador_classes = Counter(self.dados.values())  # Conta quantas vezes cada classe aparece

        # Exibir a contagem das classes
        print("\nContagem das Classes Detectadas:")
        for classe, quantidade in self.contador_classes.items():
            print(f"{classe}: {quantidade}")'''
    
    '''
    def salvar_csv(self, filename="detecoes.csv"):
        """
        Salva os dados das detecções em um arquivo CSV.
        """
        with open(filename, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["ID", "Classe"])  # Cabeçalho
            for obj_id, classe in self.dados.items():
                writer.writerow([obj_id, classe])

        print(f"\nDados salvos em {filename}")'''
    '''
    def contar_classes2(self, ids, classes):
        """Atualiza a contagem acumulada das classes sem repetição dos mesmos IDs."""
        dados = dict(zip(ids, classes))  # Cria um dicionário associando ID à classe
        for classe in set(dados.values()):  # Remove duplicatas para evitar contagem repetida
            self.contagem_classes[classe] += 1  # Incrementa o total da classe
        
        # Exibe o total atualizado
        print("Total atualizado:", dict(self.contagem_classes))'''