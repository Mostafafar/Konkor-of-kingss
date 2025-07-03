import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    ConversationHandler,
    CallbackQueryHandler
)
from database import (
    init_db,
    add_user,
    add_question,
    get_user_stats,
    get_random_question,
    get_categories,
    get_questions_count
)
from config import BOT_TOKEN, ADMIN_IDS, MAX_QUESTIONS_PER_USER
import re

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
(
    QUESTION_TEXT, OPTION_A, OPTION_B, OPTION_C, OPTION_D,
    CORRECT_OPTION, EXPLANATION, DIFFICULTY, CATEGORY
) = range(9)

def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    add_user(user.id, user.username, user.first_name, user.last_name)
    
    welcome_message = (
        f"👋 سلام {user.first_name}!\n\n"
        "به ربات سوالات تستی خوش آمدید! 🤖\n\n"
        "شما می‌توانید سوالات تستی خود را اضافه کنید و از سوالات دیگران استفاده کنید.\n\n"
        "📝 دستورات:\n"
        "/add_question - اضافه کردن سوال جدید\n"
        "/quiz - پاسخ به سوالات تصادفی\n"
        "/stats - آمار شما\n"
        "/categories - مشاهده دسته‌بندی‌ها\n"
        "/help - راهنمایی\n"
    )
    
    update.message.reply_text(welcome_message)

def help_command(update: Update, context: CallbackContext) -> None:
    help_text = (
        "📚 راهنمای ربات:\n\n"
        "/add_question - شروع فرآیند اضافه کردن سوال جدید\n"
        "/quiz - دریافت یک سوال تصادفی برای پاسخ دادن\n"
        "/stats - مشاهده آمار سوالات اضافه شده توسط شما\n"
        "/categories - مشاهده دسته‌بندی‌های موجود\n"
        "/help - نمایش این راهنما\n\n"
        "⚠️ نکات:\n"
        "- سوالات شما پس از تایید به بانک سوالات اضافه می‌شوند\n"
        "- می‌توانید برای سوالات خود توضیح اضافه کنید\n"
        "- می‌توانید سطح دشواری سوال را مشخص کنید\n"
    )
    
    update.message.reply_text(help_text)

def stats_command(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    stats = get_user_stats(user_id)
    total_questions = get_questions_count()
    
    stats_message = (
        f"📊 آمار شما:\n\n"
        f"✅ سوالات اضافه شده: {stats['questions_added']}\n"
        f"📚 کل سوالات بانک: {total_questions}\n\n"
        f"💡 شما می‌توانید حداکثر {MAX_QUESTIONS_PER_USER} سوال اضافه کنید."
    )
    
    update.message.reply_text(stats_message)

def categories_command(update: Update, context: CallbackContext) -> None:
    categories = get_categories()
    
    if not categories:
        update.message.reply_text("هنوز هیچ دسته‌بندی وجود ندارد.")
        return
    
    categories_text = "📚 دسته‌بندی‌های موجود:\n\n" + "\n".join(f"🔹 {cat}" for cat in categories)
    update.message.reply_text(categories_text)

def add_question_command(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    stats = get_user_stats(user_id)
    
    if stats['questions_added'] >= MAX_QUESTIONS_PER_USER:
        update.message.reply_text(
            f"شما به حداکثر تعداد سوالات ({MAX_QUESTIONS_PER_USER}) رسیده‌اید. "
            "برای اضافه کردن سوالات بیشتر با ادمین تماس بگیرید."
        )
        return ConversationHandler.END
    
    update.message.reply_text(
        "📝 لطفا متن سوال خود را ارسال کنید:\n\n"
        "مثال: 'پایتخت ایران کدام است؟'"
    )
    
    return QUESTION_TEXT

def question_text_received(update: Update, context: CallbackContext) -> int:
    context.user_data['question_text'] = update.message.text
    
    update.message.reply_text(
        "گزینه الف را وارد کنید:\n\n"
        "مثال: 'تهران'"
    )
    
    return OPTION_A

def option_a_received(update: Update, context: CallbackContext) -> int:
    context.user_data['option_a'] = update.message.text
    
    update.message.reply_text(
        "گزینه ب را وارد کنید:\n\n"
        "مثال: 'مشهد'"
    )
    
    return OPTION_B

def option_b_received(update: Update, context: CallbackContext) -> int:
    context.user_data['option_b'] = update.message.text
    
    update.message.reply_text(
        "گزینه ج را وارد کنید:\n\n"
        "مثال: 'اصفهان'"
    )
    
    return OPTION_C

def option_c_received(update: Update, context: CallbackContext) -> int:
    context.user_data['option_c'] = update.message.text
    
    update.message.reply_text(
        "گزینه د را وارد کنید:\n\n"
        "مثال: 'شیراز'"
    )
    
    return OPTION_D

def option_d_received(update: Update, context: CallbackContext) -> int:
    context.user_data['option_d'] = update.message.text
    
    keyboard = [
        [InlineKeyboardButton("الف", callback_data='A')],
        [InlineKeyboardButton("ب", callback_data='B')],
        [InlineKeyboardButton("ج", callback_data='C')],
        [InlineKeyboardButton("د", callback_data='D')],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    question_text = context.user_data['question_text']
    options = (
        f"الف) {context.user_data['option_a']}\n"
        f"ب) {context.user_data['option_b']}\n"
        f"ج) {context.user_data['option_c']}\n"
        f"د) {context.user_data['option_d']}"
    )
    
    update.message.reply_text(
        f"سوال: {question_text}\n\n{options}\n\n"
        "لطفا گزینه صحیح را انتخاب کنید:",
        reply_markup=reply_markup
    )
    
    return CORRECT_OPTION

def correct_option_received(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    
    context.user_data['correct_option'] = query.data
    
    query.edit_message_text(
        text=f"گزینه {query.data} به عنوان پاسخ صحیح انتخاب شد.\n\n"
             "آیا می‌خواهید توضیحی برای این سوال اضافه کنید؟ (اختیاری)\n\n"
             "مثال: 'تهران از سال 1200 پایتخت ایران بوده است.'\n\n"
             "اگر نمی‌خواهید توضیحی اضافه کنید، /skip را ارسال کنید."
    )
    
    return EXPLANATION

def explanation_received(update: Update, context: CallbackContext) -> int:
    context.user_data['explanation'] = update.message.text
    
    update.message.reply_text(
        "سطح دشواری سوال را از 1 تا 5 مشخص کنید:\n\n"
        "1 - بسیار آسان\n"
        "2 - آسان\n"
        "3 - متوسط\n"
        "4 - دشوار\n"
        "5 - بسیار دشوار\n\n"
        "پیش‌فرض: 3 (میانگین)"
    )
    
    return DIFFICULTY

def skip_explanation(update: Update, context: CallbackContext) -> int:
    context.user_data['explanation'] = ""
    
    update.message.reply_text(
        "سطح دشواری سوال را از 1 تا 5 مشخص کنید:\n\n"
        "1 - بسیار آسان\n"
        "2 - آسان\n"
        "3 - متوسط\n"
        "4 - دشوار\n"
        "5 - بسیار دشوار\n\n"
        "پیش‌فرض: 3 (میانگین)"
    )
    
    return DIFFICULTY

def difficulty_received(update: Update, context: CallbackContext) -> int:
    try:
        difficulty = int(update.message.text)
        if 1 <= difficulty <= 5:
            context.user_data['difficulty'] = difficulty
        else:
            raise ValueError
    except ValueError:
        update.message.reply_text(
            "لطفا عددی بین 1 تا 5 وارد کنید. پیش‌فرض 3 در نظر گرفته شد."
        )
        context.user_data['difficulty'] = 3
    
    categories = get_categories()
    if categories:
        keyboard = [
            [KeyboardButton(category)] for category in categories[:5]
        ]
        keyboard.append([KeyboardButton("دسته‌بندی جدید")])
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        
        update.message.reply_text(
            "لطفا یک دسته‌بندی انتخاب کنید یا 'دسته‌بندی جدید' را انتخاب نمایید:",
            reply_markup=reply_markup
        )
    else:
        update.message.reply_text(
            "لطفا دسته‌بندی این سوال را وارد کنید:\n\n"
            "مثال: 'جغرافیا' یا 'ریاضی'"
        )
    
    return CATEGORY

def category_received(update: Update, context: CallbackContext) -> int:
    context.user_data['category'] = update.message.text
    
    # Save the question to database
    add_question(update.effective_user.id, context.user_data)
    
    # Prepare question summary
    question_text = context.user_data['question_text']
    options = (
        f"الف) {context.user_data['option_a']}\n"
        f"ب) {context.user_data['option_b']}\n"
        f"ج) {context.user_data['option_c']}\n"
        f"د) {context.user_data['option_d']}"
    )
    correct_option = context.user_data['correct_option']
    explanation = context.user_data.get('explanation', 'بدون توضیح')
    difficulty = context.user_data.get('difficulty', 3)
    category = context.user_data['category']
    
    stars = '⭐' * difficulty + '☆' * (5 - difficulty)
    
    summary = (
        f"✅ سوال شما با موفقیت ثبت شد!\n\n"
        f"📝 سوال: {question_text}\n\n"
        f"🔹 گزینه‌ها:\n{options}\n\n"
        f"✅ پاسخ صحیح: {correct_option}\n"
        f"📖 توضیح: {explanation}\n"
        f"⚡ سطح دشواری: {stars}\n"
        f"🏷 دسته‌بندی: {category}\n\n"
        f"🙏 از مشارکت شما سپاسگزاریم!"
    )
    
    update.message.reply_text(summary)
    
    # Clear user data
    context.user_data.clear()
    
    return ConversationHandler.END

def quiz_command(update: Update, context: CallbackContext) -> None:
    categories = get_categories()
    
    if not categories:
        update.message.reply_text("هنوز هیچ سوالی در بانک وجود ندارد.")
        return
    
    keyboard = [
        [InlineKeyboardButton("سوال تصادفی", callback_data='random')]
    ] + [
        [InlineKeyboardButton(category, callback_data=f'category_{category}')]
        for category in categories[:5]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(
        "لطفا نوع سوال را انتخاب کنید:",
        reply_markup=reply_markup
    )

def quiz_question_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    if query.data == 'random':
        question = get_random_question()
    elif query.data.startswith('category_'):
        category = query.data.split('_', 1)[1]
        question = get_random_question(category)
    else:
        return
    
    if not question:
        query.edit_message_text("هیچ سوالی در این دسته‌بندی یافت نشد.")
        return
    
    keyboard = [
        [InlineKeyboardButton("الف", callback_data=f"answer_A_{question['question_id']}")],
        [InlineKeyboardButton("ب", callback_data=f"answer_B_{question['question_id']}")],
        [InlineKeyboardButton("ج", callback_data=f"answer_C_{question['question_id']}")],
        [InlineKeyboardButton("د", callback_data=f"answer_D_{question['question_id']}")],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    question_text = (
        f"📝 سوال:\n{question['question_text']}\n\n"
        f"الف) {question['option_a']}\n"
        f"ب) {question['option_b']}\n"
        f"ج) {question['option_c']}\n"
        f"د) {question['option_d']}\n\n"
        f"🏷 دسته‌بندی: {question['category']}\n"
        f"⚡ سطح دشواری: {'⭐' * question['difficulty'] + '☆' * (5 - question['difficulty'])}"
    )
    
    query.edit_message_text(
        text=question_text,
        reply_markup=reply_markup
    )

def answer_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    _, selected_option, question_id = query.data.split('_')
    question_id = int(question_id)
    
    conn = sqlite3.connect('quiz_bot.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT correct_option, explanation FROM questions WHERE question_id = ?
    ''', (question_id,))
    
    correct_option, explanation = cursor.fetchone()
    conn.close()
    
    if selected_option == correct_option:
        result_text = "✅ پاسخ شما صحیح است!"
    else:
        result_text = f"❌ پاسخ شما نادرست است. پاسخ صحیح: {correct_option}"
    
    explanation_text = f"\n\n📖 توضیح:\n{explanation}" if explanation else ""
    
    query.edit_message_text(
        text=query.message.text + f"\n\n{result_text}{explanation_text}"
    )

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        "عملیات اضافه کردن سوال لغو شد.",
        reply_markup=ReplyKeyboardRemove()
    )
    
    context.user_data.clear()
    return ConversationHandler.END

def error_handler(update: Update, context: CallbackContext) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    
    if update.effective_message:
        update.effective_message.reply_text(
            "⚠️ خطایی رخ داده است. لطفا دوباره امتحان کنید."
        )

def main() -> None:
    # Initialize database
    init_db()
    
    # Create the Updater and pass it your bot's token.
    updater = Updater(BOT_TOKEN)
    
    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    
    # Add conversation handler for adding questions
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('add_question', add_question_command)],
        states={
            QUESTION_TEXT: [MessageHandler(Filters.text & ~Filters.command, question_text_received)],
            OPTION_A: [MessageHandler(Filters.text & ~Filters.command, option_a_received)],
            OPTION_B: [MessageHandler(Filters.text & ~Filters.command, option_b_received)],
            OPTION_C: [MessageHandler(Filters.text & ~Filters.command, option_c_received)],
            OPTION_D: [MessageHandler(Filters.text & ~Filters.command, option_d_received)],
            CORRECT_OPTION: [CallbackQueryHandler(correct_option_received)],
            EXPLANATION: [
                MessageHandler(Filters.text & ~Filters.command, explanation_received),
                CommandHandler('skip', skip_explanation)
            ],
            DIFFICULTY: [MessageHandler(Filters.text & ~Filters.command, difficulty_received)],
            CATEGORY: [MessageHandler(Filters.text & ~Filters.command, category_received)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    dispatcher.add_handler(conv_handler)
    
    # Add command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("stats", stats_command))
    dispatcher.add_handler(CommandHandler("categories", categories_command))
    dispatcher.add_handler(CommandHandler("quiz", quiz_command))
    
    # Add callback query handlers
    dispatcher.add_handler(CallbackQueryHandler(quiz_question_handler, pattern='^(random|category_)'))
    dispatcher.add_handler(CallbackQueryHandler(answer_handler, pattern='^answer_'))
    
    # Add error handler
    dispatcher.add_error_handler(error_handler)
    
    # Start the Bot
    updater.start_polling()
    
    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()