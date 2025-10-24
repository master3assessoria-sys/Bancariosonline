import os
import re
import http.server
import socketserver
import threading
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from respostas_bot import respostas

# Mensagem de boas-vindas para /start
async def boas_vindas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nome = update.effective_user.first_name
    mensagem = (
        f"Olá, {nome}. Sou a assistente do BancariosOnLine, criada para orientar bancárias e bancários "
        "sobre seus direitos previstos nos ACTs e CCTs da categoria.\n\n"
        "Digite uma palavra-chave como 'plr', 'filiação' ou 'campanha salarial' e eu mostro o que mudou com base nos acordos mais recentes."
    )
    await update.message.reply_text(mensagem)

# Função segura para detectar intents
def extrair_intent(texto):
    texto = texto.lower().strip()
    for chave in sorted(respostas.keys(), key=len, reverse=True):
        padrao = r'\b' + re.escape(chave.lower()) + r'\b'
        if re.search(padrao, texto):
            return chave
    return None

# Função principal de resposta
async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text
    intent = extrair_intent(texto)

    if intent:
        await update.message.reply_text(respostas[intent])
    else:
        await update.message.reply_text(
            "Desculpe, não encontrei informações sobre esse tema. "
            "Tente usar palavras como 'plr', 'licença saúde', 'campanha salarial', 'filiação' ou 'vales'."
        )

# Função para manter porta falsa aberta (Render)
def manter_porta_aberta():
    PORT = 10000
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()

# Função principal
def main():
    threading.Thread(target=manter_porta_aberta, daemon=True).start()

    token = os.environ.get("TOKEN")
    if not token:
        print("❌ TOKEN não encontrado. Verifique as variáveis de ambiente no Render.")
        return

    app = ApplicationBuilder().token(token).build()

    # Corrigido: CommandHandler para /start
    app.add_handler(CommandHandler("start", boas_vindas))

    # Corrigido: MessageHandler para texto normal
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))

    print("✅ Bot sindical BancariosOnLine está funcionando com excelência!")
    app.run_polling()

# Executa o bot
if __name__ == "__main__":
    main()
