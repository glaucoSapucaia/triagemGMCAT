import os
import time
import re

from utils import logger

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class SiatuAuto:
    """
    Classe para automatizar tarefas relacionadas ao SIATU via Selenium.

    Parâmetros:
        driver (selenium.webdriver): Instância do WebDriver para controle do navegador.
        url (str): URL de login ou página inicial do SIATU.
        usuario (str): Nome de usuário para autenticação no sistema.
        senha (str): Senha do usuário para autenticação.
        pasta_download (str): Caminho da pasta onde os arquivos baixados serão armazenados.
    """

    def __init__(self, driver, url, usuario, senha, pasta_download):
        self.driver = driver
        self.url = url
        self.usuario = usuario
        self.senha = senha
        self.pasta_download = pasta_download
        self.wait = WebDriverWait(self.driver, timeout=5)

    def _click(self, element):
        """
        Tenta clicar em um elemento, usando JavaScript como fallback."""
        try:
            element.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", element)

    def acessar(self):
        """
        Aceessa a página inicial do sistema Siatu.
        """
        try:
            logger.info("Acessando o Sistema 1: SIATU")
            self.driver.get(self.url)
            return True
        except Exception as e:
            logger.error("Erro ao acessar o sistema: %s", e)
            return False

    def login(self):
        """
        Realiza o login no sistema Siatu."""
        try:
            logger.info("Preenchendo usuário e senha")
            self.wait.until(
                EC.presence_of_element_located((By.ID, "usuario"))
            ).send_keys(self.usuario)
            self.wait.until(EC.presence_of_element_located((By.ID, "senha"))).send_keys(
                self.senha
            )
            self.wait.until(EC.element_to_be_clickable((By.NAME, "Login"))).click()
            logger.info("Login realizado com sucesso")
            return True
        except Exception as e:
            logger.error("Erro no login: %s", e)
            return False

    def navegar(self):
        """
        Inicia a navegação até a página de consulta de índice cadastral.
        """
        try:
            # Espera iframe no menu
            iframe = self.wait.until(
                EC.presence_of_element_located((By.NAME, "iframe"))
            )
            self.driver.switch_to.frame(iframe)

            # Espera botão '+' e clica no pai <a>
            btn_plus = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//img[@id='nodeIcon2']/parent::a")
                )
            )
            self._click(btn_plus)

            # Clica no link de consulta
            link_consulta = self.wait.until(
                EC.element_to_be_clickable((By.ID, "itemTextLink3"))
            )
            self._click(link_consulta)

            self.driver.switch_to.default_content()
            return True
        except Exception as e:
            logger.error("Erro durante a navegação: %s", e)
            try:
                self.driver.switch_to.default_content()
            except:
                pass
            return False

    def planta_basica(self, indice_cadastral: str):
        """
        Consulta índice e obtem a planta básica resumida (PDF).
        """

        try:
            logger.info("Iniciando download da PB: %s", indice_cadastral)

            # Preenche índice cadastral
            campo_indice = self.wait.until(
                EC.presence_of_element_located((By.ID, "indiceCadastral"))
            )
            campo_indice.clear()
            campo_indice.send_keys(indice_cadastral)
            logger.info("Índice cadastral preenchido")

            # Clica em exercício e aguarda a página recarregar
            campo_exercicio = self.wait.until(
                EC.presence_of_element_located((By.ID, "exercicio"))
            )
            self._click(campo_exercicio)
            logger.info("Exercício clicado")
            time.sleep(2)

            # Clica no botão "planta básica"
            btn_planta = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//input[@type='submit' and @value='planta básica']")
                )
            )
            self._click(btn_planta)
            logger.info("Botão 'planta básica' clicado")
            time.sleep(2)

            # Links que podem existir
            links_xpaths = {
                "Exercício Seguinte": "//a[contains(text(),'Exercício Seguinte')]",
                "Recalculado": "//a[contains(@href, 'tipoRegistro=Recalculado')]",
                "Primeiro do Ano": "//a[contains(text(),'Primeiro do Ano')]",
            }

            dados_PB = self._capturar_dados_imovel()

            for nome, xpath in links_xpaths.items():
                try:
                    # Tenta localizar o link
                    link = self.wait.until(
                        EC.presence_of_element_located((By.XPATH, xpath))
                    )
                    self._click(link)
                    logger.info(f"Link '{nome}' clicado")
                    time.sleep(2)

                    # Após clicar no link, dispara o download
                    link_planta_resumida = self.wait.until(
                        EC.element_to_be_clickable(
                            (
                                By.XPATH,
                                "//a[contains(text(),'Gera Planta Básica Resumida')]",
                            )
                        )
                    )

                    janela_principal = self.driver.current_window_handle
                    self._click(link_planta_resumida)
                    logger.info(f"Download da PB disparado após '{nome}'")
                    time.sleep(2)

                    # Fecha qualquer janela nova aberta
                    janelas_atuais = self.driver.window_handles
                    for janela in janelas_atuais:
                        if janela != janela_principal:
                            self.driver.switch_to.window(janela)
                            self.driver.close()

                    self.driver.switch_to.window(janela_principal)
                    time.sleep(2)

                except TimeoutException:
                    logger.info(f"Link '{nome}' não encontrado, seguindo...")

            self._print_alteracoes()

            return dados_PB

        except TimeoutException as e:
            logger.error("Timeout ao tentar gerar Planta Básica Resumida: %s", e)
            return False
        except NoSuchElementException as e:
            logger.error("Elemento não encontrado: %s", e)
            return False
        except Exception as e:
            logger.error("Erro inesperado em planta_basica: %s", e)
            return False

    def download_anexos(self, indice_cadastral: str):
        """
        Faz o download dos arquivos da seção anexos (apenas PDFs) do Siatu.
        """
        try:
            logger.info(
                "Iniciando download de anexos para índice: %s",
                indice_cadastral,
            )

            # Clicar no link "Anexos"
            link_anexos = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[text()='Anexos']"))
            )
            self._click(link_anexos)
            logger.info("Link 'Anexos' clicado")
            time.sleep(2)

            # Janela principal
            janela_principal = self.driver.current_window_handle

            # Busca todos os PDFs na primeira tabela
            anexos_pdf = self.driver.find_elements(
                By.XPATH,
                "//table[.//b[text()='Imagens anexadas']]/preceding::table[1]//tr/td[1]/a"
                "[contains(@onclick, 'exibeDocumento') and "
                "contains(translate(text(), 'PDF','pdf'), '.pdf')]",
            )

            if not anexos_pdf:
                logger.info("Nenhum PDF disponível para download")
                return 0

            logger.info("Número de PDFs encontrados inicialmente: %d", len(anexos_pdf))
            qtd_anexos = 0

            for i, _ in enumerate(anexos_pdf, start=1):
                # Refetch para evitar StaleElementReference
                anexos_pdf_refetch = self.driver.find_elements(
                    By.XPATH,
                    "//table[.//b[text()='Imagens anexadas']]/preceding::table[1]//tr/td[1]/a"
                    "[contains(@onclick, 'exibeDocumento') and "
                    "contains(translate(text(), 'PDF','pdf'), '.pdf')]",
                )

                if i - 1 >= len(anexos_pdf_refetch):
                    logger.warning("PDF %d não encontrado após refetch, pulando...", i)
                    continue

                anexo = anexos_pdf_refetch[i - 1]
                nome_arquivo_raw = anexo.text.strip()
                nome_arquivo = self._sanitize_filename(nome_arquivo_raw)
                arquivo_caminho = os.path.join(self.pasta_download, nome_arquivo)

                logger.info("Processando PDF %d/%d", i, len(anexos_pdf))
                self._click(anexo)
                logger.info("Clique realizado no PDF")

                # Espera o download concluir
                if self._esperar_download_concluir(arquivo_caminho, timeout=120):
                    logger.info("Download concluído")
                else:
                    logger.warning(
                        "Download NÃO concluído no tempo limite: %s", nome_arquivo_raw
                    )

                time.sleep(1)
                # Fecha janelas extras
                for janela in self.driver.window_handles:
                    if janela != janela_principal:
                        self.driver.switch_to.window(janela)
                        self.driver.close()

                # Retorna para a janela principal
                self.driver.switch_to.window(janela_principal)

                qtd_anexos += 1

            logger.info(
                "Download de anexos finalizado. Total de PDFs processados: %d",
                qtd_anexos,
            )
            return qtd_anexos

        except TimeoutException as e:
            logger.error("Timeout ao tentar baixar anexos: %s", e)
            return False
        except NoSuchElementException as e:
            logger.error("Elemento não encontrado: %s", e)
            return False
        except Exception as e:
            logger.error("Erro inesperado em download_anexos: %s", e)
            return False

    def _capturar_dados_imovel(self):
        """
        Captura os dados do imóvel: Área Construída, Exercício, Tipo de Uso,
        Matrícula de Registro e Cartório.
        Caso não existam, retorna 'Não informado' (texto).
        """

        logger.info("Capturando dados do imóvel na página.")
        dados = {}

        # EXERCÍCIO
        try:
            exercicio_elem = self.driver.find_element(
                By.XPATH,
                "(//table[contains(@class,'table_item')][.//td[text()='Exercício']]//tr)[2]/td[@class='valor_campo']",
            )
            dados["exercicio"] = exercicio_elem.text.strip()
        except Exception:
            dados["exercicio"] = "Não informado"

        # PATRIMÔNIO (substituindo o tipo de uso)
        try:
            patrimonio_elem = self.driver.find_element(
                By.XPATH,
                "//td[@class='label_campo' and normalize-space(text())='Patrimônio']/following::td[@class='valor_campo'][1]",
            )
            dados["patrimonio"] = patrimonio_elem.text.strip()
        except Exception:
            dados["patrimonio"] = "Não informado"

        # ENDEREÇO DO IMÓVEL
        try:
            endereco_elem = self.driver.find_element(
                By.XPATH,
                "//table[contains(@class,'table_item')][.//td[text()='Endereço do Imóvel']]//tr[2]/td[@class='valor_campo']",
            )
            valor = endereco_elem.text.strip()
            dados["endereco_imovel"] = valor if valor else "Não informado"
        except Exception:
            dados["endereco_imovel"] = "Não informado"

        # CAPTURA TODOS OS VALORES DE ÁREA CONSTRUÍDA
        try:
            area_elems = self.driver.find_elements(
                By.XPATH, "//table[contains(@class,'table_grid2')]//tr/td[3]"
            )
            areas = []
            for elem in area_elems:
                txt = elem.text.strip()
                if txt:  # ignora células vazias
                    try:
                        areas.append(float(txt.replace(",", ".")))  # caso use vírgula
                    except ValueError:
                        pass

            if areas:
                soma_areas = sum(areas)
                dados["area_construida"] = "{:.2f}".format(soma_areas)
            else:
                dados["area_construida"] = "Não informado"
        except Exception:
            dados["area_construida"] = "Não informado"

        # MATRÍCULA DE REGISTRO
        try:
            matricula_elem = self.driver.find_element(
                By.XPATH,
                "//table[contains(@class,'table_item')][.//td[text()='Matrícula de Registro']]//tr[2]/td[@class='valor_campo']",
            )
            valor = matricula_elem.text
            if valor and valor.strip():
                dados["matricula_registro"] = valor.strip()
            else:
                dados["matricula_registro"] = "Não informado"
        except Exception:
            dados["matricula_registro"] = "Não informado"

        # CARTÓRIO
        try:
            cartorio_elem = self.driver.find_element(
                By.XPATH,
                "//table[contains(@class,'table_item')][.//td[text()='Cartório']]//tr[2]/td[@class='valor_campo']",
            )
            dados["cartorio"] = (
                cartorio_elem.text.strip()
                if cartorio_elem.text.strip() not in [None, "", "-"]  # trata o valor
                else "Não informado"
            )
        except Exception:
            dados["cartorio"] = "Não informado"

        return dados

    def _esperar_download_concluir(self, caminho_arquivo, timeout=120):
        """
        Espera até que o arquivo seja completamente baixado na pasta de destino.
        Funciona mesmo que o navegador use nomes temporários diferentes.
        """
        pasta = os.path.dirname(caminho_arquivo)
        nome_base = self._sanitize_filename(os.path.basename(caminho_arquivo))
        temporarios = (".crdownload", ".part", ".tmp")
        inicio = time.time()

        # Mapear arquivos existentes e seus tamanhos
        try:
            arquivos_anteriores = {
                f: os.path.getsize(os.path.join(pasta, f)) for f in os.listdir(pasta)
            }
        except FileNotFoundError:
            arquivos_anteriores = {}

        while True:
            try:
                arquivos_atuais = {
                    f: os.path.getsize(os.path.join(pasta, f))
                    for f in os.listdir(pasta)
                }
            except FileNotFoundError:
                arquivos_atuais = {}

            for f, tamanho in arquivos_atuais.items():
                if f.endswith(temporarios):
                    continue  # ignora arquivos temporários
                sanitized = self._sanitize_filename(f)
                # Detecta se é novo ou mudou de tamanho
                if (
                    sanitized == nome_base
                    or (f not in arquivos_anteriores)
                    or (arquivos_anteriores.get(f) != tamanho)
                ):
                    return True

            if time.time() - inicio > timeout:
                logger.warning("Timeout aguardando download: %s", caminho_arquivo)
                return False

            time.sleep(0.2)

    def _print_alteracoes(self):
        try:
            # Clica na aba do menu "Alterações"
            alteracoes_link = self.driver.find_element(
                By.XPATH,
                "//a[contains(@href, 'consultaPlantaBasica') and contains(text(), 'Alterações')]",
            )
            alteracoes_link.click()
            logger.info("Aba 'Alterações' acessada com sucesso.")

            time.sleep(2)

            # Aumenta o zoom antes do print
            self.driver.execute_script("document.body.style.zoom='200%'")
            time.sleep(1)

            # Print da tela
            screenshot_path = os.path.join(self.pasta_download, "alteracoes_siatu.png")
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"Print da aba Alterações salvo.")

            # Restaura o zoom original
            self.driver.execute_script("document.body.style.zoom='100%'")

        except Exception as e:
            logger.error(f"Erro ao acessar a aba Alterações: {e}")

    def _sanitize_filename(self, nome):
        """Remove caracteres inválidos em nomes de arquivos no Windows."""
        return re.sub(r'[<>:"/\\|?*]', "_", nome)
