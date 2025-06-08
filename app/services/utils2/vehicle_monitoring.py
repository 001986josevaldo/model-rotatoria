import time
import cv2
import numpy as np


class MonitoramentoVeiculo:
    def __init__(self):
        self.tempo_entrada_por_veiculo = {}
        self.ultimo_veiculo_id = None
        self.contador_tempo = 0

    def atualizar_tempo_veiculo(self, obj_id, x1, y1, img, veiculo_na_area_risco):
        # Se o veículo entrou na área OU já teve sua contagem iniciada, continua
        if veiculo_na_area_risco(x1, y1) or obj_id in self.tempo_entrada_por_veiculo:
            tempo_atual = time.time()  # Captura o tempo atual

            if obj_id not in self.tempo_entrada_por_veiculo:
                # Se um novo veículo entrou, reinicia a contagem
                self.tempo_entrada_por_veiculo.clear()  # Limpa registros antigos
                self.tempo_entrada_por_veiculo[obj_id] = tempo_atual
                self.ultimo_veiculo_id = obj_id  # Atualiza o último veículo ativo
                self.contador_tempo = 0  # Reinicia o contador
                #print(f"Veículo {obj_id} entrou na área. Iniciando nova contagem.")

            # Calcula o tempo decorrido para aquele veículo específico
            self.contador_tempo = tempo_atual - self.tempo_entrada_por_veiculo[obj_id]

            # Converte o tempo para minutos e segundos
            minutos = int(self.contador_tempo // 60)
            segundos = int(self.contador_tempo % 60)
            tempo_formatado = f"{minutos:02d}:{segundos:02d}"

            #print(f"Veículo {obj_id} tempo total: {tempo_formatado} minutos.")

            # Exibe a contagem de tempo na imagem
            #cv2.putText(img, f"PET = ID {obj_id} Tempo: {tempo_formatado}", (350, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)






class DetectorLinhaUnica:
    def __init__(self, coordenadas_linha, cor=(0, 255, 255), espessura=1, margem=5):
        """
        Inicializa o detector com uma única linha de cruzamento
        
        Args:
            coordenadas_linha (tuple): (x1, y1, x2, y2) - Coordenadas da linha
            cor (tuple): Cor da linha no formato BGR (padrão: amarelo)
            espessura (int): Espessura da linha em pixels (padrão: 2)
            margem (int): Margem de detecção em pixels (padrão: 15)
        """
        self.linha = coordenadas_linha
        self.cor = cor
        self.espessura = espessura
        self.margem = margem
        
        # Validação inicial
        x1, y1, x2, y2 = self.linha
        if not (x1 == x2 or y1 == y2):
            raise ValueError("A linha deve ser horizontal ou vertical")

    def verificar_cruzamento(self, img, cx, cy):
        """
        Verifica se o ponto (cx, cy) cruzou a linha e desenha a linha na imagem
        
        Args:
            img: Imagem onde a linha será desenhada
            cx (int): Coordenada x do ponto (centro do veículo)
            cy (int): Coordenada y do ponto (centro do veículo)
            
        Returns:
            tuple: (bool, img) - (True se cruzou, imagem com linha desenhada)
        """
        x1, y1, x2, y2 = self.linha
        cruzou = False
        
        # Desenha a linha na imagem
        #cv2.line(img, (x1, y1), (x2, y2), self.cor, self.espessura)
        
        # Verifica se é linha horizontal
        if y1 == y2:
            dentro_x = min(x1, x2) <= cx <= max(x1, x2)
            dentro_y = (y1 - self.margem) <= cy <= (y1 + self.margem)
            cruzou = dentro_x and dentro_y
            if cruzou:
                # linha que pisca
                #cv2.line(img, (x1, (y1-5)), (x2, (y1-5)), (0, 165, 255), 1)
                cv2.circle(img, (cx,cy), 5, (0, 165, 255), -1)
            # Opcional: desenha área de detecção
            #cv2.line(img, (x1, y1-self.margem), (x2, y1-self.margem), (0, 165, 255), 1)
            #cv2.line(img, (x1, y1+self.margem), (x2, y1+self.margem), (0, 165, 255), 1)
        
        # Verifica se é linha vertical
        else:
            dentro_x = (x1 - self.margem) <= cx <= (x1 + self.margem)
            dentro_y = min(y1, y2) <= cy <= max(y1, y2)
            cruzou = dentro_x and dentro_y
            if cruzou:
                # linha que pisca
                #cv2.line(img, ((x1-5),y1), ((x1-5), y2), (0, 165, 255), 1)
                cv2.circle(img, (cx,cy), 5, (0, 165, 255), -1)
            # Opcional: desenha área de detecção
            #cv2.line(img, (x1-self.margem, y1), (x1-self.margem, y2), (0, 165, 255), 1)
            #cv2.line(img, (x1+self.margem, y1), (x1+self.margem, y2), (0, 165, 255), 1)
        
        return cruzou, img