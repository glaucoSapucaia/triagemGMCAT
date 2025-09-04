import os
import re
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
    anexos_count,
    projetos_count,
    pasta_anexos=None,
    prps_trabalhador="Nome do trabalhador",
    nome_pdf="relatorio_profissional.pdf",
    dados_planta=None,
    dados_projeto=None,
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
    anexos_planta, anexos_siatu, anexos_projetos = [], [], []

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
                or "certidao_baixa" in arq.lower()
                or "alvara_construcao" in arq.lower()
                or "projeto" in arq.lower()
            ):
                anexos_projetos.append(arq)
            else:
                anexos_siatu.append(arq)

    # Seções
    # COL
    adicionar_secao(
        "1. Certidão de Origem de Lote",
        "Verifique se a COL está na lista de anexos Siatu. "
        "<br/>Caso não a encontre, busque manualmente a certidão de origem de lote (COL). "
        "<br/><b>Informação obtida no portal:</b> "
        '<a href="https://siurbe.pbh.gov.br/#/solicitacao/CertidaoOrigemLote">'
        '<font color="blue"><u>https://siurbe.pbh.gov.br/#/solicitacao/CertidaoOrigemLote</u></font></a>',
    )

    if dados_planta:
        texto_planta = f"""
        <b>Área Construída Total:</b> {dados_planta.get('area_construida', 'Não encontrado')}<br/>
        <b>Exercício:</b> {dados_planta.get('exercicio', 'Não encontrado')}<br/>
        <b>Tipo de uso:</b> {dados_planta.get('tipo_uso', 'Não encontrado')}
        """
    else:
        texto_planta = "Planta Básica não encontrada."

    # PB
    adicionar_secao(
        "2. Planta Básica - Exercício Seguinte e/ou Recalculado e/ou Primeiro do Ano",
        texto_planta,
    )
    adicionar_anexos(anexos_planta)

    # ANEXOS SIATU
    adicionar_secao(
        "3. Croqui e Anexos Siatu", f"{anexos_count} anexo(s) encontrado(s)."
    )
    adicionar_anexos(anexos_siatu)

    # PROJETO, ALVARÁ E BAIXA DE CONSTRUÇÃO
    texto_projeto = f"{projetos_count} anexo(s) encontrado(s)."
    if dados_projeto:
        texto_projeto += "<br/>"
        texto_projeto += (
            f"<b>Tipo:</b> {dados_projeto.get('tipo', 'Não informado')}<br/>"
        )
        texto_projeto += f"<b>Requerimento:</b> {dados_projeto.get('requerimento', 'Não informado')}<br/>"
        texto_projeto += f"<b>Última Alteração:</b> {dados_projeto.get('ultima_alteracao', 'Não informado')}<br/>"
        texto_projeto += f"<b>Área do(s) lote(s):</b> {dados_projeto.get('area_lotes', 'Não informado')}"
    adicionar_secao("4. Projeto, Alvará e Baixa de Construção", texto_projeto)
    adicionar_anexos(anexos_projetos)

    # MATRÍCULA E CARTÓRIO
    if dados_planta:
        texto_matricula = f"""
        <b>Número:</b> {dados_planta.get('matricula_registro', 'Não informado')}<br/>
        <b>Cartório:</b> {dados_planta.get('cartorio', 'Não informado')}
        """
    else:
        texto_matricula = "Não informado"
    adicionar_secao("5. Matrícula do Imóvel", texto_matricula)

    # MORADORES (BASE CEMIG)
    adicionar_secao("6. Moradores Ocupantes", "Pesquisa realizada na base da CEMIG.")
    moradores = ["Morador 1 exemplo", "Morador 2 exemplo"]
    lista_moradores = ListFlowable(
        [ListItem(Paragraph(m, estilo_texto)) for m in moradores],
        bulletType="bullet",
        leftIndent=20,
    )
    elementos.append(lista_moradores)
    elementos.append(Spacer(1, 12))

    # OBSERVAÇÕES
    adicionar_secao("7. Observações Gerais", "Observações de exemplo.")

    # CONCLUSÃO
    adicionar_secao("8. Conclusão Parcial", "Conclusão de exemplo.")

    # Gera o PDF
    doc.build(elementos)
