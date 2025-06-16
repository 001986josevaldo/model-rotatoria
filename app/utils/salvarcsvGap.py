import csv

class SalvarCSVGap:
    def salvarcsvGap(self, lista_entrada, arquivo="gap_veiculos.csv"):
        """
        Salva os dados de comparação entre veículos e gaps em um arquivo CSV.
        """
        with open(arquivo, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                'Tempo 1', 'ID 1', 'Veículo 1', 'Velocidade 1',
                'Tempo 2', 'ID 2', 'Veículo 2', 'Velocidade 2',
                'Gap (s)', 'Status'
            ])

            for v in lista_entrada:
                linha = [
                    v[0],     # Tempo 1
                    v[1],     # ID 1
                    v[2],     # Veículo 1
                    f"{v[3]}Km",  # Velocidade 1

                    v[4],     # Tempo 2
                    v[5],     # ID 2
                    v[6],     # Veículo 2
                    f"{v[7]}Km",  # Velocidade 2

                    f"{round(v[8], 2)}s" if v[8] is not None else "N/A",  # Gap
                    v[9]      # Status
                ]
                writer.writerow(linha)
