import time
import os

from utils import logger

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class UrbanoAuto:
    """
    Classe para automatizar tarefas relacionadas ao sistema Urbano via Selenium.

    Parâmetros:
        driver (selenium.webdriver): Instância do WebDriver para controle do navegador.
        url (str): URL de login ou página inicial do sistema Urbano.
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
        """Tenta clicar diretamente, se falhar usa JavaScript."""
        try:
            element.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", element)

    def acessar(self):
        """Abre o sistema Urbano."""
        try:
            logger.info("Acessando o sistema 2: URBANO")
            self.driver.get(self.url)
            return True
        except Exception as e:
            logger.error("Erro ao acessar o sistema Urbano: %s", e)
            return False

    def login(self):
        """Realiza login no Urbano PBH."""
        try:
            logger.info("Iniciando login no Urbano")

            # Clica no botão de acesso
            btn_acesso = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//div[@class='panel-body' and text()='Acesso PBH']")
                )
            )
            self._click(btn_acesso)
            logger.info("Botão 'Acesso PBH' clicado")

            # Preenche usuário
            campo_usuario = self.wait.until(
                EC.presence_of_element_located((By.ID, "usuario"))
            )
            campo_usuario.clear()
            campo_usuario.send_keys(self.usuario)

            # Preenche senha
            campo_senha = self.wait.until(
                EC.presence_of_element_located((By.ID, "senha"))
            )
            campo_senha.clear()
            campo_senha.send_keys(self.senha)

            # Confirma login
            btn_login = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//input[@type='submit' and @name='Login']")
                )
            )
            self._click(btn_login)
            logger.info("Login realizado com sucesso no Urbano")

            return True
        except Exception as e:
            logger.error("Erro no login do Urbano: %s", e)
            return False

    def download_projeto(self, indice: str):
        """
        Pesquisa o projeto no Urbano e retorna a quantidade de projetos encontrados.
        Também salva prints e tenta baixar certidão de baixa, alvará ou projeto se existirem.
        """
        try:
            logger.info("Iniciando pesquisa de projeto para índice: %s", indice)
            indice = indice.strip()
            if len(indice) < 11:
                raise ValueError(f"Índice inválido: {indice}")

            # Divisão do índice
            parte1, parte2, parte3 = indice[0:3], indice[3:7], indice[7:11]

            time.sleep(5)

            # Preenche campos
            campo1 = self.wait.until(
                EC.presence_of_element_located((By.NAME, "zonaFiscal"))
            )
            campo1.clear()
            campo1.send_keys(parte1)

            campo2 = self.wait.until(lambda d: d.find_element(By.NAME, "quart"))
            WebDriverWait(self.driver, 5).until(lambda d: campo2.is_enabled())
            campo2.clear()
            campo2.send_keys(parte2)

            campo3 = self.wait.until(lambda d: d.find_element(By.NAME, "lote"))
            WebDriverWait(self.driver, 5).until(lambda d: campo3.is_enabled())
            campo3.clear()
            campo3.send_keys(parte3)

            # Realiza pesquisa
            btn_pesquisar = self.wait.until(
                EC.element_to_be_clickable((By.ID, "btnPesquisar"))
            )
            self._click(btn_pesquisar)
            time.sleep(15)

            # Scroll para o print (caso necessário)
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
            time.sleep(2)

            # Verifica a tabela e conta projetos
            try:
                tabela_div = self.driver.find_element(
                    By.CSS_SELECTOR,
                    "div.table-responsive table tbody.project-search-results",
                )
                linhas = tabela_div.find_elements(By.TAG_NAME, "tr")
                qtd_projetos = len(linhas)
                logger.info("%d projetos encontrados", qtd_projetos)

                if qtd_projetos == 0:
                    dados_projeto = self._capturar_dados_projeto(
                        nome_arquivo="Não informado"
                    )

                    # Print da pesquisa sem resultados
                    screenshot_path = os.path.join(
                        self.pasta_download, "Pesquisa de Projeto.png"
                    )
                    self.driver.save_screenshot(screenshot_path)
                    logger.info("Print da tela salvo")

                    return 0, dados_projeto

                # Clica no primeiro projeto para tentar baixar documentos
                primeiro_projeto = linhas[0].find_element(By.TAG_NAME, "a")
                self._click(primeiro_projeto)
                logger.info("Clicado no primeiro projeto da lista")
                time.sleep(
                    20
                )  # Aguarda carregar a página do projeto (geralmente demora)

            except NoSuchElementException:
                logger.info("Projetos não encontrados na pesquisa")
                dados_projeto = self._capturar_dados_projeto(
                    nome_arquivo="Não informado"
                )

                # Print da pesquisa em caso de erros
                screenshot_path = os.path.join(self.pasta_download, "Sem_Projeto.png")
                self.driver.save_screenshot(screenshot_path)
                logger.info("Print da tela salvo")

                return 0, dados_projeto

            # Tenta baixar certidão de baixa
            certidao = self.driver.find_elements(
                By.XPATH,
                "//a[contains(@href,'certidao-de-baixa') and text()='visualizar']",
            )
            if certidao:
                certidao[0].click()
                logger.info("Certidão de baixa baixada (clique realizado)")
                time.sleep(10)
                dados_projeto = self._capturar_dados_projeto(
                    nome_arquivo="Certidão de Baixa"
                )
                return qtd_projetos, dados_projeto

            # Tenta baixar alvará
            alvara = self.driver.find_elements(
                By.XPATH,
                "//a[contains(text(),'visualizar') and @ng-click='statusCtrl.abrirAlvara()']",
            )
            if alvara:
                alvara[0].click()
                logger.info("Alvará baixado (clique realizado)")
                time.sleep(10)
                dados_projeto = self._capturar_dados_projeto(
                    nome_arquivo="Alvará de Contrução"
                )
                return qtd_projetos, dados_projeto

            # Se nenhum documento encontrado, salvar print e acessa "Documentos Anexos"
            if not certidao and not alvara:
                time.sleep(10)  # Espera extra para garantir carregamento
                screenshot_sem_doc = os.path.join(
                    self.pasta_download, "Sem Alvara-Baixa.png"
                )
                self.driver.save_screenshot(screenshot_sem_doc)
                logger.info(
                    "Nenhum documento encontrado, print salvo em: %s",
                    screenshot_sem_doc,
                )

                # Clica em "Documentos Anexos"
                try:
                    documentos_anexos = self.wait.until(
                        EC.element_to_be_clickable(
                            (By.XPATH, "//li[@ui-sref='home.perm.projeto.anexos']")
                        )
                    )
                    documentos_anexos.click()
                    logger.info("Clicado em 'Documentos Anexos'")
                except TimeoutException:
                    logger.warning(
                        "Não foi possível encontrar o botão 'Documentos Anexos'"
                    )
                    return qtd_projetos, self._capturar_dados_projeto(
                        nome_arquivo="Não informado"
                    )

                # Aguarda aparecer o painel "Pranchas do Projeto"
                try:
                    time.sleep(15)
                    self.wait.until(
                        EC.presence_of_element_located(
                            (By.XPATH, "//h3[contains(text(),'Pranchas do Projeto')]")
                        )
                    )
                    logger.info("Painel 'Pranchas do Projeto' carregado")
                except TimeoutException:
                    logger.warning("Painel 'Pranchas do Projeto' não carregou a tempo")
                    return qtd_projetos, self._capturar_dados_projeto(
                        nome_arquivo="Não informado"
                    )

                # Clica no primeiro arquivo da tabela
                try:
                    primeiro_arquivo = self.wait.until(
                        EC.presence_of_element_located(
                            (By.XPATH, "//table//tbody//tr[1]//td[1]//a")
                        )
                    )
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView(true);", primeiro_arquivo
                    )
                    self.wait.until(
                        EC.element_to_be_clickable(
                            (By.XPATH, "//table//tbody//tr[1]//td[1]//a")
                        )
                    )

                    nome_arquivo = primeiro_arquivo.text.strip()
                    try:
                        primeiro_arquivo.click()
                    except Exception:
                        # fallback se o Selenium não conseguir clicar
                        self.driver.execute_script(
                            "arguments[0].click();", primeiro_arquivo
                        )

                    logger.info("Download iniciado para: %s", nome_arquivo)
                    time.sleep(10)

                    dados_projeto = self._capturar_dados_projeto(nome_arquivo="Projeto")
                    return qtd_projetos, dados_projeto
                except TimeoutException:
                    logger.warning("Nenhum arquivo encontrado na tabela de anexos")
                    return qtd_projetos, self._capturar_dados_projeto(
                        nome_arquivo="Não informado"
                    )

        except Exception as e:
            logger.error("Erro ao pesquisar projeto no Urbano (%s): %s", indice, e)
            dados_projeto = self._capturar_dados_projeto(nome_arquivo=nome_arquivo)
            return 0, dados_projeto

    def _capturar_dados_projeto(self, nome_arquivo=None):
        """
        Captura os dados do projeto:
        - Tipo: nome do arquivo baixado
        - Requerimento
        - Última alteração
        - Área do(s) lote(s)
        Caso algum campo não seja encontrado, retorna 'Não informado'.
        """
        dados = {}
        time.sleep(2)

        # Tipo: nome do arquivo
        dados["tipo"] = nome_arquivo if nome_arquivo else "Não informado"

        try:
            # Requerimento
            requerimento_elem = self.driver.find_element(
                By.XPATH,
                "//span[@ng-if='$ctrl.ps.modoVisualizacao() || !$ctrl.isNomeEditavel']",
            )
            dados["requerimento"] = requerimento_elem.text.strip()
        except Exception:
            dados["requerimento"] = "Não informado"

        try:
            # Localiza o span que contém o texto "Última alteração"
            # e pega o segundo <small> dentro dele (após o <br>)
            ultima_alteracao_elem = self.driver.find_element(
                By.XPATH, "//span[small[text()='Última alteração']]/small[2]"
            )
            dados["ultima_alteracao"] = ultima_alteracao_elem.text.strip()
        except Exception:
            dados["ultima_alteracao"] = "Não informado"

        try:
            # Área do(s) lote(s)
            area_lote_elem = self.driver.find_element(
                By.XPATH,
                "//p[@class='form-control-static ng-binding']//span[@class='ng-binding']",
            )
            dados["area_lotes"] = area_lote_elem.text.strip()
        except Exception:
            dados["area_lotes"] = "Não informado"

        try:
            # Área construída
            area_construida_elem = self.driver.find_element(
                By.ID, "pb_area_total_visualizacao"
            )
            # Pega apenas o texto do span (ex.: "72,93 m²")
            area_construida_span = area_construida_elem.find_element(
                By.TAG_NAME, "span"
            )
            dados["area_construida"] = area_construida_span.text.strip()
        except Exception:
            dados["area_construida"] = "Não informado"

        return dados
