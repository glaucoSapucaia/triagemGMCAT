import re


def normalizar_nome(arq: str) -> str:
    """Substitui qualquer caractere fora de AZ, az, 09, _, . ou - por '_'."""
    return re.sub(r"[^A-Za-z0-9_.-]", "_", arq)


def extrair_elementos_do_endereco_para_comparacao(endereco: str):
    """
    Extrai rua, número e CEP de um endereço, para fins de comparação.
    Normaliza CEP removendo hífen e pega o primeiro número após a rua.
    """
    if not endereco or endereco.lower() in ["não informado", ""]:
        return None, None, None

    # Extrai CEP (último grupo de 8 dígitos ou 5+3 dígitos)
    cep_match = re.search(r"(\d{5}-?\d{3}|\d{8})", endereco.replace(" ", ""))
    cep = cep_match.group(1) if cep_match else None
    if cep:
        cep = cep.replace("-", "")  # normaliza removendo hífen

    # Extrai número do imóvel: primeiro número após vírgula
    numero_match = re.search(r",\s*(\d+)", endereco)
    numero = numero_match.group(1) if numero_match else None

    # Rua = tudo antes da primeira vírgula
    rua = endereco.split(",")[0].strip() if "," in endereco else endereco.strip()

    return rua.lower(), numero, cep


def limpar_area(valor):
    """Converte string de área em formato brasileiro ou internacional para float."""
    if not valor:
        return None
    v = str(valor).lower().replace("m²", "").replace("m2", "").strip()

    # Detecta se é formato brasileiro com vírgula decimal
    if "," in v and "." in v:
        # '1.088,24' -> '1088.24'
        v = v.replace(".", "").replace(",", ".")
    elif "," in v:
        # '1088,24' -> '1088.24'
        v = v.replace(",", ".")
    # se tiver apenas ponto, assume decimal internacional
    v = re.sub(r"[^\d\.]", "", v)
    return v


def parse_area(valor):
    """
    Valida valor de área
    """
    if not valor or str(valor).strip().lower() in ["não informado", ""]:
        return None
    try:
        resultado = float(limpar_area(valor))
        return resultado
    except Exception as e:
        return None


def formatar_area(valor):
    """
    Formata valor de área
    """
    if valor is None:
        return "Não informado"
    try:
        resultado = (
            f"{valor:,.2f} m²".replace(",", "X").replace(".", ",").replace("X", ".")
        )
        return resultado
    except Exception as e:
        return str(valor)
