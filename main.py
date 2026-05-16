import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- ١. دروستکردنی بنکەی دراوەی ناوەندی (Database) ---
def init_db():
    conn = sqlite3.connect("royal_post_cloud.db")
    cursor = conn.cursor()
    
    # خشتەی ئەژماری ئۆفیسەکان و لقی نوێ
    cursor.execute('''CREATE TABLE IF NOT EXISTS offices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        office_name TEXT,
                        email TEXT UNIQUE,
                        password TEXT,
                        status TEXT DEFAULT 'Branch')''')
    
    # خشتەی تۆمارکردنی بارەکان
    cursor.execute('''CREATE TABLE IF NOT EXISTS shipments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        office_id INTEGER,
                        customer_name TEXT,
                        phone TEXT,
                        address TEXT,
                        item_details TEXT,
                        price TEXT,
                        date TEXT,
                        FOREIGN KEY(office_id) REFERENCES offices(id))''')
    conn.commit()
    conn.close()

init_db()

# --- ٢. ڕێکخستنی شاشە و دیزاین ---
st.set_page_config(page_title="Royal Post Cloud", page_icon="🌐", layout="wide")

# شێوازی فۆنت و ڕەنگەکان بە CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght=400;700&display=swap');
    html, body, [data-testid="stSidebar"] {
        font-family: 'Cairo', sans-serif;
        direction: rtl;
    }
    .main-title { text-align: center; color: #1a237e; font-size: 36px; font-weight: bold; }
    .sub-title { text-align: center; color: #555; font-size: 18px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<div class='main-title'>📦 Royal Post Cloud System</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>سیستەمی ئۆنلاینی بەڕێوەبردنی بارەکانی ڕۆیاڵ پۆست</div>", unsafe_allow_html=True)
st.write("---")

# بەڕێوەبردنی بارودۆخی چوونەژوورەوە (Session State)
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.user_role = ""
    st.session_state.office_id = None
    st.session_state.office_name = ""

# --- ٣. شاشەی چوونەژوورەوە (Login System) ---
if not st.session_state.logged_in:
    st.info("""
    💡 *زانیاری بۆ چوونەژوورەوە و تاقیکردنەوەی سیستەمەکە:*
    * *ئیمەیڵی ئەدمین:* admin@royalpost.com
    * *کۆدی نهێنی (Password):* admin123
    """)
    
    st.subheader("🔑 چوونەژوورەوە بۆ سیستەم / Login")
    login_email = st.text_input("گیمەیڵ یان ئیمەیڵی بەکارهێنەر (Email)").strip()
    login_pass = st.text_input("کۆدی نهێنی (Password)", type="password").strip()
    
    if st.button("چوونەژوورەوە", use_container_width=True):
        # پشکنینی ڕاستەوخۆ بۆ ئەدمینی سەرەکی بۆ ئەوەی بەبێ کێشە داخڵ ببیت
        if login_email == "admin@royalpost.com" and login_pass == "admin123":
            st.session_state.logged_in = True
            st.session_state.user_email = login_email
            st.session_state.office_id = 1
            st.session_state.office_name = "Super Admin"
            st.session_state.user_role = "Admin"
            st.rerun()
        else:
            # پشکنینی لقەکان لە ناو داتابەیس
            conn = sqlite3.connect("royal_post_cloud.db")
            cursor = conn.cursor()
            cursor.execute("SELECT id, office_name, status FROM offices WHERE email=? AND password=?", (login_email, login_pass))
            user = cursor.fetchone()
            conn.close()
            
            if user:
                st.session_state.logged_in = True
                st.session_state.user_email = login_email
                st.session_state.office_id = user[0]
                st.session_state.office_name = user[1]
                st.session_state.user_role = user[2]
                st.rerun()
            else:
                st.error("گیمەیڵ یان کۆدی چوونەژوورەوەکە هەڵەیە!")
else:
    # بەشی Sidebar بۆ دەرچوون و زانیاری بەکارهێنەر
    st.sidebar.markdown(f"### 👤 بخێربێیت، {st.session_state.office_name}")
    st.sidebar.write(f"لێپرسراوێتی: {st.session_state.user_role}")
    if st.sidebar.button("🚪 چوونەدەرەوە (Logout)", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()
    st.sidebar.write("---")

    # ==================== [ بەشی یەکەم: ئەدمینی سەرەکی - SUPER ADMIN ] ====================
    if st.session_state.user_role == "Admin":
        menu = st.sidebar.radio("پەڕەکانی کۆنتڕۆڵ:", ["📊 بینینی گشتی هەموو بارەکان", "🏢 زیادکردن و بەڕێوەبردنی ئۆفیسەکان"])
        
        if menu == "📊 بینینی گشتی هەموو بارەکان":
            st.header("📋 گشت داتاکانی کۆمپانیا (هەموو لکەکان)")
            conn = sqlite3.connect("royal_post_cloud.db")
            try:
                df = pd.read_sql_query("""
                    SELECT shipments.id AS 'کۆدی بار', offices.office_name AS 'ئۆفیسی نێرەر', shipments.customer_name AS 'ناوی وەرگر', 
                    shipments.phone AS 'مۆبایل', shipments.address AS 'ناونیشان', shipments.item_details AS 'زانیاری بار', 
                    shipments.price AS 'نرخ', shipments.date AS 'بەروار و کات' 
                    FROM shipments JOIN offices ON shipments.office_id = offices.id ORDER BY shipments.id DESC
                """, conn)
            except:
                df = pd.DataFrame()
            conn.close()
            
            if not df.empty:
                search = st.text_input("🔍 گەڕانی خێرا لە ناو هەموو داتاکاندا (ناو یان ژمارە مۆبایل)...")
                if search:
                    df = df[df['ناوی وەرگر'].str.contains(search, na=False) | df['مۆبایل'].astype(str).str.contains(search, na=False)]
                st.dataframe(df, use_container_width=True)
            else:
                st.info("هیچ بارێک تا ئێستا لەلایەن هیچ لقێکەوە تۆمار نەکراوە.")
            
        elif menu == "🏢 زیادکردن و بەڕێوەبردنی ئۆفیسەکان":
            st.header("➕ دروستکردنی ئەژماری نوێ بۆ لقی نوێ")
            with st.form("new_office_form", clear_on_submit=True):
                new_name = st.text_input("ناوی ئۆفیس / لقی نوێ (بۆ نموونە: لقی حاجیئاوا)")
                new_email = st.text_input("گیمەیڵی لکەکە (Email)")
                new_pass = st.text_input("کۆدی چوونەژوورەوەی لکەکە (Password)")
                submit_office = st.form_submit_button("تۆمارکردن و چالاککردنی لق")
                
                if submit_office and new_name and new_email and new_pass:
                    try:
                        conn = sqlite3.connect("royal_post_cloud.db")
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO offices (office_name, email, password) VALUES (?, ?, ?)", (new_name, new_email, new_pass))
                        conn.commit()
                        conn.close()
                        st.success(f"لقی نوێی ({new_name}) بە سەرکەوتوویی زیادکرا و گیمەیڵەکەی چالاک بوو!")
                    except:
                        st.error("ئەم گیمەیڵە پێشتر تۆمارکراوە! تکایە گیمەیڵێکی تر بەکاربهێنە.")

    # ==================== [ بەشی دووەم: بەکارهێنەری ئۆفیسەکان - BRANCHES ] ====================
    else:
        menu = st.sidebar.radio("مێنیوی کارەکان:", ["➕ تۆمارکردنی باری نوێ", "📦 بارەکانی ئەم ئۆفیسە و چاپکردن"])
        
        if menu == "➕ تۆمارکردنی باری نوێ":
            st.header(f"تۆمارکردنی بار لە لایەن: {st.session_state.office_name}")
            with st.form("shipment_form", clear_on_submit=True):
                c_name = st.text_input("ناوی تەواوی وەرگر (Customer Name)")
                c_phone = st.text_input("ژمارەی مۆبایلی وەرگر (Phone)")
                c_address = st.text_input("ناونیشانی تەواو / شوێنی وەرگرتن (Address)")
                item_details = st.text_input("زانیاری بار و کێش (Item Details)")
                price = st.text_input("نرخی گەیاندن یان بڕی پارە (Price)")
                
                submit = st.form_submit_button("پاشەکەوتکردنی زانیارییەکان")
                if submit:
                    if c_name and c_phone and c_address:
                        conn = sqlite3.connect("royal_post_cloud.db")
                        cursor = conn.cursor()
                        now = datetime.now().strftime("%Y-%m-%d %H:%M")
                        cursor.execute("INSERT INTO shipments (office_id, customer_name, phone, address, item_details, price, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                       (st.session_state.office_id, c_name, c_phone, c_address, item_details, price, now))
                        conn.commit()
                        conn.close()
                        st.success("بارەکە بە سەرکەوتوویی لە سەر داتابەیسی سەرەکی پاشەکەوت کرا! 🎉")
                    else:
                        st.error("تکایە خانە سەرەکییەکان (ناو، مۆبایل، ناونیشان) پڕبکەرەوە.")
                    
        elif menu == "📦 بارەکانی ئەم ئۆفیسە و چاپکردن":
            st.header(f"بارە نێردراوەکانی لقی {st.session_state.office_name}")
            conn = sqlite3.connect("royal_post_cloud.db")
            df = pd.read_sql_query(f"SELECT id, customer_name, phone, address, item_details, price, date FROM shipments WHERE office_id={st.session_state.office_id} ORDER BY id DESC", conn)
            conn.close()
            
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                st.write("---")
                
                selected_id = st.selectbox("کۆدی بارەکە (ID) هەڵبژێرە بۆ چاپکردن (Print):", df["id"].tolist())
                
                if selected_id:
                    conn = sqlite3.connect("royal_post_cloud.db")
                    cursor = conn.cursor()
                    cursor.execute("SELECT id, customer_name, phone, address, item_details, price, date FROM shipments WHERE id=?", (selected_id,))
                    row = cursor.fetchone()
                    conn.close()
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("📄 ۱. شێوازی وەسڵ (A4 Receipt)")
                        st.markdown(f"""
                        <div style="border:1px solid #1a237e; padding:20px; font-family:Arial, sans-serif; direction:rtl; text-align:right; background:white; color:black; border-radius:8px;">
                            <h2 style="text-align:center; margin:0; color:#1a237e;">ROYAL POST - ڕۆیاڵ پۆست</h2>
                            <p style="text-align:center; font-size:12px; color:gray; margin:5px 0;">قەڵای گەیاندنی خێرا</p>
                            <hr style="border:0.5px solid #ccc;">
                            <table style="width:100%; font-size:14px; line-height:2;">
                                <tr><td><b>ژمارەی وەسڵ:</b> #{row[0]}</td><td><b>بەروار:</b> {row[6]}</td></tr>
                                <tr><td colspan="2"><b>ناوی کڕیار (وەرگر):</b> {row[1]}</td></tr>
                                <tr><td colspan="2"><b>ژمارەی تەلەفۆن:</b> {row[2]}</td></tr>
                                <tr><td colspan="2"><b>ناونیشانی گەیاندن:</b> {row[3]}</td></tr>
                                <tr><td><b>ناوەرۆکی بار:</b> {row[4]}</td><td><b>کۆی نرخ:</b> <span style="font-size:16px; font-weight:bold; color:#1a237e;">{row[5]}</span> IQD</td></tr>
                            </table>
                            <hr style="border:0.5px solid #ccc;">
                            <p style="text-align:center; font-size:11px; color:#555;">سوپاس بۆ هەڵبژاردنی ڕۆیاڵ پۆست.</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with col2:
                        st.subheader("🏷️ ٢. لەزگەی سەر کارتۆن (Label)")
                        st.markdown(f"""
                        <div style="border: 4px solid #000; padding:15px; font-family:Arial, sans-serif; background:#fff; color:#000; max-width:380px; margin:auto; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);">
                            <h1 style="text-align:center; margin:0; color:#1a237e; font-size:32px; font-weight:bold; letter-spacing:1px;">ROYAL POST</h1>
                            <div style="background:#000; color:white; text-align:center; padding:4px; font-size:16px; font-weight:bold; margin-top:5px;">⚠️ SHIPMENT INFORMATION</div>
                            <div style="margin-top:15px; font-size:18px; line-height:1.6;">
                                <p style="margin:5px 0;"><b>👤 TO:</b> {row[1]}</p>
                                <p style="margin:5px 0;"><b>📞 TEL:</b> {row[2]}</p>
                                <p style="margin:5px 0;"><b>📍 ADDR:</b> {row[3]}</p>
                                <p style="margin:5px 0; font-size:14px; color:#444;"><b>📦 ITEM:</b> {row[4]}</p>
                            </div>
                            <hr style="border:1px dashed #000; margin:15px 0;">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <span style="font-size:14px;"><b>TRACKING ID:</b> #{row[0]}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    st.success("💡 بۆ پرینتکردن: دوگمەکانی Ctrl + P دابگرە.")
            else:
                st.info("تا ئێستا هیچ بارێک لەم لقە تۆمار نەکراوە.")
