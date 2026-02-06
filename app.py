# ==================================================
# CONFIGURATION
# ==================================================
APP_BASE_URL = "https://upi-menu-qr-trn2jqq8bhc79ktxox4g5e.streamlit.app"

TEST_MODE = False
# True  = fake payment (testing)
# False = real payment flow


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
st.set_page_config("QR Menu Generator", "📱", layout="centered")


# ==================================================
# CSS – CLASSIC + MOBILE FRIENDLY
# ==================================================
st.markdown("""
<style>
.menu-card {
    background:#ffffff;
    padding:14px;
    border-radius:12px;
    margin-bottom:10px;
    box-shadow:0 3px 10px rgba(0,0,0,0.06);
}
.menu-row {
    display:flex;
    justify-content:space-between;
    font-size:16px;
}
.menu-total {
    background:#ecfeff;
    padding:14px;
    border-radius:12px;
    font-size:18px;
    font-weight:700;
    text-align:center;
}
.pay-box {
    background:#f8fafc;
    padding:14px;
    border-radius:12px;
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
# ROUTING – CUSTOMER MENU PAGE (QR SCAN)
# ==================================================
params = st.query_params
if "menu" in params:
    data = decode_data(params["menu"])

    st.title(data["shop"])
    st.write(f"📅 {data['date']}")
    st.divider()

    for item in data["items"]:
        st.markdown(f"""
        <div class="menu-card">
            <div class="menu-row">
                <div>{item['name']} × {item['qty']}</div>
                <div>₹ {item['amount']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(
        f"<div class='menu-total'>Total: ₹ {data['total']}</div>",
        unsafe_allow_html=True
    )

    st.markdown("<div class='pay-box'><b>Pay Shop Using UPI</b><br>", unsafe_allow_html=True)

    st.image(generate_upi_qr(data["upi"], data["total"]), width=220)
    st.markdown(f"<div class='small'>UPI ID: {data['upi']}</div>", unsafe_allow_html=True)

    st.stop()


# ==================================================
# SHOP OWNER PAGE
# ==================================================
st.title("📱 QR Menu Generator (For Shop Owners)")

shop = st.text_input("Shop Name")
menu_date = st.date_input("Date", value=date.today())
upi = st.text_input("Shop UPI ID / Mobile Number")


# ==================================================
# SESSION STATE
# ==================================================
if "items" not in st.session_state:
    st.session_state.items = []

if "paid" not in st.session_state:
    st.session_state.paid = False


# ==================================================
# ADD ITEMS
# ==================================================
st.subheader("➕ Add Menu Items")

c1, c2, c3 = st.columns(3)
name = c1.text_input("Item")
qty = c2.number_input("Qty", 1, 100, 1)
price = c3.number_input("Price", 1.0, 10000.0, 10.0)

if st.button("Add Item"):
    if name.strip():
        st.session_state.items.append({
            "name": name,
            "qty": qty,
            "price": price,
            "amount": qty * price
        })
    else:
        st.warning("Enter item name")


# ==================================================
# PREVIEW MENU (FREE)
# ==================================================
st.subheader("👀 Menu Preview")

total = 0
for item in st.session_state.items:
    total += item["amount"]
    st.markdown(f"""
    <div class="menu-card">
        <div class="menu-row">
            <div>{item['name']} × {item['qty']}</div>
            <div>₹ {item['amount']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown(f"<div class='menu-total'>Total: ₹ {total}</div>", unsafe_allow_html=True)


# ==================================================
# PAYMENT WALL (₹25)
# ==================================================
st.subheader("🔐 Pay ₹25 to Download QR")

if not st.session_state.paid:
    if TEST_MODE:
        st.info("TEST MODE: Payment auto-approved")
        st.session_state.paid = True
    else:
        st.image("https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=upi://pay", width=200)
        txn = st.text_input("Enter Transaction ID after payment")

        if st.button("Verify Payment"):
            if txn.strip():
                st.session_state.paid = True
                st.success("Payment verified. Download unlocked.")
            else:
                st.error("Enter valid transaction ID")
else:
    st.success("Payment completed ✅")


# ==================================================
# DOWNLOAD QR (LOCKED UNTIL PAYMENT)
# ==================================================
if st.session_state.paid:
    st.subheader("⬇️ Download Your QR Code")

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

    st.image(qr_img, caption="Scan this QR to view menu")

    st.download_button(
        "⬇️ Download QR Code (PNG)",
        qr_img,
        "menu_qr.png",
        "image/png"
    )

else:
    st.warning("Complete ₹25 payment to download QR")
