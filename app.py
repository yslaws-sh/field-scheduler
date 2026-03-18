import streamlit as st
import pandas as pd
import requests
import os
import io
from datetime import datetime, timedelta

# הגדרות אפליקציה רשמית
st.set_page_config(page_title="הפועל הרצליה - מערכת ניהול", page_icon="⚽", layout="wide")

# עיצוב RTL ויישור לימין
st.markdown("""
    <style>
    .main { direction: rtl; text-align: right; background-color: #f8f9fa; }
    body { direction: rtl; }
    .main-header { background-color: #e31e24; padding: 20px; border-radius: 0 0 20px 20px; color: white; text-align: center; margin-bottom: 20px; }
    .stButton>button { width: 100%; height: 3.5em; background-color: #e31e24 !important; color: white !important; border-radius: 12px; font-weight: bold; }
    th, td { text-align: center !important; border: 1px solid #dee2e6 !important; }
    </style>
    <div class="main-header">
        <h1 style='margin:0; font-size: 24px;'>מועדון כדורגל הפועל הרצליה</h1>
        <p style='margin:0; font-size: 16px;'>מערכת ניהול ושיבוץ חכמה</p>
    </div>
    """, unsafe_allow_html=True)

# --- הגדרות מגרשים ורבעים מעודכנות ---
ALL_FIELD_OPTIONS = [
    'קאנטרי קדמי 1', 'קאנטרי קדמי 2', 'קאנטרי אחורי 1', 'קאנטרי אחורי 2',
    'משק קדמי 1', 'משק קדמי 2', 'משק אחורי 1', 'משק אחורי 2',
    'סינטטי קטן'  # המגרש החדש
]

if 'active_fields' not in st.session_state:
    st.session_state.active_fields = ALL_FIELD_OPTIONS
if 'active_slots' not in st.session_state:
    st.session_state.active_slots = ['16:30-18:00', '18:00-19:30', '19:30-21:00']

# תאריכים לשבוע ה-22/03
start_date = datetime(2026, 3, 22)
days_list = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי']
day_labels = [(start_date + timedelta(days=i)).strftime(f"יום {days_list[i]} %d/%m") for i in range(5)]

if 'db' not in st.session_state: st.session_state.db = []
if 'admin_access' not in st.session_state: st.session_state.admin_access = False

file_path = 'טבלת מאמנים.csv'
if os.path.exists(file_path):
    df_info = pd.read_csv(file_path)
    df_info['full_id'] = df_info['שם הקבוצה'] + " (" + df_info['מאמן'] + ")"
    
    tab_titles = ["📝 הזנת העדפות"]
    if st.session_state.admin_access: tab_titles.append("⚙️ ניהול מגרשים ושיבוץ")
    active_tabs = st.tabs(tab_titles)
    
    # --- טאב 1: מאמנים ---
    with active_tabs[0]:
        selected_team_id = st.selectbox("בחר קבוצה:", ["לחץ לבחירה..."] + df_info['full_id'].tolist())
        if selected_team_id != "לחץ לבחירה...":
            row = df_info[df_info['full_id'] == selected_team_id].iloc[0]
            
            # משפט הגמישות
            st.info(f"💡 **הודעה לקבוצת {row['שם הקבוצה']}:** עליך לסמן לפחות 4 ימים שונים. ככל שתיתן לנו יותר גמישות בשעות ובאפשרויות, כך נוכל לבוא לקראתך ולשבץ אותך במגרש המועדף עליך!")

            saved = [r['Unique'] for r in st.session_state.db if r['TeamID'] == selected_team_id]
            new_selections = []
            for d_label in day_labels:
                with st.expander(f"📅 {d_label}", expanded=True):
                    col1, col2 = st.columns(2)
                    u_early, u_late = f"{d_label}_מוקדם", f"{d_label}_מאוחר"
                    if col1.checkbox("☀️ מוקדם (משמרת 1)", key=f"cb_{selected_team_id}_{u_early}", value=(u_early in saved)):
                        new_selections.append({"TeamID": selected_team_id, "Coach": row['מאמן'], "Day": d_label, "Shift": "מוקדם", "Unique": u_early})
                    if col2.checkbox("🌙 מאוחר (משמרת 2)", key=f"cb_{selected_team_id}_{u_late}", value=(u_late in saved)):
                        new_selections.append({"TeamID": selected_team_id, "Coach": row['מאמן'], "Day": d_label, "Shift": "מאוחר", "Unique": u_late})

            if st.button("שמור העדפות 🚀"):
                if len(set([x['Day'] for x in new_selections])) < 4:
                    st.error("❌ חובה לסמן לפחות 4 ימים שונים.")
                else:
                    st.session_state.db = [r for r in st.session_state.db if r['TeamID'] != selected_team_id]
                    st.session_state.db.extend(new_selections)
                    st.success("הבחירה נשמרה בהצלחה! תודה על הגמישות.")
                    st.balloons()
        
        if not st.session_state.admin_access:
            st.markdown("---")
            admin_key = st.text_input("כניסת מנהל (סיסמה):", type="password")
            if admin_key == "1906":
                st.session_state.admin_access = True
                st.rerun()

    # --- טאב 2: מנהל ---
    if st.session_state.admin_access:
        with active_tabs[1]:
            st.subheader("🛠️ מרכז שליטה למנהל - ניהול מגרשים")
            col_cfg1, col_cfg2 = st.columns(2)
            
            with col_cfg1:
                st.session_state.active_fields = st.multiselect(
                    "בחר אילו מגרשים/רבעים פעילים השבוע:",
                    ALL_FIELD_OPTIONS,
                    default=st.session_state.active_fields
                )
            
            with col_cfg2:
                slot_input = st.text_input("זמני אימונים (הפרד בפסיק):", value=",".join(st.session_state.active_slots))
                st.session_state.active_slots = [s.strip() for s in slot_input.split(",")]

            st.markdown("---")
            
            # לוגיקת שיבוץ
            grid = []
            for d in day_labels:
                for s in st.session_state.active_slots:
                    for f in st.session_state.active_fields:
                        grid.append({"יום": d, "שעה": s, "מגרש": f, "שיבוץ": "", "מאמן": ""})
            df_grid = pd.DataFrame(grid)
            
            usage = {tid: 0 for tid in df_info['full_id']}
            quota = {row['full_id']: int(row['מספר אימונים']) for _, row in df_info.iterrows()}

            # שיבוץ לפי היררכיה
            for tid in df_info['full_id'].tolist():
                team_reqs = [r for r in st.session_state.db if r['TeamID'] == tid]
                for req in team_reqs:
                    if usage[tid] >= quota[tid]: break
                    day, coach = req['Day'], req['Coach']
                    if len(df_grid[(df_grid['יום'] == day) & (df_grid['שיבוץ'] == tid)]) >= 1: continue
                    
                    prev_assignment = df_grid[(df_grid['יום'] == day) & (df_grid['מאמן'] == coach)]
                    half = len(st.session_state.active_slots) // 2
                    allowed = st.session_state.active_slots[:half+1] if req['Shift'] == "מוקדם" else st.session_state.active_slots[half:]
                    
                    for slot in allowed:
                        if not prev_assignment.empty:
                            target_f = prev_assignment.iloc[0]['מגרש']
                            mask = (df_grid['יום'] == day) & (df_grid['שעה'] == slot) & (df_grid['מגרש'] == target_f) & (df_grid['שיבוץ'] == "")
                        else:
                            mask = (df_grid['יום'] == day) & (df_grid['שעה'] == slot) & (df_grid['שיבוץ'] == "") & (df_grid['מאמן'] != coach)
                        
                        free_idx = df_grid[mask].index
                        if len(free_idx) > 0:
                            df_grid.at[free_idx[0], 'שיבוץ'] = tid
                            df_grid.at[free_idx[0], 'מאמן'] = coach
                            usage[tid] += 1
                            break

            if not df_grid.empty:
                final_df = df_grid.pivot_table(index=['שעה', 'מגרש'], columns='יום', values='שיבוץ', aggfunc='first', fill_value="").reset_index()
                st.table(final_df)
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    final_df.to_excel(writer, sheet_name='Herzliya', index=False)
                    workbook, worksheet = writer.book, writer.sheets['Herzliya']
                    f_red = workbook.add_format({'bg_color': '#FF9999', 'border': 1, 'align': 'center', 'bold': True})
                    f_blue = workbook.add_format({'bg_color': '#99CCFF', 'border': 1, 'align': 'center', 'bold': True})
                    f_green = workbook.add_format({'bg_color': '#C6EFCE', 'border': 1, 'align': 'center', 'bold': True}) # צבע למגרש סינטטי
                    
                    for r_num in range(len(final_df)):
                        m_val = str(final_df.iloc[r_num]['מגרש'])
                        if "קאנטרי" in m_val: fmt = f_red
                        elif "משק" in m_val: fmt = f_blue
                        else: fmt = f_green # סינטטי קטן
                        
                        worksheet.set_row(r_num + 1, 30, fmt)
                    worksheet.set_column('A:B', 25)
                    worksheet.set_column('C:G', 25)
                st.download_button("📥 הורד לוח לצילום מסך", data=output.getvalue(), file_name="hapoel_schedule.xlsx")

            if st.button("🔴 יציאה ממצב מנהל"):
                st.session_state.admin_access = False
                st.rerun()
else:
    st.error("קובץ CSV חסר ב-GitHub")
