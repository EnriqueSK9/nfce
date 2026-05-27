from lxml import html
import requests
from lxml import html
from urllib.parse import urlparse


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
        produto["codigo"] = extrai_numeros(produto["codigo"])
        produto["quantidade"] = formata_numero(produto["quantidade"])
        produto["valor_unidade"] = formata_numero(produto["valor_unidade"])
        produto["valor"] = formata_numero(produto["valor"])
    
    for pagamento in nota["pagamentos"]:
        pagamento["valor"] = formata_numero(pagamento["valor"])

    dados = nota["dados"]
    dados["cpf"] = extrai_numeros(dados["cpf"])
    dados["cnpj"] = extrai_numeros(dados["cnpj"])

    nota["tributos"] = formata_numero(nota["tributos"])
    nota["chave_acesso"] = extrai_numeros(nota["chave_acesso"])


def validar_nota(nota):
    erros = []
    validos = 0
    invalidos = 0

    def ok():
        nonlocal validos
        validos += 1

    def erro(msg):
        nonlocal invalidos
        invalidos += 1
        erros.append(msg)

    def validar_string(
        valor,
        campo,
        obrigatorio=True,
        apenas_numeros=False,
        tamanho_exato=None,
    ):
        if not isinstance(valor, str):
            erro(f"{campo} deve ser string")
            return False

        if obrigatorio and valor == "":
            erro(f"{campo} não pode ser vazio")
            return False

        if len(valor) > 256:
            erro(f"{campo} excede {256} caracteres")
            return False

        if tamanho_exato is not None and len(valor) != tamanho_exato:
            erro(f"{campo} deve ter exatamente {tamanho_exato} caracteres")
            return False

        if apenas_numeros and not valor.isdigit():
            erro(f"{campo} deve conter apenas números")
            return False

        ok()
        return True

    def validar_float(valor, campo, permitir_zero=True):
        if not isinstance(valor, (int, float)):
            erro(f"{campo} deve ser numérico")
            return False

        if valor < 0:
            erro(f"{campo} não pode ser negativo")
            return False

        if not permitir_zero and valor == 0:
            erro(f"{campo} não pode ser zero")
            return False

        ok()
        return True

    def validar_url(url):
        if not isinstance(url, str):
            erro("url deve ser string")
            return False

        if url == "":
            erro("url não pode ser vazia")
            return False

        if len(url) > 256:
            erro(f"url excede {256} caracteres")
            return False

        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            erro("url inválida")
            return False

        ok()
        return True


    if not isinstance(nota, dict):
        return {
            "valido": False,
            "validos": 0,
            "invalidos": 1,
            "erros": ["nota deve ser um dicionário"],
        }


    produtos = nota.get("produtos")

    if not isinstance(produtos, list):
        erro("produtos deve ser lista")
    elif len(produtos) == 0:
        erro("produtos não pode estar vazio")
    else:
        ok()

        for i, produto in enumerate(produtos):
            if not isinstance(produto, dict):
                erro(f"produto[{i}] deve ser objeto")
                continue

            validar_string(produto.get("nome"), f"produto[{i}].nome")
            validar_string(
                produto.get("codigo"),
                f"produto[{i}].codigo",
                apenas_numeros=True,
            )

            validar_string(produto.get("unidade"), f"produto[{i}].unidade")

            validar_float(
                produto.get("quantidade"),
                f"produto[{i}].quantidade",
            )

            validar_float(
                produto.get("valor_unidade"),
                f"produto[{i}].valor_unidade",
                permitir_zero=False,
            )

            validar_float(
                produto.get("valor"),
                f"produto[{i}].valor",
                permitir_zero=False,
            )


    pagamentos = nota.get("pagamentos")

    if not isinstance(pagamentos, list):
        erro("pagamentos deve ser lista")
    elif len(pagamentos) == 0:
        erro("pagamentos não pode estar vazio")
    else:
        ok()

        for i, pagamento in enumerate(pagamentos):
            if not isinstance(pagamento, dict):
                erro(f"pagamento[{i}] deve ser objeto")
                continue

            validar_string(
                pagamento.get("forma"),
                f"pagamento[{i}].forma",
            )

            validar_float(
                pagamento.get("valor"),
                f"pagamento[{i}].valor",
                permitir_zero=False,
            )


    dados = nota.get("dados")

    if not isinstance(dados, dict):
        erro("dados deve ser objeto")
    else:
        ok()

        cpf = dados.get("cpf")
        cnpj = dados.get("cnpj")

        # CPF pode ser vazio
        if cpf != "":
            validar_string(
                cpf,
                "dados.cpf",
                obrigatorio=False,
                apenas_numeros=True,
                tamanho_exato=11,
            )
        else:
            ok()

        validar_string(
            cnpj,
            "dados.cnpj",
            apenas_numeros=True,
            tamanho_exato=14,
        )

        validar_string(dados.get("comercio"), "dados.comercio")
        validar_string(dados.get("endereco"), "dados.endereco")

        emissao = dados.get("emissao")

        if not isinstance(emissao, int):
            erro("dados.emissao deve ser unix timestamp inteiro")
        elif emissao < 0:
            erro("dados.emissao não pode ser negativo")
        else:
            ok()


    validar_url(nota.get("url"))


    validar_string(
        nota.get("chave_acesso"),
        "chave_acesso",
        apenas_numeros=True,
        tamanho_exato=32,
    )


    tributos = nota.get("tributos")

    if validar_float(tributos, "tributos"):
        total_produtos = 0
        total_pagamentos = 0

        if isinstance(produtos, list):
            total_produtos = sum(
                p.get("valor", 0)
                for p in produtos
                if isinstance(p, dict)
                and isinstance(p.get("valor"), (int, float))
            )

        if isinstance(pagamentos, list):
            total_pagamentos = sum(
                p.get("valor", 0)
                for p in pagamentos
                if isinstance(p, dict)
                and isinstance(p.get("valor"), (int, float))
            )

        total = max(total_produtos, total_pagamentos)

        if tributos > total:
            erro("tributos não pode ser maior que o valor total da nota")
        else:
            ok()

    return {
        "valido": invalidos == 0,
        "validos": validos,
        "invalidos": invalidos,
        "erros": erros,
    }


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
        formatar_nota(nota)

        valido, validos, invalidos, erros = validar_nota(nota)
        if not valido:
            print(f"{validos}/{validos+invalidos}")
            for e in erros:
                print(e)
            # retry
            return

        notas.append(nota)
    return notas