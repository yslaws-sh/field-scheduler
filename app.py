import streamlit as st
import pandas as pd
import requests
import os
import io
from datetime import datetime, timedelta

st.set_page_config(page_title="ניהול מגרשים - הפועל הרצליה", layout="wide")

# יישור לימין (RTL)
st.markdown("""
    <style>
    .main { direction: rtl; text-align: right; }
    div.stSelectbox > label { text-align: right; width: 100%; }
    th, td { text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: red;'>⚽ הפועל הרצליה - מערכת שיבוץ חכמה</h1>", unsafe_allow_html=True)

# --- תאריכים לשבוע ה-22/03 ---
start_date = datetime(2026, 3, 22)
days_list = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי']
day_labels = [(start_date + timedelta(days=i)).strftime(f"יום {days_list[i]} %d/%m") for i in range(5)]

# --- הגדרות קבועות ---
FORM_SUBMIT_URL = "https://docs.google.com/forms/d/e/1FAIpQLSd-HaGeFh0P_zU7xs1kiFjLnM5i2mjZhiaRTcUD4h_L0ETksA/formResponse"
IDS = {"coach": "entry.1199305397", "day": "entry.1231450869", "shift": "entry.1001387245"}
SLOTS = ['16:30-18:00', '18:00-19:30', '19:30-21:00']
FIELDS = ['מגרש 1 (קדמי)', 'מגרש 1 (אחורי)', 'מגרש 2 (קדמי)', 'מגרש 2 (אחורי)']

if 'db' not in st.session_state: st.session_state.db = []

file_path = 'טבלת מאמנים.csv'
if os.path.exists(file_path):
    df_info = pd.read_csv(file_path)
    df_info['full_id'] = df_info['שם הקבוצה'] + " (" + df_info['מאמן'] + ")"
    
    tab1, tab2 = st.tabs(["📋 הזנת העדפות", "📅 לוח שיבוץ סופי"])
    
    with tab1:
        selected_team_id = st.selectbox("בחר קבוצה:", ["בחר קבוצה"] + df_info['full_id'].tolist())
        if selected_team_id != "בחר קבוצה":
            row = df_info[df_info['full_id'] == selected_team_id].iloc[0]
            st.success(f"שלום! עליך לסמן לפחות **4 ימים שונים**. בתוך כל יום תוכל לסמן כמה שעות שתרצה כדי לתת לנו גמישות.")
            
            saved = [r['Unique'] for r in st.session_state.db if r['TeamID'] == selected_team_id]
            new_selections = []
            for d_label in day_labels:
                st.markdown(f"#### {d_label}")
                col1, col2 = st.columns(2)
                u_early, u_late = f"{d_label}_מוקדם", f"{d_label}_מאוחר"
                
                if col1.checkbox("מוקדם (16:30-19:30)", key=f"cb_{selected_team_id}_{u_early}", value=u_early in saved):
                    new_selections.append({"TeamID": selected_team_id, "Day": d_label, "Shift": "מוקדם", "Unique": u_early})
                if col2.checkbox("מאוחר (18:00-21:00)", key=f"cb_{selected_team_id}_{u_late}", value=u_late in saved):
                    new_selections.append({"TeamID": selected_team_id, "Day": d_label, "Shift": "מאוחר", "Unique": u_late})

            if st.button("שמור העדפות"):
                # בדיקה: לפחות 4 ימים שונים
                selected_days = set([x['Day'] for x in new_selections])
                if len(selected_days) < 4:
                    st.error(f"❌ חובה לסמן לפחות 4 ימים שונים (סימנת רק {len(selected_days)}).")
                else:
                    for sel in new_selections:
                        requests.post(FORM_SUBMIT_URL, data={IDS["coach"]: sel["TeamID"], IDS["day"]: sel["Day"], IDS["shift"]: sel["Shift"]})
                    st.session_state.db = [r for r in st.session_state.db if r['TeamID'] != selected_team_id]
                    st.session_state.db.extend(new_selections)
                    st.success(f"נשמר! תודה על הגמישות עם {len(new_selections)} אפשרויות שיבוץ.")
                    st.balloons()

    with tab2:
        # לוגיקת שיבוץ אוטומטית
        grid = []
        for d in day_labels:
            for s in SLOTS:
                for f in FIELDS:
                    grid.append({"יום": d, "שעה": s, "מגרש": f, "שיבוץ": ""})
        df_grid = pd.DataFrame(grid)
        
        usage = {tid: 0 for tid in df_info['full_id']}
        quota = {row['full_id']: row['מספר אימונים'] for _, row in df_info.iterrows()}
        team_flex = {tid: len([r for r in st.session_state.db if r['TeamID'] == tid]) for tid in df_info['full_id']}
        sorted_teams = sorted(df_info['full_id'].tolist(), key=lambda x: team_flex.get(x, 0))

        for tid in sorted_teams:
            team_reqs = [r for r in st.session_state.db if r['TeamID'] == tid]
            for req in team_reqs:
                if usage[tid] >= quota[tid]: break
                day = req['Day']
                if len(df_grid[(df_grid['יום'] == day) & (df_grid['שיבוץ'] == tid)]) >= 1: continue
                
                allowed = ['16:30-18:00', '18:00-19:30'] if req['Shift'] == "מוקדם" else ['18:00-19:30', '19:30-21:00']
                for slot in allowed:
                    mask = (df_grid['יום'] == day) & (df_grid['שעה'] == slot) & (df_grid['שיבוץ'] == "")
                    free_idx = df_grid[mask].index
                    if len(free_idx) > 0:
                        df_grid.at[free_idx[0], 'שיבוץ'] = tid
                        usage[tid] += 1
                        break

        pivot = df_grid.pivot_table(index=['שעה', 'מגרש'], columns='יום', values='שיבוץ', aggfunc='first').reindex(columns=day_labels)
        st.write("### לוח שיבוץ סופי")
        
        # תצוגת טבלה מעוצבת
        def style_rows(row):
            return ['background-color: #ffe6e6' if "מגרש 1" in str(row.name) else 'background-color: #e6f3ff' for _ in row]
        
        st.table(pivot.style.apply(style_rows, axis=1))

        # כפתור הורדה לאקסל צבעוני
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            pivot.to_excel(writer, sheet_name='לוח שיבוץ')
            workbook = writer.book
            worksheet = writer.sheets['לוח שיבוץ']
            fmt1 = workbook.add_format({'bg_color': '#FF9999', 'border': 1, 'align': 'center'})
            fmt2 = workbook.add_format({'bg_color': '#99CCFF', 'border': 1, 'align': 'center'})
            for r_num in range(len(pivot)):
                m_name = pivot.index[r_num][1]
                worksheet.set_row(r_num + 1, 25, fmt1 if "מגרש 1" in m_name else fmt2)
        
        st.download_button("📥 הורד לוח צבעוני לוואטסאפ", data=output.getvalue(), file_name=f"hapoel_schedule_{start_date.strftime('%d_%m')}.xlsx")

else:
    st.error("קובץ CSV חסר")
