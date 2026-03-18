import streamlit as st
import pandas as pd
import requests
import os
import io
import time
from datetime import datetime, timedelta

# הגדרות אפליקציה
st.set_page_config(page_title="הפועל הרצליה - מערכת ניהול", page_icon="⚽", layout="wide")

# עיצוב RTL
st.markdown("""
    <style>
    .main { direction: rtl; text-align: right; background-color: #f8f9fa; }
    body { direction: rtl; }
    .main-header { background-color: #e31e24; padding: 20px; border-radius: 0 0 20px 20px; color: white; text-align: center; margin-bottom: 20px; }
    .stButton>button { width: 100%; height: 3.5em; background-color: #e31e24 !important; color: white !important; border-radius: 12px; font-weight: bold; }
    th, td { text-align: center !important; border: 1px solid #dee2e6 !important; }
    </style>
    <div class="main-header">
        <h1 style='margin:0; font-size: 24px;'>מועדון כדורגל הפועל הרצליה</h1>
        <p style='margin:0; font-size: 16px;'>מערכת ניהול ושיבוץ חכמה</p>
    </div>
    """, unsafe_allow_html=True)

# --- הגדרות חיבור לגוגל ---
FORM_RESPONSE_URL = "https://docs.google.com/forms/d/e/1FAIpQLSd-HaGeFh0P_zU7xs1kiFjLnM5i2mjZhiaRTcUD4h_L0ETksA/formResponse"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR8In1pn4dPWFvpIrxj1eLufbA7KQ6_wupxQiDbfxsAmvjsHrsO8ehPc3f5fT0TbenxVaLr8Tet6h5u/pub?output=csv"

ENTRY_IDS = {
    "coach": "entry.1199305397",
    "day": "entry.1231450869",
    "shift": "entry.1001387245"
}

# פונקציית טעינה עם מנגנון מניעת Cache חזק
def load_data_from_google():
    try:
        # יצירת קישור ייחודי בכל פעם כדי שגוגל לא יביא נתונים ישנים מהזיכרון
        t = int(time.time())
        url = f"{SHEET_CSV_URL}&cache_bust={t}"
        res = requests.get(url)
        if res.status_code == 200:
            df = pd.read_csv(io.StringIO(res.text))
            df.columns = [c.strip() for c in df.columns]
            # מנקה שורות ריקות אם יש
            df = df.dropna(subset=[df.columns[1]])
            return df
    except Exception as e:
        st.error(f"שגיאה בטעינה: {e}")
    return pd.DataFrame()

# --- הגדרות מערכת ---
ALL_FIELDS = ['קאנטרי קדמי 1', 'קאנטרי קדמי 2', 'קאנטרי אחורי 1', 'קאנטרי אחורי 2', 'משק קדמי 1', 'משק קדמי 2', 'משק אחורי 1', 'משק אחורי 2', 'סינטטי קטן']
if 'active_fields' not in st.session_state: st.session_state.active_fields = ALL_FIELDS
if 'active_slots' not in st.session_state: st.session_state.active_slots = ['16:30-18:00', '18:00-19:30', '19:30-21:00']

start_date = datetime(2026, 3, 22)
days_list = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי']
day_labels = [(start_date + timedelta(days=i)).strftime(f"יום {days_list[i]} %d/%m") for i in range(5)]

file_path = 'טבלת מאמנים.csv'
if os.path.exists(file_path):
    df_info = pd.read_csv(file_path)
    df_info['full_id'] = df_info['שם הקבוצה'] + " (" + df_info['מאמן'] + ")"
    
    tabs = ["📝 הזנת העדפות", "📊 לוח שיבוץ (מנהל)"]
    active_tabs = st.tabs(tabs)
    
    with active_tabs[0]:
        selected_team = st.selectbox("בחר קבוצה:", ["לחץ לבחירה..."] + df_info['full_id'].tolist())
        if selected_team != "לחץ לבחירה...":
            row = df_info[df_info['full_id'] == selected_team].iloc[0]
            st.info(f"💡 **קבוצת {row['שם הקבוצה']}:** סמנו לפחות 4 ימים שונים.")

            slots = st.session_state.active_slots
            mid = len(slots) // 2
            early_range = f"{slots[0].split('-')[0]} - {slots[mid].split('-')[-1]}"
            late_range = f"{slots[mid].split('-')[0]} - {slots[-1].split('-')[-1]}"

            new_selections = []
            for d_label in day_labels:
                with st.expander(f"📅 {d_label}", expanded=True):
                    c1, c2 = st.columns(2)
                    if c1.checkbox(f"⏰ {early_range}", key=f"e_{selected_team}_{d_label}"):
                        new_selections.append({"Day": d_label, "Shift": "מוקדם"})
                    if c2.checkbox(f"⏰ {late_range}", key=f"l_{selected_team}_{d_label}"):
                        new_selections.append({"Day": d_label, "Shift": "מאוחר"})

            if st.button("שמור העדפות 🚀"):
                if len(set([x['Day'] for x in new_selections])) < 4:
                    st.error("❌ חובה לסמן לפחות 4 ימים שונים.")
                else:
                    with st.spinner("שומר בגיליון..."):
                        for sel in new_selections:
                            payload = {ENTRY_IDS["coach"]: selected_team, ENTRY_IDS["day"]: sel["Day"], ENTRY_IDS["shift"]: sel["Shift"]}
                            requests.post(FORM_RESPONSE_URL, data=payload)
                        st.success("נשמר בהצלחה! הנתונים יופיעו בלוח תוך רגע.")
                        st.balloons()

    with active_tabs[1]:
        admin_key = st.text_input("סיסמת מנהל:", type="password")
        if admin_key == "1906":
            col_a, col_b = st.columns([1,1])
            with col_a:
                if st.button("רענן נתונים מגוגל 🔄"):
                    st.rerun()
            
            raw_data = load_data_from_google()
            
            if not raw_data.empty:
                # זיהוי עמודות דינמי
                col_coach = raw_data.columns[1]
                col_day = raw_data.columns[2]
                col_shift = raw_data.columns[3]
                
                # יצירת גריד ריק
                grid = []
                for d in day_labels:
                    for s in st.session_state.active_slots:
                        for f in st.session_state.active_fields:
                            grid.append({"יום": d, "שעה": s, "מגרש": f, "שיבוץ": "", "מאמן": ""})
                df_grid = pd.DataFrame(grid)
                
                # לוגיקת שיבוץ
                for tid in df_info['full_id'].tolist():
                    team_resps = raw_data[raw_data[col_coach] == tid]
                    for _, req in team_resps.iterrows():
                        day, shift = req[col_day], req[col_shift]
                        if len(df_grid[(df_grid['יום'] == day) & (df_grid['שיבוץ'] == tid)]) >= 1: continue
                        
                        half = len(st.session_state.active_slots) // 2
                        allowed = st.session_state.active_slots[:half+1] if shift == "מוקדם" else st.session_state.active_slots[half:]
                        coach_name = tid.split('(')[-1].replace(')', '').strip()
                        
                        for slot in allowed:
                            mask = (df_grid['יום'] == day) & (df_grid['שעה'] == slot) & (df_grid['שיבוץ'] == "") & (df_grid['מאמן'] != coach_name)
                            idx = df_grid[mask].index
                            if len(idx) > 0:
                                df_grid.at[idx[0], 'שיבוץ'] = tid
                                df_grid.at[idx[0], 'מאמן'] = coach_name
                                break

                final_df = df_grid.pivot_table(index=['שעה', 'מגרש'], columns='יום', values='שיבוץ', aggfunc='first', fill_value="").reset_index()
                st.table(final_df)
                
                # כפתור הורדה
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    final_df.to_excel(writer, index=False)
                st.download_button("📥 הורד קובץ אקסל", data=output.getvalue(), file_name="hapoel_schedule.xlsx")
                
                with st.expander("ראה נתונים גולמיים (ביקורת)"):
                    st.write(f"נמצאו {len(raw_data)} שורות בגוגל שיטס.")
                    st.dataframe(raw_data)
            else:
                st.warning("הגיליון ריק או שגוגל לא מחזיר נתונים.")
else:
    st.error("קובץ CSV חסר")
