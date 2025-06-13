import csv
from collections import defaultdict
import time

    
class ContadorVeiculos:
    def __init__(self, linhaA, linhaB):
        """
        Inicializa a classe com as coordenadas das linhas A e B.
        :param linhaA: Coordenadas da linha A (x1, y, x2).
        :param linhaB: Coordenadas da linha B (y1, x, y2).
        """
        self.linhaA = linhaA
        self.linhaB = linhaB
        
        self.contadorA = []  # Lista para armazenar IDs que cruzaram a linha A
        self.contadorB = []  # Lista para armazenar IDs que cruzaram a linha B
        # ----------------------------------------------------------------
        self.contIdA = []
        self.contIdB = []
 

        self.contagem_veiculos = {"carro": 0, "moto": 0, "caminhao": 0}

        # Mapeamento dos números para os nomes dos veículos
        self.mapeamento_veiculos = {0: "caminhao", 1: "carro", 2: "moto"}

    def verificar_cruzamento_linhaA(self, cx, cy, obj_id):
        """
        Verifica se o objeto cruzou a linha A e atualiza o contador.
        :param cx: Coordenada x do centro do objeto.
        :param cy: Coordenada y do centro do objeto.
        :param obj_id: ID do objeto.
        :return: Nenhum.
        """
        if self.linhaA[0] < cx < self.linhaA[2] and self.linhaA[1] - 15 < cy < self.linhaA[1] + 15:
            if obj_id not in self.contadorA:
                self.contadorA.append(obj_id)

    def verificar_cruzamento_linhaB(self, cx, cy, obj_id):
        """
        Verifica se o objeto cruzou a linha B e atualiza o contador.
        :param cx: Coordenada x do centro do objeto.
        :param cy: Coordenada y do centro do objeto.
        :param obj_id: ID do objeto.
        :return: Nenhum.
        """
        if self.linhaB[0] - 15 < cx < self.linhaB[1] + 15 and self.linhaB[1] < cy < self.linhaB[3]:
            if obj_id not in self.contadorB:
                self.contadorB.append(obj_id)

# ----------------------------------------------------------------
    def verificar_cruzamento_linha_id_obj(self, cx, cy, obj_id, nomeObjeto):
        """
        Verifica se um veículo cruzou a linha A ou B e atualiza a contagem.

        :param cx: Coordenada X do centro do objeto
        :param cy: Coordenada Y do centro do objeto
        :param obj_id: ID do objeto detectado
        :param nomeObjeto: Nome numérico do objeto (0 = caminhão, 1 = carro, 2 = moto)
        :return: Quantidade atualizada de caminhões, carros e motos
        """       
        nome_veiculo = self.mapeamento_veiculos.get(nomeObjeto, "desconhecido")
        # Salva a contagem anterior para comparação
        self.contagem_anterior = self.contagem_veiculos.copy()

        # Verifica a passagem pela Linha A
        x1, y1, x2, y2 = self.linhaA
        if x1 <= cx <= x2 and (y1 - 5) <= cy <= (y1 + 5):
            if obj_id not in self.contIdA:
                self.contIdA.append(obj_id)
                if nome_veiculo in self.contagem_veiculos:
                    self.contagem_veiculos[nome_veiculo] += 1  # Soma à contagem

        # Verifica a passagem pela Linha B
        x1, y1, x2, y2 = self.linhaB
        margem = 2  # Margem de tolerância para detecção
        # Verifica se é uma linha vertical (mesmo x)
        if x1 == x2:
        # Verifica se cx está dentro da margem e cy está entre y1 e y2
            if (x1 - margem <= cx <= x1 + margem) and (min(y1, y2) <= cy <= max(y1, y2)):
            
                if obj_id not in self.contIdB:
                    self.contIdB.append(obj_id)
                    if nome_veiculo in self.contagem_veiculos:
                        self.contagem_veiculos[nome_veiculo] += 1

        # Obtém valores atuais
        caminhao = self.contagem_veiculos["caminhao"]
        carro = self.contagem_veiculos["carro"]
        moto = self.contagem_veiculos["moto"]

        # Verifica se houve mudança na contagem
        #if self.contagem_veiculos != self.contagem_anterior:
            #print(f"Contagem A e B: Caminhão: {caminhao}, Carro: {carro}, Moto: {moto}")
            #print("----------------------------------------------------------------")
        return caminhao, carro, moto
    




    # -------------- SALVAR O ARQUIVO .CSV --------------------------------
    def salvar_contagem_csv(self, lista_entrada, lista_saida, arquivo="contagem_veiculos.csv"):
        """
        Gera relatório CSV combinando dados de entrada e saída de veículos,
        ordenado pelo tempo em ordem crescente, garantindo sequência crescente para a coluna "Number".
        """
        entrada_por_id = {v['id']: v for v in lista_entrada}
        saida_por_id = {v['id']: v for v in lista_saida}
        todos_ids = set(entrada_por_id.keys()).union(saida_por_id.keys())

        registros_preliminares = []

        for veiculo_id in todos_ids:
            entrada = entrada_por_id.get(veiculo_id, {})
            saida = saida_por_id.get(veiculo_id, {})
            classe = entrada.get('class', saida.get('class', 'Desconhecido'))

            registros_preliminares.append({
                'time': entrada.get('time') or saida.get('time') or 'null',
                'id': veiculo_id,
                'class': classe,
                'speed': entrada.get('speed') or saida.get('speed') or 'null',
                'entrada': entrada.get('EB') or entrada.get('EA') or 'null',
                'saida': saida.get('Saida', 'null')
            })

        def time_to_seconds(t):
            """Converte string de tempo no formato MM:SS ou segundos decimais para float."""
            if t == 'null':
                return float('inf')
            try:
                if ':' in t:
                    m, s = map(float, t.split(':'))
                    return m * 60 + s
                return float(t)
            except ValueError:
                return float('inf')

        registros_ordenados = sorted(registros_preliminares, key=lambda x: time_to_seconds(x['time']))

        contagem_seq = defaultdict(int)
        for registro in registros_ordenados:
            contagem_seq[registro['class']] += 1
            registro['number'] = contagem_seq[registro['class']]

        with open(arquivo, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Time', 'Id', 'Class', 'Number', 'Speed', 'Entrada', 'Saida', 'Total Geral'])

            for i, registro in enumerate(registros_ordenados):
                writer.writerow([
                    registro['time'],
                    registro['id'],
                    registro['class'],
                    registro['number'],
                    f"{round(float(registro['speed']))}" if registro['speed'] != 'null' else 'null',
                    registro['entrada'],
                    registro['saida'],
                    len(todos_ids) if i == 0 else ""
                ])
    def obter_contagem_final(self):
        return self.contagem_veiculos
    
    def get_contadorA(self):
        """
        Retorna a lista de IDs que cruzaram a linha A.
        :return: Lista de IDs.
        """
        return self.contadorA

    def get_contadorB(self):
        """
        Retorna a lista de IDs que cruzaram a linha B.
        :return: Lista de IDs.
        """
        return self.contadorB
    

    # MÉTODO para calcular o tempo
class CalcularTempo:
    def __init__(self, inicio=None):
        """
        Inicializa o formatador de tempo.
        
        Args:
            inicio (float, optional): Timestamp inicial. Se None, usa o tempo atual.
        """
        self.inicio = inicio if inicio is not None else time.time()

    def tempo_decorrido(self, incluir_milissegundos=True):
        """
        Calcula e formata o tempo decorrido desde o início.
        
        Args:
            incluir_milissegundos (bool): Se True, inclui milissegundos no formato.
        
        Returns:
            str: Tempo formatado como "MM:SS" ou "MM:SS.mmm".
        """
        tempo_decorrido = time.time() - self.inicio
        
        minutos = int(tempo_decorrido // 60)
        segundos = int(tempo_decorrido % 60)
        
        if incluir_milissegundos:
            milissegundos = int((tempo_decorrido % 1) * 1000)
            return f"{minutos:02d}:{segundos:02d}.{milissegundos:02d}"
        else:
            return f"{minutos:02d}:{segundos:02d}"

    def reiniciar(self, novo_inicio=None):
        """
        Reinicia o contador de tempo.
        
        Args:
            novo_inicio (float, optional): Novo timestamp inicial. Se None, usa o tempo atual.
        """
        self.inicio = novo_inicio if novo_inicio is not None else time.time()

class TempoVideoPorFrame:
    def __init__(self, fps):
        self.fps = fps

    def calcular_segundos(self, frame_atual):
        """Retorna o tempo decorrido em segundos (float) com base no número do frame."""
        return round(frame_atual / self.fps, 3) # 3 casas decimais ao final

    def calcular_tempo_formatado(self, frame_atual):
        """Retorna o tempo formatado como string (MM:SS.mmm)."""
        tempo_segundos = self.calcular_segundos(frame_atual)
        minutos = int(tempo_segundos // 60)
        segundos = int(tempo_segundos % 60)
        milissegundos = int((tempo_segundos % 1) * 1000)
        return f"{minutos:02d}:{segundos:02d}.{milissegundos:03d}"
