import os
import re
from reportlab.platypus import Table, TableStyle
from reportlab.lib.pagesizes import A4
from urllib.parse import quote
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    ListFlowable,
    ListItem,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from datetime import datetime


def normalizar_nome(arq: str) -> str:
    """Substitui qualquer caractere fora de AZ, az, 09, _, . ou - por '_'."""
    return re.sub(r"[^A-Za-z0-9_.-]", "_", arq)


def gerar_relatorio(
    indice_cadastral,
    anexos_count=None,
    projetos_count=None,
    pasta_anexos=None,
    prps_trabalhador="Nome do trabalhador",
    nome_pdf="relatorio_profissional.pdf",
    dados_planta=None,
    dados_projeto=None,
    dados_sisctm=None,
):
    """
    Gera um relatório PDF com base nos dados fornecidos.
    """
    doc = SimpleDocTemplate(
        nome_pdf,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=18,
    )
    elementos = []

    styles = getSampleStyleSheet()
    style_normal = styles["Normal"]
    style_normal.fontSize = 10

    def gerar_tabela_secao(
        titulo_secao, dados_dict=None, chaves=None, nomes_legiveis=None, anexos=None
    ):
        """
        Cria uma tabela de chave/valor para uma seção do relatório.
        """
        data = [["Chave", "Valor"]]

        # Definir quais chaves devem ser tratadas como área
        chaves_area = [
            "lote_cp_ativo_area_informada",
            "iptu_ctm_geo_area",
            "iptu_ctm_geo_area_terreno",
            "area_construida",
            "area_lotes",
        ]

        if dados_dict and chaves:
            for chave in chaves:
                valor = dados_dict.get(chave)

                # Garante que None ou string vazia vire "Não informado"
                if valor is None or valor == "":
                    valor = "Não informado"

                # Padroniza unidades de área
                if chave in chaves_area and valor not in ["Não informado", ""]:
                    valor = re.sub(
                        r"\s*m2\s*|\s*m²\s*", "", str(valor), flags=re.IGNORECASE
                    )
                    valor = f"{valor} m²"

                # Substitui vírgula por ponto em valores numéricos
                if valor not in ["Não informado", ""] and isinstance(valor, str):
                    valor = valor.replace(",", ".")

                # Cria Paragraph para permitir quebra de linha
                valor_paragraph = Paragraph(str(valor), style_normal)
                data.append(
                    [
                        nomes_legiveis.get(chave, chave) if nomes_legiveis else chave,
                        valor_paragraph,
                    ]
                )

        # Adiciona anexos se houver
        if anexos:
            for i, anexo in enumerate(anexos, start=1):
                # Normaliza o nome do arquivo para o link
                href = "./" + quote(
                    anexo,
                    safe="._-ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789",
                )
                link = Paragraph(
                    f'<a href="{href}" color="blue">{anexo}</a>', style_normal
                )
                data.append([f"Anexo {i}", link])

        tabela = Table(data, colWidths=[200, 300])
        tabela.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ]
            )
        )

        adicionar_secao(titulo_secao)
        elementos.append(tabela)
        elementos.append(Spacer(1, 12))

    def extrair_elementos_para_comparacao(endereco: str):
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

    # Estilos
    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle(
        "Titulo",
        parent=estilos["Title"],
        fontSize=18,
        alignment=TA_CENTER,
        textColor=colors.darkblue,
        spaceAfter=12,
    )
    estilo_info_normal = ParagraphStyle(
        "InfoNormal",
        parent=estilos["Normal"],
        fontSize=11,
        alignment=TA_CENTER,
        spaceAfter=20,
    )
    estilo_secao = ParagraphStyle(
        "Secao",
        parent=estilos["Normal"],
        fontSize=13,
        leading=16,
        spaceAfter=6,
        spaceBefore=12,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1f4e78"),
    )
    estilo_texto = ParagraphStyle(
        "Texto",
        parent=estilos["Normal"],
        fontSize=11,
        leading=16,
        spaceAfter=10,
    )
    estilo_link = ParagraphStyle(
        "Link",
        parent=estilo_texto,
        textColor=colors.blue,
        underline=True,
    )

    # Cabeçalho
    titulo = f"Relatório de Triagem - IC {indice_cadastral}"
    elementos.append(Paragraph(titulo, estilo_titulo))
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")
    elementos.append(
        Paragraph(
            f"<b>Data:</b> {data_atual} <b>Trabalhador(a):</b> {prps_trabalhador}",
            estilo_info_normal,
        )
    )

    # Seções utilitárias
    def adicionar_secao(titulo_secao, texto_secao=None):
        elementos.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        elementos.append(Spacer(1, 8))
        elementos.append(Paragraph(titulo_secao, estilo_secao))
        if texto_secao:
            elementos.append(Paragraph(texto_secao, estilo_texto))
        elementos.append(Spacer(1, 12))

    # Adiciona anexos às seções com o prefixo "./" no href (para abrir localmente com links relativos)
    def adicionar_anexos(lista_arquivos):
        for arq in lista_arquivos:
            # Normaliza o do nome do arquivo para o link
            href = "./" + quote(
                arq,
                safe="._-ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789",
            )
            elementos.append(Paragraph(f'<a href="{href}">{arq}</a>', estilo_link))
            elementos.append(Spacer(1, 5))

    # Prepara anexos (com renomeação no disco para nomes seguros)
    anexos_planta, anexos_siatu, anexos_projetos, anexos_sisctm, anexos_google = (
        [],
        [],
        [],
        [],
        [],
    )

    if pasta_anexos and os.path.exists(pasta_anexos):
        for arq in sorted(os.listdir(pasta_anexos)):
            nome_norm = normalizar_nome(arq)
            src = os.path.join(pasta_anexos, arq)
            dst = os.path.join(pasta_anexos, nome_norm)
            if arq != nome_norm:
                try:
                    os.rename(src, dst)
                except FileExistsError:
                    # Se já existir um igual, desambiguação simples
                    base, ext = os.path.splitext(nome_norm)
                    i = 1
                    while os.path.exists(dst):
                        dst = os.path.join(pasta_anexos, f"{base}_{i}{ext}")
                        i += 1
                    os.rename(src, dst)
                    nome_norm = os.path.basename(dst)
                except Exception:
                    # Se não conseguir renomear, segue com o nome original
                    nome_norm = arq

            arq = nome_norm

            # Classificação dos anexos
            if "Planta_Basica" in arq:
                anexos_planta.append(arq)
            elif (
                "sem_projeto" in arq.lower()
                or "sem_alvara-baixa" in arq.lower()
                or "certidao_baixa" in arq.lower()
                or "alvara_construcao" in arq.lower()
                or "projeto" in arq.lower()
            ):
                anexos_projetos.append(arq)
            elif "CTM" in arq:
                anexos_sisctm.append(arq)
            elif "google" in arq:
                anexos_google.append(arq)
            else:
                anexos_siatu.append(arq)

    # Seções
    # COL
    adicionar_secao(
        "1. Certidão de Origem de Lote",
        "Verifique se a COL está na lista de Anexos SIATU. "
        "<br/>Caso não a encontre, busque manualmente a certidão de origem de lote (COL). "
        "<br/><b>Informação obtida no portal:</b> "
        '<a href="https://siurbe.pbh.gov.br/#/solicitacao/CertidaoOrigemLote">'
        '<font color="blue"><u>https://siurbe.pbh.gov.br/#/solicitacao/CertidaoOrigemLote</u></font></a>',
    )

    # 2. Planta Básica - Exercício Seguinte e/ou Recalculado e/ou Primeiro do Ano
    if dados_planta:
        chaves_pb = ["area_construida", "exercicio", "tipo_uso", "endereco_imovel"]
        nomes_legiveis_pb = {
            "area_construida": "Área Construída Total",
            "exercicio": "Exercício",
            "tipo_uso": "Tipo de uso",
            "endereco_imovel": "Endereço do Imóvel (SIATU)",
        }
        gerar_tabela_secao(
            "2. Planta Básica - Exercício Seguinte e/ou Recalculado e/ou Primeiro do Ano",
            dados_planta,
            chaves_pb,
            nomes_legiveis_pb,
            anexos_planta,
        )
    else:
        adicionar_secao(
            "2. Planta Básica - Exercício Seguinte e/ou Recalculado e/ou Primeiro do Ano",
            "Planta Básica não encontrada.",
        )

    # 3. Croqui e Anexos Siatu
    # data = [["Chave", "Valor"]]
    # data.append(["Total de Anexos", f"{anexos_count} anexo(s) encontrado(s)."])

    if anexos_siatu:
        gerar_tabela_secao(
            "3. Anexos SIATU",
            # {"Total de Anexos": f"{anexos_count} anexo(s) encontrado(s)."},
            # ["Total de Anexos"],
            anexos=anexos_siatu,
        )
    else:
        adicionar_secao(
            "3. Anexos SIATU",
            "Nenhum anexo encontrado.",
        )

    # 4. SISCTM
    if dados_sisctm:
        nomes_legiveis = {
            "iptu_ctm_geo_area": "Área (IPTU CTM GEO)",
            "iptu_ctm_geo_area_terreno": "Área do Terreno (IPTU CTM GEO)",
            "lote_cp_ativo_area_informada": "Área Informada (Lote CP - Ativo)",
            "endereco_ctmgeo": "Endereço (CTM GEO)",
        }
        chaves = [
            "iptu_ctm_geo_area",
            "iptu_ctm_geo_area_terreno",
            "lote_cp_ativo_area_informada",
            "endereco_ctmgeo",
        ]
        gerar_tabela_secao(
            "4. Dados SISCTM", dados_sisctm, chaves, nomes_legiveis, anexos_sisctm
        )
    else:
        adicionar_secao(
            "4. Dados SISCTM",
            "Nenhum dado encontrado.",
        )

    # 5. Google Maps
    # data = [["Chave", "Valor"]]
    # data.append(["Total de Anexos", f"{anexos_count} anexo(s) encontrado(s)."])

    if anexos_google:
        gerar_tabela_secao(
            "5. Google Maps",
            # {"Total de Anexos": f"{anexos_count} anexo(s) encontrado(s)."},
            # ["Total de Anexos"],
            anexos=anexos_google,
        )
    else:
        adicionar_secao(
            "5. Google Maps",
            "Endereço não encontrado.",
        )

    # 6. Projeto, Alvará e Baixa de Construção
    if dados_projeto:
        chaves_projeto = [
            "tipo",
            "requerimento",
            "ultima_alteracao",
            "area_lotes",
            "area_construida",
        ]
        nomes_legiveis_projeto = {
            "tipo": "Tipo",
            "requerimento": "Requerimento",
            "ultima_alteracao": "Última Alteração",
            "area_lotes": "Área do(s) lote(s)",
            "area_construida": "Área Construída",
        }
        dados_projeto_temp = dados_projeto if dados_projeto else {}
        gerar_tabela_secao(
            "6. Projeto, Alvará e Baixa de Construção",
            dados_projeto_temp,
            chaves_projeto,
            nomes_legiveis_projeto,
            anexos_projetos,
        )
    else:
        adicionar_secao(
            "6. Projeto, Alvará e Baixa de Construção",
            "Nenhum dado encontrado.",
        )

    # 7. Matrícula do Imóvel
    if dados_planta:
        nomes_legiveis = {
            "matricula_registro": "Número da Matrícula",
            "cartorio": "Cartório",
        }
        chaves = ["matricula_registro", "cartorio"]
        gerar_tabela_secao(
            "7. Matrícula do Imóvel", dados_planta, chaves, nomes_legiveis
        )
    else:
        adicionar_secao("7. Matrícula do Imóvel", "Nenhum dado encontrado.")

        # MORADORES (BASE CEMIG)
        # adicionar_secao(
        #     "6. Moradores Ocupantes", "Pesquisa realizada na base da CEMIG."
        # )
        # moradores = ["Morador 1 exemplo", "Morador 2 exemplo"]
        # lista_moradores = ListFlowable(
        #     [ListItem(Paragraph(m, estilo_texto)) for m in moradores],
        #     bulletType="bullet",
        #     leftIndent=20,
        # )
        # elementos.append(lista_moradores)
        # elementos.append(Spacer(1, 12))

    # OBSERVAÇÕES
    # adicionar_secao("7. Observações Gerais", "Observações de exemplo.")

    # 8. CONCLUSÃO
    if dados_planta and dados_sisctm:
        endereco_siatu = dados_planta.get("endereco_imovel", "")
        endereco_ctm = dados_sisctm.get("endereco_ctmgeo", "")

        rua_s, numero_s, cep_s = extrair_elementos_para_comparacao(endereco_siatu)
        rua_c, numero_c, cep_c = extrair_elementos_para_comparacao(endereco_ctm)

        if (rua_s, numero_s, cep_s) == (rua_c, numero_c, cep_c):
            texto_conclusao = "Endereço SIATU e CTM GEO são iguais."
        else:
            texto_conclusao = "Endereço SIATU e CTM GEO são diferentes."

        # Adiciona na seção de conclusão
        adicionar_secao("8. Conclusão Parcial", texto_conclusao)
    else:
        adicionar_secao(
            "8. Conclusão Parcial",
            "Não há dados para analise.",
        )

    # Gera o PDF
    doc.build(elementos)
