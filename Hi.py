import os
import logging
import fitz  # pymupdf
import easyocr

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# ============ CONFIG ============
TOKEN = os.getenv("TOKEN", "")

DPI = 300
# ================================

logging.basicConfig(level=logging.ERROR)

reader = easyocr.Reader(['hi'], gpu=False, verbose=False)

async def pdf_to_hindi_txt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        doc = update.message.document

        if not doc.file_name.lower().endswith(".pdf"):
            await update.message.reply_text("❌ Sirf PDF bheje")
            return

        chat_id = update.message.chat_id
        pdf_path = f"{chat_id}.pdf"
        txt_path = f"{chat_id}.txt"

        tg_file = await doc.get_file()
        await tg_file.download_to_drive(pdf_path)

        await update.message.reply_text("⚡ OCR start...")

        pdf = fitz.open(pdf_path)
        full_text = ""

        for page_no, page in enumerate(pdf, start=1):
            pix = page.get_pixmap(dpi=DPI)
            img_path = f"{chat_id}_{page_no}.png"
            pix.save(img_path)

            results = reader.readtext(img_path, detail=0)

            full_text += f"\n===== Page {page_no} =====\n"
            for line in results:
                full_text += line + "\n"

            os.remove(img_path)

        pdf.close()

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(full_text)

        await update.message.reply_document(
            document=open(txt_path, "rb"),
            caption="✅ Hindi TXT ready (FAST OCR)"
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        if os.path.exists(txt_path):
            os.remove(txt_path)

# ============ MAIN ============
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.Document.PDF, pdf_to_hindi_txt))
    print("🤖 Fast OCR Bot Running...")
    app.run_polling()
