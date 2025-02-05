from datetime import datetime
from seleniumbase import Driver
from selenium.webdriver.common.by import By
from seleniumbase.common.exceptions import NoSuchElementException
import argparse
import pandas as pd
import os

def iniciar_driver():
    return Driver(uc=True, headless=False)

url = "https://servicos.pf.gov.br/epol-sinic-publico/"
pasta_download = os.path.join(os.getcwd(), "downloaded_files")

# Configura o argumento via CLI
parser = argparse.ArgumentParser(description="Processar um arquivo Excel.")
parser.add_argument("file_id", type=str, help="ID do diretório onde está o arquivo")

# Pega o argumento passado
args = parser.parse_args()
file_id = args.file_id  # Esse é o ID recebido

# Monta o caminho correto
file_path = os.path.join("uploads", file_id, "dados.xlsx")

# Verifica se o arquivo existe antes de tentar abrir
if not os.path.exists(file_path):
    raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

df = pd.read_excel(file_path, engine="openpyxl", dtype={'CPF': str})
cpfs_pulados = []

for index, row in df.iterrows():
    driver = iniciar_driver()
    driver.uc_open_with_reconnect(url, reconnect_time=6)
    driver.uc_gui_click_captcha()
    
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
        cpf_input = driver.find_element('pf-input-cpf input[type="text"]')
        cpf_input.send_keys(cpf)
        nome_input = driver.find_element('[formcontrolname="nome"]')
        nome_input.send_keys(nome)

        erro_cpf = driver.wait_for_element('span.p-confirm-dialog-message.ng-tns-c58-1', timeout=1)
        if "Formato do CPF inválido." in erro_cpf.text:
            cpfs_pulados.append([cpf, nome, data_nasc, nome_mae])
            driver.quit()
            continue
    except NoSuchElementException:
        pass
    
    local = driver.wait_for_element('.p-multiselect.p-component')
    local.click()
    driver.wait_for_element('.p-multiselect-filter.p-inputtext')
    driver.send_keys('.p-multiselect-filter.p-inputtext', "Brasil")
    driver.click('.p-checkbox-box')

    data_input = driver.find_element('.ng-tns-c64-8.pf-inputtext')
    data_input.send_keys(data_nasc if isinstance(data_nasc, str) else data_nasc.strftime("%d/%m/%Y"))

    nome_mae_input = driver.find_element('input[formcontrolname="nomeMae"]')
    nome_mae_input.send_keys(nome_mae)
    driver.click('#btn-emitir-cac')
    driver.click('#btn-fechar-modal')
    
    try:
        error_cac = driver.wait_for_element(By.XPATH, "//span[contains(text(), 'Dados (nome, nome da mãe ou data de nascimento) não conferem com o CPF informado.')]", timeout=1)
        cpfs_pulados.append([cpf, nome, data_nasc, nome_mae])
    except NoSuchElementException:
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
    df_pulados = pd.DataFrame(cpfs_pulados, columns=["CPF", "Nome", "Data Nascimento", "Nome Mãe"])
    df_pulados.to_excel("cpfs_pulados.xlsx", index=False)
    print("CPFs pulados foram salvos em 'cpfs_pulados.xlsx'.")
else:
    print("Nenhum CPF foi pulado.")
