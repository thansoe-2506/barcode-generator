import os
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import barcode
from barcode.writer import ImageWriter
from fpdf import FPDF

# === Config ===
CSV_FILE = 'source/items2.csv'
OUTPUT_DIR = 'barcodes'
FINAL_PDF = 'barcodes_table_format.pdf'
FONT_SIZE = 24
BOTTOM_PADDING = 40  # Space below text

# PDF Layout
COLUMNS = 3
ROWS_PER_PAGE = 5
PAGE_WIDTH_MM = 210
PAGE_HEIGHT_MM = 297
MARGIN_MM = 10
CELL_SPACING_MM = 5

# Fonts (make sure these font files are in the correct directory)
BURMESE_FONT_PATH = 'fonts/Noto_Sans_Myanmar/NotoSansMyanmar-Regular.ttf'
LATIN_FONT_PATH = 'fonts/Noto_Sans/static/NotoSans-Regular.ttf'

# === Helpers ===
def is_burmese(char):
    return 'က' <= char <= '႟' or 'ꩠ' <= char <= 'ꩿ'

def draw_text_dual_font(draw, position, text, burmese_font, latin_font, fill="black"):
    x, y = position
    for char in text:
        font = burmese_font if is_burmese(char) else latin_font
        draw.text((x, y), char, font=font, fill=fill)
        x += draw.textlength(char, font=font)

def wrap_text(text, font, max_width):
    lines = []
    words = text.split()
    current_line = ""
    dummy_draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))

    for word in words:
        test_line = f"{current_line} {word}".strip()
        if dummy_draw.textlength(test_line, font=font) <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines

# === Main Processing ===
os.makedirs(OUTPUT_DIR, exist_ok=True)

try:
    df = pd.read_csv(CSV_FILE, header=None, names=["item_code", "barcode_number", "item_name"])
except Exception as e:
    raise RuntimeError(f"❌ Failed to load CSV file '{CSV_FILE}': {e}")

try:
    burmese_font = ImageFont.truetype(BURMESE_FONT_PATH, FONT_SIZE)
    latin_font = ImageFont.truetype(LATIN_FONT_PATH, FONT_SIZE)
except Exception as e:
    print(f"⚠ Font loading failed: {e}. Using default font.")
    burmese_font = latin_font = ImageFont.load_default()

font = latin_font
final_images = []

for index, row in df.iterrows():
    item_code = str(row['item_code']).strip()
    barcode_number = str(row['barcode_number']).strip()
    item_name = str(row['item_name']).strip().replace('\n', ' ')

    try:
        BARCODE_CLASS = barcode.get_barcode_class('code128')
        barcode_obj = BARCODE_CLASS(barcode_number, writer=ImageWriter())
        barcode_path = barcode_obj.save(os.path.join(OUTPUT_DIR, item_code))

        img = Image.open(barcode_path)

        wrapped_lines = wrap_text(item_name, font, img.width - 20)
        line_height = font.getbbox("Ay")[3] - font.getbbox("Ay")[1]
        total_text_height = line_height * len(wrapped_lines) + BOTTOM_PADDING

        new_img = Image.new("RGB", (img.width, img.height + total_text_height), "white")
        new_img.paste(img, (0, 0))

        draw = ImageDraw.Draw(new_img)
        y_text = img.height + 5

        for line in wrapped_lines:
            line_width = sum(draw.textlength(c, font=burmese_font if is_burmese(c) else latin_font) for c in line)
            x_text = (img.width - line_width) // 2
            draw_text_dual_font(draw, (x_text, y_text), line, burmese_font, latin_font)
            y_text += line_height

        final_path = os.path.join(OUTPUT_DIR, f"{item_code}_with_text.png")
        new_img.save(final_path)
        final_images.append(final_path)

        print(f"✔ Created barcode: {final_path}")
    except Exception as e:
        print(f"❌ Failed to process item '{item_code}': {e}")

# === Export to PDF in grid layout ===
if final_images:
    pdf = FPDF(unit="mm", format="A4")
    pdf.add_page()
    cell_width = (PAGE_WIDTH_MM - 2 * MARGIN_MM - (COLUMNS - 1) * CELL_SPACING_MM) / COLUMNS
    cell_height = (PAGE_HEIGHT_MM - 2 * MARGIN_MM - (ROWS_PER_PAGE - 1) * CELL_SPACING_MM) / ROWS_PER_PAGE

    x_start = MARGIN_MM
    y_start = MARGIN_MM
    x = x_start
    y = y_start
    count = 0

    for image_file in final_images:
        if count > 0 and count % (COLUMNS * ROWS_PER_PAGE) == 0:
            pdf.add_page()
            x = x_start
            y = y_start

        pdf.image(image_file, x=x, y=y, w=cell_width, h=cell_height)
        count += 1
        x += cell_width + CELL_SPACING_MM

        if count % COLUMNS == 0:
            x = x_start
            y += cell_height + CELL_SPACING_MM

    pdf.output(FINAL_PDF)
    print(f"\n✅ All barcodes combined into table format PDF: {FINAL_PDF}")
else:
    print("⚠ No barcodes generated.")
