import os

# Remove logs do tensorflow (Selenium)
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # 0=all, 1=warn, 2=error, 3=fatal

from pipeline import processar_indice, pasta_resultados, processar_protocolo
from utils import logger, abrir_pasta
from gui import iniciar_interface

from datetime import datetime


def main() -> None:
    """Função principal de execução."""
    try:
        credenciais, protocolos = iniciar_interface()

        for protocolo in protocolos:
            try:
                indices = processar_protocolo(protocolo, credenciais)
            except Exception as e:
                logger.error(f"Erro no processamento do protocolo {protocolo}: {e}")

            if indices:
                for indice in indices:
                    try:
                        processar_indice(indice, credenciais, protocolo)
                    except Exception as e:
                        logger.error(f"Erro no processamento do índice {indice}: {e}")

            else:
                continue

        if os.path.exists(pasta_resultados):
            logger.info(f"Abrindo pasta de resultados: {pasta_resultados}")
            abrir_pasta(pasta_resultados)
        else:
            logger.warning(f"Pasta de resultados não encontrada: {pasta_resultados}")

    except Exception as e:
        logger.error(f"Erro crítico no main: {e}")


if __name__ == "__main__":
    inicio = datetime.now()
    main()
    duracao = datetime.now() - inicio
    minutos, segundos = divmod(duracao.total_seconds(), 60)
    logger.info(f"Tempo de execução: {int(minutos)} min {int(segundos)} seg")
