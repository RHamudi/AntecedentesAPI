from datetime import datetime
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from seleniumbase.common.exceptions import NoSuchElementException, TimeoutException
import argparse
import pandas as pd
import os

chrome_options = Options()

def iniciar_driver():
    user_data_dir = os.path.join(os.getenv('LOCALAPPDATA'), r'Google\Chrome\User Data')

    # chrome_options.add_argument(r'--user-data-dir=C:\Users\RHamudi\AppData\Local\Google\Chrome\User Data')
    chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
    chrome_options.add_argument('--profile-directory=Default')

    return webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)

url = "https://servicos.pf.gov.br/epol-sinic-publico/"
pasta_download = os.path.join(r'C:\Users\Administrator\Downloads')
# Configura o argumento via CLI
parser = argparse.ArgumentParser(description="Processar um arquivo Excel.")
parser.add_argument("file_id", type=str, help="ID do diretório onde está o arquivo")
parser.add_argument("file_name", type=str, help="Nome do arquivo a ser processado")

# Pega o argumento passado
args = parser.parse_args()
file_id = args.file_id  # Esse é o ID recebido
file_name = args.file_name

# Monta o caminho correto
file_path = os.path.join("uploads", file_id, file_name)

# Verifica se o arquivo existe antes de tentar abrir
if not os.path.exists(file_path):
    raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

df = pd.read_excel(file_path, engine="openpyxl", dtype={'CPF': str})
cpfs_pulados = []

for index, row in df.iterrows():
      # Define o display virtual
    driver = iniciar_driver()
    driver.get(url)
    elementos = driver.find_elements(By.CSS_SELECTOR, "h1.zone-name-title.h1")
    if(elementos):
        time.sleep(20)
    else:
        pass
    # driver.uc_gui_click_captcha()
    
    cpf = row["CPF"]
    nome = row["Nome"]
    data_nasc = row["Data Nascimento"]
    nome_mae = row["Nome Mãe"]

    if not all([
        not pd.isna(cpf) and str(cpf).strip(),
        not pd.isna(nome) and str(nome).strip(),
        not pd.isna(data_nasc) and str(data_nasc).strip(),
        not pd.isna(nome_mae) and str(nome_mae).strip()
    ]):
        cpfs_pulados.append([cpf, nome, data_nasc, nome_mae])
        driver.quit()
        continue

    try:
        cpf_input = driver.find_element(By.CSS_SELECTOR, "input.p-inputmask.p-inputtext.p-component")
        cpf_input.send_keys(cpf)
        nome_input = driver.find_element(By.CSS_SELECTOR, '[formcontrolname="nome"]')
        nome_input.send_keys(nome)

        try:
            erro_cpf = WebDriverWait(driver, 4).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'span.p-confirm-dialog-message.ng-tns-c58-1'))
            )
            if "Formato do CPF inválido." in erro_cpf.text:
                cpfs_pulados.append([cpf, nome, data_nasc, nome_mae])
                driver.quit()
                continue
        except:
            pass

    except NoSuchElementException:
        pass
    # continr aqui
    local = WebDriverWait(driver, 4).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, '.p-multiselect.p-component'))
    )
    local.click()
    nacioinput = WebDriverWait(driver, 4).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, '.p-multiselect-filter.p-inputtext'))
    )
    # driver.wait_for_element('.p-multiselect-filter.p-inputtext')
    nacioinput.send_keys("Brasil")
    checkbox = driver.find_element(By.CSS_SELECTOR, '.p-checkbox-box')
    checkbox.click()

    data_input = driver.find_element(By.CSS_SELECTOR, '.ng-tns-c64-8.pf-inputtext')
    data_input.send_keys(data_nasc if isinstance(data_nasc, str) else data_nasc.strftime("%d/%m/%Y"))

    nome_mae_input = driver.find_element(By.CSS_SELECTOR, 'input[formcontrolname="nomeMae"]')
    nome_mae_input.send_keys(nome_mae)
    emitirCAC = driver.find_element(By.CSS_SELECTOR, '#btn-emitir-cac')
    emitirCAC.click()
    time.sleep(3)
    fecharModal = driver.find_element(By.CSS_SELECTOR, '#btn-fechar-modal')
    fecharModal.click()
    
    try:
        error_cac = WebDriverWait(driver, 3).until(
            EC.visibility_of_element_located((By.XPATH, "//span[contains(text(), 'Dados (nome, nome da mãe ou data de nascimento) não conferem com o CPF informado.')]"))
        )
        cpfs_pulados.append([cpf, nome, data_nasc, nome_mae])
    except:
        arquivos = os.listdir(f'{pasta_download}')
        arquivos = [os.path.join(pasta_download, f) for f in arquivos]
        arquivo_baixado = max(arquivos, key=os.path.getctime)
        file_certs = os.path.join("uploads", file_id)
        pasta_certificados = os.path.join(file_certs, "certificados")
        os.makedirs(pasta_certificados, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.rename(arquivo_baixado, os.path.join(pasta_certificados, f"{nome}_{timestamp}{os.path.splitext(arquivo_baixado)[1]}"))
    
    driver.quit()

if cpfs_pulados:
    file_certs = os.path.join("uploads", file_id)
    df_pulados = pd.DataFrame(cpfs_pulados, columns=["CPF", "Nome", "Data Nascimento", "Nome Mãe"])
    file_path = os.path.join(file_certs, "cpfs_pulados.xlsx")
    df_pulados.to_excel(file_path, index=False)
    print("CPFs pulados foram salvos em 'cpfs_pulados.xlsx'.")
else:
    print("Nenhum CPF foi pulado.")
