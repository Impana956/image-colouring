from flask import Flask, render_template, request, send_from_directory, flash, redirect
import os
import fitz  # PyMuPDF

app = Flask(__name__)
app.secret_key = "your_secret_key"

UPLOAD_FOLDER = "uploads"
CONVERTED_FOLDER = "converted"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CONVERTED_FOLDER'] = CONVERTED_FOLDER

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("file")
        format_choice = request.form.get("format")
        pdf_img_format = request.form.get("pdf_img_format", "jpg")

        if not file or file.filename == '':
            flash("No file selected.")
            return redirect(request.url)

        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        base_name, ext = os.path.splitext(filename)
        ext = ext.lower()

        try:
            if ext == ".pdf" and format_choice in ["jpg", "png"]:
                # Convert PDF to image using PyMuPDF
                doc = fitz.open(filepath)
                output_filename = f"{base_name}.{pdf_img_format}"
                output_path = os.path.join(app.config['CONVERTED_FOLDER'], output_filename)

                page = doc.load_page(0)
                pix = page.get_pixmap()
                pix.save(output_path)

                return render_template("index.html", paths=[output_filename])

            elif format_choice == "pdf":
                # Convert image to PDF using Pillow and img2pdf with compression
                from PIL import Image as PILImage
                import img2pdf

                img = PILImage.open(filepath).convert("RGB")

                # Resize to reduce file size
                MAX_WIDTH, MAX_HEIGHT = 1024, 1024
                img.thumbnail((MAX_WIDTH, MAX_HEIGHT))

                # Save as compressed JPEG
                temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{base_name}_temp.jpg")
                img.save(temp_path, format="JPEG", quality=60, optimize=True)

                # Convert to PDF
                output_pdf_path = os.path.join(app.config['CONVERTED_FOLDER'], f"{base_name}.pdf")
                with open(output_pdf_path, "wb") as f:
                    f.write(img2pdf.convert(temp_path))

                os.remove(temp_path)
                return render_template("index.html", paths=[f"{base_name}.pdf"])

            else:
                # Convert image to JPG or PNG
                from PIL import Image

                img = Image.open(filepath).convert("RGBA")
                white_bg = Image.new("RGB", img.size, (255, 255, 255))
                alpha = img.getchannel("A")
                white_bg.paste(img, mask=alpha)

                output_filename = f"{base_name}.{format_choice}"
                output_path = os.path.join(app.config['CONVERTED_FOLDER'], output_filename)

                if format_choice == "jpg":
                    white_bg.save(output_path, "JPEG", quality=70, optimize=True)
                elif format_choice == "png":
                    white_bg.save(output_path, "PNG", compress_level=9)

                return render_template("index.html", paths=[output_filename])

        except Exception as e:
            flash(f"Error during conversion: {str(e)}")
            return redirect(request.url)

    return render_template("index.html", paths=None)

@app.route("/converted/<filename>")
def download_file(filename):
    return send_from_directory(app.config['CONVERTED_FOLDER'], filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
