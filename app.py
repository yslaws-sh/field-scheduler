import streamlit as st
import pandas as pd
import requests
import os
import io
from datetime import datetime, timedelta

# הגדרות אפליקציה רשמית
st.set_page_config(page_title="הפועל הרצליה - מערכת ניהול", page_icon="⚽", layout="wide")

# עיצוב RTL
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

# --- הגדרות חיבור לגוגל ---
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSd-HaGeFh0P_zU7xs1kiFjLnM5i2mjZhiaRTcUD4h_L0ETksA/formResponse"
SHEET_TSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR8In1pn4dPWFvpIrxj1eLufbA7KQ6_wupxQiDbfxsAmvjsHrsO8ehPc3f5fT0TbenxVaLr8Tet6h5u/pub?output=tsv"

IDS = {
    "coach": "entry.1199305397",
    "day": "entry.1231450869",
    "shift": "entry.1001387245"
}

# פונקציה למשיכת נתונים מהגיליון
def load_google_data():
    try:
        res = requests.get(SHEET_TSV_URL)
        if res.status_code == 200:
            df = pd.read_csv(io.StringIO(res.text), sep='\t')
            # התאמת שמות עמודות מגוגל שיטס (לפי הסדר בטופס)
            df.columns = ['Timestamp', 'CoachSelection', 'DaySelection', 'ShiftSelection']
            return df
    except:
        pass
    return pd.DataFrame()

# --- הגדרות מערכת ---
ALL_FIELDS = ['קאנטרי קדמי 1', 'קאנטרי קדמי 2', 'קאנטרי אחורי 1', 'קאנטרי אחורי 2', 'משק קדמי 1', 'משק קדמי 2', 'משק אחורי 1', 'משק אחורי 2', 'סינטטי קטן']
if 'active_fields' not in st.session_state: st.session_state.active_fields = ALL_FIELDS
if 'active_slots' not in st.session_state: st.session_state.active_slots = ['16:30-18:00', '18:00-19:30', '19:30-21:00']

start_date = datetime(2026, 3, 22)
days_list = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי']
day_labels = [(start_date + timedelta(days=i)).strftime(f"יום {days_list[i]} %d/%m") for i in range(5)]

file_path = 'טבלת מאמנים.csv'
if os.path.exists(file_path):
    df_info = pd.read_csv(file_path)
    df_info['full_id'] = df_info['שם הקבוצה'] + " (" + df_info['מאמן'] + ")"
    
    tabs = ["📝 הזנת העדפות", "⚙️ ניהול מגרשים ושיבוץ"]
    active_tabs = st.tabs(tabs)
    
    with active_tabs[0]:
        selected_team = st.selectbox("בחר קבוצה:", ["לחץ לבחירה..."] + df_info['full_id'].tolist())
        if selected_team != "לחץ לבחירה...":
            row = df_info[df_info['full_id'] == selected_team].iloc[0]
            st.info(f"💡 **הודעה לקבוצת {row['שם הקבוצה']}:** סמנו לפחות 4 ימים שונים.")

            slots = st.session_state.active_slots
            mid = len(slots) // 2
            early_txt = f"{slots[0].split('-')[0]}-{slots[mid].split('-')[-1]}"
            late_txt = f"{slots[mid].split('-')[0]}-{slots[-1].split('-')[-1]}"

            new_selections = []
            for d_label in day_labels:
                with st.expander(f"📅 {d_label}", expanded=True):
                    col1, col2 = st.columns(2)
                    if col1.checkbox(f"☀️ מוקדם ({early_txt})", key=f"e_{selected_team}_{d_label}"):
                        new_selections.append({"Day": d_label, "Shift": "מוקדם"})
                    if col2.checkbox(f"🌙 מאוחר ({late_txt})", key=f"l_{selected_team}_{d_label}"):
                        new_selections.append({"Day": d_label, "Shift": "מאוחר"})

            if st.button("שמור העדפות 🚀"):
                if len(set([x['Day'] for x in new_selections])) < 4:
                    st.error("❌ חובה לסמן לפחות 4 ימים שונים.")
                else:
                    with st.spinner("שומר בגיליון המרכזי..."):
                        for sel in new_selections:
                            data = {IDS["coach"]: selected_team, IDS["day"]: sel["Day"], IDS["shift"]: sel["Shift"]}
                            requests.post(FORM_URL, data=data)
                    st.success("הבחירה נשמרה בהצלחה!")
                    st.balloons()

    with active_tabs[1]:
        admin_key = st.text_input("סיסמת מנהל:", type="password")
        if admin_key == "1906":
            st.subheader("🛠️ הגדרות מגרשים ושיבוץ")
            
            c1, c2 = st.columns(2)
            with c1:
                st.session_state.active_fields = st.multiselect("מגרשים פעילים:", ALL_FIELDS, default=st.session_state.active_fields)
            with c2:
                slot_input = st.text_input("זמני אימונים:", value=",".join(st.session_state.active_slots))
                current_slots = [s.strip() for s in slot_input.split(",")]
                st.session_state.active_slots = current_slots

            # טעינת נתונים מגוגל
            raw_responses = load_google_data()
            
            if not raw_responses.empty:
                # לוגיקת שיבוץ על בסיס הנתונים מגוגל
                grid = []
                for d in day_labels:
                    for s in current_slots:
                        for f in st.session_state.active_fields:
                            grid.append({"יום": d, "שעה": s, "מגרש": f, "שיבוץ": "", "מאמן": ""})
                df_grid = pd.DataFrame(grid)
                
                usage = {tid: 0 for tid in df_info['full_id']}
                quota = {row['full_id']: int(row['מספר אימונים']) for _, row in df_info.iterrows()}

                for tid in df_info['full_id'].tolist():
                    # מושך מהגיליון רק את הבחירות של הקבוצה הספציפית
                    team_reqs = raw_responses[raw_responses['CoachSelection'] == tid]
                    for _, req in team_reqs.iterrows():
                        if usage[tid] >= quota[tid]: break
                        day, shift = req['DaySelection'], req['ShiftSelection']
                        
                        # מונע כפל באותו יום
                        if len(df_grid[(df_grid['יום'] == day) & (df_grid['שיבוץ'] == tid)]) >= 1: continue
                        
                        half = len(current_slots) // 2
                        allowed = current_slots[:half+1] if shift == "מוקדם" else current_slots[half:]
                        
                        coach_name = tid.split('(')[-1].replace(')', '').strip()
                        for slot in allowed:
                            prev = df_grid[(df_grid['יום'] == day) & (df_grid['מאמן'] == coach_name)]
                            if not prev.empty:
                                target_f = prev.iloc[0]['מגרש']
                                mask = (df_grid['יום'] == day) & (df_grid['שעה'] == slot) & (df_grid['מגרש'] == target_f) & (df_grid['שיבוץ'] == "")
                            else:
                                mask = (df_grid['יום'] == day) & (df_grid['שעה'] == slot) & (df_grid['שיבוץ'] == "") & (df_grid['מאמן'] != coach_name)
                            
                            idx = df_grid[mask].index
                            if len(idx) > 0:
                                df_grid.at[idx[0], 'שיבוץ'] = tid
                                df_grid.at[idx[0], 'מאמן'] = coach_name
                                usage[tid] += 1
                                break

                # יצירת הטבלה הסופית
                final_df = df_grid.pivot_table(index=['שעה', 'מגרש'], columns='יום', values='שיבוץ', aggfunc='first', fill_value="").reset_index()
                final_df['שעה'] = pd.Categorical(final_df['שעה'], categories=current_slots, ordered=True)
                final_df = final_df.sort_values(['שעה', 'מגרש'])

                st.write("### 📅 לוח שיבוץ סופי (מבוסס תשובות מאמנים)")
                
                def color_rows(row):
                    m = str(row['מגרש'])
                    if "קאנטרי" in m: c = '#ffcccc'
                    elif "משק" in m: c = '#cce5ff'
                    else: c = '#C6EFCE'
                    return [f'background-color: {c}'] * len(row)

                st.table(final_df.style.apply(color_rows, axis=1))
                
                # יצירת קובץ להורדה
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    final_df.to_excel(writer, sheet_name='Hapoel', index=False)
                    workbook, worksheet = writer.book, writer.sheets['Hapoel']
                    f_red = workbook.add_format({'bg_color': '#FF9999', 'border': 1})
                    f_blue = workbook.add_format({'bg_color': '#99CCFF', 'border': 1})
                    f_green = workbook.add_format({'bg_color': '#C6EFCE', 'border': 1})
                    for r_num in range(len(final_df)):
                        m_val = str(final_df.iloc[r_num]['מגרש'])
                        fmt = f_red if "קאנטרי" in m_val else f_blue if "משק" in m_val else f_green
                        worksheet.set_row(r_num + 1, 30, fmt)
                    worksheet.set_column('A:B', 20)
                
                st.download_button("📥 הורד קובץ אקסל לשיבוץ", data=output.getvalue(), file_name="hapoel_final_schedule.xlsx")
            else:
                st.warning("הגיליון ריק. וודאו שמאמנים מילאו את ההעדפות.")

else:
    st.error("קובץ CSV חסר")
