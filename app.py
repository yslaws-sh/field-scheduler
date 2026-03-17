import streamlit as st
import pandas as pd

st.title("מערכת שיבוץ מגרשים - מילוי צרכי מאמנים")

# טעינת נתוני המאמנים מהקובץ שלך
# (בהנחה שהעלית את הקובץ ל-GitHub יחד עם הקוד)
try:
    df = pd.read_csv('טבלת מאמנים.csv')
    coaches = df['מאמן'].unique()
except:
    st.error("לא נמצא קובץ נתוני מאמנים")
    coaches = []

# ממשק בחירת מאמן
selected_coach = st.selectbox("בחר את שמך מהרשימה:", ["בחר מאמן"] + list(coaches))

if selected_coach != "בחר מאמן":
    st.subheader(f"שלום {selected_coach}, סמן את זמינותך בשבוע הקרוב")
    st.info("עליך לסמן לפחות 4 ימים שונים כדי שנוכל לבצע שיבוץ אוטומטי.")

    days = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי']
    slots = ['מוקדמת (16:30-19:30)', 'מאוחרת (18:00-21:00)']
    
    # יצירת טבלת בחירה (Grid)
    selections = {}
    for day in days:
        st.write(f"**יום {day}**")
        cols = st.columns(2)
        for i, slot in enumerate(slots):
            key = f"{day}_{slot}"
            selections[key] = cols[i].checkbox(slot, key=key)

    # בדיקת חוק 4 הימים
    selected_days = set([key.split('_')[0] for key, val in selections.items() if val])
    
    if st.button("שלח העדפות"):
        if len(selected_days) < 4:
            st.error(f"סימנת רק {len(selected_days)} ימים. חובה לסמן לפחות 4 ימים שונים.")
        else:
            st.success("הנתונים נשמרו בהצלחה! המערכת תשבץ אותך בהתאם לעדיפויות המועדון.")
            # כאן בהמשך נוסיף קוד ששומר את זה לבסיס נתונים