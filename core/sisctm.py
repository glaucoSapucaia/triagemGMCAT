import logging
import time
import os
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)


class SisctmAuto:
    def __init__(
        self,
        driver,
        url: str,
        usuario: str,
        senha: str,
        pasta_download,
        timeout: int = 10,
    ):
        self.driver = driver
        self.url = url
        self.usuario = usuario
        self.senha = senha
        self.pasta_download = pasta_download
        self.wait = WebDriverWait(self.driver, timeout=timeout)

    def _click(self, element):
        """Tenta clicar diretamente, se falhar usa JavaScript."""
        try:
            element.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", element)

    def login(self) -> bool:
        """Realiza login no Keycloak PBH em páginas Vue.js."""
        try:
            logger.info("Iniciando login no Keycloak PBH")
            self.driver.get(self.url)
            logger.info("URL de login acessada: %s", self.url)

            time.sleep(3)  # Espera inicial para o Vue renderizar

            # 1. Espera o formulário completo aparecer
            self.wait.until(
                lambda driver: driver.find_element(By.ID, "kc-form-servidor-login")
            )

            # 2. Preenche usuário via JS
            campo_usuario = self.driver.find_element(By.ID, "username")
            self.driver.execute_script(
                "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input'));",
                campo_usuario,
                self.usuario,
            )
            logger.info("Campo de usuário preenchido via JS")

            # 3. Preenche senha via JS
            campo_senha = self.driver.find_element(By.ID, "password")
            self.driver.execute_script(
                "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input'));",
                campo_senha,
                self.senha,
            )
            logger.info("Campo de senha preenchido via JS")

            # 4. Clica no botão via JS
            btn_login = self.driver.find_element(By.ID, "kc-login")
            self.driver.execute_script("arguments[0].click();", btn_login)
            logger.info("Login realizado com sucesso no Keycloak PBH")

            time.sleep(10)  # Espera para garantir que o login foi processado

            return True

        except Exception as e:
            logger.error("Erro no login do Keycloak PBH: %s", e)
            return False

    def navegar(self, indice_cadastral) -> bool:
        """Navega pelo menu do sistema Sisctm PBH."""
        try:
            logger.info("Iniciando navegação pelo sistema")

            # 1. Clica no ícone para expandir o menu
            btn_menu = self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//i[@class='q-icon on-right notranslate material-icons' and text()='expand_more']",
                    )
                )
            )
            self._click(btn_menu)
            logger.info("Menu expandido")
            time.sleep(1)

            # 2. Clica no item "Fazenda" para marcá-lo
            item_fazenda = self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//div[contains(@class,'q-item__section') and contains(text(),'Fazenda')]",
                    )
                )
            )
            self._click(item_fazenda)
            logger.info("Item 'Fazenda' marcado")
            time.sleep(0.5)

            # 3. Clica no item "IDE-BHGeo" para desativá-lo
            item_idebhgeo = self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//div[contains(@class,'q-item__section') and contains(text(),'IDE-BHGeo')]",
                    )
                )
            )
            self._click(item_idebhgeo)
            logger.info("Item 'IDE-BHGeo' desativado")
            time.sleep(0.5)

            # 4. Clica no ícone "camadas"
            btn_camadas = self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//i[@class='q-icon notranslate material-icons' and text()='layers']",
                    )
                )
            )
            self._click(btn_camadas)
            logger.info("Camadas abertas")
            time.sleep(1)

            # 5. Seleciona a camada "Tributário"
            camada_tributario = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//div[text()='Tributário']"))
            )
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", camada_tributario
            )
            time.sleep(0.3)
            self._click(camada_tributario)
            logger.info("Camada 'Tributário' selecionada")
            time.sleep(0.5)

            # 6. Abre menu do item "CTM GEO" dentro da camada Tributário
            # Localiza o container da camada Tributário
            camada_tributario_container = self.wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//div[text()='Tributário']/ancestor::div[contains(@class,'q-tree__node')]",
                    )
                )
            )

            # Busca todos os ícones more_vert dentro dessa camada
            more_vert_icons = camada_tributario_container.find_elements(
                By.XPATH,
                ".//i[@class='q-icon notranslate material-icons' and text()='more_vert']",
            )

            # Clica no quarto ícone (índice 3)
            if len(more_vert_icons) >= 4:
                self._click(more_vert_icons[3])
                logger.info("Menu do item 'IPTU CTM GEO' aberto")
            else:
                logger.error(
                    "Não foi encontrado o quarto ícone more_vert dentro da camada Tributário"
                )
                return False

            # 7. Clica no elemento de filtro
            btn_filtro = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Filtro']"))
            )
            self._click(btn_filtro)
            logger.info("Filtro aberto")
            time.sleep(0.5)

            # 8. Clica no elemento de "fazer filtro"
            btn_fazer_filtro = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//span/i[contains(@class,'mdi-filter-plus')]")
                )
            )
            self._click(btn_fazer_filtro)
            logger.info("Opção de fazer filtro selecionada")
            time.sleep(0.5)

            # 9. Seleciona o item "_INDICE_CADASTRAL"
            item_indice = self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//div[@class='q-item__label' and text()='_INDICE_CADASTRAL']",
                    )
                )
            )
            self._click(item_indice)
            logger.info("Item '_INDICE_CADASTRAL' selecionado")
            time.sleep(0.5)

            # 10. Espera o input de busca aparecer no dropdown e insere o índice cadastral
            campo_busca = self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//input[@type='search' and contains(@aria-label,'Valor')]",
                    )
                )
            )
            campo_busca.clear()
            campo_busca.send_keys(indice_cadastral)
            logger.info(
                "Índice cadastral inserido no campo correto: %s", indice_cadastral
            )

            # 11. Clica no botão "Aplicar"
            btn_aplicar = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Aplicar']"))
            )
            self._click(btn_aplicar)
            logger.info("Filtro aplicado com sucesso")
            time.sleep(5)

            # Fecha a janela do filtro
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(0.5)
            logger.info("Janela do filtro fechada")

            # Print da pesquisa em caso de erros
            screenshot_path = os.path.join(self.pasta_download, "CTM_Aereo.png")
            self.driver.save_screenshot(screenshot_path)
            logger.info("Print da tela salvo em: %s", screenshot_path)

            # 1. Clica no elemento "BHMap"
            elemento_bhmap = self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//div[@class='q-img__content absolute-full']//div[@class='titulo ellipsis' and text()='BHMap']",
                    )
                )
            )
            self._click(elemento_bhmap)
            logger.info("Elemento 'BHMap' clicado")
            time.sleep(1)

            # 2. Seleciona a ortofoto 2025 (ou 2015 no seu exemplo)
            elemento_ortofoto = self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//div[@class='q-img__content absolute-full']//div[contains(@class,'ellipsis') and text()='Ortofoto 2015']",
                    )
                )
            )
            self._click(elemento_ortofoto)
            logger.info("Ortofoto selecionada")
            time.sleep(5)

            # 3. Novo print da tela
            screenshot_path_orto = os.path.join(self.pasta_download, "CTM_Orto.png")
            self.driver.save_screenshot(screenshot_path_orto)
            logger.info("Print da tela salvo em: %s", screenshot_path_orto)

            return True

        except Exception as e:
            logger.error("Erro ao navegar no sistema Sisctm PBH: %s", e)
            return False

    def informacoes_sisctm(self) -> dict:
        """Coleta informações do lote filtrado no Sisctm PBH."""
        try:
            logger.info("Iniciando coleta de informações do Sisctm")

            # Localiza o container da camada Tributário
            camada_tributario_container = self.wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//div[text()='Tributário']/ancestor::div[contains(@class,'q-tree__node')]",
                    )
                )
            )

            # Busca todos os ícones more_vert dentro dessa camada
            more_vert_icons = camada_tributario_container.find_elements(
                By.XPATH,
                ".//i[@class='q-icon notranslate material-icons' and text()='more_vert']",
            )

            # Verifica se existe o quarto ícone (IPTU CTM GEO)
            if len(more_vert_icons) >= 4:
                vert_icon = more_vert_icons[3]
            else:
                logger.error(
                    "Não foi encontrado o quarto ícone more_vert dentro da camada Tributário"
                )
                return {}

            # 1. Localiza o elemento 'IPTU CTM GEO' relativo ao ícone
            elemento_iptu = vert_icon.find_element(
                By.XPATH,
                "./ancestor::div[contains(@class,'q-tree__node')]//div[contains(@class,'header-publication') and contains(text(),'IPTU CTM GEO')]",
            )
            # Rola até ele e clica via JS
            self.driver.execute_script(
                "arguments[0].scrollIntoView(true);", elemento_iptu
            )
            time.sleep(0.3)
            self.driver.execute_script("arguments[0].click();", elemento_iptu)
            logger.info("Elemento 'IPTU CTM GEO' clicado")
            time.sleep(5)

            # 2. Marca o lote filtrado
            checkbox_lote = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//div[@class='q-checkbox__bg absolute']")
                )
            )
            self._click(checkbox_lote)
            logger.info("Lote filtrado marcado")
            time.sleep(0.5)

            # 3. Coleta todas as chaves e valores da tabela
            tabela_lote = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//tbody"))
            )

            linhas = tabela_lote.find_elements(By.XPATH, ".//tr")
            info_dict = {}

            for linha in linhas:
                try:
                    chave_elem = linha.find_element(By.XPATH, ".//td[1]")
                    valor_elem = linha.find_element(By.XPATH, ".//td[2]")
                    chave = chave_elem.text.strip()
                    valor = valor_elem.text.strip()
                    if chave:  # Ignora linhas sem chave
                        info_dict[chave] = valor
                except Exception as e:
                    logger.warning("Erro ao processar linha da tabela: %s", e)
                    continue

            # Print para verificar os dados coletados
            print(info_dict)

            logger.info("Informações coletadas com sucesso: %s", info_dict)
            return info_dict

        except Exception as e:
            logger.error("Erro ao coletar informações no Sisctm PBH: %s", e)
            return {}
