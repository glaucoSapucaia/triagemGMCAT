import time
from functools import wraps
from .logger import logger


def retry(max_retries=3, delay=5, exceptions=(Exception,)):
    """
    Decorador para repetir a execução de uma função em caso de erro.
    Nesse contexto, não é necessário refresh do Selenium, porque
    cada tentativa recria o driver.

    Args:
        max_retries (int): número máximo de tentativas.
        delay (int): tempo (segundos) para esperar entre tentativas.
        exceptions (tuple): exceções que devem disparar retry.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    logger.error(
                        "Erro na execução de %s (tentativa %d/%d): %s",
                        func.__name__,
                        attempt,
                        max_retries,
                        e,
                    )
                    if attempt < max_retries:
                        logger.info(
                            f"Aguardando {delay}s antes da próxima tentativa..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            "Falha definitiva em %s após %d tentativas",
                            func.__name__,
                            max_retries,
                        )
                        raise

        return wrapper

    return decorator
