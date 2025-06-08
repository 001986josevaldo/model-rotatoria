class DetectorCruzamentoVeiculos123:
    def __init__(self, linhas):
        self.linhas = linhas
        self.ids_contabilizados = {nome: [] for nome in linhas}  # IDs já contabilizados
        self.nomes_contabilizados = {nome: [] for nome in linhas}  # Nomes dos objetos
        self.contagem_por_linha = {
            nome: {"caminhao": 0, "carro": 0, "moto": 0} for nome in linhas
        }
        self.mapeamento_veiculos = {0: "caminhao", 1: "carro", 2: "moto"}
        self.ids_registrados = {nome: set() for nome in linhas}  # Evita duplicações

    def verificar_cruzamento(self, cx, cy, linha):
        """Verifica se (cx, cy) cruzou a linha (otimizado)."""
        x1, y1, x2, y2 = linha
        if y1 == y2:  # Linha horizontal
            return x1 <= cx <= x2 and (y1 - 15) <= cy <= (y1 + 15)
        elif x1 == x2:  # Linha vertical
            return (x1 - 15) <= cx <= (x1 + 15) and y1 <= cy <= y2
        return False

    def contabilizar_cruzamento(self, cx, cy, obj_id, nome_objeto, nome_linha):
        """Contabiliza a passagem do veículo pela linha, se válida."""
        if nome_linha not in self.linhas:
            return None

        linha = self.linhas[nome_linha]
        nome_veiculo = self.mapeamento_veiculos.get(nome_objeto, "desconhecido")

        if (
            self.verificar_cruzamento(cx, cy, linha)
            and obj_id not in self.ids_contabilizados[nome_linha]
        ):
            self.ids_contabilizados[nome_linha].append(obj_id)
            self.nomes_contabilizados[nome_linha].append(nome_objeto)
            
            if nome_veiculo in self.contagem_por_linha[nome_linha]:
                self.contagem_por_linha[nome_linha][nome_veiculo] += 1

            return {
                "obj_id": obj_id,
                "nome_veiculo": nome_veiculo,
                "linha": nome_linha,
            }
        return None

    def obter_contagem_por_linha(self):
        return self.contagem_por_linha

    def obter_total_geral(self):
        """Calcula o total geral a partir das linhas (sem redundância)."""
        total = {"caminhao": 0, "carro": 0, "moto": 0}
        for linha in self.contagem_por_linha.values():
            for veiculo, qtd in linha.items():
                total[veiculo] += qtd
        return total

# ----------------------------------------------------------------
    def contabilizar_cruzamento2(self, cx, cy, obj_id, tipo_veiculo, nome_linha):
        """Registra cruzamento se for válido"""
        if nome_linha not in self.linhas:
            return False

        if obj_id not in self.ids_registrados[nome_linha]:
            if self._verificar_cruzamento2(cx, cy, self.linhas[nome_linha]):
                self.ids_registrados[nome_linha].add(obj_id)
                self.contagem_por_linha[nome_linha][tipo_veiculo] += 1
                return True
        return False
    
    def _verificar_cruzamento2(self, cx, cy, linha):
        # """Lógica de detecção de cruzamento"""
        x1, y1, x2, y2 = linha
        if y1 == y2:  # Linha horizontal
            return x1 <= cx <= x2 and (y1-10) <= cy <= (y1+10)
        else:  # Linha vertical
            return (x1-10) <= cx <= (x1+10) and y1 <= cy <= y2

    def somar_linhas2(self, linhaA, linhaB):
        """Retorna a soma das contagens de duas linhas"""
        return {
            "caminhao": self.contagem_por_linha[linhaA]["caminhao"] + self.contagem_por_linha[linhaB]["caminhao"],
            "carro": self.contagem_por_linha[linhaA]["carro"] + self.contagem_por_linha[linhaB]["carro"],
            "moto": self.contagem_por_linha[linhaA]["moto"] + self.contagem_por_linha[linhaB]["moto"]
        }