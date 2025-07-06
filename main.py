import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

# Função para imprimir texto vermelho no terminal (erros)
def print_erro(texto):
    RED = "\033[31m"
    RESET = "\033[0m"
    print(f"{RED}{texto}{RESET}")

def tentar_login(driver, username, senha):
    driver.get("https://www.saucedemo.com/")
    wait = WebDriverWait(driver, 15)
    wait.until(EC.visibility_of_element_located((By.ID, "user-name")))

    driver.find_element(By.ID, "user-name").clear()
    driver.find_element(By.ID, "password").clear()

    driver.find_element(By.ID, "user-name").send_keys(username)
    driver.find_element(By.ID, "password").send_keys(senha)
    driver.find_element(By.ID, "login-button").click()

def login_com_senhas(driver, username, senha_correta):
    senhas_testadas = set()
    tentativas = 0
    max_tentativas = 5  # 4 erradas + 1 correta

    while tentativas < max_tentativas:
        if tentativas < 4:
            while True:
                senha_teste = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8))
                if senha_teste != senha_correta and senha_teste not in senhas_testadas:
                    break
            senhas_testadas.add(senha_teste)
            print(f"Tentativa {tentativas + 1}: tentando senha incorreta '{senha_teste}'")
            tentar_login(driver, username, senha_teste)
            time.sleep(2)
            try:
                erro = driver.find_element(By.CSS_SELECTOR, "[data-test='error']")
                print_erro(f"Erro esperado na tentativa {tentativas + 1}: {erro.text}")
            except NoSuchElementException:
                print_erro("Não encontrou erro, possível login inesperado. Parando tentativas.")
                return False
        else:
            print(f"Tentativa {tentativas + 1}: tentando senha correta")
            tentar_login(driver, username, senha_correta)
            try:
                WebDriverWait(driver, 5).until(EC.url_contains("/inventory.html"))
                print("Login com senha correta efetuado com sucesso!")
                return True
            except TimeoutException:
                print_erro("Falha ao logar com a senha correta.")
                return False
        tentativas += 1
    return False

def fechar_menu_hamburger(driver):
    """Fecha o menu hamburger se estiver aberto e remove possíveis elementos sobrepostos."""
    try:
        menu_aberto = driver.find_element(By.CLASS_NAME, "bm-menu-wrap")
        if menu_aberto.get_attribute("aria-hidden") == "false":
            close_button = driver.find_element(By.ID, "react-burger-cross-btn")
            close_button.click()
            WebDriverWait(driver, 5).until(EC.invisibility_of_element((By.CLASS_NAME, "bm-menu-wrap")))
            print("Menu hamburger fechado com sucesso.")
    except (NoSuchElementException, TimeoutException):
        print("Menu hamburger não estava aberto ou não encontrado.")

    # Remove o badge do carrinho para evitar sobreposições
    try:
        driver.execute_script("var badge = document.querySelector('.shopping_cart_badge'); if (badge) badge.style.display = 'none';")
        print("Badge do carrinho removido para evitar sobreposições.")
    except Exception:
        print("Badge do carrinho não encontrado ou não removível.")

def pegar_todos_ids_produtos(driver):
    wait = WebDriverWait(driver, 15)
    wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "inventory_item")))

    produtos_inventario = driver.find_elements(By.CLASS_NAME, "inventory_item")
    id_para_nome = {}

    for item in produtos_inventario:
        try:
            botao_add = item.find_element(By.CSS_SELECTOR, "button.btn_inventory")
            prod_id = botao_add.get_attribute("id").replace("add-to-cart-", "").lower()
            nome = item.find_element(By.CLASS_NAME, "inventory_item_name").text
            id_para_nome[prod_id] = nome
        except NoSuchElementException:
            print_erro("Erro ao obter ID ou nome de um produto no inventário.")
            continue

    return list(id_para_nome.keys()), id_para_nome

def scroll_to_element(driver, element):
    driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", element)
    time.sleep(2)  # Tempo fixo para estabilizar o DOM

def click_element(driver, element):
    element_id = element.get_attribute('id') or 'desconhecido'
    try:
        if not element.is_displayed():
            print_erro(f"Elemento {element_id} não está visível")
            return False
        if not element.is_enabled():
            print_erro(f"Elemento {element_id} não está habilitado")
            return False
        element.click()
        print(f"Clique bem-sucedido no elemento {element_id}")
        return True
    except ElementClickInterceptedException:
        print_erro(f"ElementClickInterceptedException em {element_id}, tentando clique via JavaScript")
        driver.execute_script("arguments[0].click();", element)
        print(f"Clique via JavaScript bem-sucedido em {element_id}")
        return True
    except Exception as e:
        print_erro(f"Erro ao clicar no elemento {element_id}: {str(e)}")
        return False

def verificar_badge_carrinho(driver, esperado=None):
    """Verifica o número de itens no badge do carrinho."""
    try:
        badge = driver.find_element(By.CLASS_NAME, "shopping_cart_badge")
        numero_itens = int(badge.text)
        print(f"Badge do carrinho atualizado: {numero_itens} itens")
        if esperado is not None and numero_itens != esperado:
            print_erro(f"Badge do carrinho esperado: {esperado}, encontrado: {numero_itens}")
        return numero_itens
    except NoSuchElementException:
        print("Badge do carrinho não encontrado (carrinho vazio).")
        return 0

def adicionar_produtos(driver, lista_produtos):
    wait = WebDriverWait(driver, 30)
    wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "inventory_item")))
    fechar_menu_hamburger(driver)

    itens_antes = verificar_badge_carrinho(driver)
    for prod_id in lista_produtos:
        try:
            print(f"Tentando adicionar {prod_id} com XPath //*[@id=\"add-to-cart-{prod_id}\"]")
            botao_add = wait.until(EC.element_to_be_clickable((By.XPATH, f"//*[@id='add-to-cart-{prod_id}']")))
            scroll_to_element(driver, botao_add)
            driver.execute_script("arguments[0].style.zIndex = '9999';", botao_add)
            driver.execute_script("arguments[0].style.display = 'block'; arguments[0].style.opacity = '1';", botao_add)
            if click_element(driver, botao_add):
                time.sleep(1.5)  # Pausa adicional após o clique
                try:
                    wait.until(EC.element_to_be_clickable((By.XPATH, f"//*[@id='remove-{prod_id}']")), 15)  # Timeout maior
                    itens_depois = verificar_badge_carrinho(driver, esperado=itens_antes + 1)
                    print(f"Adicionado: {prod_id} (confirmado pelo botão Remove)")
                    itens_antes = itens_depois
                except TimeoutException:
                    print_erro(f"Botão 'Remove' para {prod_id} não apareceu, verificando badge do carrinho")
                    itens_depois = verificar_badge_carrinho(driver)
                    if itens_depois > itens_antes:
                        print(f"Adicionado: {prod_id} (confirmado pelo badge do carrinho)")
                        itens_antes = itens_depois
                    else:
                        print_erro(f"Falha ao confirmar adição de {prod_id} (badge não atualizado)")
            else:
                print_erro(f"Falha ao clicar no botão de {prod_id}")
        except (TimeoutException, NoSuchElementException, ElementClickInterceptedException) as e:
            print_erro(f"Erro ao adicionar {prod_id}: {str(e)}")

def remover_produtos(driver, lista_produtos):
    wait = WebDriverWait(driver, 20)
    itens_antes = verificar_badge_carrinho(driver)
    for prod_id in lista_produtos:
        try:
            print(f"Tentando remover {prod_id} com XPath //*[@id=\"remove-{prod_id}\"]")
            botao_remove = wait.until(EC.element_to_be_clickable((By.XPATH, f"//*[@id='remove-{prod_id}']")))
            scroll_to_element(driver, botao_remove)
            driver.execute_script("arguments[0].style.zIndex = '9999';", botao_remove)
            if click_element(driver, botao_remove):
                wait.until(EC.element_to_be_clickable((By.XPATH, f"//*[@id='add-to-cart-{prod_id}']")))
                itens_depois = verificar_badge_carrinho(driver, esperado=itens_antes - 1)
                if itens_depois < itens_antes:
                    print(f"Removido: {prod_id}")
                    itens_antes = itens_depois
                else:
                    print_erro(f"Falha ao confirmar remoção de {prod_id} (badge não atualizado)")
            else:
                print_erro(f"Falha ao clicar no botão de remoção para {prod_id}")
        except (TimeoutException, NoSuchElementException) as e:
            print_erro(f"Erro ao remover {prod_id}: {str(e)}")

def abrir_carrinho(driver):
    wait = WebDriverWait(driver, 10)
    carrinho = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "shopping_cart_link")))
    driver.execute_script("arguments[0].style.zIndex = '9999';", carrinho)
    if click_element(driver, carrinho):
        print("Carrinho aberto com sucesso.")
    else:
        print_erro("Falha ao abrir o carrinho.")

def obter_produtos_no_carrinho(driver):
    wait = WebDriverWait(driver, 10)
    try:
        wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "cart_item")))
        itens = driver.find_elements(By.CLASS_NAME, "cart_item")
        nomes = [item.find_element(By.CLASS_NAME, "inventory_item_name").text for item in itens]
        return nomes
    except TimeoutException:
        print("Carrinho vazio ou itens não encontrados.")
        return []

def finalizar_compra(driver):
    wait = WebDriverWait(driver, 10)

    try:
        checkout = wait.until(EC.element_to_be_clickable((By.ID, "checkout")))
        driver.execute_script("arguments[0].style.zIndex = '9999';", checkout)
        if click_element(driver, checkout):
            print("Botão Checkout clicado com sucesso.")
        else:
            print_erro("Falha ao clicar no botão Checkout.")
            return False
    except TimeoutException:
        print_erro("Botão Checkout não encontrado (carrinho possivelmente vazio). Abortando compra.")
        return False

    try:
        wait.until(EC.visibility_of_element_located((By.ID, "first-name")))
        driver.find_element(By.ID, "first-name").send_keys("Fulano")
        driver.find_element(By.ID, "last-name").send_keys("da Silva")
        driver.find_element(By.ID, "postal-code").send_keys("12345")
        continue_button = driver.find_element(By.ID, "continue")
        driver.execute_script("arguments[0].style.zIndex = '9999';", continue_button)
        if click_element(driver, continue_button):
            print("Botão Continue clicado com sucesso.")
        else:
            print_erro("Falha ao clicar no botão Continue.")
            return False
    except TimeoutException:
        print_erro("Erro ao preencher informações de checkout.")
        return False

    try:
        finish = wait.until(EC.element_to_be_clickable((By.ID, "finish")))
        driver.execute_script("arguments[0].style.zIndex = '9999';", finish)
        if click_element(driver, finish):
            print("Botão Finish clicado com sucesso.")
        else:
            print_erro("Falha ao clicar no botão Finish.")
            return False
    except TimeoutException:
        print_erro("Botão Finish não encontrado.")
        return False

    try:
        mensagem = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "complete-header"))).text
        if "THANK YOU FOR YOUR ORDER" in mensagem.upper():
            print("Compra finalizada com sucesso!")
            return True
        else:
            print_erro(f"Mensagem inesperada na finalização: {mensagem}")
            return False
    except TimeoutException:
        print_erro("Mensagem de confirmação da compra não encontrada.")
        return False

def main():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    username = "standard_user"
    senha_correta = "secret_sauce"

    try:
        sucesso = login_com_senhas(driver, username, senha_correta)
        if not sucesso:
            print_erro("Não foi possível logar com a senha correta.")
            return

        ids_produtos, id_para_nome = pegar_todos_ids_produtos(driver)

        qtd_add = random.randint(1, len(ids_produtos))
        produtos_para_adicionar = random.sample(ids_produtos, qtd_add)
        adicionar_produtos(driver, produtos_para_adicionar)

        qtd_remove = random.randint(0, len(produtos_para_adicionar))
        produtos_para_remover = random.sample(produtos_para_adicionar, qtd_remove)
        remover_produtos(driver, produtos_para_remover)

        abrir_carrinho(driver)
        produtos_no_carrinho = obter_produtos_no_carrinho(driver)
        print("\nProdutos no carrinho atualmente:")
        for p in produtos_no_carrinho:
            print("-", p)

        produtos_restantes = set(produtos_para_adicionar) - set(produtos_para_remover)
        nomes_esperados = [id_para_nome[prod_id] for prod_id in produtos_restantes]

        if len(produtos_no_carrinho) == len(nomes_esperados):
            print("\nQuantidade no carrinho confere!")
        else:
            print_erro("\nQuantidade no carrinho NÃO confere com o esperado.")

        if sorted(produtos_no_carrinho) == sorted(nomes_esperados):
            print("Produtos no carrinho conferem com os esperados!")
        else:
            print_erro("Produtos no carrinho NÃO correspondem ao esperado.")
            print_erro(f"Esperado: {nomes_esperados}")
            print_erro(f"Encontrado: {produtos_no_carrinho}")

        if produtos_no_carrinho:
            sucesso_compra = finalizar_compra(driver)
            if not sucesso_compra:
                print_erro("Falha ao finalizar a compra.")
        else:
            print("Carrinho vazio, não finalizando compra.")

    except Exception as e:
        print_erro(f"Erro durante execução: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
