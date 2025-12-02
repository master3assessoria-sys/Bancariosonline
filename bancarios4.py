import os
import re
import http.server
import socketserver
import threading
import logging
import difflib
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from respostas_bot import respostas

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mensagem de boas-vindas para /start
async def boas_vindas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nome = update.effective_user.first_name
    mensagem = (
        f"Olá, {nome}. Sou a assistente do BancariosOnLine, criada para orientar bancárias e bancários "
        "sobre seus direitos previstos nos ACTs e CCTs da categoria.\n\n"
        "Digite uma palavra-chave como 'plr', 'filiação' ou 'campanha salarial' e eu mostro o que mudou com base nos acordos mais recentes.\n\n"
        "💡 Dica: você também pode usar o comando /help para ver todas as palavras-chave disponíveis ou clicar nos botões abaixo."
    )

    # Criar botões com as palavras-chave
    keyboard = [
        [InlineKeyboardButton(chave, callback_data=chave)]
        for chave in sorted(respostas.keys())
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(mensagem, reply_markup=reply_markup)

# Comando /help para listar intents disponíveis
async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chaves = ", ".join(sorted(respostas.keys()))
    mensagem = (
        "📖 Lista de palavras-chave disponíveis:\n\n"
        f"{chaves}\n\n"
        "Você pode digitar uma delas ou clicar nos botões que aparecem ao iniciar o bot (/start)."
    )
    await update.message.reply_text(mensagem)

# Função segura para detectar intents
def extrair_intent(texto):
    texto = texto.lower().strip()
    chaves = respostas.keys()
    # Primeiro tenta regex exata
    for chave in sorted(chaves, key=len, reverse=True):
        padrao = r'\b' + re.escape(chave.lower()) + r'\b'
        if re.search(padrao, texto):
            return chave
    # Se não encontrou, tenta aproximação com difflib
    match = difflib.get_close_matches(texto, chaves, n=1, cutoff=0.7)
    return match[0] if match else None

# Função principal de resposta
async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        texto = update.message.text
        intent = extrair_intent(texto)

        if intent:
            await update.message.reply_text(respostas[intent])
        else:
            await update.message.reply_text(
                "Desculpe, não encontrei informações sobre esse tema. "
                "Tente usar palavras como 'plr', 'licença saúde', 'campanha salarial', 'filiação' ou 'vales'. "
                "Ou digite /help para ver todas as opções."
            )
    except Exception as e:
        await update.message.reply_text("⚠️ Ocorreu um erro interno. Tente novamente mais tarde.")
        logger.error(f"Erro ao responder: {e}")

# Função para tratar cliques nos botões
async def botao_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chave = query.data
    resposta = respostas.get(chave, "Informação não encontrada.")
    await query.message.reply_text(resposta)

# Servidor falso para manter porta aberta (Render)
class DummyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot ativo")

def manter_porta_aberta():
    PORT = 10000
    with socketserver.TCPServer(("", PORT), DummyHandler) as httpd:
        httpd.serve_forever()

# Função principal
def main():
    threading.Thread(target=manter_porta_aberta, daemon=True).start()

    token = os.environ.get("TOKEN")
    if not token or len(token) < 30:  # validação simples
        logger.error("❌ TOKEN inválido ou não encontrado. Verifique as variáveis de ambiente no Render.")
        return

    app = ApplicationBuilder().token(token).build()

    # Handlers
    app.add_handler(CommandHandler("start", boas_vindas))
    app.add_handler(CommandHandler("help", ajuda))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))
    app.add_handler(CallbackQueryHandler(botao_callback))

    logger.info("✅ Bot sindical BancariosOnLine está funcionando com excelência!")
    app.run_polling()

# Executa o bot
if __name__ == "__main__":
    main()
