import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

# Set page config
st.set_page_config(page_title="EduInsight | Institute Analytics", layout="wide")

# Load custom CSS
if os.path.exists("styles.css"):
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- Session State Initialization ---
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "🏛️ Overview"
if 'previous_tab' not in st.session_state:
    st.session_state.previous_tab = "🏛️ Overview"
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""

# Helper to load data
def load_data():
    # Force reload by not using cache and checking file existence
    if os.path.exists("institute_data.csv"):
        df = pd.read_csv("institute_data.csv")
        return df
    return pd.DataFrame()

df = load_data()

# --- Sidebar Filters & Navigation ---
st.sidebar.image("https://img.icons8.com/fluency/96/university.png", width=80)
st.sidebar.title("EduInsight Menu")

# Navigation
st.session_state.active_tab = st.sidebar.radio(
    "Navigation", 
    ["🏛️ Overview", "🔍 Search", "🚨 Intervention"],
    index=["🏛️ Overview", "🔍 Search", "🚨 Intervention"].index(st.session_state.active_tab)
)

st.sidebar.markdown("---")
st.sidebar.subheader("Global Filters")

dept_list = ["All"] + sorted(df["Department"].unique().tolist())
selected_dept = st.sidebar.selectbox("Select Department", dept_list)

year_list = ["All"] + sorted(df["Year"].unique().tolist())
selected_year = st.sidebar.selectbox("Select Year", year_list)

# Filter dataframe
filtered_df = df.copy()
if selected_dept != "All":
    filtered_df = filtered_df[filtered_df["Department"] == selected_dept]
if selected_year != "All":
    filtered_df = filtered_df[filtered_df["Year"] == selected_year]

# --- Main Content ---
st.markdown(f"""
    <div class='main-header'>
        <div style='display: flex; justify-content: space-between; align-items: center;'>
            <h1>🎓 EduInsight: {st.session_state.active_tab}</h1>
            {"<button style='background: white; color: #1e3c72; border: none; padding: 8px 15px; border-radius: 5px; font-weight: bold; cursor: pointer;' onclick='window.location.reload()'>🔄 Refresh</button>" if st.session_state.active_tab == "🏛️ Overview" else ""}
        </div>
        <p>Institute-wide Performance Tracking & Intervention</p>
    </div>
""", unsafe_allow_html=True)

# Helper for Back Button
def back_button():
    target = st.session_state.get('previous_tab', '🏛️ Overview')
    if st.button(f"⬅️ Back to {target}"):
        st.session_state.active_tab = target
        st.session_state.search_query = ""
        st.rerun()

# --- Overview View ---
if st.session_state.active_tab == "🏛️ Overview":
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Students", len(filtered_df))
    with col2:
        avg_att = filtered_df["Attendance_Pct"].mean() if not filtered_df.empty else 0
        st.metric("Avg Attendance", f"{avg_att:.1f}%")
    with col3:
        avg_sgpa = filtered_df["SGPA"].mean() if not filtered_df.empty else 0
        st.metric("Avg SGPA", f"{avg_sgpa:.2f}")
    with col4:
        pass_pct = (filtered_df["External_Marks"] >= 28).mean() * 100 if not filtered_df.empty else 0
        st.metric("Pass % (End-Sem)", f"{pass_pct:.1f}%")

    st.markdown("---")
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader(f"Academic Performance by Department ({selected_year if selected_year != 'All' else 'All Years'})")
        if not filtered_df.empty:
            dept_perf = filtered_df.groupby("Department")["SGPA"].mean().reset_index()
            fig_dept = px.bar(dept_perf, x="Department", y="SGPA", color="SGPA", 
                              color_continuous_scale="Blues", template="plotly_white",
                              labels={'SGPA': 'Avg SGPA'})
            st.plotly_chart(fig_dept, use_container_width=True)
        else:
            st.info("No data for current filters.")
        
    with c2:
        st.subheader("Attendance Categories")
        def categorize_attendance(pct):
            if pct >= 75: return "✅ Safe (75%+)"
            if pct >= 50: return "⚠️ Warning (50-75%)"
            return "🚨 Danger (< 50%)"
        
        if not filtered_df.empty:
            filtered_df['Attendance_Status'] = filtered_df['Attendance_Pct'].apply(categorize_attendance)
            att_counts = filtered_df['Attendance_Status'].value_counts().reset_index()
            att_counts.columns = ['Status', 'Student Count']
            
            fig_att = px.bar(att_counts, x="Status", y="Student Count", 
                             color="Status", 
                             color_discrete_map={
                                 "✅ Safe (75%+)": "#00cc96",
                                 "⚠️ Warning (50-75%)": "#ffa500",
                                 "🚨 Danger (< 50%)": "#ff4b4b"
                             },
                             template="plotly_white")
            st.plotly_chart(fig_att, use_container_width=True)
        else:
            st.info("No data for current filters.")

# --- Search View ---
elif st.session_state.active_tab == "🔍 Search":
    back_button()
    st.subheader("Unified Student Search")
    
    # Use session state for the search query
    search_input = st.text_input("Type to Filter (Name or Roll No)", 
                                value=st.session_state.search_query,
                                placeholder="e.g. Aarav or AID SE-01")
    
    st.session_state.search_query = search_input
    
    # Filter the list based on typing
    if search_input:
        search_results = df[
            df["Name"].str.contains(search_input, case=False) | 
            df["Student_ID"].str.contains(search_input, case=False)
        ]
    else:
        # Show all students filtered by sidebar if no search query
        search_results = filtered_df

    if not search_results.empty:
        selected_student_name = st.selectbox("Select Student Profile", search_results["Name"].tolist())
        student = search_results[search_results["Name"] == selected_student_name].iloc[0]
    else:
        st.error("No records found for that search.")
        student = None

    if student is not None:
        st.markdown("---")
        st.markdown(f"<div style='padding: 20px; background: white; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05);'>", unsafe_allow_html=True)
        st.markdown(f"### Profile: {student['Name']} ({student['Student_ID']})")
        p_col1, p_col2 = st.columns(2)
        
        with p_col1:
            st.info(f"**Dept:** {student['Department']}\n\n**Year:** {student['Year']}\n\n**Semester:** {student['Semester']}")
            
            # Radar Chart
            categories = ['Internal', 'External', 'Practical']
            values = [student['Internal_Marks']/30*100, student['External_Marks']/70*100, student['Practical_Marks']/25*100]
            
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=values, theta=categories, fill='toself', name=student['Name'], line_color='#1e3c72'
            ))
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False)
            st.plotly_chart(fig_radar, use_container_width=True)

        with p_col2:
            # Attendance Gauge
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = student['Attendance_Pct'],
                title = {'text': "Attendance %"},
                gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#1e3c72"},
                         'steps': [{'range': [0, 50], 'color': "#ff4b4b"},
                                   {'range': [50, 75], 'color': "#ffa500"},
                                   {'range': [75, 100], 'color': "#00cc96"}]}
            ))
            st.plotly_chart(fig_gauge, use_container_width=True)
            st.metric("Academic SGPA", student['SGPA'])
        st.markdown("</div>", unsafe_allow_html=True)

# --- Intervention View ---
elif st.session_state.active_tab == "🚨 Intervention":
    back_button()
    st.subheader("Priority Student Intervention")
    st.write("Criteria: Attendance < 50%, Marks < 40%, or SGPA < 5.0")
    
    alert_df = df[
        (df["Attendance_Pct"] < 50) | 
        (df["External_Marks"] < 28) | 
        (df["SGPA"] < 5.0)
    ]
    
    if alert_df.empty:
        st.success("No students currently require intervention.")
    else:
        for idx, row in alert_df.iterrows():
            with st.container():
                st.markdown(f"""
                <div class='intervention-card'>
                    <h4 style='color: #ff4b4b; margin-bottom: 5px;'>{row['Name']} ({row['Student_ID']})</h4>
                    <p style='margin: 0;'><b>Dept:</b> {row['Department']} | <b>Year:</b> {row['Year']}</p>
                    <p style='margin: 0;'>
                        <span style='color: {"#ff4b4b" if row["Attendance_Pct"] < 50 else "#555"}'>Attendance: {row['Attendance_Pct']}%</span> | 
                        <span style='color: {"#ff4b4b" if row["External_Marks"] < 28 else "#555"}'>End-Sem: {row['External_Marks']}</span> | 
                        <span style='color: {"#ff4b4b" if row["SGPA"] < 5.0 else "#555"}'>SGPA: {row['SGPA']}</span>
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # FUNCTIONAL Analyze Button
                if st.button(f"Analyze {row['Name']}", key=f"btn_{row['Student_ID']}"):
                    st.session_state.previous_tab = "🚨 Intervention"
                    st.session_state.active_tab = "🔍 Search"
                    st.session_state.search_query = row['Student_ID']
                    st.rerun()

# Footer
st.markdown("---")
st.markdown(f"<p style='text-align: center; color: #888;'>EduInsight Dashboard v1.1 | {datetime.now().strftime('%Y-%m-%d')}</p>", unsafe_allow_html=True)
