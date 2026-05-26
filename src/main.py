from sys import exit
from pprint import pprint
from qrcodes import extrai_qrcode_arquivos
from webscrapping import extrai_nota_fiscais

pasta_qrcodes = './notas'
urls = extrai_qrcode_arquivos(pasta_qrcodes)

if not urls:
    exit()

notas = extrai_nota_fiscais(urls)

if not notas:
    exit()

pprint(notas)