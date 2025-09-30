import sys
from pathlib import Path
import logging

# Detecta se está rodando via PyInstaller
if getattr(sys, "frozen", False):
    ROOT = Path.cwd()  # pasta do PyInstaller
else:
    ROOT = Path(__file__).parent.parent.parent

# Ou, se você quer criar o log junto do executável:
# ROOT = Path.cwd()

LOG_FILE = "Detalhes da Triagem.txt"

# Cria pasta do log se não existir
log_file = ROOT / LOG_FILE
log_file.parent.mkdir(parents=True, exist_ok=True)

# Formatter para o console (limpo, sem milissegundos)
console_formatter = logging.Formatter("%(levelname)s: %(message)s")

# Formatter para o arquivo (com timestamp completo)
file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

# Handlers
console_handler = logging.StreamHandler()
console_handler.setFormatter(console_formatter)

file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
file_handler.setFormatter(file_formatter)

# Logger central
logger = logging.getLogger("triagem_logger")
logger.setLevel(logging.INFO)
logger.addHandler(console_handler)
logger.addHandler(file_handler)
