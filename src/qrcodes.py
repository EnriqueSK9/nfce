from pathlib import Path
from PIL import Image
from pyzbar.pyzbar import decode

def decodifica_imagem(imagem:Image) -> str:
    if not decode(imagem):
        return None
    return decode(imagem)[0].data.decode('utf-8')


def extrai_qrcode_arquivos(pasta:str,extensoes:list[str] = [".png",".jpg",".jpeg"]):
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