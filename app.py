import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="ניהול מגרשים - הפועל הרצליה", layout="wide")

st.markdown("<h1 style='text-align: center; color: red;'>⚽ הפועל הרצליה - מערכת שיבוץ חכמה</h1>", unsafe_allow_html=True)

# הגדרות חיבור לגוגל
FORM_SUBMIT_URL = "https://docs.google.com/forms/d/e/1FAIpQLSd-HaGeFh0P_zU7xs1kiFjLnM5i2mjZhiaRTcUD4h_L0ETksA/formResponse"
IDS = {"coach": "entry.1199305397", "day": "entry.1231450869", "shift": "entry.1001387245"}

# הגדרות זמן
start_date = datetime(2026, 3, 22)
days = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי']
day_labels = [(start_date + timedelta(days=i)).strftime(f"יום {days[i]} (%d/%m)") for i in range(5)]

# משמרות אימון אמיתיות
SLOTS = ['16:30-18:00', '18:00-19:30', '19:30-21:00']
FIELDS = ['מגרש 1 (קדמי)', 'מגרש 1 (אחורי)', 'מגרש 2 (קדמי)', 'מגרש 2 (אחורי)']

if 'db' not in st.session_state: st.session_state.db = []

file_path = 'טבלת מאמנים.csv'
if os.path.exists(file_path):
    coaches_df = pd.read_csv(file_path)
    coaches_list = coaches_df['מאמן'].unique()
    
    tab1, tab2 = st.tabs(["📋 הזנת העדפות", "📅 לוח שיבוץ סופי"])
    
    with tab1:
        current_coach = st.selectbox("בחר שם מאמן:", ["בחר מאמן"] + list(coaches_list))
        if current_coach != "בחר מאמן":
            saved = [r['Unique'] for r in st.session_state.db if r['Coach'] == current_coach]
            st.info(f"שלום {current_coach}, סמן את הסבבים הנוחים לך (המערכת תשבץ רק אחד ליום):")
            
            new_selections = []
            for i, day_name in enumerate(days):
                st.markdown(f"#### {day_labels[i]}")
                col1, col2 = st.columns(2)
                u_early = f"{day_name}_מוקדם"
                u_late = f"{day_name}_מאוחר"
                
                if col1.checkbox("מוקדם (16:30-19:30)", key=f"cb_{current_coach}_{u_early}", value=u_early in saved):
                    new_selections.append({"Coach": current_coach, "Day": day_name, "Shift": "מוקדם", "Unique": u_early})
                if col2.checkbox("מאוחר (18:00-21:00)", key=f"cb_{current_coach}_{u_late}", value=u_late in saved):
                    new_selections.append({"Coach": current_coach, "Day": day_name, "Shift": "מאוחר", "Unique": u_late})

            if st.button("שמור ועדכן שיבוץ"):
                if len(set([x['Day'] for x in new_selections])) < 4:
                    st.error("חובה לבחור לפחות 4 ימים!")
                else:
                    for sel in new_selections:
                        requests.post(FORM_SUBMIT_URL, data={IDS["coach"]: sel["Coach"], IDS["day"]: sel["Day"], IDS["shift"]: sel["Shift"]})
                    st.session_state.db = [r for r in st.session_state.db if r['Coach'] != current_coach]
                    st.session_state.db.extend(new_selections)
                    st.success("הבחירה נשמרה בהצלחה!")

    with tab2:
        st.subheader("הצבה אוטומטית במגרשים (אימון אחד ליום למאמן)")
        
        # יצירת לוח ריק
        grid = []
        for day in days:
            for slot in SLOTS:
                for field in FIELDS:
                    grid.append({"יום": day, "שעה": slot, "מגרש": field, "מאמן": ""})
        df_grid = pd.DataFrame(grid)

        # אלגוריתם הצבה חכם עם מניעת כפילויות ליום
        for day in days:
            # רשימת המאמנים ששובצו כבר היום
            assigned_today = []
            daily_reqs = [r for r in st.session_state.db if r['Day'] == day]
            
            for req in daily_reqs:
                coach = req['Coach']
                
                # אם המאמן כבר שובץ היום (וזה לא שי/אלברטו שיש להם 2 קבוצות) - דלג
                if coach in assigned_today and coach not in ['שי', 'אלברטו']:
                    continue
                
                shift = req['Shift']
                allowed_slots = ['16:30-18:00', '18:00-19:30'] if shift == "מוקדם" else ['18:00-19:30', '19:30-21:00']
                
                for slot in allowed_slots:
                    mask = (df_grid['יום'] == day) & (df_grid['שעה'] == slot) & (df_grid['מאמן'] == "")
                    free_idx = df_grid[mask].index
                    if len(free_idx) > 0:
                        df_grid.at[free_idx[0], 'מאמן'] = coach
                        assigned_today.append(coach)
                        break 

        pivot = df_grid.pivot_table(index=['שעה', 'מגרש'], columns='יום', values='מאמן', aggfunc='first').reindex(columns=days)
        pivot.columns = day_labels
        st.table(pivot)

else:
    st.error("קובץ המאמנים חסר.")
