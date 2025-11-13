import csv
import io
import os
import tempfile
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters


# ✅ /csvpoll command
async def start_csv_poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📂 Send a *CSV file* or paste CSV-style text directly (MCQs).\n"
        "I will convert it into a `.txt` file format.",
        parse_mode="Markdown"
    )


# ✅ Convert CSV rows → formatted text
def convert_csv_to_text(reader):
    output = io.StringIO()
    for idx, row in enumerate(reader, start=1):
        # Handle both header & no-header CSVs
        if isinstance(row, dict):
            q = row.get('Question', '').strip() or row.get('', '').strip()
            a = row.get('Option A', '').strip() or row.get('A', '').strip()
            b = row.get('Option B', '').strip() or row.get('B', '').strip()
            c = row.get('Option C', '').strip() or row.get('C', '').strip()
            d = row.get('Option D', '').strip() or row.get('D', '').strip()
            ans = row.get('Answer', '').strip() or row.get('ans', '').strip()
            desc = row.get('Description', '').strip() or '@SecondCoaching'
        else:
            # For files with no header row
            q, a, b, c, d, ans, *desc = row + [""] * (7 - len(row))
            desc = desc[0].strip() if desc else "@SecondCoaching"

        output.write(f"{idx}. {q}\n")
        output.write(f"A. {a}\n")
        output.write(f"B. {b}\n")
        output.write(f"C. {c}\n")
        output.write(f"D. {d}\n")
        output.write(f"Answer: {ans}\n")
        output.write(f"{desc or '@SecondCoaching'}\n\n")

    return output.getvalue()


# ✅ Handle CSV File
async def handle_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.document.get_file()
    csv_path = tempfile.mktemp(suffix=".csv")
    txt_path = tempfile.mktemp(suffix=".txt")
    await file.download_to_drive(csv_path)

    with open(csv_path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    try:
        # Try reading with headers
        f = io.StringIO(content)
        reader = csv.DictReader(f)
        if reader.fieldnames is None or reader.fieldnames[0].startswith("Question") is False:
            # Force as normal rows if no headers
            f.seek(0)
            reader = csv.reader(f)
        text_output = convert_csv_to_text(reader)
    except Exception:
        # Fallback to simple line split
        f = io.StringIO(content)
        reader = csv.reader(f)
        text_output = convert_csv_to_text(reader)

    with open(txt_path, "w", encoding="utf-8") as out:
        out.write(text_output)

    await update.message.reply_document(open(txt_path, "rb"))

    os.remove(csv_path)
    os.remove(txt_path)


# ✅ Handle text message (CSV-style text)
async def handle_text_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if "," not in text:
        return  # ignore normal text

    txt_path = tempfile.mktemp(suffix=".txt")

    f = io.StringIO(text)
    reader = csv.reader(f)
    text_output = convert_csv_to_text(reader)

    with open(txt_path, "w", encoding="utf-8") as out:
        out.write(text_output)

    await update.message.reply_document(open(txt_path, "rb"))
    os.remove(txt_path)


# ✅ Handle Poll → TXT
async def handle_poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    poll = update.message.poll
    if not poll or poll.type != "quiz":
        return

    txt_file = tempfile.mktemp(suffix=".txt")
    with open(txt_file, "w", encoding="utf-8") as out:
        out.write(f"1. {poll.question}\n")
        for i, opt in enumerate(poll.options):
            out.write(f"{chr(65+i)}. {opt.text}\n")

        correct_letter = chr(65 + poll.correct_option_id)
        out.write(f"Answer: {correct_letter}\n")
        out.write("@SecondCoaching\n\n")

    await update.message.reply_document(open(txt_file, "rb"))
    os.remove(txt_file)


# ✅ Register handlers
def setup_csv_poll_handlers(application):
    application.add_handler(CommandHandler("csvpoll", start_csv_poll))
    application.add_handler(MessageHandler(filters.Document.FileExtension("csv"), handle_csv))
    application.add_handler(MessageHandler(filters.POLL, handle_poll))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_csv))
