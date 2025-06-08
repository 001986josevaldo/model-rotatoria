import csv
from collections import defaultdict
import time

    
class ContadorVeiculos123:
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
        if self.contagem_veiculos != self.contagem_anterior:
            print(f"Contagem A e B: Caminhão: {caminhao}, Carro: {carro}, Moto: {moto}")
            print("----------------------------------------------------------------")
        return caminhao, carro, moto
    




    # -------------- SALVAR O ARQUIVO .CSV --------------------------------

class ContadorEntradas123:
    def salvar_contagem_csv(self, lista_entrada, arquivo="contagem_veiculos.csv"):
        def time_to_seconds(t):
            m, s = map(int, t.split(':'))
            return m * 60 + s

        def calcular_pet(t1, t2):
            return f"{int(time_to_seconds(t2) - time_to_seconds(t1)):02}s"

        # Ordenar os dados por tempo
        lista_entrada.sort(key=lambda x: time_to_seconds(x.get('time', '00:00')))

        # Contadores por classe
        contadores = defaultdict(int)
        contador_por_id = {}

        # Atribui um contador por tipo de veículo
        for v in lista_entrada:
            tipo = v['class']
            contadores[tipo] += 1
            contador_por_id[v['id']] = contadores[tipo]

        # Gera o CSV
        with open(arquivo, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                'Tempo', 'ID', 'Veículo', 'Velocidade', 'Contador',
                'Tempo', 'ID', 'Veículo', 'Velocidade', 'Contador', 'PET'
            ])

            # Só até o penúltimo par (evita última linha incompleta)
            for i in range(len(lista_entrada) - 1):
                v1 = lista_entrada[i]
                v2 = lista_entrada[i + 1]

                linha = [
                    v1.get('time', ''),
                    v1.get('id', ''),
                    v1.get('class', ''),
                    f"{v1.get('speed', '')}Km",
                    contador_por_id[v1['id']],
                    v2.get('time', ''),
                    v2.get('id', ''),
                    v2.get('class', ''),
                    f"{v2.get('speed', '')}Km",
                    contador_por_id[v2['id']],
                    calcular_pet(v1['time'], v2['time'])
                ]
                writer.writerow(linha)



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
            return f"{minutos:02d}:{segundos:02d}.{milissegundos:03d}"
        else:
            return f"{minutos:02d}:{segundos:02d}"

    def reiniciar(self, novo_inicio=None):
        """
        Reinicia o contador de tempo.
        
        Args:
            novo_inicio (float, optional): Novo timestamp inicial. Se None, usa o tempo atual.
        """
        self.inicio = novo_inicio if novo_inicio is not None else time.time()
