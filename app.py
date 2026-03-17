import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="ניהול מגרשים - הפועל הרצליה", layout="wide")

st.markdown("<h1 style='text-align: center; color: red;'>⚽ הפועל הרצליה - מערכת שיבוץ חכמה</h1>", unsafe_allow_html=True)

# חישוב תאריכים לשבוע הקרוב (החל מיום ראשון 22/03/2026)
start_date = datetime(2026, 3, 22)
days_with_dates = [(start_date + timedelta(days=i)).strftime("%d/%m") for i in range(5)]
days = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי']
day_labels = [f"יום {d} ({date})" for d, date in zip(days, days_with_dates)]

shifts = ['מוקדם (16:30-19:30)', 'מאוחר (18:00-21:00)']
field_parts = [
    ('מגרש 1', 'חצי קדמי'), ('מגרש 1', 'חצי אחורי'),
    ('מגרש 2', 'חצי קדמי'), ('מגרש 2', 'חצי אחורי')
]

# ניהול נתונים (State)
if 'db' not in st.session_state:
    st.session_state.db = []
if 'last_coach' not in st.session_state:
    st.session_state.last_coach = "בחר מאמן"

# טעינת מאמנים מהקובץ שהעלית
file_path = 'טבלת מאמנים.csv'
if os.path.exists(file_path):
    coaches = pd.read_csv(file_path)['מאמן'].unique()
    
    tab1, tab2 = st.tabs(["📋 הזנת העדפות מאמנים", "📅 לוח שיבוץ שבועי"])
    
    with tab1:
        current_coach = st.selectbox("בחר שם מאמן:", ["בחר מאמן"] + list(coaches))
        
        # אם החלפנו מאמן - מרעננים את הדף כדי לטעון את הבחירות שלו
        if current_coach != st.session_state.last_coach:
            st.session_state.last_coach = current_coach
            st.rerun()

        if current_coach != "בחר מאמן":
            # שליפת בחירות קיימות של המאמן מה"בסיס נתונים"
            saved_choices = [row['סבב_יום'] for row in st.session_state.db if row['מאמן'] == current_coach]
            
            st.write(f"שלום **{current_coach}**, אלו הבחירות שלך לשבוע של ה-{days_with_dates[0]}:")
            
            current_selections = []
            for i, label in enumerate(day_labels):
                st.write(f"**{label}**")
                cols = st.columns(2)
                for j, shift in enumerate(shifts):
                    unique_key = f"{days[i]}_{shift}"
                    # הצגת הצ'קבוקס מסומן אם הוא קיים בזיכרון
                    is_checked = unique_key in saved_choices
                    if cols[j].checkbox(f"{shift}", key=f"cb_{unique_key}", value=is_checked):
                        current_selections.append({"יום": days[i], "סבב": shift, "סבב_יום": unique_key, "מאמן": current_coach})
            
            if st.button("שמור ועדכן שיבוץ"):
                unique_days_count = len(set([x['יום'] for x in current_selections]))
                if unique_days_count < 4:
                    st.error(f"בחרת רק {unique_days_count} ימים. חובה לסמן לפחות 4 ימים שונים.")
                else:
                    # מחיקת הישן והוספת החדש (Update)
                    st.session_state.db = [row for row in st.session_state.db if row['מאמן'] != current_coach]
                    st.session_state.db.extend(current_selections)
                    st.success("הבחירות עודכנו ונשמרו בלוח!")
                    st.balloons()

    with tab2:
        st.subheader(f"לוח שיבוץ - שבוע {days_with_dates[0]}-{days_with_dates[-1]}")
        
        # יצירת לוח ריק להצבה
        schedule = []
        for day in days:
            for shift in shifts:
                for field, part in field_parts:
                    schedule.append({"יום": day, "סבב": shift, "מגרש": field, "מיקום": part, "מאמן": ""})
        df_schedule = pd.DataFrame(schedule)

        # הצבת מאמנים לתוך הלוח (אלגוריתם חלוקת מגרשים)
        for record in st.session_state.db:
            mask = (df_schedule['יום'] == record['יום']) & \
                   (df_schedule['סבב'] == record['סבב']) & \
                   (df_schedule['מאמן'] == "")
            
            free_slots = df_schedule[mask].index
            if len(free_slots) > 0:
                df_schedule.at[free_slots[0], 'מאמן'] = record['מאמן']

        # תצוגה מעוצבת של הטבלה
        st.dataframe(df_schedule, use_container_width=True, height=600)

else:
    st.error("קובץ 'טבלת מאמנים.csv' לא נמצא ב-GitHub.")
