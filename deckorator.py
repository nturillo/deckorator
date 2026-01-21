import math
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter, PathCompleter
from PIL import Image, ImageDraw
import argparse
import os

# Common paper sizes in inches (width, height)
PAPER_SIZES = {
    "letter": (8.5, 11.0),
    "legal": (8.5, 14.0),
    "tabloid": (11.0, 17.0),
    "a0": (33.1, 46.8),
    "a1": (23.4, 33.1),
    "a2": (16.5, 23.4),
    "a3": (11.7, 16.5),
    "a4": (8.27, 11.7),
    "a5": (5.83, 8.27),
    "a6": (4.13, 5.83),
    "b0": (39.4, 55.7),
    "b1": (27.8, 39.4),
    "b2": (19.7, 27.8),
    "b3": (13.9, 19.7),
    "b4": (9.84, 13.9),
    "b5": (6.93, 9.84),
}

DPI = 300
GUIDE_WIDTH = 5
CARD_BACK="dots.png"
CARD_W_IN, CARD_H_IN = 2.48031, 3.46457  # MTG card size

def main():
    parser = argparse.ArgumentParser(description="Make proxy sheets from card PNGs")
    parser.add_argument(
        "--paper",
        default="letter",
        choices=PAPER_SIZES.keys(),
        help="Paper size (default: letter)",
    )
    parser.add_argument(
        "--output",
        default="proxies.pdf",
        help="Output PDF file (default: proxies.pdf)",
    )
    args = parser.parse_args()
    
    folder = prompt(
        "Directory of card jpgs: ",
        completer=PathCompleter(only_directories=True, expanduser=True),
    )

    folder = os.path.abspath(os.path.expanduser(folder))

    if not os.path.isdir(folder):
        raise ValueError(f"Folder does not exist: {folder}")

    page_w_in, page_h_in = PAPER_SIZES[args.paper]
    page_w = int(page_w_in * DPI)
    page_h = int(page_h_in * DPI)
    card_w = int(CARD_W_IN * DPI)
    card_h = int(CARD_H_IN * DPI)

    cols = page_w // card_w
    rows = page_h // card_h

    buffer_h = (page_h - card_h * rows) // 2
    buffer_w = (page_w - card_w * cols) // 2

    files = sorted(f for f in os.listdir(folder) if f.lower().endswith(".jpg"))

    if not files:
        raise ValueError("No JPG files found in folder")

    #remove double sided cards
    double_sided = set()
    new_files = []
    file_set = set(files)  # for quick lookup
    for f in files:
        if f.endswith("_back.jpg"):
            front = f[:-9] + ".jpg"  # remove "_back" and add .jpg
            if front in file_set:
                double_sided.add(front)
                continue  # skip adding the _back file itself
        new_files.append(f)
    files = new_files
    
    #card backs
    card_back_sheet = Image.new("RGB", (page_w, page_h), "white")
    for r in range(rows):
       y = r * card_h + buffer_h
       for c in range(cols):
           img = Image.open("card_backs/" + CARD_BACK)
           img = img.resize((card_w, card_h), Image.LANCZOS)
           card_back_sheet.paste(img, (c * card_w + buffer_w, r * card_h + buffer_h))
    draw = ImageDraw.Draw(card_back_sheet)
    for r in range(rows + 1):
        y = r * card_h + buffer_h
        draw.line([(0, y), (page_w, y)], fill="black", width=GUIDE_WIDTH)
    for c in range(cols + 1):
        x = c * card_w + buffer_w
        draw.line([(x, 0), (x, page_h)], fill="black", width=GUIDE_WIDTH)
    card_back_sheet = card_back_sheet.transpose(Image.FLIP_LEFT_RIGHT)

    pages = []
    i = 0
    while i < len(files):
        sheet = Image.new("RGB", (page_w, page_h), "white")
        back_sheet = card_back_sheet.copy()

        for r in range(rows):
            y = r * card_h + buffer_h
            for c in range(cols):
                if i >= len(files):
                    break
                img = Image.open(os.path.join(folder, files[i]))
                img = img.resize((card_w, card_h), Image.LANCZOS)
                sheet.paste(img, (c * card_w + buffer_w, r * card_h + buffer_h))
                
                if files[i] in double_sided:
                    back_img = Image.open(os.path.join(folder, files[i][:-4] + "_back.jpg"))
                    back_img = back_img.resize((card_w, card_h), Image.LANCZOS)
                    back_img = back_img.transpose(Image.FLIP_LEFT_RIGHT)
                    back_sheet.paste(back_img, ((cols - 1 - c) * card_w + buffer_w, r * card_h + buffer_h))
                i += 1

        # add guidelines
        draw = ImageDraw.Draw(sheet)
        for r in range(rows + 1):
            y = r * card_h + buffer_h
            draw.line([(0, y), (page_w, y)], fill="black", width=GUIDE_WIDTH)
        for c in range(cols + 1):
            x = c * card_w + buffer_w
            draw.line([(x, 0), (x, page_h)], fill="black", width=GUIDE_WIDTH)
        pages.append(sheet)
        pages.append(back_sheet)

    # Save PDF
    pages[0].save(
        args.output,
        save_all=True,
        append_images=pages[1:],
        resolution=DPI,
    )

    print(f"Saved {args.output} with {len(pages)} page(s) on {args.paper} paper.")


if __name__ == "__main__":
    main()