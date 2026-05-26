from lxml import html
import requests
from lxml import html
import locale

def limpa_texto(input:str|list[str]) -> str|list[str]:
    def limpa(s:str):
        return s.strip().replace('\n','').replace('\t','').replace('\r','').lower()

    if type(input) == str:
        return limpa(input)
    return [limpa(s) for s in input if s.strip() ]


def formata_numero(value: str) -> float:
    value = value.strip()

    if "," in value and "." in value:
        if value.rfind(",") > value.rfind("."):
            # 1.234,56
            value = value.replace(".", "")
            value = value.replace(",", ".")
        else:
            # 1,234.56
            value = value.replace(",", "")
    else:
        value = value.replace(",", ".")

    return float(value)


def extrai_numeros(value: str) -> str:
    return "".join(c for c in value if c.isdigit())


def formatar_nota(nota):
    for produto in nota["produtos"]:
        produto["quantidade"] = formata_numero(produto["quantidade"])
        produto["valor_unidade"] = formata_numero(produto["valor_unidade"])
        produto["valor"] = formata_numero(produto["valor"])
    
    for pagamento in nota["pagamentos"]:
        pagamento["valor"] = formata_numero(pagamento["valor"])

    dados = nota["dados"]
    dados["cpf"] = extrai_numeros(dados["cpf"])
    dados["cnpj"] = extrai_numeros(dados["cnpj"])

    nota["tributos"] = formata_numero(nota["tributos"])
    nota["chave_acesso"] = nota["chave_acesso"].replace(' ','')


def validar_nota(nota) -> bool:
    pass


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
            "nome": limpa_texto(nome),
            "codigo": limpa_texto(codigo),
            "quantidade": limpa_texto(quantidade),
            "unidade": limpa_texto(unidade),
            "valor_unidade": limpa_texto(valor_unidade),
            "valor": limpa_texto(valor)
        }
        produtos.append(produto)
    return produtos


def extrai_pagametos_tributos(pagina_html:html):
    formas_pagamento = pagina_html.xpath('//*[@id="linhaTotal"]/label/text()')
    valores_pagamento = pagina_html.xpath('//*[@id="linhaTotal"]/span/text()')
    
    formas_pagamento = limpa_texto(formas_pagamento)
    valores_pagamento = limpa_texto(valores_pagamento)
    
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
        "cpf": limpa_texto(cpf),
        "cnpj": limpa_texto(cnpj),
        "comercio": limpa_texto(comercio),
        "endereco": limpa_texto(endereco),
        "emissao": limpa_texto(emissao),
    }
    chave_acesso = limpa_texto(chave)
    return dados, chave_acesso


def extrai_nota_fiscal(pagina_html:html):
    produtos = extrai_produtos(pagina_html)
    pagamentos, tributos = extrai_pagametos_tributos(pagina_html)
    dados, chave_aceso = extrai_dados_chave(pagina_html)
    
    nota_fiscal = {
        "produtos": produtos,
        "pagamentos": pagamentos,
        "tributos": tributos,
        "dados": dados,
        "chave_acesso": chave_aceso,
    }
    return nota_fiscal


def extrai_nota_fiscais(urls:list[str]):
    notas = []
    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except:
            continue
        pagina_html = html.fromstring(response.content)
        nota = extrai_nota_fiscais(url,pagina_html)
        nota["url"] = url
        notas.append(nota)
    return notas