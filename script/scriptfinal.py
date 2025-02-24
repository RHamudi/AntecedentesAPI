from datetime import date, datetime
import locale
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from seleniumbase.common.exceptions import NoSuchElementException, TimeoutException
import argparse
import pandas as pd
import os

chrome_options = Options()
locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

def iniciar_driver():
    user_data_dir = "/root/.config/google-chrome"

    chrome_options = Options()
    chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
    chrome_options.add_argument('--profile-directory=Profile 1')
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--no-sandbox')

    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

url = "https://servicos.pf.gov.br/epol-sinic-publico/"
pasta_download = os.path.join(r'/root/Downloads')
# pasta_download = os.path.join(r'C:\Users\RHamudi\Downloads')
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
    max_attempts = 3  # número máximo de tentativas
    attempt = 0

    while attempt < max_attempts:
        try:
            if driver.find_elements(By.CSS_SELECTOR, "h1.zone-name-title.h1"):
                # Aguarda até 60 segundos para que o captcha seja resolvido
                wait = WebDriverWait(driver, 60)
                wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "h1.zone-name-title.h1")))
                print("Captcha resolvido, prosseguindo com a automação.")
                break
            else:
                break
        except:
            attempt += 1
            print(f"Tentativa {attempt}: O captcha não foi resolvido em 60 segundos. Realizando reload...")
            driver.refresh()
            time.sleep(5)  # espera um pouco para o reload estabilizar

    if attempt == max_attempts:
        print("Tentativas máximas atingidas. Captcha não resolvido.")
    
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
        driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input'));", cpf_input, cpf)

        nome_input = driver.find_element(By.CSS_SELECTOR, '[formcontrolname="nome"]')
        driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input'));", nome_input, nome)

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

    local = WebDriverWait(driver, 4).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, '.p-multiselect.p-component'))
    )
    local.click()
    nacioinput = WebDriverWait(driver, 4).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, '.p-multiselect-filter.p-inputtext'))
    )
    nacioinput.send_keys("Brasil")
    checkbox = driver.find_element(By.CSS_SELECTOR, '.p-checkbox-box')
    checkbox.click()

    data_input = driver.find_element(By.CSS_SELECTOR, '.ng-tns-c64-8.pf-inputtext')

    data_nasc = (datetime.strptime(data_nasc, "%Y-%m-%d").date() if "-" in data_nasc else datetime.strptime(data_nasc, "%d/%m/%Y").date()) if isinstance(data_nasc, str) else data_nasc if isinstance(data_nasc, date) else None

    # Obter o dia, mês e ano
    dia_desejado = data_nasc.day
    mes_desejado = data_nasc.strftime('%B').capitalize() # Nome do mês completo, ex: Fevereiro
    ano_desejado = str(data_nasc.year)
    # Selecionar o campo de data
    data_input.click()

    # Função para buscar os botões novamente após a atualização do DOM
    def get_navigation_buttons():
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '.pf-datepicker-next'))
        )
        previous_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '.pf-datepicker-prev'))
        )
        return next_button, previous_button

    # Função para verificar o mês e o ano exibido no calendário
    def get_month_year():
        month_text = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '.pf-datepicker-month'))
        ).text
        year_text = driver.find_element(By.CSS_SELECTOR, '.pf-datepicker-year').text
        return month_text, year_text

    # Navegar até o mês e ano desejado
    month, year = get_month_year()

    while not (month == mes_desejado and year == ano_desejado):
        # Obter os botões novamente, já que o DOM pode ter mudado
        next_button, previous_button = get_navigation_buttons()

        # Clicar no botão de "Próximo" para avançar ou no botão "Anterior" caso necessário
        previous_button.click()  # ou previous_button.click(), dependendo do caso

        # Obter novamente o mês e ano após a atualização do calendário
        month, year = get_month_year()

    # Selecionar o dia desejado (por exemplo, o dia 23)
    day_to_select = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, f"//td[span[text()='{dia_desejado}']]"))
    )
    day_to_select.click()

    nome_mae_input = driver.find_element(By.CSS_SELECTOR, 'input[formcontrolname="nomeMae"]')
    driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input'));", nome_mae_input, nome_mae)

    try:
        botao = WebDriverWait(driver, 1).until(
            EC.element_to_be_clickable((By.ID, "btn-emitir-cac"))
        )
        botao.click()

        try:
            WebDriverWait(driver, 3).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[contains(@class, 'p-toast-message-content') and contains(., 'Falha ao emitir Cac.')]")
                )
            )

            cpfs_pulados.append([cpf, nome, data_nasc, nome_mae])
            driver.quit()
            continue
        except:
            time.sleep(2)
            fecharModal = driver.find_element(By.CSS_SELECTOR, '#btn-fechar-modal')
            fecharModal.click() 
    except:
        continue
          
    try:
        error_cac = WebDriverWait(driver, 3).until(
            EC.visibility_of_element_located((By.XPATH, "//span[contains(text(), 'Dados (nome, nome da mãe ou data de nascimento) não conferem com o CPF informado.')]"))
        )
        cpfs_pulados.append([cpf, nome, data_nasc, nome_mae])
        continue
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
    file_certscpf = os.path.join("uploads", file_id)
    print(file_certscpf)
    df_pulados = pd.DataFrame(cpfs_pulados, columns=["CPF", "Nome", "Data Nascimento", "Nome Mãe"])
    file_path = os.path.join(file_certscpf, "cpfs_pulados.xlsx")
    df_pulados.to_excel(file_path, index=False)
    print("CPFs pulados foram salvos em 'cpfs_pulados.xlsx'.")
else:
    print("Nenhum CPF foi pulado.")
