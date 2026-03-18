import streamlit as st
import pandas as pd
import requests
import os
import io
import time
from datetime import datetime, timedelta

# 1. הגדרות אפליקציה והסתרת תפריטים למראה נקי
st.set_page_config(
    page_title="הפועל הרצליה - ניהול", 
    page_icon="⚽", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS להסתרת תפריטי Streamlit ועיצוב RTL
st.markdown("""
    <style>
    /* הסתרת אלמנטים של Streamlit למאמנים */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    
    .main { direction: rtl; text-align: right; background-color: #f8f9fa; }
    body { direction: rtl; }
    .main-header { 
        background-color: #e31e24; 
        padding: 20px; 
        border-radius: 0 0 20px 20px; 
        color: white; 
        text-align: center; 
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stButton>button { 
        width: 100%; 
        background-color: #e31e24 !important; 
        color: white !important; 
        border-radius: 12px; 
        font-weight: bold; 
        height: 3.5em;
    }
    th, td { text-align: center !important; border: 1px solid #dee2e6 !important; padding: 8px !important; }
    </style>
    <div class="main-header">
        <h1 style='margin:0; font-size: 26px;'>⚽ הפועל הרצליה - מערכת שיבוץ מגרשים</h1>
    </div>
    """, unsafe_allow_html=True)

# 2. ניהול Session State
if 'start_date' not in st.session_state:
    today = datetime.now()
    # ברירת מחדל ליום ראשון הקרוב
    st.session_state.start_date = today + timedelta(days=(6 - today.weekday() if today.weekday() != 6 else 0))

if 'skip_rows' not in st.session_state:
    st.session_state.skip_rows = 0

# 3. הגדרות קישורים
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR8In1pn4dPWFvpIrxj1eLufbA7KQ6_wupxQiDbfxsAmvjsHrsO8ehPc3f5fT0TbenxVaLr8Tet6h5u/pub?output=csv"
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSd-HaGeFh0P_zU7xs1kiFjLnM5i2mjZhiaRTcUD4h_L0ETksA/formResponse"
ENTRY_IDS = {"coach": "entry.1199305397", "day": "entry.1231450869", "shift": "entry.1001387245"}

def get_day_labels(base_date):
    days = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי']
    return [f"יום {days[i]} {(base_date + timedelta(days=i)).strftime('%d/%m')}" for i in range(5)]

def load_data_from_google():
    try:
        res = requests.get(f"{SHEET_CSV_URL}&nocache={time.time()}")
        if res.status_code == 200:
            res.encoding = 'utf-8'
            df = pd.read_csv(io.StringIO(res.text))
            # מנגנון איפוס (דילוג על שורות ישנות)
            if st.session_state.skip_rows > 0:
                df = df.iloc[st.session_state.skip_rows:]
            df = df.applymap(lambda x: str(x).strip() if pd.notnull(x) else "")
            return df
    except: pass
    return pd.DataFrame()

# 4. לוגיקה מרכזית
file_path = 'טבלת מאמנים.csv'
if os.path.exists(file_path):
    df_info = pd.read_csv(file_path)
    df_info['full_id'] = df_info['שם הקבוצה'].str.strip() + " (" + df_info['מאמן'].str.strip() + ")"
    day_labels = get_day_labels(st.session_state.start_date)

    tabs = st.tabs(["📝 הזנת העדפות מאמנים", "⚙️ ניהול ושיבוץ (מנהל)"])
    
    # --- טאב מאמנים ---
    with tabs[0]:
        st.subheader(f"מילוי העדפות לשבוע המתחיל ב- {st.session_state.start_date.strftime('%d/%m/%Y')}")
        selected_team = st.selectbox("בחר קבוצה מהרשימה:", ["לחץ לבחירה..."] + df_info['full_id'].tolist())
        
        if selected_team != "לחץ לבחירה...":
            st.info("💡 אנא סמנו לפחות 4 אופציות שונות בימים ובשעות; גמישות זו קריטית ליכולת של המערכת למקסם את שיבוץ הקבוצות ולקלוע בצורה הטובה ביותר לבקשות של כולם.")
            
            # הגדרת שעות לתצוגה
            slots_list = ['16:30-18:00', '18:00-19:30', '19:30-21:00']
            early_range = "16:30 - 19:30"
            late_range = "18:00 - 21:00"
            
            new_selections = []
            for d_label in day_labels:
                with st.expander(f"📅 {d_label}"):
                    c1, c2 = st.columns(2)
                    if c1.checkbox(f"⏰ {early_range}", key=f"e_{selected_team}_{d_label}"): 
                        new_selections.append({"Day": d_label, "Shift": "מוקדם"})
                    if c2.checkbox(f"⏰ {late_range}", key=f"l_{selected_team}_{d_label}"): 
                        new_selections.append({"Day": d_label, "Shift": "מאוחר"})
            
            if st.button("שלח ושמור 🚀"):
                if not new_selections:
                    st.warning("לא נבחרה משבצת.")
                else:
                    for sel in new_selections:
                        requests.post(FORM_URL, data={ENTRY_IDS["coach"]: selected_team, ENTRY_IDS["day"]: sel["Day"], ENTRY_IDS["shift"]: sel["Shift"]})
                    st.success("נשמר בהצלחה! הנתונים בדרך ללוח המנהל.")

    # --- טאב מנהל ---
    with tabs[1]:
        if st.text_input("סיסמת מנהל (1906):", type="password") == "1906":
            st.markdown("### 🛠 הגדרות שבוע וניהול")
            c1, c2, c3 = st.columns(3)
            with c1:
                new_d = st.date_input("בחר יום ראשון של השבוע:", value=st.session_state.start_date)
                if new_d != st.session_state.start_date.date():
                    st.session_state.start_date = datetime.combine(new_d, datetime.min.time())
                    st.rerun()
            with c2: 
                st.button("רענן נתונים 🔄")
            with c3:
                if st.button("איפוס מוחלט (ניקוי לוח) 🗑️"):
                    res = requests.get(SHEET_CSV_URL)
                    if res.status_code == 200:
                        temp_df = pd.read_csv(io.StringIO(res.text))
                        st.session_state.skip_rows = len(temp_df)
                        st.warning("המערכת נוקתה. דיווחים ישנים לא יופיעו בטבלה.")
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
                            allowed_slots = slots[:2] if "מוקדם" in shift_v else slots[1:]
                            for slot in allowed_slots:
                                # בדיקת כפל מאמן
                                if df_grid[(df_grid['יום'] == matched_d) & (df_grid['שעה'] == slot) & (df_grid['מאמן'] == coach_n)].empty:
                                    mask = (df_grid['יום'] == matched_d) & (df_grid['שעה'] == slot) & (df_grid['שיבוץ'] == "")
                                    idx = df_grid[mask].index
                                    if len(idx) > 0:
                                        df_grid.at[idx[0], 'שיבוץ'] = tid
                                        df_grid.at[idx[0], 'מאמן'] = coach_n
                                        break

                # יצירת טבלה עם סדר ימים קבוע (א-ה)
                final_df = df_grid.pivot_table(index=['שעה', 'מגרש'], columns='יום', values='שיבוץ', aggfunc='first', fill_value="")
                final_df = final_df.reindex(columns=day_labels).reset_index()
                
                st.write(f"### 📅 לוח שיבוץ מגרשים - {st.session_state.start_date.strftime('%d/%m')}")
                st.table(final_df)
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    final_df.to_excel(writer, index=False)
                st.download_button("📥 הורד קובץ אקסל סופי", output.getvalue(), f"Hapoel_Herzliya_{st.session_state.start_date.strftime('%d_%m')}.xlsx")
            else:
                st.info("הלוח נקי. ממתין לדיווחים.")
else:
    st.error("שגיאה: קובץ המאמנים חסר.")
