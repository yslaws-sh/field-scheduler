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

# שעות האימון האמיתיות (שעה וחצי כל אחד)
SLOTS = ['16:30-18:00', '18:00-19:30', '19:30-21:00']
FIELDS = ['מגרש 1 (קדמי)', 'מגרש 1 (אחורי)', 'מגרש 2 (קדמי)', 'מגרש 2 (אחורי)']

if 'db' not in st.session_state: st.session_state.db = []

file_path = 'טבלת מאמנים.csv'
if os.path.exists(file_path):
    df_coaches = pd.read_csv(file_path)
    coaches_list = df_coaches['מאמן'].unique()
    
    tab1, tab2 = st.tabs(["📋 הזנת העדפות", "📅 לוח שיבוץ סופי"])
    
    with tab1:
        current_coach = st.selectbox("בחר שם מאמן:", ["בחר מאמן"] + list(coaches_list))
        if current_coach != "בחר מאמן":
            # בדיקה כמה קבוצות יש למאמן
            num_teams = 2 if current_coach in ['שי', 'אלברטו'] else 1
            st.info(f"שלום {current_coach}, למערכת ידוע שיש לך {num_teams} קבוצות. בחר 4 ימים:")
            
            # שליפת בחירות קיימות כדי שלא יימחקו מהמסך
            saved = [r['Unique'] for r in st.session_state.db if r['Coach'] == current_coach]
            
            new_selections = []
            for i, day_name in enumerate(days):
                st.markdown(f"#### {day_labels[i]}")
                col1, col2 = st.columns(2)
                # סבב מוקדם
                u_early = f"{day_name}_מוקדם"
                if col1.checkbox("מוקדם (16:30-19:30)", key=f"cb_{current_coach}_{u_early}", value=u_early in saved):
                    new_selections.append({"Coach": current_coach, "Day": day_name, "Shift": "מוקדם", "Unique": u_early})
                # סבב מאוחר
                u_late = f"{day_name}_מאוחר"
                if col2.checkbox("מאוחר (18:00-21:00)", key=f"cb_{current_coach}_{u_late}", value=u_late in saved):
                    new_selections.append({"Coach": current_coach, "Day": day_name, "Shift": "מאוחר", "Unique": u_late})

            if st.button("שמור ועדכן שיבוץ"):
                if len(set([x['Day'] for x in new_selections])) < 4:
                    st.error("חובה לבחור לפחות 4 ימים!")
                else:
                    # שליחה לגוגל ועדכון זיכרון
                    for sel in new_selections:
                        requests.post(FORM_SUBMIT_URL, data={IDS["coach"]: sel["Coach"], IDS["day"]: sel["Day"], IDS["shift"]: sel["Shift"]})
                    st.session_state.db = [r for r in st.session_state.db if r['Coach'] != current_coach]
                    st.session_state.db.extend(new_selections)
                    st.success("הבחירה נשמרה!")

    with tab2:
        st.subheader("הצבה אוטומטית במגרשים")
        
        # בניית לוח ריק לפי שעות אימון אמיתיות
        grid = []
        for day in days:
            for slot in SLOTS:
                for field in FIELDS:
                    grid.append({"יום": day, "שעה": slot, "מגרש": field, "מאמן": ""})
        df_grid = pd.DataFrame(grid)

        # אלגוריתם הצבה חכם
        for day in days:
            # רשימת המאמנים שביקשו את היום הזה
            daily_reqs = [r for r in st.session_state.db if r['Day'] == day]
            
            for req in daily_reqs:
                coach = req['Coach']
                shift = req['Shift']
                
                # קביעת טווח השעות לפי הסבב
                allowed_slots = ['16:30-18:00', '18:00-19:30'] if shift == "מוקדם" else ['18:00-19:30', '19:30-21:00']
                
                # מציאת מקום פנוי ראשון בטווח
                for slot in allowed_slots:
                    mask = (df_grid['יום'] == day) & (df_grid['שעה'] == slot) & (df_grid['מאמן'] == "")
                    free_indices = df_grid[mask].index
                    if len(free_indices) > 0:
                        df_grid.at[free_indices[0], 'מאמן'] = coach
                        break # מאמן שובץ, עוברים לבקשה הבאה

        # תצוגה
        pivot = df_grid.pivot_table(index=['שעה', 'מגרש'], columns='יום', values='מאמן', aggfunc='first').reindex(columns=days)
        pivot.columns = day_labels
        st.table(pivot)

else:
    st.error("קובץ המאמנים חסר.")
