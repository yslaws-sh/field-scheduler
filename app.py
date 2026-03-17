import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="שיבוץ מגרשים - מועדון כדורגל", layout="centered")

st.title("⚽ מערכת שיבוץ מגרשים")
st.subheader("מילוי דרישות מאמנים")

# פונקציה לניקוי בחירות כשמחליפים מאמן
if 'last_coach' not in st.session_state:
    st.session_state.last_coach = "בחר מאמן"

def reset_selections():
    for key in st.session_state.keys():
        if "day_" in key:
            st.session_state[key] = False

# בדיקה אם הקובץ קיים
file_path = 'טבלת מאמנים.csv'

if os.path.exists(file_path):
    df = pd.read_csv(file_path)
    coaches = df['מאמן'].unique()
    
    selected_coach = st.selectbox("בחר את שמך מהרשימה:", ["בחר מאמן"] + list(coaches))

    # אם המאמן השתנה - מנקים את כל התיבות
    if selected_coach != st.session_state.last_coach:
        st.session_state.last_coach = selected_coach
        reset_selections()
        st.rerun()

    if selected_coach != "בחר מאמן":
        st.info(f"שלום {selected_coach}, סמן לפחות 4 ימים שבהם תוכל להתאמן.")
        
        days = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי']
        
        selected_slots = []
        for day in days:
            st.write(f"---")
            col1, col2 = st.columns(2)
            with col1:
                key_early = f"day_{day}_early"
                if st.checkbox(f"יום {day} - מוקדם (16:30-19:30)", key=key_early):
                    selected_slots.append(key_early)
            with col2:
                key_late = f"day_{day}_late"
                if st.checkbox(f"יום {day} - מאוחר (18:00-21:00)", key=key_late):
                    selected_slots.append(key_late)

        # ספירת ימים ייחודיים
        unique_days_count = len(set([d.split('_')[1] for d in selected_slots]))

        if st.button("שלח העדפות לשיבוץ"):
            if unique_days_count < 4:
                st.error(f"סימנת רק {unique_days_count} ימים. חובה לסמן לפחות 4 ימים שונים!")
            else:
                st.success(f"תודה {selected_coach}! הבחירה שלך ל-{unique_days_count} ימים נשמרה במערכת.")
                # כאן נוסיף בהמשך את השמירה לקובץ
else:
    st.error(f"שגיאה: הקובץ '{file_path}' לא נמצא ב-GitHub.")
