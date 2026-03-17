import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="ניהול מגרשים - הפועל הרצליה", layout="wide")

st.markdown("<h1 style='text-align: center; color: red;'>⚽ הפועל הרצליה - מערכת שיבוץ חכמה</h1>", unsafe_allow_html=True)

# --- הגדרות חיבור לגוגל ---
FORM_SUBMIT_URL = "https://docs.google.com/forms/d/e/1FAIpQLSd-HaGeFh0P_zU7xs1kiFjLnM5i2mjZhiaRTcUD4h_L0ETksA/formResponse"
IDS = {"coach": "entry.1199305397", "day": "entry.1231450869", "shift": "entry.1001387245"}

# --- הגדרות זמן ---
start_date = datetime(2026, 3, 22)
days = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי']
day_labels = [(start_date + timedelta(days=i)).strftime(f"יום {days[i]} (%d/%m)") for i in range(5)]
SLOTS = ['16:30-18:00', '18:00-19:30', '19:30-21:00']
FIELDS = ['מגרש 1 (קדמי)', 'מגרש 1 (אחורי)', 'מגרש 2 (קדמי)', 'מגרש 2 (אחורי)']

if 'db' not in st.session_state: st.session_state.db = []

def clear_ui():
    for key in list(st.session_state.keys()):
        if key.startswith("cb_"): del st.session_state[key]

file_path = 'טבלת מאמנים.csv'
if os.path.exists(file_path):
    df_info = pd.read_csv(file_path)
    # יצירת מזהה ייחודי: שם הקבוצה (שם המאמן)
    df_info['full_id'] = df_info['שם הקבוצה'] + " (" + df_info['מאמן'] + ")"
    
    tab1, tab2 = st.tabs(["📋 הזנת העדפות קבוצה", "📅 לוח שיבוץ סופי"])
    
    with tab1:
        selected_team_id = st.selectbox("בחר קבוצה לשיבוץ:", ["בחר קבוצה"] + df_info['full_id'].tolist(), on_change=clear_ui)
        
        if selected_team_id != "בחר קבוצה":
            row = df_info[df_info['full_id'] == selected_team_id].iloc[0]
            required_days = row['מספר אימונים']
            coach_name = row['מאמן']
            
            st.info(f"שלום {coach_name}, לקבוצת **{row['שם הקבוצה']}** דרושים **{required_days}** אימונים בשבוע.")
            
            # טעינת בחירות קיימות מהזיכרון
            saved = [r['Unique'] for r in st.session_state.db if r['TeamID'] == selected_team_id]
            
            new_selections = []
            for day in days:
                st.markdown(f"#### יום {day}")
                col1, col2 = st.columns(2)
                u_early, u_late = f"{day}_מוקדם", f"{day}_מאוחר"
                
                # מפתח ייחודי לצ'קבוקס
                key_e = f"cb_{selected_team_id}_{u_early}"
                key_l = f"cb_{selected_team_id}_{u_late}"
                
                if col1.checkbox("מוקדם (16:30-19:30)", key=key_e, value=u_early in saved):
                    new_selections.append({"TeamID": selected_team_id, "Day": day, "Shift": "מוקדם", "Unique": u_early})
                if col2.checkbox("מאוחר (18:00-21:00)", key=key_l, value=u_late in saved):
                    new_selections.append({"TeamID": selected_team_id, "Day": day, "Shift": "מאוחר", "Unique": u_late})

            if st.button("שמור שיבוץ"):
                selected_days_count = len(set([x['Day'] for x in new_selections]))
                if selected_days_count != required_days:
                    st.error(f"עליך לבחור בדיוק {required_days} ימים (בחרת {selected_days_count}).")
                else:
                    # שליחה לגוגל
                    for sel in new_selections:
                        requests.post(FORM_SUBMIT_URL, data={IDS["coach"]: sel["TeamID"], IDS["day"]: sel["Day"], IDS["shift"]: sel["Shift"]})
                    
                    # עדכון הזיכרון
                    st.session_state.db = [r for r in st.session_state.db if r['TeamID'] != selected_team_id]
                    st.session_state.db.extend(new_selections)
                    st.success(f"העדפות עבור {selected_team_id} נשמרו!")
                    st.balloons()

    with tab2:
        st.subheader("לוח שיבוץ אוטומטי (קבוצה + מאמן)")
        
        # יצירת לוח ריק לפי שעות אימון אמיתיות
        grid = []
        for day in days:
            for slot in SLOTS:
                for field in FIELDS:
                    grid.append({"יום": day, "שעה": slot, "מגרש": field, "שיבוץ": ""})
        df_grid = pd.DataFrame(grid)

        # הצבה חכמה: כל קבוצה מקבלת אימון אחד ביום שבחרה
        for day in days:
            daily_reqs = [r for r in st.session_state.db if r['Day'] == day]
            for req in daily_reqs:
                # טווח השעות לפי הסבב שנבחר
                allowed = ['16:30-18:00', '18:00-19:30'] if req['Shift'] == "מוקדם" else ['18:00-19:30', '19:30-21:00']
                
                shuffled_slots = allowed # ניתן לערבב אם רוצים אקראיות
                assigned = False
                for slot in shuffled_slots:
                    mask = (df_grid['יום'] == day) & (df_grid['שעה'] == slot) & (df_grid['שיבוץ'] == "")
                    free_idx = df_grid[mask].index
                    if len(free_idx) > 0:
                        df_grid.at[free_idx[0], 'שיבוץ'] = req['TeamID']
                        assigned = True
                        break

        pivot = df_grid.pivot_table(index=['שעה', 'מגרש'], columns='יום', values='שיבוץ', aggfunc='first').reindex(columns=days)
        pivot.columns = day_labels
        st.table(pivot)
else:
    st.error("קובץ 'טבלת מאמנים.csv' חסר ב-GitHub.")
