import requests
from bs4 import BeautifulSoup
from datetime import datetime
from simulador.models import HistoricoPrecoMilho  # ajuste o import conforme sua estrutura

def coletar_cotacao_milho():
    url = "https://www.cepea.org.br/br/widgetproduto.js.php?fonte=arial&tamanho=10&largura=400px&corfundo=dbd6b2&cortexto=333333&corlinha=ede7bf&id_indicador%5B%5D=77"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    tr = soup.find("table", class_="imagenet-widget-tabela").find("tbody").find("tr")
    tds = tr.find_all("td")

    data_str = tds[0].text.strip()
    valor_str = tds[2].text.strip().replace("R$", "").replace(".", "").replace(",", ".")

    data = datetime.strptime(data_str, "%d/%m/%Y").date()
    valor = float(valor_str)
    
    # Verifica se a data já está no banco
    if not HistoricoPrecoMilho.objects.filter(data=data).exists():
        HistoricoPrecoMilho.objects.create(data=data, preco_milho=valor)
        print(f"Inserido: {data} - R$ {valor}")
    else:
        print(f"Cotação do milho para {data} já está no banco.")
