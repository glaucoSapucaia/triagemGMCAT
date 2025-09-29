import os
import re
from utils import logger

from utils import (
    normalizar_nome,
    extrair_elementos_do_endereco_para_comparacao,
    parse_area,
    formatar_area,
)

from reportlab.platypus import Table, TableStyle
from reportlab.lib.pagesizes import A4
from urllib.parse import quote
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from datetime import datetime


def gerar_relatorio(
    indice_cadastral,
    anexos_count=None,
    projetos_count=None,
    pasta_anexos=None,
    prps_trabalhador="Pr não informado",
    nome_pdf="Relatorio de triagem.pdf",
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

        # Defini quais chaves devem ser tratadas como área
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
    def adicionar_secao(titulo_secao=None, texto_secao=None):
        if titulo_secao:
            elementos.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
            elementos.append(Spacer(1, 8))
            elementos.append(Paragraph(titulo_secao, estilo_secao))
        if texto_secao:
            elementos.append(Paragraph(texto_secao, estilo_texto))
        if titulo_secao and texto_secao:
            elementos.append(Spacer(1, 12))

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
            if "Planta_Basica" in arq or "alteracoes_siatu" in arq.lower():
                anexos_planta.append(arq)
            elif (
                "sem_projeto" in arq.lower()
                or "sem_alvara-baixa" in arq.lower()
                or "certidao_baixa" in arq.lower()
                or "alvara_construcao" in arq.lower()
                or "projeto" in arq.lower()
                or "prancha" in arq.lower()
            ):
                anexos_projetos.append(arq)
            elif "CTM" in arq:
                anexos_sisctm.append(arq)
            elif "google" in arq:
                anexos_google.append(arq)
            else:
                anexos_siatu.append(arq)

    logger.info("Criando relatório PDF")

    # Seções
    # 1. SIGEDE
    logger.info("Adicionando seção 1: SIGEDE")
    adicionar_secao(
        "1. SIGEDE - Busca por Protocolo e ICs vinculados",
        "A presente seção será igual para todos os ICs vínculados ao mesmo protocolo.",
    )

    # Busca arquivos .pdf e .png um nível acima (pasta protocolo)
    arquivos_sigede = []
    if pasta_anexos and os.path.exists(pasta_anexos):
        pasta_pai = os.path.dirname(pasta_anexos)
        count = 0
        for arq in sorted(os.listdir(pasta_pai)):
            if arq.lower().endswith((".pdf", ".png")):
                count += 1
                # Caminho relativo (../arquivo.pdf)
                href = "../" + quote(
                    arq,
                    safe="._-ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789",
                )
                link = Paragraph(
                    f'<a href="{href}" color="blue">{arq}</a>', style_normal
                )
                arquivos_sigede.append([f"Anexo {count}", link])

    if arquivos_sigede:
        tabela_col = Table(
            [["Anexo(s)", "Link"]] + arquivos_sigede, colWidths=[200, 300]
        )
        tabela_col.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ]
            )
        )
        elementos.append(tabela_col)
        elementos.append(Spacer(1, 12))
    else:
        elementos.append(
            Paragraph("Nenhum registro encontrado no SIGEDE.", style_normal)
        )
        elementos.append(Spacer(1, 12))

    # 2. Planta Básica - Exercício Seguinte e/ou Recalculado e/ou Primeiro do Ano
    logger.info("Adicionando seção 2: Planta Básica")
    if dados_planta and dados_planta["area_construida"] != "Não informado":
        chaves_pb = ["area_construida", "exercicio", "patrimonio", "endereco_imovel"]
        nomes_legiveis_pb = {
            "area_construida": "Área Construída Total",
            "exercicio": "Exercício",
            "patrimonio": "Patrimônio",
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
    logger.info("Adicionando seção 3: Anexos SIATU")
    if anexos_siatu:
        gerar_tabela_secao(
            "3. Anexos SIATU",
            anexos=anexos_siatu,
        )
    else:
        adicionar_secao(
            "3. Anexos SIATU",
            "Nenhum anexo encontrado.",
        )

    # 4. SISCTM
    logger.info("Adicionando seção 4: Dados SISCTM")
    if dados_sisctm:
        nomes_legiveis = {
            "iptu_ctm_geo_area_terreno": "Área de Terreno (SIATU)",
            "iptu_ctm_geo_area": "Área Georeferenciada",
            "lote_cp_ativo_area_informada": "Área COL",
            "endereco_ctmgeo": "Endereço (CTM GEO)",
        }
        chaves = [
            "iptu_ctm_geo_area_terreno",
            "iptu_ctm_geo_area",
            "lote_cp_ativo_area_informada",
            "endereco_ctmgeo",
        ]
        gerar_tabela_secao(
            "4. Dados SISCTM", dados_sisctm, chaves, nomes_legiveis, anexos_sisctm
        )
    else:
        gerar_tabela_secao(
            "4. Dados SISCTM - IC NÃO ENCONTRADO ou LOTE NÃO CENTRALIZADO",
            anexos=anexos_sisctm,
        )

    # 5. Google Maps
    logger.info("Adicionando seção 5: Google Maps")
    if anexos_google:
        gerar_tabela_secao(
            "5. Google Maps",
            anexos=anexos_google,
        )
    else:
        adicionar_secao(
            "5. Google Maps",
            "Endereço não encontrado.",
        )

    # 6. Projeto, Alvará e Baixa de Construção
    logger.info("Adicionando seção 6: Projeto, Alvará e Baixa de Construção")
    if dados_projeto:
        chaves_projeto = [
            "tipo",
            "area_lotes",
            "area_construida",
        ]
        nomes_legiveis_projeto = {
            "tipo": "Tipo",
            "area_lotes": "Área do(s) lote(s)",
            "area_construida": "Área Construída",
        }
        dados_projeto_temp = dados_projeto if dados_projeto else {}

        if dados_projeto_temp["tipo"] == "Não informado":
            gerar_tabela_secao(
                "6. Projeto, Alvará e Baixa de Construção",
                anexos=anexos_projetos,
            )

        else:
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
    logger.info("Adicionando seção 7: Matrícula do Imóvel")

    if isinstance(dados_planta, dict) and (
        dados_planta.get("matricula_registro") != "Não informado"
        or dados_planta.get("cartorio") != "Não informado"
    ):
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

    # 8. Conclusão Parcial - Endereço + Áreas
    logger.info("Adicionando seção 8: Conclusão Parcial")
    adicionar_secao("8. Conclusão Parcial - Endereços e Áreas")

    # Compara endereços - SIATU vs IPTU CTMGEO
    endereco_siatu = dados_planta.get("endereco_imovel", "") if dados_planta else ""
    endereco_ctm = dados_sisctm.get("endereco_ctmgeo", "") if dados_sisctm else ""

    if endereco_siatu and endereco_ctm:
        rua_s, numero_s, cep_s = extrair_elementos_do_endereco_para_comparacao(
            endereco_siatu
        )
        rua_c, numero_c, cep_c = extrair_elementos_do_endereco_para_comparacao(
            endereco_ctm
        )

        if None in (rua_s, numero_s, cep_s, rua_c, numero_c, cep_c):
            resultado_endereco = "Não foi possível comparar (dados faltando)"
        else:
            resultado_endereco = (
                "Iguais"
                if (rua_s, numero_s, cep_s) == (rua_c, numero_c, cep_c)
                else "Diferentes"
            )

        data_endereco = [
            ["Endereço", ""],
            [
                "Endereço SIATU",
                Paragraph(endereco_siatu or "Não informado", style_normal),
            ],
            [
                "Endereço IPTU CTMGEO",
                Paragraph(endereco_ctm or "Não informado", style_normal),
            ],
            ["Resultado", Paragraph(resultado_endereco, style_normal)],
        ]

        tabela_endereco = Table(data_endereco, colWidths=[200, 300])
        tabela_endereco.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ("TEXTCOLOR", (0, -1), (-1, -1), colors.darkblue),
                ]
            )
        )
        elementos.append(tabela_endereco)
        elementos.append(Spacer(1, 12))

    # Extrai valores numéricos das áreas
    a_pb = parse_area(dados_planta.get("area_construida") if dados_planta else None)
    a_urb = parse_area(dados_projeto.get("area_construida") if dados_projeto else None)

    if a_pb is not None or a_urb is not None:
        # Formata valores
        area_pb = formatar_area(a_pb)
        area_urbano = formatar_area(a_urb)

        # Monta tabela apenas com os valores de área
        data_area = [
            ["Área Construída", ""],
            ["Área PB", Paragraph(area_pb, style_normal)],
            ["Área URBANO", Paragraph(area_urbano, style_normal)],
        ]

        tabela_area = Table(data_area, colWidths=[200, 300])
        tabela_area.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ]
            )
        )
        elementos.append(tabela_area)
        elementos.append(Spacer(1, 12))

    # Não cria tabelas se não há dados
    if (not a_pb and not a_urb) and (not endereco_siatu or not endereco_ctm):
        adicionar_secao(texto_secao="Não há dados para análise.")

    # Gera o PDF
    doc.build(elementos)
