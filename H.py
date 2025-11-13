from telegram import Update, Poll
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CommandHandler, ContextTypes
import csv
import tempfile
import os

BOT_TOKEN = "7877886995:AAH_w_RZ-bzKZl2buaPNGg0N93NKFTWsdXs"  # Replace with your token


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send CSV or Anonymous Poll. I will convert into TXT format."
    )


async def handle_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.document.get_file()

    csv_file = tempfile.mktemp(suffix=".csv")
    txt_file = tempfile.mktemp(suffix=".txt")

    await file.download_to_drive(csv_file)

    with open(csv_file, "r", encoding="utf-8") as f, open(txt_file, "w", encoding="utf-8") as out:
        reader = csv.DictReader(f)

        for idx, row in enumerate(reader, start=1):
            out.write(f"{idx}. {row['Question']}\n")
            out.write(f"A. {row['Option A']}\n")
            out.write(f"B. {row['Option B']}\n")
            out.write(f"C. {row['Option C']}\n")
            out.write(f"D. {row['Option D']}\n")
            out.write(f"{row['Answer']}\n")   # Answer NUMBER
            out.write(f"{row.get('Description', '').strip()}\n\n")

    await update.message.reply_document(open(txt_file, "rb"))

    os.remove(csv_file)
    os.remove(txt_file)


async def poll_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # Poll message hamesha update.message.poll me hota hai
    poll = update.message.poll

    if poll is None:
        return  # safety check

    if poll.type != "quiz":
        return  # Only quiz poll allowed

    txt_file = tempfile.mktemp(suffix=".txt")

    with open(txt_file, "w", encoding="utf-8") as out:
        out.write(f"1. {poll.question}\n")
        out.write(f"A. {poll.options[0].text}\n")
        out.write(f"B. {poll.options[1].text}\n")
        out.write(f"C. {poll.options[2].text}\n")
        out.write(f"D. {poll.options[3].text}\n")

        # Answer index number
        answer_index = poll.correct_option_id + 1
        out.write(f"{answer_index}\n")

        # Description blank (as requested)
        out.write("\n")

    await update.message.reply_document(document=open(txt_file, "rb"))
    os.remove(txt_file)



def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.FileExtension("csv"), handle_csv))
    app.add_handler(MessageHandler(filters.POLL, poll_handler))


    print("Bot Running...")
    app.run_polling()


if __name__ == "__main__":
    main()
