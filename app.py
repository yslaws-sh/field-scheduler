import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="ניהול מגרשים - שיבוץ חכם", layout="wide")

st.title("⚽ מערכת שיבוץ מגרשים חכמה")

# פונקציה לניקוי בחירות כשמחליפים מאמן
if 'last_coach' not in st.session_state:
    st.session_state.last_coach = "בחר מאמן"

def reset_selections():
    for key in st.session_state.keys():
        if "day_" in key:
            st.session_state[key] = False

# הגדרת מבנה המגרשים
FIELDS = {
    'מגרש 1': ['חצי קדמי (רבע 1-2)', 'חצי אחורי (רבע 3-4)'],
    'מגרש 2': ['חצי קדמי (רבע 5-6)', 'חצי אחורי (רבע 7-8)']
}

file_path = 'טבלת מאמנים.csv'

if os.path.exists(file_path):
    df = pd.read_csv(file_path)
    coaches = df['מאמן'].unique()
    
    tab1, tab2 = st.tabs(["📋 מילוי דרישות מאמנים", "📅 לוח שיבוץ מגרשים"])
    
    with tab1:
        selected_coach = st.selectbox("בחר את שמך מהרשימה:", ["בחר מאמן"] + list(coaches))

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

            if st.button("שלח העדפות לשיבוץ"):
                unique_days = len(set([d.split('_')[1] for d in selected_slots]))
                if unique_days < 4:
                    st.error(f"סימנת רק {unique_days} ימים. חובה לסמן 4.")
                else:
                    st.success(f"הבחירה של {selected_coach} נשמרה!")

    with tab2:
        st.subheader("שיבוץ שבועי לפי מגרשים וחלקים")
        days = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי']
        times = ['מוקדם (16:30-19:30)', 'מאוחר (18:00-21:00)']
        
        grid_data = []
        for day in days:
            for time in times:
                for field, parts in FIELDS.items():
                    for part in parts:
                        grid_data.append({
                            "יום": day, "שעה": time, "מגרש": field, "מיקום": part, "מאמן/קבוצה": "---"
                        })
        
        st.dataframe(pd.DataFrame(grid_data), use_container_width=True, height=600)

else:
    st.error("קובץ 'טבלת מאמנים.csv' חסר ב-GitHub")
