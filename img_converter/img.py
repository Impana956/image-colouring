from flask import Flask, render_template, request, send_from_directory, flash, redirect
import os
import fitz  # PyMuPDF
from PIL import Image
import io
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "your_secret_key"

UPLOAD_FOLDER = "uploads"
CONVERTED_FOLDER = "converted"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CONVERTED_FOLDER'] = CONVERTED_FOLDER

MAX_SIZE_KB = 50

def compress_image(input_image, output_path, format_choice):
    quality = 85 if format_choice == "jpg" else None
    compress_level = 9 if format_choice == "png" else None

    img = input_image.convert("RGBA")
    white_bg = Image.new("RGB", img.size, (255, 255, 255))
    alpha = img.getchannel("A")
    white_bg.paste(img, mask=alpha)

    buffer = io.BytesIO()

    if format_choice == "jpg":
        while quality > 10:
            buffer.seek(0)
            buffer.truncate(0)
            white_bg.save(buffer, format="JPEG", quality=quality, optimize=True)
            size_kb = buffer.tell() / 1024
            if size_kb <= MAX_SIZE_KB:
                break
            quality -= 5
    elif format_choice == "png":
        while compress_level >= 0:
            buffer.seek(0)
            buffer.truncate(0)
            white_bg.save(buffer, format="PNG", compress_level=compress_level, optimize=True)
            size_kb = buffer.tell() / 1024
            if size_kb <= MAX_SIZE_KB:
                break
            compress_level -= 1

    with open(output_path, "wb") as f:
        f.write(buffer.getvalue())

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("file")
        format_choice = request.form.get("format")
        desired_name = request.form.get("filename", "converted_file")
        pdf_img_format = request.form.get("pdf_img_format", "jpg")

        if not file or file.filename == '':
            flash("No file selected.")
            return redirect(request.url)

        filename = secure_filename(file.filename)
        desired_name = secure_filename(desired_name)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        base_name, ext = os.path.splitext(filename)
        ext = ext.lower()

        try:
            if ext == ".pdf" and format_choice in ["jpg", "png"]:
                doc = fitz.open(filepath)
                page = doc.load_page(0)
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                output_filename = f"{desired_name}.{pdf_img_format}"
                output_path = os.path.join(app.config['CONVERTED_FOLDER'], output_filename)
                compress_image(img, output_path, pdf_img_format)

                return render_template("index.html", paths=[output_filename])

            elif format_choice == "pdf":
                from PIL import Image as PILImage
                import img2pdf

                img = PILImage.open(filepath).convert("RGB")
                temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{desired_name}_temp.jpg")
                img.save(temp_path, quality=85, optimize=True)

                output_pdf_path = os.path.join(app.config['CONVERTED_FOLDER'], f"{desired_name}.pdf")
                with open(output_pdf_path, "wb") as f:
                    f.write(img2pdf.convert(temp_path))

                os.remove(temp_path)
                return render_template("index.html", paths=[f"{desired_name}.pdf"])

            else:
                img = Image.open(filepath)
                output_filename = f"{desired_name}.{format_choice}"
                output_path = os.path.join(app.config['CONVERTED_FOLDER'], output_filename)

                compress_image(img, output_path, format_choice)

                return render_template("index.html", paths=[output_filename])

        except Exception as e:
            flash(f"Error during conversion: {str(e)}")
            return redirect(request.url)

    return render_template("index.html", paths=None)

@app.route("/converted/<filename>")
def download_file(filename):
    user_friendly_name = request.args.get("download_as", filename)
    return send_from_directory(
        app.config['CONVERTED_FOLDER'],
        filename,
        as_attachment=True,
        download_name=user_friendly_name
    )

if __name__ == "__main__":
    app.run(debug=True)
