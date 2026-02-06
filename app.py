# ==================================================
# CONFIGURATION
# ==================================================
APP_BASE_URL = "https://upi-menu-qr-trn2jqq8bhc79ktxox4g5e.streamlit.app"

TEST_MODE = False
# True  = Fake payment QR (testing)
# False = Real UPI QR (production)


# ==================================================
# IMPORTS
# ==================================================
import streamlit as st
import segno
import base64
import json
import io
from datetime import date


# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config("QR Menu", "📱", layout="centered")


# ==================================================
# CSS (CLASSIC CLEAN LOOK)
# ==================================================
st.markdown("""
<style>
.card {
    background:#ffffff;
    padding:14px;
    border-radius:10px;
    margin-bottom:10px;
    box-shadow:0 2px 8px rgba(0,0,0,0.06);
}
.row {
    display:flex;
    justify-content:space-between;
    font-size:16px;
}
.total {
    background:#f0fdf4;
    padding:14px;
    border-radius:10px;
    font-size:18px;
    font-weight:700;
    text-align:center;
}
.pay {
    margin-top:20px;
    padding:14px;
    border-radius:10px;
    background:#f8fafc;
    text-align:center;
}
.small {
    font-size:12px;
    color:gray;
}
</style>
""", unsafe_allow_html=True)


# ==================================================
# HELPERS
# ==================================================
def encode_data(data):
    return base64.urlsafe_b64encode(json.dumps(data).encode()).decode()

def decode_data(encoded):
    return json.loads(base64.urlsafe_b64decode(encoded.encode()).decode())

def generate_qr(data):
    qr = segno.make(data)
    buf = io.BytesIO()
    qr.save(buf, kind="png", scale=6)
    buf.seek(0)
    return buf

def generate_upi_qr(upi, amount):
    return generate_qr(f"upi://pay?pa={upi}&am={amount}")


# ==================================================
# ROUTING – CUSTOMER VIEW
# ==================================================
params = st.query_params
if "menu" in params:
    data = decode_data(params["menu"])

    st.title(data["shop"])
    st.write(f"📅 {data['date']}")
    st.divider()

    for item in data["items"]:
        st.markdown(f"""
        <div class="card">
            <div class="row">
                <div>{item['name']} × {item['qty']}</div>
                <div>₹ {item['amount']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"<div class='total'>Total: ₹ {data['total']}</div>", unsafe_allow_html=True)

    st.markdown("<div class='pay'><b>Pay Using UPI</b><br>", unsafe_allow_html=True)

    if TEST_MODE:
        st.image(generate_qr("TEST PAYMENT"), width=200)
        st.markdown("<div class='small'>TEST MODE – No real payment</div>", unsafe_allow_html=True)
    else:
        st.image(generate_upi_qr(data["upi"], data["total"]), width=200)
        st.markdown(f"<div class='small'>UPI: {data['upi']}</div>", unsafe_allow_html=True)

    st.stop()


# ==================================================
# SHOP OWNER PAGE
# ==================================================
st.title("📱 QR Menu Generator")

shop = st.text_input("Shop Name")
menu_date = st.date_input("Date", value=date.today())
upi = st.text_input("UPI ID / Mobile Number")

# ---------- ITEM LIST ----------
st.subheader("Menu Items")

if "items" not in st.session_state:
    st.session_state.items = []

col1, col2, col3 = st.columns(3)
name = col1.text_input("Item")
qty = col2.number_input("Qty", 1, 100, 1)
price = col3.number_input("Price", 1.0, 10000.0, 10.0)

if st.button("➕ Add Item"):
    st.session_state.items.append({
        "name": name,
        "qty": qty,
        "price": price,
        "amount": qty * price
    })

total = 0
for i, item in enumerate(st.session_state.items):
    total += item["amount"]
    st.markdown(f"• {item['name']} × {item['qty']} = ₹ {item['amount']}")

st.markdown(f"### Total: ₹ {total}")

# ---------- PAYMENT INFO ----------
if TEST_MODE:
    st.info("TEST MODE ENABLED – No real payment required")
else:
    st.success("REAL PAYMENT MODE ENABLED")


# ==================================================
# GENERATE QR
# ==================================================
if st.button("Generate Menu QR"):
    menu_data = {
        "shop": shop,
        "date": str(menu_date),
        "upi": upi,
        "items": st.session_state.items,
        "total": total
    }

    encoded = encode_data(menu_data)
    menu_url = f"{APP_BASE_URL}/?menu={encoded}"

    qr_img = generate_qr(menu_url)

    st.success("QR Generated")
    st.image(qr_img)
    st.download_button("⬇️ Download QR", qr_img, "menu_qr.png", "image/png")
    st.code(menu_url)
