from flask import Flask, render_template_string, request, send_file
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from zoneinfo import ZoneInfo
import random, os, io

app = Flask(__name__)

# Paths for images and fonts (in same folder as this script)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OPAY_TEMPLATE = os.path.join(BASE_DIR, "opay.jpg")
MON_TEMPLATE = os.path.join(BASE_DIR, "mon.jpg")
ROBOTO_BOLD = os.path.join(BASE_DIR, "Roboto-Bold.ttf")
ROBOTO_REGULAR = os.path.join(BASE_DIR, "Roboto-Regular.ttf")

css_style = """
<style>
body {
    font-family: Arial, sans-serif;
    text-align: center;
    background: linear-gradient(270deg, red, orange, yellow, green, blue, indigo, violet);
    background-size: 1400% 1400%;
    animation: gradientBG 20s ease infinite;
    color: white;
    margin: 0; padding: 0;
}
@keyframes gradientBG {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
.container { margin-top: 100px; }
.glow-text {
    font-size: 3em;
    text-shadow: 0 0 10px white, 0 0 20px yellow, 0 0 40px cyan;
}
.buttons { margin-top: 50px; }
.rainbow-button {
    padding: 15px 40px;
    font-size: 1.5em;
    text-decoration: none;
    color: white;
    border-radius: 30px;
    background: linear-gradient(45deg, red, orange, yellow, green, blue, indigo, violet);
    box-shadow: 0 0 20px white, 0 0 30px yellow;
    transition: transform 0.2s, box-shadow 0.2s;
}
.rainbow-button:hover {
    transform: scale(1.1);
    box-shadow: 0 0 40px white, 0 0 60px cyan;
}
form {
    background: rgba(255,255,255,0.1);
    padding: 20px;
    border-radius: 20px;
    display: inline-block;
    box-shadow: 0 0 20px white, 0 0 30px cyan;
    margin-top: 20px;
}
input {
    padding: 10px;
    margin: 10px;
    border-radius: 10px;
    border: none;
    width: 250px;
    font-size: 1em;
}
button {
    padding: 10px 20px;
    border: none;
    border-radius: 10px;
    background: linear-gradient(45deg, red, orange, yellow, green, blue, indigo, violet);
    color: white;
    font-size: 1em;
    cursor: pointer;
    margin-top: 10px;
}
button:hover {
    transform: scale(1.1);
}
</style>
"""

def load_font(style, size):
    try:
        if style.lower() == "bold":
            return ImageFont.truetype(ROBOTO_BOLD, size)
        else:
            return ImageFont.truetype(ROBOTO_REGULAR, size)
    except Exception:
        return ImageFont.load_default()

@app.route("/")
def index():
    return render_template_string(f"""
    <!DOCTYPE html>
    <html>
    <head><title>Choose Receipt Type</title>{css_style}</head>
    <body>
        <div class="container">
            <h1 class="glow-text">Choose Your Receipt Type</h1>
            <div class="buttons">
                <a href="/opay" class="rainbow-button">OPay</a>
                <a href="/moniepoint" class="rainbow-button">Moniepoint</a>
            </div>
        </div>
    </body>
    </html>
    """)

@app.route("/opay", methods=["GET", "POST"])
def opay_form():
    if request.method == "POST":
        A = request.form.get("amount", "").strip()
        N = request.form.get("recipient_name", "").strip().upper()
        B = request.form.get("recipient_bank", "").strip().upper()
        C = request.form.get("recipient_account", "").strip()
        S = request.form.get("sender_name", "").strip().upper()
        O = request.form.get("opay_number", "").strip()

        if not all([A, N, B, C, S]):
            return "<h2 style='color:white;'>Missing required fields.</h2>", 400
        if not os.path.exists(OPAY_TEMPLATE):
            return f"<h2 style='color:white;'>OPay template image not found at {OPAY_TEMPLATE}</h2>", 500

        try:
            img = Image.open(OPAY_TEMPLATE).convert("RGB")
            d = ImageDraw.Draw(img)
            f = lambda s, z: load_font(s, z)

            if C.isdigit() and len(C) == 11:
                C = f"{C[:3]} {C[3:6]} {C[6:]}"
            
            # Mask Opay number in sender info
            if O and len(O) >= 6:
                M = f"Opay | {O[:3]}****{O[-3:]}"
            else:
                M = "Opay"
            
            now = datetime.now()
            sfx = lambda d: "th" if 11 <= d <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(d % 10, "th")
            dt = now.strftime(f"%b {now.day}{sfx(now.day)}, %Y %H:%M:%S")
            tx = ''.join(str(random.randint(0, 9)) for _ in range(30))

            amt_val = int(float(A))
            amt = f"₦{amt_val:,}.00"
            ax = (img.width - d.textlength(amt, f("Bold", 46))) // 2
            d.text((ax, 190), amt, font=f("Bold", 46), fill=(29, 207, 159))

            dx = (img.width - d.textlength(dt, f("Regular", 20))) // 2
            d.text((dx, 300), dt, font=f("Regular", 20), fill="black")

            R = lambda t, y, fo: d.text((img.width - 40 - d.textlength(t, fo), y), t, font=fo, fill="black")
            R(N, 380, f("Bold", 24))
            R(f"{B} | {C}", 420, f("Regular", 24))
            R(S, 490, f("Bold", 24))
            R(M, 530, f("Regular", 24))
            R(tx, 600, f("Regular", 26))

            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            return send_file(buf, as_attachment=True, download_name="opay_receipt.png", mimetype="image/png")
        except Exception as e:
            return f"<h2 style='color:white;'>Error: {e}</h2>", 500

    return render_template_string(f"""
    <!DOCTYPE html>
    <html>
    <head><title>OPay Form</title>{css_style}</head>
    <body>
        <h1 class="glow-text">OPay Receipt</h1>
        <form method="POST">
            <input type="number" step="0.01" name="amount" placeholder="Amount (₦)" required><br>
            <input type="text" name="recipient_name" placeholder="Recipient Name" required><br>
            <input type="text" name="recipient_bank" placeholder="Recipient Bank" required><br>
            <input type="text" name="recipient_account" placeholder="Recipient Account Number" required><br>
            <input type="text" name="sender_name" placeholder="Sender Name" required><br>
            <input type="text" name="opay_number" placeholder="Opay Number (optional)"><br>
            <button type="submit">Generate OPay Receipt</button>
        </form>
    </body>
    </html>
    """)

@app.route("/moniepoint", methods=["GET", "POST"])
def moniepoint_form():
    if request.method == "POST":
        A = request.form.get("amount", "").strip()
        N = request.form.get("recipient_name", "").strip().upper()
        B = request.form.get("recipient_bank", "").strip().title()
        C = request.form.get("recipient_account", "").strip()
        S = request.form.get("sender_name", "").strip().upper()

        if not all([A, N, B, C, S]):
            return "<h2 style='color:white;'>Missing required fields.</h2>", 400
        if not os.path.exists(MON_TEMPLATE):
            return f"<h2 style='color:white;'>Moniepoint template image not found at {MON_TEMPLATE}</h2>", 500

        try:
            img = Image.open(MON_TEMPLATE).convert("RGB")
            print(f"Loaded moniepoint image size: {img.size}")  # Debug print

            d = ImageDraw.Draw(img)
            f = lambda s, z=20: load_font(s, z)

            T = ''.join(str(random.randint(0, 9)) for _ in range(30))
            now = datetime.now(ZoneInfo("Africa/Lagos"))
            D = now.strftime("%A, %B %d, %Y | %I:%M %p").replace(" 0", " ")

            amt_val = int(float(A))
            d.text((50, 210), f"₦{amt_val:,}.00", font=f("Bold", 46), fill=(0, 0, 0))
            d.text((72, 460), f"{N} | {C}", font=f("Regular"), fill=(0, 0, 0))
            d.text((72, 560), B, font=f("Regular"), fill=(0, 0, 0))
            d.text((72, 660), S, font=f("Regular"), fill=(0, 0, 0))
            d.text((72, 750), "MONIEPOINT", font=f("Regular"), fill=(0, 0, 0))
            d.text((72, 840), D, font=f("Regular"), fill=(0, 0, 0))
            d.text((72, 940), T, font=f("Regular"), fill=(0, 0, 0))
            d.text((72, 1020), S, font=f("Regular"), fill=(0, 0, 0))

            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            return send_file(buf, as_attachment=True, download_name="moniepoint_receipt.png", mimetype="image/png")
        except Exception as e:
            print("Error generating moniepoint receipt:", e)
            return f"<h2 style='color:white;'>Error generating receipt: {e}</h2>", 500

    return render_template_string(f"""
    <!DOCTYPE html>
    <html>
    <head><title>Moniepoint Form</title>{css_style}</head>
    <body>
        <h1 class="glow-text">Moniepoint Receipt</h1>
        <form method="POST">
            <input type="number" step="0.01" name="amount" placeholder="Amount (₦)" required><br>
            <input type="text" name="recipient_name" placeholder="Recipient Name" required><br>
            <input type="text" name="recipient_bank" placeholder="Recipient Bank" required><br>
            <input type="text" name="recipient_account" placeholder="Recipient Account Number" required><br>
            <input type="text" name="sender_name" placeholder="Sender Name" required><br>
            <button type="submit">Generate Moniepoint Receipt</button>
        </form>
    </body>
    </html>
    """)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
