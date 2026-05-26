from sys import exit
from pathlib import Path
from PIL import Image
from pyzbar.pyzbar import decode
import requests
from lxml import html
from pprint import pprint


def limpa_string(input:str|list[str]):
    def limpa(s:str):
        return s.strip().replace('\n','').replace('\t','').replace('\r','').lower()

    if type(input) == str:
        return limpa(input)
    return [limpa(s) for s in input if s.strip() ]


def decodifica_imagem(imagem):
    if not decode(imagem):
        return None
    return decode(imagem)[0].data.decode('utf-8')


def extrai_qrcode_arquivos(pasta:str,extensoes:list[str]=[".png",".jpg",".jpeg"]):
    pasta = Path(pasta)
    conteudo = []
    for arquivo in pasta.glob('*'):
        if not arquivo.suffix.lower() in extensoes:
            continue
        imagem = Image.open(arquivo)
        if not imagem:
            continue
        decodificado = decodifica_imagem(imagem)
        if not decodificado or decodificado in conteudo:
            continue
        conteudo.append(decodificado)
    return conteudo    


# Webscrap pipeline

def extrai_produtos(pagina_html:html):
    produtos = []
    tabela_compras = pagina_html.xpath('//*[@id="tabResult"]/tr')
    for linha in tabela_compras:
        nome = linha.xpath('.//span[@class="txtTit"]/text()')
        codigo = linha.xpath('.//span[@class="RCod"]/text()')
        quantidade = linha.xpath('.//span[@class="Rqtd"]/text()')
        unidade = linha.xpath('.//span[@class="RUN"]/text()')
        valor_unidade = linha.xpath('.//span[@class="RvlUnit"]/text()')
        valor = linha.xpath('.//span[@class="valor"]/text()')
        produto = {
            "nome": limpa_string(nome),
            "codigo": limpa_string(codigo),
            "quantidade": limpa_string(quantidade),
            "unidade": limpa_string(unidade),
            "valor_unidade": limpa_string(valor_unidade),
            "valor": limpa_string(valor)
        }
        produtos.append(produto)
    return produtos


def extrai_pagametos_tributos(pagina_html:html):
    formas_pagamento = pagina_html.xpath('//*[@id="linhaTotal"]/label/text()')
    valores_pagamento = pagina_html.xpath('//*[@id="linhaTotal"]/span/text()')
    
    formas_pagamento = limpa_string(formas_pagamento)
    valores_pagamento = limpa_string(valores_pagamento)
    
    pagamentos = []
    tributos = ''
    
    for f,v in zip(formas_pagamento, valores_pagamento):
        if 'qtd' in f or 'valor a pagar' in f:
            continue
        if "tributos" in f:
            tributos = v
            continue
        pagamento = {
            "forma": f,
            "valor": v,
        }
        pagamentos.append(pagamento)
    return pagamentos, tributos


def extrai_dados_chave(pagina_html:html):
    bloco_empresa = pagina_html.xpath('//div[.//div[@id="u20"]][1]')[0]
    bloco_infos = pagina_html.xpath('//div[@id="infos"]')[0]
    
    cnpj = bloco_empresa.xpath('.//div[contains(text(),"CNPJ")]/text()')
    comercio = bloco_empresa.xpath('.//div[@id="u20"]/text()')
    endereco = bloco_empresa.xpath('.//div[@class="text"][2]//text()')
    
    cpf = bloco_infos.xpath('.//li[strong[contains(., "CPF")]]/text()')
    chave = bloco_infos.xpath('.//span[@class="chave"]/text()')
    emissao = bloco_infos.xpath('.//li[strong[contains(., "Emissão")]]/text()')
    
    for e in emissao:
        if not "Via" in e:
            continue
        emissao = "".join(e)
        break
    dados = {
        "cpf": limpa_string(cpf),
        "cnpj": limpa_string(cnpj),
        "comercio": limpa_string(comercio),
        "endereco": limpa_string(endereco),
        "emissao": limpa_string(emissao),
    }
    chave_acesso = limpa_string(chave)
    return dados, chave_acesso


def extrai_nota_fiscal(url,pagina_html:html):
    produtos = extrai_produtos(pagina_html)
    pagamentos, tributos = extrai_pagametos_tributos(pagina_html)
    dados, chave_aceso = extrai_dados_chave(pagina_html)
    
    nota_fiscal = {
        "produtos": produtos,
        "pagamentos": pagamentos,
        "tributos": tributos,
        "dados": dados,
        "url": url,
        "chave_acesso": chave_aceso,
    }
    return nota_fiscal


pasta_qrcodes = './notas'
urls = extrai_qrcode_arquivos(pasta_qrcodes)

if len(urls) == 0:
    exit()

for url in urls:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except:
        continue
    pagina_html = html.fromstring(response.content)
    nota = extrai_nota_fiscal(url,pagina_html)
    pprint(nota)
    print('')

# TODOs:
# - Formatar dados
# - Validar os dados
# - Salvar em csv
# - Testes
# - Front End