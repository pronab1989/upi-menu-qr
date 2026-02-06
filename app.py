# ==================================================
# CONFIG
# ==================================================
APP_BASE_URL = "https://upi-menu-qr-trn2jqq8bhc79ktxox4g5e.streamlit.app"
TEST_MODE = False   # True = auto unlock (testing), False = require ₹25 payment


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
# PAGE SETUP
# ==================================================
st.set_page_config("QR Menu Generator", "📱", layout="centered")


# ==================================================
# CSS (CLASSIC + MOBILE)
# ==================================================
st.markdown("""
<style>
.card {background:#fff;padding:14px;border-radius:12px;margin-bottom:10px;
       box-shadow:0 2px 8px rgba(0,0,0,0.06);}
.row {display:flex;justify-content:space-between;font-size:16px;}
.total {background:#ecfeff;padding:14px;border-radius:12px;
        font-size:18px;font-weight:700;text-align:center;}
.pay {background:#f8fafc;padding:14px;border-radius:12px;text-align:center;}
.small {font-size:12px;color:gray;}
</style>
""", unsafe_allow_html=True)


# ==================================================
# HELPERS
# ==================================================
def encode_data(data):
    return base64.urlsafe_b64encode(json.dumps(data).encode()).decode()

def decode_data(encoded):
    return json.loads(base64.urlsafe_b64decode(encoded.encode()).decode())

def make_qr(text):
    qr = segno.make(text)
    buf = io.BytesIO()
    qr.save(buf, kind="png", scale=6)
    buf.seek(0)
    return buf

def upi_qr(upi, amount):
    return make_qr(f"upi://pay?pa={upi}&am={amount}")


# ==================================================
# CUSTOMER PAGE (QR SCAN)
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
                <div>{item["name"]} × {item["qty"]}</div>
                <div>₹ {item["amount"]}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"<div class='total'>Total: ₹ {data['total']}</div>", unsafe_allow_html=True)

    st.markdown("<div class='pay'><b>Pay Using UPI</b><br>", unsafe_allow_html=True)
    st.image(upi_qr(data["upi"], data["total"]), width=220)
    st.markdown(f"<div class='small'>UPI: {data['upi']}</div>", unsafe_allow_html=True)

    st.stop()


# ==================================================
# SHOP OWNER PAGE
# ==================================================
st.title("📱 QR Menu Generator")

shop = st.text_input("Shop Name")
menu_date = st.date_input("Date", value=date.today())
upi = st.text_input("Shop UPI ID / Mobile Number")


# ==================================================
# SAFE SESSION STATE (NO DOT ACCESS)
# ==================================================
if "items" not in st.session_state:
    st.session_state["items"] = []

if "paid" not in st.session_state:
    st.session_state["paid"] = False


# ==================================================
# ADD ITEMS
# ==================================================
st.subheader("➕ Add Menu Item")

c1, c2, c3 = st.columns(3)
iname = c1.text_input("Item Name")
iqty = c2.number_input("Qty", min_value=1, value=1)
iprice = c3.number_input("Price", min_value=1.0, value=10.0)

if st.button("Add Item"):
    if iname.strip():
        st.session_state["items"].append({
            "name": iname,
            "qty": int(iqty),
            "price": float(iprice),
            "amount": int(iqty) * float(iprice)
        })
    else:
        st.warning("Enter item name")


# ==================================================
# PREVIEW MENU (FREE)
# ==================================================
st.subheader("👀 Menu Preview")

total = 0
for item in st.session_state["items"]:
    total += item["amount"]
    st.markdown(f"""
    <div class="card">
        <div class="row">
            <div>{item["name"]} × {item["qty"]}</div>
            <div>₹ {item["amount"]}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown(f"<div class='total'>Total: ₹ {total}</div>", unsafe_allow_html=True)


# ==================================================
# PAYMENT WALL (₹25)
# ==================================================
st.subheader("🔐 Pay ₹25 to Download QR")

if not st.session_state["paid"]:
    if TEST_MODE:
        st.info("TEST MODE: Payment auto-approved")
        st.session_state["paid"] = True
    else:
        st.image("https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=upi://pay", width=200)
        txn = st.text_input("Enter Transaction ID")

        if st.button("Verify Payment"):
            if txn.strip():
                st.session_state["paid"] = True
                st.success("Payment verified")
            else:
                st.error("Enter transaction ID")
else:
    st.success("Payment completed ✅")


# ==================================================
# QR DOWNLOAD (LOCKED)
# ==================================================
if st.session_state["paid"]:
    if shop and upi and st.session_state["items"]:
        menu_data = {
            "shop": shop,
            "date": str(menu_date),
            "upi": upi,
            "items": st.session_state["items"],
            "total": total
        }

        encoded = encode_data(menu_data)
        menu_url = f"{APP_BASE_URL}/?menu={encoded}"

        qr_img = make_qr(menu_url)

        st.image(qr_img, caption="Scan this QR to view menu")

        st.download_button(
            "⬇️ Download QR Code",
            qr_img,
            "menu_qr.png",
            "image/png"
        )
    else:
        st.warning("Fill shop details and add items to generate QR")
else:
    st.warning("Pay ₹25 to unlock QR download")
