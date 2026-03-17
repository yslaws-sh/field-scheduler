import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="ניהול מגרשים - מועדון כדורגל", layout="wide")

st.title("⚽ מערכת שיבוץ מגרשים חכמה")

# הגדרת מבנה המגרשים
FIELDS = {
    'מגרש 1': ['חצי קדמי (רבע 1-2)', 'חצי אחורי (רבע 3-4)'],
    'מגרש 2': ['חצי קדמי (רבע 5-6)', 'חצי אחורי (רבע 7-8)']
}

# פונקציה לניקוי בחירות
if 'last_coach' not in st.session_state:
    st.session_state.last_coach = "בחר מאמן"

def reset_selections():
    for key in st.session_state.keys():
        if "day_" in key:
            st.session_state[key] = False

# טעינת קובץ המאמנים
file_path = 'טבלת מאמנים.csv'
if os.path.exists(file_path):
    df_coaches = pd.read_csv(file_path)
    coaches_list = df_coaches['מאמן'].unique()
    
    tab1, tab2 = st.tabs(["📋 מילוי דרישות מאמנים", "📅 לוח שיבוץ ויזואלי"])
    
    with tab1:
        selected_coach = st.selectbox("בחר את שמך מהרשימה:", ["בחר מאמן"] + list(coaches_list))

        if selected_coach != st.session_state.last_coach:
            st.session_state.last_coach = selected_coach
            reset_selections()
            st.rerun()

        if selected_coach != "בחר מאמן":
            st.info(f"שלום {selected_coach}, סמן לפחות 4 ימים שבהם תוכל להתאמן.")
            days = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי']
            selected_slots = []
            
            for day in days:
                st.markdown(f"### יום {day}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.checkbox(f"מוקדם (16:30-19:30)", key=f"day_{day}_early"):
                        selected_slots.append(f"{day} מוקדם")
                with col2:
                    if st.checkbox(f"מאוחר (18:00-21:00)", key=f"day_{day}_late"):
                        selected_slots.append(f"{day} מאוחר")

            if st.button("שלח העדפות לשיבוץ"):
                unique_days = len(set([s.split(' ')[0] for s in selected_slots]))
                if unique_days < 4:
                    st.error(f"סימנת רק {unique_days} ימים. חובה לסמן לפחות 4 ימים שונים!")
                else:
                    st.success(f"הבחירה של {selected_coach} נשמרה בהצלחה!")
                    st.balloons()
                    # כאן אפשר להוסיף שמירה לקובץ מקומי או שליחה למייל

    with tab2:
        st.subheader("לוח שיבוץ שבועי")
        days = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי']
        times = ['מוקדם (16:30-19:30)', 'מאוחר (18:00-21:00)']
        
        # יצירת מבנה הטבלה הוויזואלית שביקשת
        grid = []
        for day in days:
            for time in times:
                for field, parts in FIELDS.items():
                    for part in parts:
                        grid.append({
                            "יום": day,
                            "משמרת": time,
                            "מגרש": field,
                            "מיקום": part,
                            "מאמן משובץ": "" 
                        })
        
        display_df = pd.DataFrame(grid)
        st.dataframe(display_df, use_container_width=True, height=800)

else:
    st.error("קובץ המאמנים לא נמצא.")
