from selenium import webdriver
import time
from selenium.webdriver.common.keys import Keys
import mysql.connector
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

try:
    conexao = mysql.connector.connect(   #conectando com o banco de dados
        host="localhost",
        user="root",
        port=3306,
        password="",
        database="automacao_pesquisa"
    )

    if conexao.is_connected():  #verificando conexão
        print("conexão estabelecida com sucesso...")

    time.sleep(1)
    
except Exception as erro:
    print(str(erro))
    print("Encerrando o programa...")
    time.sleep(2)
    exit()


driver = webdriver.Chrome("chromedriver.exe")  #abrindo o chromedriver 
driver.get("https://www.google.com") #abrindo o google
wait = WebDriverWait(driver, 20)

campo_pesquisa = driver.find_element_by_xpath("//textarea[@name='q']") #selecionando o campo de pesquisa
campo_pesquisa.clear()
campo_pesquisa.send_keys("preço dolar hoje")
campo_pesquisa.send_keys(Keys.ENTER)
time.sleep(1)
dolar = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "span[class^='DFlfde SwHCTb']"))).text  #pegando o preço do dólar

time.sleep(0.20)
driver.quit()
dolar = float((dolar).replace(",",".")) #formatando o valor para não haver problemas com a vírgula no float()
print("Valor do dólar hoje: %s" % dolar)


produtos = set() #cria o grupo produtos para apresentar os resultados depois

time.sleep(1)

continuar = ""

continuar = input("Deseja fazer uma pesquisa ? Y/N: ")
print()
if continuar == "N" or continuar == "n": 
    exit()
else:

    while continuar == "Y" or continuar == "y":  #enquanto o usuário desejar fazer uma pesquisa o programa irá repetir o looping
    

        print("Digite o produto específico a ser pesquisado...")
        print()
        pesquisa=input("Digite o produto a ser pesquisado: ")
        time.sleep(0.50)
        print("iniciando a pesquisa...")
        time.sleep(1)

        driver = webdriver.Chrome("chromedriver.exe")
        driver.get("https://www.google.com")
        wait = WebDriverWait(driver, 20) #temo limite para o chromedriver abrir

        # seleciona o campo de pesquisa e digita a pesquisa do usuário
        campo_pesquisa = driver.find_element_by_xpath("//textarea[@name='q']")
        campo_pesquisa.clear()
        campo_pesquisa.send_keys(pesquisa)
        campo_pesquisa.send_keys(Keys.ENTER)

        try:
            #tenta identificar se as divs estão presentes na página
            divs = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[class^='mnr-c']"))) #atribui as divs do html dos anúncios à vaiável "divs"

            #se as divs forem encontradas, o programa irá realizar as operações para pegar os valor de cada anúncio
            if len(divs) >0: 
            
                print("%s produtos encontrados"%len(divs))
                print()
                print()

                #percorre div por div para pegar os valores precisos
                for div in divs:
                    
                    produto_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[class^='plantl pla-unit-title-link']")))
                    link_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[id^='plaurlg_']")))
                    valor_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span[class^='e10twf']")))
                    loja_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span[class^='zPEcBd VZqTOd']")))

                #se a quantidade de elementos de cada div for igual, ele atribui os valores à cada variável
                if len(produto_elements) == len(link_elements) == len(loja_elements) == len(valor_elements):
                    print("quantidade de elementos correspondendo...")
                    print()
                    for  produto_element, link_element, valor_element, loja_element in zip(produto_elements, link_elements, valor_elements, loja_elements):
                        produto = produto_element.get_attribute("aria-label")
                        link = link_element.get_attribute("href")
                        valor = valor_element.text
                        loja = loja_element.text

                        #faz a tratativa do valor para retirar o sinal de R$ e substituir a vírgula por ponto
                        valor = float(valor.replace(".","").replace(",",".").replace("R$ ","")) 

                        #converte o valor real para o dólar
                        valor_dolar = valor / dolar

                        #arredonda o valor para 2 cada decimais
                        valor_dolar = round(valor_dolar,2)

                        #converte o número para uma string para salvar no banco
                        valor = str(valor)
                        valor_dolar = str(valor_dolar)

                        #adiciona os elementos ao grupo produtos
                        produtos.add((produto, link, valor,valor_dolar, loja))

                        #faz a inserção no banco de dados e confirma a transação de dados
                        cursor=conexao.cursor()
                        query="insert into pesquisas(produto, loja, valor_real,valor_dolar, link) values (%s,%s,%s,%s,%s)"
                        cursor.execute(query,(produto,loja, valor, valor_dolar, link))
                        conexao.commit()
                        
                else:
                    #se a quantidade de elementos não forem igual entre si, o sistema retornará uma mensagem avisando que as quantidades não são iguais
                    print("A quantidade de elementos nas listas não corresponde.")
                    print("Verifique se os seletores CSS estão corretos.")

                #conforme os dados inseridos no grupo produtos, o sistema irá mostrar os dados de cada produto encontrado na pesquisa   
                for produto, link, valor, valor_dolar, loja in produtos:
                    print("Produto: ", produto)
                    print("Link: ", link)
                    print("Valor: ", valor)
                    print("Valor dólar: ", valor_dolar)
                    print("Loja: ", loja)
                    print()
                    print()

                
                #confere se os dados foram inseridos com sucesso
                if cursor.rowcount >0:
                    print("Dados inseridos com sucesso...")
                else:
                    print("Houve um problema ao inserir os dados...")
                
                    
            #se o programa não identificar os anúncios, o sistema fechará o chromedriver
            else:
                driver.quit()

        except TimeoutException:
            print("Tempo excedido. Não foi possível encontrar as divs.")
        finally:
            driver.quit()


        #pergunta se o usuário deseja fazer mais uma pesquisa
        continuar = input("Deseja fazer uma pesquisa ? Y/N: ")

        #se o usuário desejar fazer mais uma pesquisa, o sistema fechará o chrome atual fará o looping novamente
        if continuar == "N" or continuar == "n":
            driver.quit()
            exit()           
        else:
            driver.quit()



