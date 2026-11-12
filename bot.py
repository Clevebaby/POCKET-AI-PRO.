import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def menu():
    keyboard = [
        [
            InlineKeyboardButton("📊 FOREX", callback_data="forex"),
            InlineKeyboardButton("🌐 OTC", callback_data="otc")
        ],
        [
            InlineKeyboardButton("⬆️ UP", callback_data="up"),
            InlineKeyboardButton("⬇️ DOWN", callback_data="down")
        ],
        [
            InlineKeyboardButton("🧠 ANÁLISE IA", callback_data="ia")
        ],
        [
            InlineKeyboardButton("📈 ESTATÍSTICAS", callback_data="stats")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 BEM-VINDO AO POCKET AI PRO\n\n"
        "Sistema de análise Forex e OTC.\n\n"
        "Escolhe uma opção:",
        reply_markup=menu()
    )

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    messages = {
        "forex": "📊 Selecionaste FOREX.\n\nEm breve: análise de pares Forex.",
        "otc": "🌐 Selecionaste OTC.\n\nAguardando fonte de dados OTC fiável.",
        "up": "⬆️ UP: ainda não há sinal confirmado.",
        "down": "⬇️ DOWN: ainda não há sinal confirmado.",
        "ia": "🧠 Módulo de IA em preparação.",
        "stats": "📈 Ainda não existem operações registadas."
    }

    await query.edit_message_text(
        messages.get(query.data, "Opção inválida."),
        reply_markup=menu()
    )

def main():
    if not TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN não configurado!")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))

    print("POCKET AI PRO iniciado!")
    app.run_polling()

if __name__ == "__main__":
    main()
