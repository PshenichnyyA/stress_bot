import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
from datetime import datetime

# 🔐 Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = 494237449  # Замените на ваш Telegram ID

questions = [
    ("Я повышаю голос или становлюсь агрессивным, когда чувствую угрозу.", "Fight"),
    ("Я пытаюсь физически или мысленно уйти от ситуации.", "Flight"),
    ("Я замираю и не могу действовать.", "Freeze"),
    ("Я стараюсь угодить другим, чтобы сохранить мир, даже если расстроен.", "Fawn"),
    ("Я чувствую прилив адреналина и готовлюсь «дать отпор».", "Fight"),
    ("Мне хочется немедленно убежать.", "Flight"),
    ("Я эмоционально отключаюсь или чувствую оцепенение.", "Freeze"),
    ("Я сразу стараюсь угодить, чтобы избежать конфликта.", "Fawn"),
]

scenarios = [
    {
        "text": "Сценарий 1: Коллега критикует вас при всех.",
        "options": [
            ("Спорю или защищаюсь.", "Fight"),
            ("Ухожу или избегаю человека.", "Flight"),
            ("Молчу и замираю.", "Freeze"),
            ("Извиняюсь/соглашаюсь, чтобы сохранить мир.", "Fawn"),
        ]
    },
    {
        "text": "Сценарий 2: Кто-то издает громкий / резкий звук за спиной в компании.",
        "options": [
            ("Разворачиваюсь и требую объяснений.", "Fight"),
            ("Быстро отхожу.", "Flight"),
            ("Замираю.", "Freeze"),
            ("Смеюсь или шучу, чтобы снять напряжение.", "Fawn"),
        ]
    },
    {
        "text": "Сценарий 3: Друг забыл ваш день рождения.",
        "options": [
            ("Конфликтую и злюсь.", "Fight"),
            ("Избегаю общения.", "Flight"),
            ("Чувствую растерянность.", "Freeze"),
            ("Говорю, что это ерунда.", "Fawn"),
        ]
    },
]

QUESTION, SCENARIO = range(2)

reaction_labels = {
    "Fight": "Борьба – агрессия, конфронтация",
    "Flight": "Бегство – избегание, побег",
    "Freeze": "Замирание – оцепенение, ступор",
    "Fawn": "Угодничество – попытка угодить, чтобы избежать конфликта",
}

def restart_keyboard():
    return ReplyKeyboardMarkup([["Начать заново"]], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "Добро пожаловать в тест на определение стрессовых реакций!\n\n"
        "Этот тест был адаптирован с англоязычного источника и переведён специально для вас.\n"
        "Автор бота: психолог @flauriss\n"
        "Подробнее о реакциях на стресс: t.me/psysredaa/46\n\n"
        "_(Примечание: данный бот является некоммерческим проектом и создан для образовательных целей.)_"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=restart_keyboard())
    await update.message.reply_text("Чтобы начать тест, нажмите кнопку или введите /test.")

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["current_q"] = 0
    context.user_data["scores"] = {"Fight": 0, "Flight": 0, "Freeze": 0, "Fawn": 0}

    intro_text = (
        "*I. Идентификация стрессовых реакций*\n"
        "_Инструкция:_ Оцените, насколько каждое утверждение соответствует вашей реакции в стрессе "
        "(1 – Никогда, 5 – Всегда)."
    )
    await update.message.reply_text(intro_text, parse_mode="Markdown")

    return await ask_question(update, context)

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q_index = context.user_data["current_q"]
    if q_index < len(questions):
        question_text, _ = questions[q_index]
        keyboard = ReplyKeyboardMarkup(
            [["1", "2", "3", "4", "5"], ["Начать заново"]],
            one_time_keyboard=False, resize_keyboard=True
        )
        await update.message.reply_text(
            f"{q_index + 1}. {question_text}\n(Ответьте от 1 до 5)",
            reply_markup=keyboard
        )
        return QUESTION
    else:
        return await start_scenarios(update, context)

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text.strip()
    if answer.lower() == "начать заново":
        return await start(update, context)

    if answer not in ["1", "2", "3", "4", "5"]:
        await update.message.reply_text("Пожалуйста, введите число от 1 до 5.")
        return QUESTION

    score = int(answer)
    q_index = context.user_data["current_q"]
    _, category = questions[q_index]
    context.user_data["scores"][category] += score
    context.user_data["current_q"] += 1

    return await ask_question(update, context)

async def start_scenarios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["scenario_index"] = 0
    context.user_data["scenario_scores"] = {"Fight": 0, "Flight": 0, "Freeze": 0, "Fawn": 0}
    await update.message.reply_text("Теперь переходим ко второй части теста. Выберите наиболее близкий вам вариант ответа.")
    return await ask_scenario(update, context)

async def ask_scenario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    index = context.user_data["scenario_index"]
    if index < len(scenarios):
        s = scenarios[index]
        options = [[opt[0]] for opt in s["options"]]
        options.append(["Начать заново"])
        keyboard = ReplyKeyboardMarkup(options, one_time_keyboard=False, resize_keyboard=True)
        await update.message.reply_text(s["text"], reply_markup=keyboard)
        return SCENARIO
    else:
        return await show_final_results(update, context)

async def handle_scenario_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text.strip()
    if answer.lower() == "начать заново":
        return await start(update, context)

    index = context.user_data["scenario_index"]
    s = scenarios[index]

    matched = [cat for text, cat in s["options"] if text == answer]
    if not matched:
        await update.message.reply_text("Пожалуйста, выберите один из предложенных вариантов.")
        return SCENARIO

    category = matched[0]
    context.user_data["scenario_scores"][category] += 1
    context.user_data["scenario_index"] += 1
    return await ask_scenario(update, context)

async def show_final_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    scores = context.user_data["scores"]
    scenario_scores = context.user_data["scenario_scores"]

    combined = {k: scores[k] + scenario_scores[k] * 2 for k in scores}
    result_lines = [f"{reaction_labels[k]}: {combined[k]} баллов" for k in combined]

    dominant = max(combined, key=combined.get)
    sorted_types = sorted(combined.items(), key=lambda x: x[1], reverse=True)
    secondary = sorted_types[1][0]

    result_text = (
        "🧠 Ваши результаты:\n\n" +
        "\n".join(result_lines) +
        f"\n\n🔹 Ведущая реакция: *{reaction_labels[dominant]}*\n"
        f"🔸 Запасная реакция: *{reaction_labels[secondary]}*\n\n"
        "Этот тест помогает вам исследовать свои врожденные стрессовые реакции по модели \"бей-беги-замри-угождай\".\n\n"
        "*Важно понимать:* Все варианты реакций естественны и формировались как механизмы выживания.\n"
        "Однако при травматическом опыте они могут закрепляться слишком жестко — в таких случаях рекомендуется консультация специалиста.\n\n"
        "Тест дает лишь общее представление о ваших склонностях, так как реальное поведение зависит от множества факторов:\n"
        "— контекста ситуации,\n"
        "— вашего состояния,\n"
        "— прошлого опыта.\n\n"
        "Результаты лучше рассматривать как точку для саморефлексии.\n\n"
        "*Спасибо за прохождение теста!*\n"
        "А также приглашаю вас в свой телеграм-канал [psysredaa](https://t.me/psysredaa) и на индивидуальные консультации."
    )

    await update.message.reply_text(result_text, parse_mode="Markdown", reply_markup=restart_keyboard())

    username = update.effective_user.username or f"id_{update.effective_user.id}"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    short_result = ", ".join([f"{k}: {v}" for k, v in combined.items()])
    admin_message = (
        f"📜 Результаты от @{username} ({timestamp}):\n"
        f"{short_result}\n"
        f"Ведущая: {reaction_labels[dominant]}"
    )

    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message)

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Тест отменён.", reply_markup=restart_keyboard())
    return ConversationHandler.END

def main():
    if not TOKEN:
        print("❌ Токен не найден. Убедитесь, что переменная TELEGRAM_BOT_TOKEN задана в .env файле.")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("test", test)],
        states={
            QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer)],
            SCENARIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_scenario_answer)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.Regex("^Начать заново$"), start))

    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()

#python bot.py
