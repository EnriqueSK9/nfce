# NFCE
Este projeto lê o qr-code de notas fiscais e tenta(best-effort) extrair os dados das compras usando webscrapping.

## TO-DO
- [ ] Core
  - [x] Ler pasta de qrcodes
  - [x] Extrair os campos de texto que contém os dados
  - [ ] Formatar os dados, extrair apenas a informação útil
  - [ ] Validar os dados, para ter certeza de sua consistência. fazer retry quando necessário.
  - [ ] Testes, para saber a taxa de sucesso em cada etapa.
- [ ] FrontEnd
  - [ ] Receber arquivos qrcode
  - [ ] Receber qrcode escaneado
  - [ ] Receber entradas manuais
  - [ ] Dashboard
  - [ ] Preferências/mapeamento
- [ ] BackEnd:
  - [ ] Registrar os dados em um DB local
  - [ ] Query de dados do DB local
