import os

# Remove logs do tensorflow (Selenium)
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # 0=all, 1=warn, 2=error, 3=fatal

from pipeline import processar_indice, pasta_resultados, processar_protocolo
from utils import logger, abrir_pasta
from gui import iniciar_interface

from datetime import datetime


def main() -> None:
    """
    Função principal de execução.
    Normaliza protocos e ICs.
    """
    try:
        credenciais, protocolos = iniciar_interface()
        count_protocol = 0
        count_IC = 0

        for protocolo in protocolos:
            count_protocol += 1
            # Remove todos os "-" e "/"
            # Protocolos não podem ter "-" e "/" para inserção no SIGEDE
            protocolo_normalizado = (
                protocolo.replace("-", "").replace("/", "").replace(".", "")
            )

            try:
                indices = processar_protocolo(protocolo_normalizado, credenciais)
            except Exception as e:
                logger.error(f"Erro no processamento do protocolo {protocolo}: {e}")

            if indices:
                for indice in indices:
                    count_IC += 1

                    # Remove todos os "-"
                    # Alguns ICs possuem "-" quando o valor é capturado do SIGEDE
                    indice_normalizado = indice.replace("-", "")

                    try:
                        processar_indice(indice_normalizado, credenciais, protocolo)
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

    return count_protocol, count_IC


if __name__ == "__main__":
    inicio = datetime.now()
    protocolos, ics = main()
    duracao = datetime.now() - inicio
    minutos, segundos = divmod(duracao.total_seconds(), 60)
    logger.info(f"Protocolos: {protocolos}")
    logger.info(f"ICs: {ics}")
    logger.info(f"Tempo de execução: {int(minutos)} min {int(segundos)} seg")
