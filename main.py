from sys import exit
from pathlib import Path
from PIL import Image
from pyzbar.pyzbar import decode
import requests
from lxml import html

pasta_notas = Path("./notas")
extensoes_arquivos = [".png",".jpg",".jpeg"]
imagens = []
conteudo_qrcodes = []

for arquivo in pasta_notas.glob("*"):
    if not arquivo.suffix.lower() in extensoes_arquivos:
        continue

    imagem = Image.open(arquivo)
    if not imagem:
        print(f"Aviso: Não foi possivel abrir a imagem {arquivo}")
        continue
    imagens.append(imagem)

    decodificado = decode(imagem)
    if not decodificado:
        continue
    if decodificado in conteudo_qrcodes:
        continue
    conteudo_qrcodes.append(decodificado[0].data.decode('utf-8'))
    print(conteudo_qrcodes[-1])

if len(conteudo_qrcodes) == 0:
    print(f"Erro: Não foi encontrado nenhum qrcode válido na pasta {pasta_notas}")
    exit()

print(f"QrCodes Encontrados: {len(conteudo_qrcodes)}/{len(imagens)}")


xpath_compra = '/html/body/div[1]/div[2]/div/table'
xpath_total = '/html/body/div[1]/div[2]/div/div[2]'

for url in conteudo_qrcodes:
    response = requests.get(url)
    response.raise_for_status()
    
    tree = html.fromstring(response.content)
    print(tree.xpath(xpath_compra))
    print(tree.xpath(xpath_total))
    print('')