import os
from datetime import datetime
from pipeline import processar_indice, processar_protocolo
from utils import logger, abrir_pasta, criar_pasta_resultados
from gui import iniciar_interface


def main():
    def processar(credenciais, protocolos, cancelar_event, atualizar_progresso):
        pasta_resultados = criar_pasta_resultados()
        count_protocol = 0
        count_IC = 0
        inicio_exec = datetime.now()

        try:
            for i, protocolo in enumerate(protocolos, 1):
                if cancelar_event.is_set():
                    logger.info("Processamento cancelado pelo usuário.")
                    break

                count_protocol += 1
                protocolo_normalizado = (
                    protocolo.replace("-", "").replace("/", "").replace(".", "")
                )

                try:
                    indices = processar_protocolo(
                        protocolo_normalizado, credenciais, pasta_resultados
                    )
                except Exception as e:
                    logger.error(f"Erro no protocolo {protocolo}: {e}")
                    indices = []

                if indices:
                    for indice in indices:
                        if cancelar_event.is_set():
                            break
                        count_IC += 1
                        indice_normalizado = indice.replace("-", "")
                        try:
                            processar_indice(
                                indice_normalizado,
                                credenciais,
                                protocolo,
                                pasta_resultados,
                            )
                        except Exception as e:
                            logger.error(f"Erro no índice {indice}: {e}")

                atualizar_progresso(i)

            if not cancelar_event.is_set():
                if os.path.exists(pasta_resultados):
                    logger.info(f"Abrindo pasta de resultados: {pasta_resultados}")
                    abrir_pasta(pasta_resultados)
                else:
                    logger.warning(
                        f"Pasta de resultados não encontrada: {pasta_resultados}"
                    )

        except Exception as e:
            logger.error(f"Erro crítico: {e}")

        finally:
            duracao = datetime.now() - inicio_exec
            minutos, segundos = divmod(duracao.total_seconds(), 60)
            logger.info(f"Protocolos processados: {count_protocol}")
            logger.info(f"ICs processados: {count_IC}")
            logger.info(f"Tempo: {int(minutos)} min {int(segundos)} seg")
            root.after(0, resetar_interface)

    root, resetar_interface, _ = iniciar_interface(processar)
    root.mainloop()


if __name__ == "__main__":
    main()
