
# ==================================================
# APP BASE URL (CHANGE THIS ONCE AFTER DEPLOY)
# ==================================================

APP_BASE_URL = "http://upi-menu-qr-trn2jqq8bhc79ktxox4g5e.streamlit.app"

# ==================================================
# CONFIGURATION
# ==================================================

TEST_MODE = True
# ↑↑↑
# TEST_MODE = True  → fake QR (for testing only)
# TEST_MODE = False → real UPI payment QR (production)


# ==================================================
# IMPORTS
# ==================================================
import streamlit as st
import segno
import base64
import json
import io
from PIL import Image
from datetime import date


# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(
    page_title="QR Menu",
    page_icon="📱",
    layout="centered"
)


# ==================================================
# CUSTOM CSS (MOBILE FRIENDLY)
# ==================================================
st.markdown("""
<style>
body { background-color: #f8fafc; }

.menu-card {
    background: white;
    padding: 16px;
    border-radius: 14px;
    margin-bottom: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.item-row {
    display: flex;
    justify-content: space-between;
    font-size: 16px;
    margin: 6px 0;
}

.item-name { font-weight: 500; }
.item-price { font-weight: 600; }

.total-box {
    background: #ecfeff;
    padding: 14px;
    border-radius: 12px;
    font-size: 18px;
    font-weight: 700;
    text-align: center;
    margin-top: 12px;
}

.pay-box {
    margin-top: 20px;
    padding: 14px;
    border-radius: 14px;
    background: #f1f5f9;
    text-align: center;
}

.small-text {
    font-size: 12px;
    color: gray;
}
</style>
""", unsafe_allow_html=True)


# ==================================================
# HELPER FUNCTIONS
# ==================================================

def parse_menu(text):
    """
    Format:
    Item, Qty, Price
    """
    items = []
    total = 0

    for line in text.strip().split("\n"):
        name, qty, price = [x.strip() for x in line.split(",")]
        qty = int(qty)
        price = float(price)
        amount = qty * price

        items.append({
            "name": name,
            "qty": qty,
            "price": price,
            "amount": amount
        })

        total += amount

    return items, total


def encode_data(data):
    """Encode menu data into URL-safe string"""
    return base64.urlsafe_b64encode(json.dumps(data).encode()).decode()


def decode_data(encoded):
    """Decode menu data from URL"""
    return json.loads(base64.urlsafe_b64decode(encoded.encode()).decode())


def generate_qr(data):
    """Generate QR image"""
    qr = segno.make(data)
    buf = io.BytesIO()
    qr.save(buf, kind="png", scale=6)
    buf.seek(0)
    return buf


def generate_upi_qr(upi_id, amount):
    """
    REAL PAYMENT QR
    Used only when TEST_MODE = False
    """
    upi_url = f"upi://pay?pa={upi_id}&am={amount}"
    return generate_qr(upi_url)


# ==================================================
# ROUTING (QR SCAN PAGE)
# ==================================================
params = st.query_params

if "menu" in params:
    data = decode_data(params["menu"])

    st.markdown(f"## {data['shop']}")
    st.markdown(f"📅 {data['date']}")

    st.markdown("---")

    # MENU LIST
    for item in data["items"]:
        st.markdown(f"""
        <div class="menu-card">
            <div class="item-row">
                <div class="item-name">
                    {item['name']} × {item['qty']}
                </div>
                <div class="item-price">
                    ₹ {item['amount']}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # TOTAL
    st.markdown(f"""
    <div class="total-box">
        Total Amount: ₹ {data['total']}
    </div>
    """, unsafe_allow_html=True)

    # PAYMENT SECTION
    st.markdown("""
    <div class="pay-box">
        <strong>Pay Using UPI</strong><br>
    """, unsafe_allow_html=True)

    if TEST_MODE:
        # 🧪 TEST QR (FAKE)
        st.image(generate_qr("TEST PAYMENT"), width=200)
        st.markdown("<div class='small-text'>TEST MODE – No real payment</div>", unsafe_allow_html=True)

    else:
        # 💰 REAL PAYMENT QR
        st.image(generate_upi_qr(data["upi"], data["total"]), width=200)
        st.markdown(f"<div class='small-text'>UPI ID: {data['upi']}</div>", unsafe_allow_html=True)

    st.stop()


# ==================================================
# SHOP OWNER PAGE
# ==================================================
st.title("📱 QR Menu Generator")

shop = st.text_input("Shop Name")
menu_date = st.date_input("Date", value=date.today())
upi = st.text_input("UPI ID / Mobile Number")

menu_text = st.text_area(
    "Menu (Item, Qty, Price)",
    placeholder="Tea, 2, 10\nCoffee, 1, 20"
)

st.markdown("### 🧪 Test Payment (₹25)")
st.info("TEST MODE is ON. No real payment required.")

# ==================================================
# GENERATE QR
# ==================================================
if st.button("Generate Menu QR"):
    try:
        items, total = parse_menu(menu_text)

        menu_data = {
            "shop": shop,
            "date": str(menu_date),
            "upi": upi,
            "items": items,
            "total": total
        }

        # Encode menu data
        encoded = encode_data(menu_data)

        # ✅ FULL PUBLIC URL (VERY IMPORTANT)
        menu_url = f"{APP_BASE_URL}/?menu={encoded}"

        # Generate QR
        qr_img = generate_qr(menu_url)

        st.success("QR Code Generated")

        # Show QR
        st.image(qr_img, caption="Scan this QR to view menu")

        # Download QR
        st.download_button(
            label="⬇️ Download QR Code (PNG)",
            data=qr_img,
            file_name="menu_qr.png",
            mime="image/png"
        )

        # Optional: show link
        st.markdown("🔗 Menu Link (for testing):")
        st.code(menu_url)

    except Exception as e:
        st.error(str(e))


