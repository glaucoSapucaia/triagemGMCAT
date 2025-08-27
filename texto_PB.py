from PyPDF2 import PdfReader

caminho_pdf = r"D:\gitRepos\triagemSeleniumGMCAT\resultados\012033 027 028X\Planta_Basica_Resumida9941.pdf"

# Abrir o PDF
reader = PdfReader(caminho_pdf)
texto_completo = ""

# Extrair texto de todas as páginas
for page in reader.pages:
    texto_completo += page.extract_text() + "\n"

# Salvar em arquivo de texto
with open("planta_basica_texto.txt", "w", encoding="utf-8") as f:
    f.write(texto_completo)

print("Extração concluída. Verifique 'planta_basica_texto.txt'.")
