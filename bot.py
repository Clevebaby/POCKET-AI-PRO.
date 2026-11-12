import os
import logging
import requests
import pandas as pd

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# CONFIGURAÇÕES
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_KEY = os.getenv("TWELVE_DATA_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PAIRS = {
    "EUR/USD": "EUR/USD",
    "GBP/USD": "GBP/USD",
    "USD/JPY": "USD/JPY",
    "AUD/USD": "AUD/USD",
    "AUD/NZD": "AUD/NZD",
}

TIMEFRAMES = {
    "M1": "1min",
    "M5": "5min",
    "M15": "15min"
}


# MENU PRINCIPAL
def main_menu():
    keyboard = [
        [
            InlineKeyboardButton("📊 FOREX", callback_data="forex"),
            InlineKeyboardButton("🌐 OTC", callback_data="otc")
        ],
        [
            InlineKeyboardButton("🧠 ANALISAR MERCADO", callback_data="analyze")
        ],
        [
            InlineKeyboardButton("📈 ESTATÍSTICAS", callback_data="stats")
        ],
        [
            InlineKeyboardButton("ℹ️ AJUDA", callback_data="help")
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


# MENU DE PARES
def pair_menu():
    keyboard = []

    for pair in PAIRS:
        keyboard.append([
            InlineKeyboardButton(pair, callback_data=f"pair:{pair}")
        ])

    keyboard.append([
        InlineKeyboardButton("⬅️ VOLTAR", callback_data="home")
    ])

    return InlineKeyboardMarkup(keyboard)


# MENU DE TIMEFRAMES
def timeframe_menu():
    keyboard = [
        [
            InlineKeyboardButton("M1", callback_data="tf:M1"),
            InlineKeyboardButton("M5", callback_data="tf:M5"),
            InlineKeyboardButton("M15", callback_data="tf:M15")
        ],
        [
            InlineKeyboardButton("⬅️ VOLTAR", callback_data="forex")
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


# OBTER DADOS DO MERCADO
def get_market_data(symbol, interval):

    if not API_KEY:
        raise ValueError("API KEY da Twelve Data não configurada.")

    url = "https://api.twelvedata.com/time_series"

    params = {
        "symbol": symbol,
        "interval": interval,
        "outputsize": 100,
        "apikey": API_KEY
    }

    response = requests.get(
        url,
        params=params,
        timeout=20
    )

    response.raise_for_status()

    data = response.json()

    if "values" not in data:
        raise ValueError(
            data.get("message", "Não foi possível obter os dados.")
        )

    df = pd.DataFrame(data["values"])

    df["close"] = pd.to_numeric(
        df["close"],
        errors="coerce"
    )

    df = df.dropna(subset=["close"])

    df = df.iloc[::-1].reset_index(drop=True)

    if len(df) < 30:
        raise ValueError("Dados insuficientes para análise.")

    return df


# INDICADORES TÉCNICOS
def calculate_indicators(df):

    close = df["close"]

    # EMA 9 E EMA 21
    df["EMA9"] = close.ewm(
        span=9,
        adjust=False
    ).mean()

    df["EMA21"] = close.ewm(
        span=21,
        adjust=False
    ).mean()

    # RSI 14
    delta = close.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(
        alpha=1/14,
        adjust=False,
        min_periods=14
    ).mean()

    avg_loss = loss.ewm(
        alpha=1/14,
        adjust=False,
        min_periods=14
    ).mean()

    rs = avg_gain / avg_loss

    df["RSI"] = 100 - (100 / (1 + rs))

    # MACD
    ema12 = close.ewm(
        span=12,
        adjust=False
    ).mean()

    ema26 = close.ewm(
        span=26,
        adjust=False
    ).mean()

    df["MACD"] = ema12 - ema26

    df["SIGNAL"] = df["MACD"].ewm(
        span=9,
        adjust=False
    ).mean()

    return df


# ANÁLISE DO MERCADO
def analyze_market(symbol, timeframe):

    interval = TIMEFRAMES[timeframe]

    df = get_market_data(symbol, interval)

    df = calculate_indicators(df)

    last = df.iloc[-1]

    price = last["close"]
    rsi = last["RSI"]
    ema9 = last["EMA9"]
    ema21 = last["EMA21"]
    macd = last["MACD"]
    macd_signal = last["SIGNAL"]

    if pd.isna(rsi):
        raise ValueError("Indicadores ainda não estão disponíveis.")

    # CRITÉRIOS DE COMPRA E VENDA
    bullish = [
        ema9 > ema21,
        macd > macd_signal,
        50 < rsi < 70
    ]

    bearish = [
        ema9 < ema21,
        macd < macd_signal,
        30 < rsi < 50
    ]

    up_score = sum(bullish)
    down_score = sum(bearish)

    if up_score == 3:
        direction = "UP ⬆️"
        score = 100

    elif down_score == 3:
        direction = "DOWN ⬇️"
        score = 100

    else:
        direction = "SEM SINAL ⏳"
        score = max(up_score, down_score) * 100 / 3

    return {
        "price": price,
        "rsi": rsi,
        "ema9": ema9,
        "ema21": ema21,
        "macd": macd,
        "direction": direction,
        "score": score,
        "time": last["datetime"]
    }


# INICIAR BOT
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🤖 POCKET AI PRO\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Sistema inteligente de análise Forex.\n\n"
        "Escolhe uma opção:",
        reply_markup=main_menu()
    )


# BOTÕES
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    data = query.data

    if data == "home":

        await query.edit_message_text(
            "🤖 POCKET AI PRO\n\nEscolhe uma opção:",
            reply_markup=main_menu()
        )

    elif data == "forex":

        await query.edit_message_text(
            "📊 ESCOLHE O PAR DE MOEDAS:",
            reply_markup=pair_menu()
        )

    elif data == "otc":

        await query.edit_message_text(
            "🌐 MÓDULO OTC\n\n"
            "Ainda não temos uma fonte de cotações OTC "
            "autênticas e verificadas.\n\n"
            "Por isso, não vamos inventar sinais OTC.",
            reply_markup=main_menu()
        )

    elif data.startswith("pair:"):

        pair = data.split(":", 1)[1]

        context.user_data["pair"] = pair

        await query.edit_message_text(
            f"💱 PAR: {pair}\n\n"
            "Escolhe o timeframe:",
            reply_markup=timeframe_menu()
        )

    elif data.startswith("tf:"):

        timeframe = data.split(":", 1)[1]

        pair = context.user_data.get("pair")

        if not pair:
            await query.edit_message_text(
                "Seleciona primeiro um par.",
                reply_markup=pair_menu()
            )
            return

        await query.edit_message_text(
            f"🧠 A analisar {pair} ({timeframe})...\n"
            "Aguarda um momento."
        )

        try:

            result = analyze_market(pair, timeframe)

            message = (
                "🤖 POCKET AI PRO\n"
                "━━━━━━━━━━━━━━━━━━\n"
                f"💱 PAR: {pair}\n"
                f"⏱️ TIMEFRAME: {timeframe}\n"
                f"💰 PREÇO: {result['price']}\n\n"
                "📊 INDICADORES\n"
                f"RSI: {result['rsi']:.2f}\n"
                f"EMA 9: {result['ema9']:.5f}\n"
                f"EMA 21: {result['ema21']:.5f}\n"
                f"MACD: {result['macd']:.6f}\n\n"
                "🎯 RESULTADO DA ANÁLISE\n"
                f"{result['direction']}\n"
                f"Alinhamento técnico: {result['score']:.0f}%\n\n"
                f"🕒 Última vela: {result['time']}\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "⚠️ Análise técnica experimental. "
                "Não representa probabilidade de lucro "
                "nem garantia de resultado."
            )

            await query.edit_message_text(
                message,
                reply_markup=main_menu()
            )

        except Exception as e:

            logger.exception("Erro na análise")

            await query.edit_message_text(
                f"⚠️ Não foi possível analisar o mercado.\n\n"
                f"Motivo: {str(e)[:300]}",
                reply_markup=main_menu()
            )

    elif data == "analyze":

        await query.edit_message_text(
            "🧠 ESCOLHE O MERCADO:",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "📊 FOREX",
                        callback_data="forex"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🌐 OTC",
                        callback_data="otc"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "⬅️ VOLTAR",
                        callback_data="home"
                    )
                ]
            ])
        )

    elif data == "stats":

        await query.edit_message_text(
            "📈 ESTATÍSTICAS\n\n"
            "Ainda não existem resultados de operações "
            "verificados.\n\n"
            "As análises técnicas não são contabilizadas "
            "como vitórias ou derrotas.",
            reply_markup=main_menu()
        )

    elif data == "help":

        await query.edit_message_text(
            "ℹ️ COMO UTILIZAR\n\n"
            "1. Seleciona FOREX.\n"
            "2. Escolhe um par.\n"
            "3. Escolhe M1, M5 ou M15.\n"
            "4. Consulta a análise técnica.\n\n"
            "Testa sempre em conta Demo.",
            reply_markup=main_menu()
        )


# EXECUÇÃO
def main():

    if not TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN não configurado.")

    if not API_KEY:
        raise ValueError("TWELVE_DATA_API_KEY não configurada.")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        CallbackQueryHandler(buttons)
    )

    print("POCKET AI PRO iniciado com sucesso!")

    app.run_polling()


if __name__ == "__main__":
    main()
