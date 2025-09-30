import sys
import os
import subprocess


def abrir_pasta(path):
    """Abre a pasta especificada no explorador de arquivos do sistema."""
    if sys.platform.startswith("win"):  # Windows
        os.startfile(path)
    elif sys.platform.startswith("darwin"):  # macOS
        subprocess.Popen(["open", path])
    else:  # Linux
        subprocess.Popen(["xdg-open", path])


def criar_pasta_resultados():
    """Cria uma pasta de resultados com timestamp legível em português do Brasil."""
    import locale
    from datetime import datetime

    # Define a localidade para português do Brasil
    locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")

    # Timestamp legível para a pasta resultados
    timestamp_legivel = datetime.now().strftime("Resultados - %d de %B de %Y %Hh%M")
    pasta_resultados = timestamp_legivel
    os.makedirs(pasta_resultados, exist_ok=True)

    return pasta_resultados
