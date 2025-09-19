import logging
import time
import os
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
)
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

    def ativar_camadas(self, indice_cadastral) -> bool:
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

            # CAMADA ENDEREÇO -----------------------------------------

            # Seleciona o item "Endereço" no menu principal
            menu_endereco = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//div[text()='Endereço']"))
            )
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", menu_endereco
            )
            time.sleep(0.3)
            self._click(menu_endereco)
            logger.info("Menu 'Endereço' selecionado")
            time.sleep(0.5)

            # Localiza o container da camada "Endereço"
            container_endereco = self.wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//div[text()='Endereço']/ancestor::div[contains(@class,'q-tree__node')]",
                    )
                )
            )

            # Localiza o checkbox do item "Endereço PBH" pelo src da imagem
            endereco_pbh_checkbox = container_endereco.find_element(
                By.XPATH,
                ".//div[contains(@class,'q-tree__node--child')]"
                "[.//img[contains(@src,'FazendaEnderecoPBH')]]"
                "//div[contains(@class,'q-checkbox')]",
            )

            # Rola até ele e clica
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", endereco_pbh_checkbox
            )
            time.sleep(0.3)
            self._click(endereco_pbh_checkbox)
            logger.info("Camada 'Endereço PBH' marcada")
            time.sleep(0.5)

            # CAMADA PARCELAMENTO DO SOLO -----------------------------------------

            # 1. Seleciona o item "Parcelamento do Solo" no menu principal
            menu_parcelamento = self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[text()='Parcelamento do Solo']")
                )
            )
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", menu_parcelamento
            )
            time.sleep(0.3)
            self._click(menu_parcelamento)
            logger.info("Menu 'Parcelamento do Solo' selecionado")
            time.sleep(0.5)

            # 2. Localiza o container da camada "Parcelamento do Solo"
            container_parcelamento = self.wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//div[text()='Parcelamento do Solo']/ancestor::div[contains(@class,'q-tree__node')]",
                    )
                )
            )

            # 3. Localiza o checkbox do item "Lote CP - ATIVO" pelo src da imagem
            lote_cp_checkbox = container_parcelamento.find_element(
                By.XPATH,
                ".//div[contains(@class,'q-tree__node--child')]"
                "[.//img[contains(@src,'FazendaLoteCP')]]"
                "//div[contains(@class,'q-checkbox')]",
            )

            # 4. Rola até ele e clica
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", lote_cp_checkbox
            )
            time.sleep(0.3)
            self._click(lote_cp_checkbox)
            logger.info("Camada 'Lote CP - ATIVO' marcada")
            time.sleep(0.5)

            # CAMADA TRIBUTÁRIO E FILTRO -----------------------------------------

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
            time.sleep(5)
            logger.info("Janela do filtro fechada")

            # Clique no lote canvas (mapa)
            self._clique_centro_mapa()

            # PRINTS
            self._prints_aereo()

            return True

        except Exception as e:
            logger.error("Erro ao navegar no sistema Sisctm PBH: %s", e)
            return False

    def _prints_aereo(self) -> None:
        # Print AEREO CTM
        time.sleep(15)
        screenshot_path = os.path.join(self.pasta_download, "CTM_Aereo.png")
        self.driver.save_screenshot(screenshot_path)
        logger.info("Print da tela salvo em: %s", screenshot_path)

        # Clica no elemento "BHMap"
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
        time.sleep(2)

        # Seleciona a ortofoto 2025 (ou 2015 no seu exemplo)
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
        time.sleep(10)

        # Print AEREO ORTO
        screenshot_path_orto = os.path.join(self.pasta_download, "CTM_Orto.png")
        self.driver.save_screenshot(screenshot_path_orto)
        logger.info("Print da tela salvo em: %s", screenshot_path_orto)

        return

    def _clique_centro_mapa(self):
        try:
            logging.info("Iniciando tentativa de clique no centro do mapa")

            # tenta localizar o viewport do mapa
            viewport = self.driver.find_element(By.CSS_SELECTOR, "#olmap .ol-viewport")
            logging.info(
                f"Viewport encontrado: tamanho {viewport.size['width']}x{viewport.size['height']}"
            )

            # cria a ação de mover e clicar
            action = ActionChains(self.driver)
            action.move_to_element(viewport).click().perform()
            logging.info("Clique no centro do mapa realizado com ActionChains")

            # espera o mapa processar o clique (carregamento de layers ou overlays)
            time.sleep(5)
            logging.info("Espera pós-clique concluída")

        except NoSuchElementException as e:
            logging.error(f"Elemento do mapa não encontrado: {e}")
        except WebDriverException as e:
            logging.error(f"Erro ao executar clique no mapa: {e}")
        except Exception as e:
            logging.error(f"Erro inesperado ao clicar no mapa: {e}")

    def capturar_areas(self):
        resultado = {}
        try:
            logging.info("Iniciando captura de áreas do painel lateral")

            painel = self.driver.find_element(
                By.CSS_SELECTOR,
                "#q-app > div > div.q-drawer-container > aside > div > div.fit.row.no-scroll > div.col.bg-white > div > div.col.relative-position > div",
            )

            # Função auxiliar para ativar item
            def ativar_item(nome_item):
                try:
                    item = painel.find_element(
                        By.XPATH,
                        f".//div[contains(@class,'q-item') and .//div[contains(text(),'{nome_item}')]]",
                    )
                    botao = item.find_element(By.XPATH, ".//div[@role='button']")
                    aria = botao.get_attribute("aria-expanded")
                    if aria != "true":
                        logging.info(f"{nome_item} não está ativo. Ativando...")
                        botao.click()
                        WebDriverWait(botao, 5).until(
                            lambda x: x.get_attribute("aria-expanded") == "true"
                        )
                        logging.info(f"{nome_item} ativado")
                        time.sleep(3)
                    else:
                        logging.info(f"{nome_item} já está ativo")
                    return item
                except Exception as e:
                    logging.info(f"Erro ao ativar item {nome_item}: {e}")

            # --- IPTU CTM GEO ---
            iptu_item = ativar_item("IPTU CTM GEO")
            time.sleep(2)
            # Aguarda a linha com "ÁREA" existir
            try:
                linha_area = WebDriverWait(iptu_item, 5).until(
                    EC.presence_of_element_located(
                        (By.XPATH, ".//table//tr[td[contains(text(),'ÁREA')]]/td[2]")
                    )
                )
                resultado["iptu_ctm_geo_area"] = linha_area.text.strip()
                logging.info(
                    f"Valor capturado IPTU CTM GEO: {resultado['iptu_ctm_geo_area']}"
                )
            except TimeoutException:
                logging.warning("Não foi possível capturar área IPTU CTM GEO")
                resultado["iptu_ctm_geo_area"] = None

            # Aguarda a linha com "AREA_TERRENO" existir
            try:
                linha_area_terreno = WebDriverWait(iptu_item, 5).until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            ".//table//tr[td[contains(text(),'AREA_TERRENO')]]/td[2]",
                        )
                    )
                )
                resultado["iptu_ctm_geo_area_terreno"] = linha_area_terreno.text.strip()
                logging.info(
                    f"Valor capturado IPTU CTM GEO AREA TERRENO: {resultado['iptu_ctm_geo_area_terreno']}"
                )
            except TimeoutException:
                logging.warning("Não foi possível capturar AREA TERRENO")
                resultado["iptu_ctm_geo_area_terreno"] = None

            # Captura campos do endereço
            try:
                campos = {
                    "tipo_logradouro": ".//table//tr[24]/td[2]",
                    "nome_logradouro": ".//table//tr[25]/td[2]",
                    "numero_imovel": ".//table//tr[26]/td[2]",
                    "complemento": ".//table//tr[27]/td[2]",
                    "cep": ".//table//tr[28]/td[2]",
                }

                valores = {}
                for chave, xpath in campos.items():
                    try:
                        elemento = WebDriverWait(iptu_item, 5).until(
                            EC.presence_of_element_located((By.XPATH, xpath))
                        )
                        valores[chave] = elemento.text.strip()
                    except TimeoutException:
                        valores[chave] = ""

                # Remove pontos do número do imóvel
                valores["numero_imovel"] = valores["numero_imovel"].replace(".", "")

                # Monta o endereço no formato desejado (padrão Google, sem formatar CEP)
                endereco = f"{valores['tipo_logradouro']} {valores['nome_logradouro']}, {valores['numero_imovel']}"
                if valores["complemento"]:  # só adiciona se não estiver vazio
                    endereco += f" {valores['complemento']}"
                endereco += f" - Belo Horizonte - MG, {valores['cep']}"

                resultado["endereco_ctmgeo"] = endereco
                logging.info(
                    f"Endereço CTM GEO capturado: {resultado['endereco_ctmgeo']}"
                )

            except Exception as e:
                logging.warning(f"Não foi possível capturar endereço CTM GEO: {e}")
                resultado["endereco_ctmgeo"] = None

            # Lote CP - ATIVO
            lote_cp_item = ativar_item("Lote CP - ATIVO")

            try:
                # Captura todas as linhas da tabela
                tabela = lote_cp_item.find_element(By.TAG_NAME, "table")
                linhas = tabela.find_elements(By.TAG_NAME, "tr")

                # Pega a sexta linha (índice 5, porque lista em Python é 0-based)
                linha_area = linhas[5]
                colunas = linha_area.find_elements(By.TAG_NAME, "td")
                valor = colunas[1].text.strip()  # segunda coluna
                resultado["lote_cp_ativo_area_informada"] = valor
                logging.info(f"Valor capturado Lote CP - ATIVO: {valor}")
            except Exception as e:
                logging.warning(f"Não foi possível capturar área Lote CP - ATIVO: {e}")
                resultado["lote_cp_ativo_area_informada"] = None

            # Imprime chave e valor (DEBUG)
            # for chave, valor in resultado.items():
            #     print(f"{chave}: {valor}")

            return resultado

        except NoSuchElementException as e:
            logging.error(f"Elemento não encontrado: {e}")
            return {}
        except ElementClickInterceptedException as e:
            logging.error(f"Não foi possível clicar no item: {e}")
            return {}
        except Exception as e:
            logging.error(f"Erro inesperado ao capturar áreas: {e}")
            return {}

    # MÉTODO COMENTADO PARA FUTURAMENTE USAR
    # ACESSA AS INFORMAÇÕES DO LOTE FILTRADO CLICANDO EM CTM GEO E CAPTURA TODA A TABELA

    # def informacoes_sisctm(self) -> dict:
    #     """Coleta informações do lote filtrado no Sisctm PBH."""
    #     try:
    #         logger.info("Iniciando coleta de informações do Sisctm")

    #         # Localiza o container da camada Tributário
    #         camada_tributario_container = self.wait.until(
    #             EC.presence_of_element_located(
    #                 (
    #                     By.XPATH,
    #                     "//div[text()='Tributário']/ancestor::div[contains(@class,'q-tree__node')]",
    #                 )
    #             )
    #         )

    #         # Busca todos os ícones more_vert dentro dessa camada
    #         more_vert_icons = camada_tributario_container.find_elements(
    #             By.XPATH,
    #             ".//i[@class='q-icon notranslate material-icons' and text()='more_vert']",
    #         )

    #         # Verifica se existe o quarto ícone (IPTU CTM GEO)
    #         if len(more_vert_icons) >= 4:
    #             vert_icon = more_vert_icons[3]
    #         else:
    #             logger.error(
    #                 "Não foi encontrado o quarto ícone more_vert dentro da camada Tributário"
    #             )
    #             return {}

    #         # 1. Localiza o elemento 'IPTU CTM GEO' relativo ao ícone
    #         elemento_iptu = vert_icon.find_element(
    #             By.XPATH,
    #             "./ancestor::div[contains(@class,'q-tree__node')]//div[contains(@class,'header-publication') and contains(text(),'IPTU CTM GEO')]",
    #         )
    #         # Rola até ele e clica via JS
    #         self.driver.execute_script(
    #             "arguments[0].scrollIntoView(true);", elemento_iptu
    #         )
    #         time.sleep(0.3)
    #         self.driver.execute_script("arguments[0].click();", elemento_iptu)
    #         logger.info("Elemento 'IPTU CTM GEO' clicado")
    #         time.sleep(5)

    #         # 2. Marca o lote filtrado
    #         checkbox_lote = self.wait.until(
    #             EC.element_to_be_clickable(
    #                 (By.XPATH, "//div[@class='q-checkbox__bg absolute']")
    #             )
    #         )
    #         self._click(checkbox_lote)
    #         logger.info("Lote filtrado marcado")
    #         time.sleep(0.5)

    #         # 3. Coleta todas as chaves e valores da tabela
    #         tabela_lote = self.wait.until(
    #             EC.presence_of_element_located((By.XPATH, "//tbody"))
    #         )

    #         linhas = tabela_lote.find_elements(By.XPATH, ".//tr")
    #         info_dict = {}

    #         for linha in linhas:
    #             try:
    #                 chave_elem = linha.find_element(By.XPATH, ".//td[1]")
    #                 valor_elem = linha.find_element(By.XPATH, ".//td[2]")
    #                 chave = chave_elem.text.strip()
    #                 valor = valor_elem.text.strip()
    #                 if chave:  # Ignora linhas sem chave
    #                     info_dict[chave] = valor
    #             except Exception as e:
    #                 logger.warning("Erro ao processar linha da tabela: %s", e)
    #                 continue

    #         # Print para verificar os dados coletados
    #         print(info_dict)

    #         logger.info("Informações coletadas com sucesso: %s", info_dict)
    #         return info_dict

    #     except Exception as e:
    #         logger.error("Erro ao coletar informações no Sisctm PBH: %s", e)
    #         return {}
