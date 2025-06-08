import csv
from collections import defaultdict

class RelatorioCSV:
    @staticmethod
    def salvar_contagem_csv(lista_entrada, lista_saida, arquivo="contagem_veiculos.csv"):
        """
        Gera relatório CSV combinando dados de entrada e saída de veículos,
        ordenado pelo tempo em ordem crescente, garantindo sequência crescente para a coluna "Number".
        """
        entrada_por_id = {v['id']: v for v in lista_entrada}
        saida_por_id = {v['id']: v for v in lista_saida}
        todos_ids = set(entrada_por_id.keys()).union(set(saida_por_id.keys()))
        
        registros_preliminares = []
        
        for veiculo_id in todos_ids:
            entrada = entrada_por_id.get(veiculo_id, {})
            saida = saida_por_id.get(veiculo_id, {})
            classe = entrada.get('class', saida.get('class', 'Desconhecido'))
            
            registros_preliminares.append({
                'time': entrada.get('time', saida.get('time', 'null')),
                'id': veiculo_id,
                'class': classe,
                'speed': entrada.get('speed', saida.get('speed', 'null')),
                'entrada': entrada.get('EB', entrada.get('EA', 'null')),
                'saida': saida.get('Saida', 'null')
            })

        def time_to_seconds(t):
            if t == 'null': return float('inf')
            try:
                m, s = map(int, t.split(':'))
                return m * 60 + s
            except Exception:
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

class salvarcsvPet:
    def salvarcsvPet(self, lista_entrada, arquivo="contagem_veiculos.csv"):
        # Dicionário para acompanhar o último contador por classe
        contadores_por_classe = defaultdict(int)
        # Mapeia cada ID ao número já atribuído (para reutilização do contador se o ID já apareceu)
        contador_por_id = {}

        with open(arquivo, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                'Tempo', 'ID', 'Veículo', 'Velocidade', 'Contador',
                'Tempo', 'ID', 'Veículo', 'Velocidade', 'Contador', 'PET'
            ])

            for v in lista_entrada:
                id1, classe1 = v[1], v[2]
                id2, classe2 = v[5], v[6]

                # Define ou reutiliza contador para ID1
                if id1 not in contador_por_id:
                    contadores_por_classe[classe1] += 1
                    contador_por_id[id1] = contadores_por_classe[classe1]
                contador1 = contador_por_id[id1]

                # Define ou reutiliza contador para ID2
                if id2 not in contador_por_id:
                    contadores_por_classe[classe2] += 1
                    contador_por_id[id2] = contadores_por_classe[classe2]
                contador2 = contador_por_id[id2]

                linha = [
                    v[0],  # Tempo 1
                    id1,
                    classe1,
                    f"{v[3]}Km",
                    contador1,

                    v[4],  # Tempo 2
                    id2,
                    classe2,
                    f"{v[7]}Km",
                    contador2,

                    f"{round(v[8], 2)}s" if v[8] is not None else "N/A"
                ]
                writer.writerow(linha)