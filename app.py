import streamlit as st
import pandas as pd
import requests
import os
import io
from datetime import datetime, timedelta

st.set_page_config(page_title="ניהול מגרשים - הפועל הרצליה", layout="wide")

# עיצוב RTL
st.markdown("""
    <style>
    .main { direction: rtl; text-align: right; }
    div.stSelectbox > label { text-align: right; width: 100%; }
    th, td { text-align: center !important; }
    .stTabs [data-baseweb="tab-list"] { direction: rtl; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: red;'>⚽ הפועל הרצליה - מערכת שיבוץ חכמה</h1>", unsafe_allow_html=True)

# --- תאריכים (22/03) ---
start_date = datetime(2026, 3, 22)
days_list = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי']
day_labels = [(start_date + timedelta(days=i)).strftime(f"יום {days_list[i]} %d/%m") for i in range(5)]

# --- הגדרות שמות מגרשים ושעות ---
FORM_SUBMIT_URL = "https://docs.google.com/forms/d/e/1FAIpQLSd-HaGeFh0P_zU7xs1kiFjLnM5i2mjZhiaRTcUD4h_L0ETksA/formResponse"
IDS = {"coach": "entry.1199305397", "day": "entry.1231450869", "shift": "entry.1001387245"}

SLOTS = ['16:30-18:00', '18:00-19:30', '19:30-21:00']
# סדר המגרשים קובע את סדר המילוי: קודם קאנטרי, אחר כך משק
FIELDS = ['קאנטרי (קדמי)', 'קאנטרי (אחורי)', 'משק (קדמי)', 'משק (אחורי)']

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
            st.info(f"שלום מאמן! קבוצת {row['שם הקבוצה']} צריכה {row['מספר אימונים']} אימונים. ככל שתסמן יותר אפשרויות ושעות - כך נוכל לתת לך את המגרש המועדף עליך!")

            current_selections = [r['Unique'] for r in st.session_state.db if r['TeamID'] == selected_team_id]
            new_selections = []
            for d_label in day_labels:
                st.markdown(f"**{d_label}**")
                col1, col2 = st.columns(2)
                u_early, u_late = f"{d_label}_מוקדם", f"{d_label}_מאוחר"
                if col1.checkbox("מוקדם (16:30-19:30)", key=f"cb_{selected_team_id}_{u_early}", value=u_early in current_selections):
                    new_selections.append({"TeamID": selected_team_id, "Coach": row['מאמן'], "Day": d_label, "Shift": "מוקדם", "Unique": u_early})
                if col2.checkbox("מאוחר (18:00-21:00)", key=f"cb_{selected_team_id}_{u_late}", value=u_late in current_selections):
                    new_selections.append({"TeamID": selected_team_id, "Coach": row['מאמן'], "Day": d_label, "Shift": "מאוחר", "Unique": u_late})

            if st.button("שמור העדפות"):
                if len(set([x['Day'] for x in new_selections])) < 4:
                    st.error("❌ חובה לסמן לפחות 4 ימים שונים.")
                else:
                    st.session_state.db = [r for r in st.session_state.db if r['TeamID'] != selected_team_id]
                    st.session_state.db.extend(new_selections)
                    for sel in new_selections:
                        requests.post(FORM_SUBMIT_URL, data={IDS["coach"]: sel["TeamID"], IDS["day"]: sel["Day"], IDS["shift"]: sel["Shift"]})
                    st.success("תודה על הגמישות! הלוח התעדכן.")
                    st.balloons()

    with tab2:
        # בניית לוח ריק
        grid = []
        for d in day_labels:
            for s in SLOTS:
                for f in FIELDS:
                    grid.append({"יום": d, "שעה": s, "מגרש": f, "שיבוץ": "", "מאמן": ""})
        df_grid = pd.DataFrame(grid)
        
        usage = {tid: 0 for tid in df_info['full_id']}
        quota = {row['full_id']: int(row['מספר אימונים']) for _, row in df_info.iterrows()}

        # סדר שיבוץ: לפי הסדר ב-CSV (נוער -> נערים -> ילדים)
        ordered_teams = df_info['full_id'].tolist()

        for tid in ordered_teams:
            team_reqs = [r for r in st.session_state.db if r['TeamID'] == tid]
            for req in team_reqs:
                if usage[tid] >= quota[tid]: break
                day, coach = req['Day'], req['Coach']
                
                # האם הקבוצה כבר שובצה היום?
                if len(df_grid[(df_grid['יום'] == day) & (df_grid['שיבוץ'] == tid)]) >= 1: continue
                
                # האם המאמן כבר שובץ היום עם קבוצה אחרת? (בשביל חוק "אחד אחרי השני")
                prev_assignment = df_grid[(df_grid['יום'] == day) & (df_grid['מאמן'] == coach)]
                
                allowed_slots = ['16:30-18:00', '18:00-19:30'] if req['Shift'] == "מוקדם" else ['18:00-19:30', '19:30-21:00']
                
                placed = False
                for slot in allowed_slots:
                    # אם המאמן כבר משובץ היום, ננסה לשבץ אותו באותו מגרש בשעה עוקבת
                    if not prev_assignment.empty:
                        target_field = prev_assignment.iloc[0]['מגרש']
                        mask = (df_grid['יום'] == day) & (df_grid['שעה'] == slot) & (df_grid['מגרש'] == target_field) & (df_grid['שיבוץ'] == "")
                    else:
                        # שיבוץ רגיל - מעדיף קאנטרי (לפי סדר FIELDS)
                        mask = (df_grid['יום'] == day) & (df_grid['שעה'] == slot) & (df_grid['שיבוץ'] == "") & (df_grid['מאמן'] != coach)
                    
                    free_idx = df_grid[mask].index
                    if len(free_idx) > 0:
                        df_grid.at[free_idx[0], 'שיבוץ'] = tid
                        df_grid.at[free_idx[0], 'מאמן'] = coach
                        usage[tid] += 1
                        placed = True
                        break
                
                # אם לא מצאנו מקום צמוד למאמן כפול, ננסה שיבוץ רגיל במקום פנוי אחר
                if not placed and prev_assignment.empty:
                    # (כבר טופל בלולאה למעלה)
                    pass

        pivot = df_grid.pivot_table(index=['שעה', 'מגרש'], columns='יום', values='שיבוץ', aggfunc='first').reindex(columns=day_labels)
        
        st.write("### לוח שיבוץ סופי: קאנטרי ומשק")
        st.table(pivot.style.apply(lambda r: ['background-color: #ffe6e6' if "קאנטרי" in str(r.name) else 'background-color: #e6f3ff' for _ in r], axis=1))

        # כפתור הורדה
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            pivot.to_excel(writer, sheet_name='Hapoel_Herzliya')
            workbook, worksheet = writer.book, writer.sheets['Hapoel_Herzliya']
            fmt_c = workbook.add_format({'bg_color': '#FF9999', 'border': 1, 'align': 'center', 'bold': True})
            fmt_m = workbook.add_format({'bg_color': '#99CCFF', 'border': 1, 'align': 'center', 'bold': True})
            for r_num in range(len(pivot)):
                worksheet.set_row(r_num + 1, 30, fmt_c if "קאנטרי" in pivot.index[r_num][1] else fmt_m)
        st.download_button("📥 הורד לוח צבעוני", data=output.getvalue(), file_name=f"hapoel_schedule.xlsx")
else:
    st.error("CSV חסר")
