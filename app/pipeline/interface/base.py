from abc import ABC, abstractmethod


class SistemaAutomacao(ABC):
    @abstractmethod
    def executar(self, indice, credenciais, pasta_indice):
        """Executa coleta de dados e retorna os resultados do sistema"""
        pass
