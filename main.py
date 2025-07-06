import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

def tentar_login(driver, username, senha):
    driver.get("https://www.saucedemo.com/")
    wait = WebDriverWait(driver, 10)
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
            print(f"Tentativa {tentativas+1}: tentando senha incorreta '{senha_teste}'")
            tentar_login(driver, username, senha_teste)
            time.sleep(2)
            try:
                erro = driver.find_element(By.CSS_SELECTOR, "[data-test='error']")
                print(f"Erro esperado na tentativa {tentativas+1}: {erro.text}")
            except NoSuchElementException:
                print("Não encontrou erro, possível login inesperado. Parando tentativas.")
                break
        else:
            print(f"Tentativa {tentativas+1}: tentando senha correta")
            tentar_login(driver, username, senha_correta)
            try:
                WebDriverWait(driver, 5).until(EC.url_contains("/inventory.html"))
                print("Login com senha correta efetuado com sucesso!")
                return True
            except TimeoutException:
                print("Falha ao logar com senha correta.")
                return False
        tentativas += 1
    return False

def pegar_todos_ids_produtos(driver):
    wait = WebDriverWait(driver, 10)
    wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "inventory_list")))

    produtos_inventario = driver.find_elements(By.CLASS_NAME, "inventory_item")
    id_para_nome = {}

    for item in produtos_inventario:
        botao_add = item.find_element(By.CSS_SELECTOR, "button.btn_inventory")
        prod_id = botao_add.get_attribute("id").replace("add-to-cart-", "").lower()
        nome = item.find_element(By.CLASS_NAME, "inventory_item_name").text
        id_para_nome[prod_id] = nome

    return list(id_para_nome.keys()), id_para_nome

def adicionar_produtos(driver, lista_produtos):
    for prod_id in lista_produtos:
        try:
            botao = driver.find_element(By.ID, f"add-to-cart-{prod_id}")
            botao.click()
            print(f"Adicionado: {prod_id}")
            time.sleep(0.2)
        except Exception as e:
            print(f"Erro ao adicionar {prod_id}: {e}")

def remover_produtos(driver, lista_produtos):
    for prod_id in lista_produtos:
        try:
            botao = driver.find_element(By.ID, f"remove-{prod_id}")
            botao.click()
            print(f"Removido: {prod_id}")
            time.sleep(0.2)
        except NoSuchElementException:
            print(f"Botão remover para {prod_id} não encontrado (possivelmente já removido).")
        except ElementClickInterceptedException:
            print(f"Não foi possível clicar no botão remover para {prod_id}.")
        except Exception as e:
            print(f"Erro ao remover {prod_id}: {e}")

def abrir_carrinho(driver):
    carrinho = driver.find_element(By.CLASS_NAME, "shopping_cart_link")
    carrinho.click()

def obter_produtos_no_carrinho(driver):
    wait = WebDriverWait(driver, 10)
    try:
        wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "cart_item")))
    except TimeoutException:
        # carrinho vazio possivelmente
        return []

    itens = driver.find_elements(By.CLASS_NAME, "cart_item")
    nomes = [item.find_element(By.CLASS_NAME, "inventory_item_name").text for item in itens]
    return nomes

def finalizar_compra(driver):
    wait = WebDriverWait(driver, 10)

    try:
        wait.until(EC.element_to_be_clickable((By.ID, "checkout"))).click()
    except TimeoutException:
        print("Botão Checkout não encontrado (carrinho possivelmente vazio). Abortando compra.")
        return False

    wait.until(EC.visibility_of_element_located((By.ID, "first-name"))).send_keys("Fulano")
    driver.find_element(By.ID, "last-name").send_keys("da Silva")
    driver.find_element(By.ID, "postal-code").send_keys("12345")

    driver.find_element(By.ID, "continue").click()

    wait.until(EC.element_to_be_clickable((By.ID, "finish"))).click()

    try:
        mensagem = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "complete-header"))).text
        if "THANK YOU FOR YOUR ORDER" in mensagem.upper():
            print("Compra finalizada com sucesso!")
            return True
        else:
            print("Mensagem inesperada na finalização:", mensagem)
            return False
    except TimeoutException:
        print("Mensagem de confirmação da compra não encontrada.")
        return False

def main():
    driver = webdriver.Chrome()
    username = "standard_user"
    senha_correta = "secret_sauce"

    try:
        sucesso = login_com_senhas(driver, username, senha_correta)
        if not sucesso:
            print("Não foi possível logar com a senha correta.")
            return

        ids_produtos, id_para_nome = pegar_todos_ids_produtos(driver)

        qtd_add = random.randint(1, len(ids_produtos))
        produtos_para_adicionar = random.sample(ids_produtos, qtd_add)
        adicionar_produtos(driver, produtos_para_adicionar)

        # Atualizar lista produtos que devem estar no carrinho antes da remoção
        # Removemos uma quantidade aleatória dos adicionados
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
            print("\nQuantidade no carrinho NÃO confere com o esperado.")

        if sorted(produtos_no_carrinho) == sorted(nomes_esperados):
            print("Produtos no carrinho conferem com os esperados!")
        else:
            print("Produtos no carrinho NÃO correspondem ao esperado.")
            print("Esperado:", nomes_esperados)
            print("Encontrado:", produtos_no_carrinho)

        # Finaliza a compra só se carrinho não estiver vazio
        if produtos_no_carrinho:
            sucesso_compra = finalizar_compra(driver)
            if not sucesso_compra:
                print("Falha ao finalizar a compra.")
        else:
            print("Carrinho vazio, não finalizando compra.")

    except Exception as e:
        print("Erro durante execução:", e)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
