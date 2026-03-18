import streamlit as st
import pandas as pd
import requests
import os
import io
import time
from datetime import datetime, timedelta

# הגדרות אפליקציה רשמית
st.set_page_config(page_title="הפועל הרצליה - מערכת ניהול", page_icon="⚽", layout="wide")

# עיצוב RTL ויישור לימין
st.markdown("""
    <style>
    .main { direction: rtl; text-align: right; background-color: #f8f9fa; }
    body { direction: rtl; }
    .main-header { background-color: #e31e24; padding: 20px; border-radius: 0 0 20px 20px; color: white; text-align: center; margin-bottom: 20px; }
    .stButton>button { width: 100%; height: 3.5em; background-color: #e31e24 !important; color: white !important; border-radius: 12px; font-weight: bold; }
    th, td { text-align: center !important; border: 1px solid #dee2e6 !important; padding: 8px !important; }
    div[data-baseweb="select"] { direction: rtl; }
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

def load_data_from_google():
    try:
        # מניעת Cache אגרסיבית
        res = requests.get(f"{SHEET_CSV_URL}&nocache={time.time()}")
        if res.status_code == 200:
            res.encoding = 'utf-8' # תיקון ג'יבריש
            df = pd.read_csv(io.StringIO(res.text))
            df = df.applymap(lambda x: str(x).strip() if pd.notnull(x) else "")
            return df
    except:
        pass
    return pd.DataFrame()

# --- הגדרות מערכת קבועות ---
ALL_FIELDS = [
    'קאנטרי קדמי 1', 'קאנטרי קדמי 2', 'קאנטרי אחורי 1', 'קאנטרי אחורי 2',
    'משק קדמי 1', 'משק קדמי 2', 'משק אחורי 1', 'משק אחורי 2', 'סינטטי קטן'
]
if 'active_fields' not in st.session_state: st.session_state.active_fields = ALL_FIELDS
if 'active_slots' not in st.session_state: st.session_state.active_slots = ['16:30-18:00', '18:00-19:30', '19:30-21:00']

# תאריכים לשבוע הבא (החל מ-22/03)
start_date = datetime(2026, 3, 22)
days_hebrew = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי']
day_labels = [f"יום {days_hebrew[i]} {(start_date + timedelta(days=i)).strftime('%d/%m')}" for i in range(5)]

file_path = 'טבלת מאמנים.csv'
if os.path.exists(file_path):
    df_info = pd.read_csv(file_path)
    df_info['full_id'] = df_info['שם הקבוצה'].str.strip() + " (" + df_info['מאמן'].str.strip() + ")"
    
    tabs = st.tabs(["📝 הזנת העדפות", "📊 לוח שיבוץ (מנהל)"])
    
    # --- טאב 1: מאמנים ---
    with tabs[0]:
        selected_team = st.selectbox("בחר קבוצה:", ["לחץ לבחירה..."] + df_info['full_id'].tolist())
        if selected_team != "לחץ לבחירה...":
            row = df_info[df_info['full_id'] == selected_team].iloc[0]
            st.info(f"💡 **קבוצת {row['שם הקבוצה']}:** סמנו לפחות 4 ימים שונים לגמישות מרבית!")

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
                    with st.spinner("שומר..."):
                        for sel in new_selections:
                            payload = {ENTRY_IDS["coach"]: selected_team, ENTRY_IDS["day"]: sel["Day"], ENTRY_IDS["shift"]: sel["Shift"]}
                            requests.post(FORM_RESPONSE_URL, data=payload)
                    st.success("נשמר בהצלחה! הנתונים בדרך ללוח.")
                    st.balloons()

    # --- טאב 2: מנהל ---
    with tabs[1]:
        admin_key = st.text_input("סיסמת מנהל:", type="password")
        if admin_key == "1906":
            st.button("רענן נתונים מגוגל שיטס 🔄")
            
            c1, c2 = st.columns(2)
            with c1:
                st.session_state.active_fields = st.multiselect("מגרשים פעילים:", ALL_FIELDS, default=st.session_state.active_fields)
            with c2:
                slot_input = st.text_input("זמני אימונים:", value=",".join(st.session_state.active_slots))
                current_slots = [s.strip() for s in slot_input.split(",")]
                st.session_state.active_slots = current_slots

            raw_data = load_data_from_google()
            
            if not raw_data.empty:
                col_coach, col_day, col_shift = raw_data.columns[1], raw_data.columns[2], raw_data.columns[3]
                
                grid = []
                for d in day_labels:
                    for s in current_slots:
                        for f in st.session_state.active_fields:
                            grid.append({"יום": d, "שעה": s, "מגרש": f, "שיבוץ": "", "מאמן": ""})
                df_grid = pd.DataFrame(grid)
                
                # לוגיקת שיבוץ עם חסימת כפל מאמנים
                for tid in df_info['full_id'].tolist():
                    coach_name = tid.split('(')[-1].replace(')', '').strip()
                    # חיפוש חכם שמתגבר על הבדלי קידוד/רווחים
                    team_resps = raw_data[raw_data[col_coach].apply(lambda x: tid in x or x in tid)]
                    
                    for _, req in team_resps.iterrows():
                        day_v, shift_v = str(req[col_day]), str(req[col_shift])
                        matched_d = next((d for d in day_labels if d.split(' ')[1] in day_v), None)
                        if not matched_d: continue
                        
                        # הגבלה: קבוצה לא משובצת פעמיים באותו יום
                        if len(df_grid[(df_grid['יום'] == matched_d) & (df_grid['שיבוץ'] == tid)]) >= 1: continue
                        
                        half = len(current_slots) // 2
                        allowed = current_slots[:half+1] if "מוקדם" in shift_v else current_slots[half:]
                        
                        for slot in allowed:
                            # בדיקה: האם המאמן כבר תפוס בשעה הזו במגרש אחר?
                            is_coach_busy = not df_grid[(df_grid['יום'] == matched_d) & 
                                                       (df_grid['שעה'] == slot) & 
                                                       (df_grid['מאמן'] == coach_name)].empty
                            
                            if not is_coach_busy:
                                mask = (df_grid['יום'] == matched_d) & (df_grid['שעה'] == slot) & (df_grid['שיבוץ'] == "")
                                idx = df_grid[mask].index
                                if len(idx) > 0:
                                    df_grid.at[idx[0], 'שיבוץ'] = tid
                                    df_grid.at[idx[0], 'מאמן'] = coach_name
                                    break

                # יצירת טבלה סופית עם סדר ימים קשיח (א-ה)
                final_df = df_grid.pivot_table(index=['שעה', 'מגרש'], columns='יום', values='שיבוץ', aggfunc='first', fill_value="")
                
                # סידור עמודות לפי day_labels המקורי
                existing_cols = [c for c in day_labels if c in final_df.columns]
                final_df = final_df[existing_cols].reset_index()
                
                st.write("### 📅 לוח שיבוץ סופי (ללא כפילויות מאמנים)")
                st.table(final_df)
                
                # אקסל מעוצב
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    final_df.to_excel(writer, sheet_name='Hapoel_Schedule', index=False)
                    workbook = writer.book
                    worksheet = writer.sheets['Hapoel_Schedule']
                    
                    f_red = workbook.add_format({'bg_color': '#FF9999', 'border': 1, 'align': 'center'})
                    f_blue = workbook.add_format({'bg_color': '#99CCFF', 'border': 1, 'align': 'center'})
                    f_green = workbook.add_format({'bg_color': '#C6EFCE', 'border': 1, 'align': 'center'})
                    f_head = workbook.add_format({'bg_color': '#e31e24', 'font_color': 'white', 'bold': True, 'border': 1, 'align': 'center'})

                    for col_num, value in enumerate(final_df.columns.values):
                        worksheet.write(0, col_num, value, f_head)

                    for r_num in range(len(final_df)):
                        m_val = str(final_df.iloc[r_num]['מגרש'])
                        fmt = f_red if "קאנטרי" in m_val else f_blue if "משק" in m_val else f_green
                        worksheet.set_row(r_num + 1, 30, fmt)

                    worksheet.set_column('A:B', 20)
                    worksheet.set_column('C:G', 25)
                    worksheet.right_to_left()

                st.download_button("📥 הורד לוח שיבוץ סופי (Excel)", data=output.getvalue(), file_name="hapoel_final_schedule.xlsx")
                
                with st.expander("🔍 ראה נתונים גולמיים"):
                    st.dataframe(raw_data)
else:
    st.error("קובץ CSV חסר ב-GitHub")
