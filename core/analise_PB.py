import os
import re
import PyPDF2


def ler_planta_basica(pasta_anexos):
    """
    Lê o PDF da Planta Básica e extrai:
    - ÁREA CONSTRUÍDA TOTAL
    - EXERCÍCIO
    - TIPO USO

    A leitura do PDF não esta funcional. Manterei a função aqui para possibilidade futura de uso.
    O mais acertivo, foi obter as informações diretamente do sistema web utilizando selenium.
    """
    if not pasta_anexos or not os.path.exists(pasta_anexos):
        return None

    arquivo_planta = None
    for arq in os.listdir(pasta_anexos):
        if "Planta_Basica" in arq and arq.lower().endswith(".pdf"):
            arquivo_planta = os.path.join(pasta_anexos, arq)
            break

    if not arquivo_planta:
        return None

    # Extrair texto completo
    texto_completo = ""
    with open(arquivo_planta, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            texto = page.extract_text()
            if texto:
                texto_completo += texto.replace("\n", "")

    # 1. ÁREA CONSTRUÍDA TOTAL: números com vírgula ou ponto, próximos ao título
    match_area = re.search(
        r"ÁREA CONSTRU[IÍ]DA TOTAL.*?([0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]{2})?)",
        texto_completo,
        re.IGNORECASE,
    )
    area = match_area.group(1) if match_area else None

    # 2. EXERCÍCIO: 4 dígitos antes da palavra EXERCÍCIO
    match_exercicio = re.search(r"(\d{4})EXERC[IÍ]CIO", texto_completo, re.IGNORECASE)
    exercicio = match_exercicio.group(1) if match_exercicio else None

    # 3. TIPO USO: letras maiúsculas depois de "TIPO USO"
    match_tipo_uso = re.search(r"TIPO USO\s*([A-Z]+)", texto_completo)
    tipo_uso = match_tipo_uso.group(1) if match_tipo_uso else None

    return {
        "area_construida_total": area,
        "exercicio": exercicio,
        "tipo_uso": tipo_uso,
    }
