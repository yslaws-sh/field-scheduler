import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="ניהול מגרשים - הפועל הרצליה", layout="wide")

st.markdown("<h1 style='text-align: center; color: red;'>⚽ הפועל הרצליה - מערכת שיבוץ חכמה</h1>", unsafe_allow_html=True)

# הגדרות יסוד
days = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי']
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

def reset_ui():
    for key in st.session_state.keys():
        if "choice_" in key: st.session_state[key] = False

# טעינת מאמנים
file_path = 'טבלת מאמנים.csv'
if os.path.exists(file_path):
    coaches = pd.read_csv(file_path)['מאמן'].unique()
    
    tab1, tab2 = st.tabs(["📋 הזנת העדפות מאמנים", "📅 לוח שיבוץ מגרשים"])
    
    with tab1:
        current_coach = st.selectbox("בחר שם מאמן:", ["בחר מאמן"] + list(coaches))
        
        if current_coach != st.session_state.last_coach:
            st.session_state.last_coach = current_coach
            reset_ui()
            st.rerun()

        if current_coach != "בחר מאמן":
            st.write(f"שלום **{current_coach}**, בחר את הסבב המועדף (חובה ב-4 ימים):")
            current_selections = []
            
            for day in days:
                st.write(f"**יום {day}**")
                cols = st.columns(2)
                for i, shift in enumerate(shifts):
                    if cols[i].checkbox(f"{shift}", key=f"choice_{day}_{i}"):
                        current_selections.append((day, shift))
            
            if st.button("שמור שיבוץ"):
                unique_days = len(set([x[0] for x in current_selections]))
                if unique_days < 4:
                    st.error(f"בחרת רק {unique_days} ימים. חובה לסמן 4 ימים שונים.")
                else:
                    # מחיקת בחירות קודמות של אותו מאמן (למניעת כפילויות)
                    st.session_state.db = [row for row in st.session_state.db if row['מאמן'] != current_coach]
                    
                    for day, shift in current_selections:
                        st.session_state.db.append({"יום": day, "סבב": shift, "מאמן": current_coach})
                    st.success("הבחירות נשמרו!")
                    st.balloons()

    with tab2:
        st.subheader("לוח שיבוץ מגרשים - הצבה אוטומטית")
        
        # יצירת לוח ריק
        schedule = []
        for day in days:
            for shift in shifts:
                for field, part in field_parts:
                    schedule.append({
                        "יום": day, "סבב": shift, "מגרש": field, "מיקום": part, "מאמן": ""
                    })
        df_schedule = pd.DataFrame(schedule)

        # הצבת מאמנים לתוך הלוח לפי הבחירות שלהם
        for record in st.session_state.db:
            # מוצאים משבצת פנויה ביום ובסבב שנבחרו
            mask = (df_schedule['יום'] == record['יום']) & \
                   (df_schedule['סבב'] == record['סבב']) & \
                   (df_schedule['מאמן'] == "")
            
            first_free_index = df_schedule[mask].index
            if len(first_free_index) > 0:
                df_schedule.at[first_free_index[0], 'מאמן'] = record['מאמן']

        # תצוגה
        st.dataframe(df_schedule, use_container_width=True, height=600)

else:
    st.error("קובץ המאמנים חסר.")
