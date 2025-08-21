import logging
import time
from selenium import webdriver
from selenium.webdriver.common.by import By


def urbano_auto(credenciais, indice, pasta_indice):
    try:
        logging.info(f"Acessando Sistema 2 para índice {indice}")
        driver = webdriver.Chrome()
        driver.get("https://sistema2.exemplo.com")

        # Login
        driver.find_element(By.ID, "usuario").send_keys(credenciais["usuario"])
        driver.find_element(By.ID, "senha").send_keys(credenciais["senha"])
        driver.find_element(By.ID, "login").click()
        time.sleep(2)

        # Busca pelo índice
        driver.find_element(By.ID, "indice").send_keys(indice)
        driver.find_element(By.ID, "buscar").click()
        time.sleep(2)

        # Screenshot
        screenshot_path = f"{pasta_indice}/sistema2_{indice}.png"
        driver.save_screenshot(screenshot_path)
        logging.info(f"Screenshot salvo em {screenshot_path}")

        # Simular download PDF
        pdf_path = f"{pasta_indice}/sistema2_{indice}.pdf"
        with open(pdf_path, "w") as f:
            f.write("Simulação de PDF Sistema 2")
        logging.info(f"PDF salvo em {pdf_path}")

        driver.quit()

    except Exception as e:
        logging.error(f"Erro no Sistema 2 com índice {indice}: {e}")
        raise
