import streamlit as st
import pandas as pd
import requests
import os
import io
from datetime import datetime, timedelta

# הגדרות אפליקציה
st.set_page_config(page_title="הפועל הרצליה - מערכת שיבוץ", page_icon="⚽", layout="wide")

# עיצוב RTL והדגשת השעות
st.markdown("""
    <style>
    .main { direction: rtl; text-align: right; background-color: #f8f9fa; }
    body { direction: rtl; }
    .main-header { background-color: #e31e24; padding: 20px; border-radius: 0 0 20px 20px; color: white; text-align: center; margin-bottom: 20px; }
    .stButton>button { width: 100%; height: 3.5em; background-color: #e31e24 !important; color: white !important; border-radius: 12px; font-weight: bold; }
    
    /* עיצוב הטבלה שהשעות יראו ברור */
    table { width: 100%; direction: rtl; }
    th { background-color: #f1f3f5 !important; color: black !important; font-weight: bold !important; border: 1px solid #dee2e6 !important; }
    td { border: 1px solid #dee2e6 !important; padding: 10px !important; text-align: center !important; }
    .hour-cell { background-color: #333 !important; color: white !important; font-weight: bold; }
    </style>
    <div class="main-header">
        <h1 style='margin:0; font-size: 24px;'>מועדון כדורגל הפועל הרצליה</h1>
        <p style='margin:0; font-size: 16px;'>מערכת שיבוץ מגרשים חכמה</p>
    </div>
    """, unsafe_allow_html=True)

# --- תאריכים ---
start_date = datetime(2026, 3, 22)
days_list = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי']
day_labels = [(start_date + timedelta(days=i)).strftime(f"יום {days_list[i]} %d/%m") for i in range(5)]

# --- הגדרות ---
FORM_SUBMIT_URL = "https://docs.google.com/forms/d/e/1FAIpQLSd-HaGeFh0P_zU7xs1kiFjLnM5i2mjZhiaRTcUD4h_L0ETksA/formResponse"
IDS = {"coach": "entry.1199305397", "day": "entry.1231450869", "shift": "entry.1001387245"}
SLOTS = ['16:30-18:00', '18:00-19:30', '19:30-21:00']
FIELDS = ['קאנטרי (קדמי)', 'קאנטרי (אחורי)', 'משק (קדמי)', 'משק (אחורי)']

if 'db' not in st.session_state: st.session_state.db = []
if 'admin_access' not in st.session_state: st.session_state.admin_access = False

file_path = 'טבלת מאמנים.csv'
if os.path.exists(file_path):
    df_info = pd.read_csv(file_path)
    df_info['full_id'] = df_info['שם הקבוצה'] + " (" + df_info['מאמן'] + ")"
    
    tabs = ["📝 הזנת העדפות"]
    if st.session_state.admin_access: tabs.append("📊 לוח שיבוץ (מנהל)")
    active_tabs = st.tabs(tabs)
    
    with active_tabs[0]:
        selected_team_id = st.selectbox("בחר קבוצה:", ["לחץ לבחירה..."] + df_info['full_id'].tolist())
        if selected_team_id != "לחץ לבחירה...":
            row = df_info[df_info['full_id'] == selected_team_id].iloc[0]
            st.info(f"💡 קבוצת {row['שם הקבוצה']} צריכה {row['מספר אימונים']} אימונים. ככל שתיתן גמישות, כך תקבל מגרש טוב יותר!")
            
            saved = [r['Unique'] for r in st.session_state.db if r['TeamID'] == selected_team_id]
            new_selections = []
            for d_label in day_labels:
                with st.expander(f"📅 {d_label}", expanded=True):
                    col1, col2 = st.columns(2)
                    u_early, u_late = f"{d_label}_מוקדם", f"{d_label}_מאוחר"
                    if col1.checkbox("☀️ מוקדם (16:30-19:30)", key=f"cb_{selected_team_id}_{u_early}", value=(u_early in saved)):
                        new_selections.append({"TeamID": selected_team_id, "Coach": row['מאמן'], "Day": d_label, "Shift": "מוקדם", "Unique": u_early})
                    if col2.checkbox("🌙 מאוחר (18:00-21:00)", key=f"cb_{selected_team_id}_{u_late}", value=(u_late in saved)):
                        new_selections.append({"TeamID": selected_team_id, "Coach": row['מאמן'], "Day": d_label, "Shift": "מאוחר", "Unique": u_late})

            if st.button("שמור העדפות ועדכן לוח 🚀"):
                if len(set([x['Day'] for x in new_selections])) < 4:
                    st.error("❌ חובה לסמן לפחות 4 ימים שונים.")
                else:
                    st.session_state.db = [r for r in st.session_state.db if r['TeamID'] != selected_team_id]
                    st.session_state.db.extend(new_selections)
                    for sel in new_selections:
                        try: requests.post(FORM_SUBMIT_URL, data={IDS["coach"]: sel["TeamID"], IDS["day"]: sel["Day"], IDS["shift"]: sel["Shift"]}, timeout=2)
                        except: pass
                    st.success("הבחירה נשמרה! תודה על הגמישות.")
                    st.balloons()
        
        st.markdown("---")
        admin_key = st.text_input("כניסת מנהל (סיסמה):", type="password")
        if admin_key == "1234":
            st.session_state.admin_access = True
            st.rerun()

    if st.session_state.admin_access:
        with active_tabs[1]:
            # לוגיקת שיבוץ
            grid = []
            for d in day_labels:
                for s in SLOTS:
                    for f in FIELDS:
                        grid.append({"יום": d, "שעה": s, "מגרש": f, "שיבוץ": "", "מאמן": ""})
            df_grid = pd.DataFrame(grid)
            
            usage = {tid: 0 for tid in df_info['full_id']}
            quota = {row['full_id']: int(row['מספר אימונים']) for _, row in df_info.iterrows()}
            ordered_teams = df_info['full_id'].tolist()

            for tid in ordered_teams:
                team_reqs = [r for r in st.session_state.db if r['TeamID'] == tid]
                for req in team_reqs:
                    if usage[tid] >= quota[tid]: break
                    day, coach = req['Day'], req['Coach']
                    if len(df_grid[(df_grid['יום'] == day) & (df_grid['שיבוץ'] == tid)]) >= 1: continue
                    prev_assignment = df_grid[(df_grid['יום'] == day) & (df_grid['מאמן'] == coach)]
                    allowed_slots = ['16:30-18:00', '18:00-19:30'] if req['Shift'] == "מוקדם" else ['18:00-19:30', '19:30-21:00']
                    for slot in allowed_slots:
                        if not prev_assignment.empty:
                            target_field = prev_assignment.iloc[0]['מגרש']
                            mask = (df_grid['יום'] == day) & (df_grid['שעה'] == slot) & (df_grid['מגרש'] == target_field) & (df_grid['שיבוץ'] == "")
                        else:
                            mask = (df_grid['יום'] == day) & (df_grid['שעה'] == slot) & (df_grid['שיבוץ'] == "") & (df_grid['מאמן'] != coach)
                        
                        free_idx = df_grid[mask].index
                        if len(free_idx) > 0:
                            df_grid.at[free_idx[0], 'שיבוץ'] = tid
                            df_grid.at[free_idx[0], 'מאמן'] = coach
                            usage[tid] += 1
                            break

            # הפיכת השעה והמגרש לעמודות רגילות בטבלה
            final_df = df_grid.pivot(index=['שעה', 'מגרש'], columns='יום', values='שיבוץ').reset_index()
            final_df = final_df.reindex(columns=['שעה', 'מגרש'] + day_labels)

            st.write("### 📅 לוח שיבוץ סופי (מנהל)")
            
            # פונקציית צביעה
            def color_rows(row):
                color = '#ffcccc' if "קאנטרי" in str(row['מגרש']) else '#cce5ff'
                return [f'background-color: {color}'] * len(row)

            st.table(final_df.style.apply(color_rows, axis=1))

            # כפתור הורדה
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                final_df.to_excel(writer, sheet_name='Hapoel', index=False)
                workbook, worksheet = writer.book, writer.sheets['Hapoel']
                f_red = workbook.add_format({'bg_color': '#FF9999', 'border': 1, 'align': 'center', 'bold': True})
                f_blue = workbook.add_format({'bg_color': '#99CCFF', 'border': 1, 'align': 'center', 'bold': True})
                for r_num in range(len(final_df)):
                    fmt = f_red if "קאנטרי" in str(final_df.iloc[r_num]['מגרש']) else f_blue
                    worksheet.set_row(r_num + 1, 30, fmt)
                worksheet.set_column('A:B', 20)
                worksheet.set_column('C:G', 25)

            st.download_button("📥 הורד לוח צבעוני לוואטסאפ", data=output.getvalue(), file_name="hapoel_schedule.xlsx")
            if st.button("יציאה ממצב מנהל"):
                st.session_state.admin_access = False
                st.rerun()
else:
    st.error("קובץ CSV חסר")
