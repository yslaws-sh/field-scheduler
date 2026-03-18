import streamlit as st
import pandas as pd
import requests
import os
import io
import time
from datetime import datetime, timedelta

# הגדרות אפליקציה - הסתרת תפריטים רשמית
st.set_page_config(
    page_title="הפועל הרצליה - מערכת ניהול", 
    page_icon="⚽", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# עיצוב RTL והסתרת רכיבי ממשק של Streamlit למשתמשים רגילים
st.markdown("""
    <style>
    /* הסתרת תפריט Streamlit וה-Footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .main { direction: rtl; text-align: right; background-color: #f8f9fa; }
    body { direction: rtl; }
    .main-header { 
        background-color: #e31e24; 
        padding: 25px; 
        border-radius: 0 0 25px 25px; 
        color: white; 
        text-align: center; 
        margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stButton>button { 
        width: 100%; 
        height: 3.5em; 
        background-color: #e31e24 !important; 
        color: white !important; 
        border-radius: 12px; 
        font-weight: bold;
        border: none;
    }
    th, td { text-align: center !important; border: 1px solid #dee2e6 !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #f1f1f1;
        border-radius: 10px 10px 0 0;
        padding: 10px 20px;
    }
    </style>
    <div class="main-header">
        <h1 style='margin:0; font-size: 28px;'>⚽ מועדון כדורגל הפועל הרצליה</h1>
        <p style='margin:0; font-size: 16px; opacity: 0.9;'>מערכת ניהול, שיבוץ וסנכרון חכמה</p>
    </div>
    """, unsafe_allow_html=True)

# --- ניהול מצב (Session State) ---
if 'start_date' not in st.session_state:
    today = datetime.now()
    st.session_state.start_date = today + timedelta(days=(6 - today.weekday() if today.weekday() != 6 else 0))

if 'reset_timestamp' not in st.session_state:
    st.session_state.reset_timestamp = datetime(2020, 1, 1)

def get_day_labels(base_date):
    days_hebrew = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי']
    return [f"יום {days_hebrew[i]} {(base_date + timedelta(days=i)).strftime('%d/%m')}" for i in range(5)]

# --- חיבור לגוגל ---
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSd-HaGeFh0P_zU7xs1kiFjLnM5i2mjZhiaRTcUD4h_L0ETksA/formResponse"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR8In1pn4dPWFvpIrxj1eLufbA7KQ6_wupxQiDbfxsAmvjsHrsO8ehPc3f5fT0TbenxVaLr8Tet6h5u/pub?output=csv"
ENTRY_IDS = {"coach": "entry.1199305397", "day": "entry.1231450869", "shift": "entry.1001387245"}

def load_data_from_google():
    try:
        res = requests.get(f"{SHEET_CSV_URL}&nocache={time.time()}")
        if res.status_code == 200:
            res.encoding = 'utf-8'
            df = pd.read_csv(io.StringIO(res.text))
            df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], dayfirst=True, errors='coerce')
            df = df[df.iloc[:, 0] > st.session_state.reset_timestamp]
            df = df.applymap(lambda x: str(x).strip() if pd.notnull(x) else "")
            return df
    except: pass
    return pd.DataFrame()

# --- טעינת מאמנים ---
file_path = 'טבלת מאמנים.csv'
if os.path.exists(file_path):
    df_info = pd.read_csv(file_path)
    df_info['full_id'] = df_info['שם הקבוצה'].str.strip() + " (" + df_info['מאמן'].str.strip() + ")"
    day_labels = get_day_labels(st.session_state.start_date)

    tabs = st.tabs(["📝 הזנת העדפות מאמנים", "⚙️ ניהול ושיבוץ (מנהל)"])
    
    with tabs[0]:
        st.subheader(f"מילוי העדפות לשבוע המתחיל ב- {st.session_state.start_date.strftime('%d/%m/%Y')}")
        selected_team = st.selectbox("בחר קבוצה מתוך הרשימה:", ["לחץ לבחירה..."] + df_info['full_id'].tolist())
        if selected_team != "לחץ לבחירה...":
            st.info("💡 אנא סמנו לפחות 4 אופציות שונות בימים ובשעות; גמישות זו קריטית ליכולת של המערכת למקסם את שיבוץ הקבוצות ולקלוע בצורה הטובה ביותר לבקשות של כולם.")
            new_selections = []
            for d_label in day_labels:
                with st.expander(f"📅 {d_label}"):
                    c1, c2 = st.columns(2)
                    if c1.checkbox("חלון מוקדם", key=f"e_{selected_team}_{d_label}"): new_selections.append({"Day": d_label, "Shift": "מוקדם"})
                    if c2.checkbox("חלון מאוחר", key=f"l_{selected_team}_{d_label}"): new_selections.append({"Day": d_label, "Shift": "מאוחר"})
            if st.button("שלח ושמור העדפות 🚀"):
                for sel in new_selections:
                    requests.post(FORM_URL, data={ENTRY_IDS["coach"]: selected_team, ENTRY_IDS["day"]: sel["Day"], ENTRY_IDS["shift"]: sel["Shift"]})
                st.success("הנתונים נשלחו בהצלחה! תודה על שיתוף הפעולה.")

    with tabs[1]:
        # אבטחת טאב מנהל
        admin_pass = st.text_input("הזן סיסמת מנהל לגישה להגדרות:", type="password")
        if admin_pass == "1906":
            st.markdown("### 🛠 פאנל ניהול ואיפוס שבוע")
            c1, c2, c3 = st.columns(3)
            with c1:
                new_date = st.date_input("בחר יום ראשון של השבוע הבא:", value=st.session_state.start_date)
                if new_date != st.session_state.start_date.date():
                    st.session_state.start_date = datetime.combine(new_date, datetime.min.time())
                    st.rerun()
            with c2:
                st.button("רענן לוח שיבוץ 🔄")
            with c3:
                if st.button("איפוס כל הדיווחים 🗑️"):
                    st.session_state.reset_timestamp = datetime.now()
                    st.warning("המערכת נוקתה מדיווחים ישנים.")
                    st.rerun()

            raw_data = load_data_from_google()
            if not raw_data.empty:
                slots = ['16:30-18:00', '18:00-19:30', '19:30-21:00']
                fields = ['קאנטרי קדמי 1', 'קאנטרי קדמי 2', 'קאנטרי אחורי 1', 'קאנטרי אחורי 2', 'משק קדמי 1', 'משק קדמי 2', 'משק אחורי 1', 'משק אחורי 2', 'סינטטי קטן']
                
                grid = []
                for d in day_labels:
                    for s in slots:
                        for f in fields:
                            grid.append({"יום": d, "שעה": s, "מגרש": f, "שיבוץ": "", "מאמן": ""})
                df_grid = pd.DataFrame(grid)
                
                c_coach, c_day, c_shift = raw_data.columns[1], raw_data.columns[2], raw_data.columns[3]
                for tid in df_info['full_id'].tolist():
                    coach_n = tid.split('(')[-1].replace(')', '').strip()
                    team_resps = raw_data[raw_data[c_coach].str.contains(tid.split('(')[0].strip(), na=False)]
                    for _, req in team_resps.iterrows():
                        day_v, shift_v = str(req[c_day]), str(req[c_shift])
                        matched_d = next((d for d in day_labels if d.split(' ')[1] in day_v), None)
                        if matched_d and len(df_grid[(df_grid['יום'] == matched_d) & (df_grid['שיבוץ'] == tid)]) == 0:
                            allowed = slots[:2] if "מוקדם" in shift_v else slots[1:]
                            for slot in allowed:
                                if df_grid[(df_grid['יום'] == matched_d) & (df_grid['שעה'] == slot) & (df_grid['מאמן'] == coach_n)].empty:
                                    mask = (df_grid['יום'] == matched_d) & (df_grid['שעה'] == slot) & (df_grid['שיבוץ'] == "")
                                    idx = df_grid[mask].index
                                    if len(idx) > 0:
                                        df_grid.at[idx[0], 'שיבוץ'] = tid
                                        df_grid.at[idx[0], 'מאמן'] = coach_n
                                        break

                final_df = df_grid.pivot_table(index=['שעה', 'מגרש'], columns='יום', values='שיבוץ', aggfunc='first', fill_value="")
                final_df = final_df.reindex(columns=day_labels).reset_index()
                
                st.write(f"### 📊 לוח שיבוץ מגרשים - {st.session_state.start_date.strftime('%d/%m')}")
                st.table(final_df)
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    final_df.to_excel(writer, index=False)
                st.download_button("📥 הורד כקובץ Excel", output.getvalue(), f"Hapoel_Herzliya_{st.session_state.start_date.strftime('%d_%m')}.xlsx")
            else:
                st.info("ממתין לדיווחים מהמאמנים...")
else:
    st.error("שגיאה: קובץ המאמנים לא נמצא בשרת.")
