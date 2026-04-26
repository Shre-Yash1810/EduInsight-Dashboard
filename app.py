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
    if os.path.exists("institute_data.csv"):
        return pd.read_csv("institute_data.csv")
    return pd.DataFrame()

df = load_data()

# --- Top Navigation Bar ---
st.markdown("<div class='nav-container'>", unsafe_allow_html=True)
nav_col1, nav_col2, nav_col3, nav_col4 = st.columns([2, 1, 1, 1])

with nav_col1:
    st.markdown("<h2 style='margin:0; color: #1e3c72;'>🎓 EduInsight</h2>", unsafe_allow_html=True)

# Navigation Logic
def set_tab(tab_name):
    st.session_state.active_tab = tab_name
    st.rerun()

with nav_col2:
    if st.button("🏛️ Overview", use_container_width=True, type="primary" if st.session_state.active_tab == "🏛️ Overview" else "secondary"):
        set_tab("🏛️ Overview")
with nav_col3:
    if st.button("🔍 Search", use_container_width=True, type="primary" if st.session_state.active_tab == "🔍 Search" else "secondary"):
        set_tab("🔍 Search")
with nav_col4:
    if st.button("🚨 Intervention", use_container_width=True, type="primary" if st.session_state.active_tab == "🚨 Intervention" else "secondary"):
        set_tab("🚨 Intervention")
st.markdown("</div>", unsafe_allow_html=True)

# --- Sidebar Filters ---
st.sidebar.title("Global Filters")
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

# --- Main Header ---
# Using fixed markdown without leading spaces to prevent code block rendering
header_html = f"""
<div class='main-header'>
<h1 style='margin:0;'>{st.session_state.active_tab}</h1>
<p style='margin:0; opacity: 0.8;'>Institute-wide Performance Tracking & Intervention</p>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)

# Helper for Back Button
def back_button():
    target = st.session_state.get('previous_tab', '🏛️ Overview')
    if st.button(f"⬅️ Back to {target}"):
        st.session_state.active_tab = target
        st.session_state.search_query = ""
        st.rerun()

# --- Views ---
if st.session_state.active_tab == "🏛️ Overview":
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Total Students", len(filtered_df))
    with col2: st.metric("Avg Attendance", f"{filtered_df['Attendance_Pct'].mean():.1f}%" if not filtered_df.empty else "0%")
    with col3: st.metric("Avg SGPA", f"{filtered_df['SGPA'].mean():.2f}" if not filtered_df.empty else "0.00")
    with col4: st.metric("Pass %", f"{(filtered_df['External_Marks'] >= 28).mean()*100:.1f}%" if not filtered_df.empty else "0%")

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Performance by Department")
        if not filtered_df.empty:
            dept_perf = filtered_df.groupby("Department")["SGPA"].mean().reset_index()
            st.plotly_chart(px.bar(dept_perf, x="Department", y="SGPA", color="SGPA", color_continuous_scale="Blues", template="plotly_white"), use_container_width=True)
    with c2:
        st.subheader("Attendance Categories")
        if not filtered_df.empty:
            def cat_att(p):
                if p >= 75: return "✅ Safe"
                if p >= 50: return "⚠️ Warning"
                return "🚨 Danger"
            filtered_df['Status'] = filtered_df['Attendance_Pct'].apply(cat_att)
            att_counts = filtered_df['Status'].value_counts().reset_index()
            att_counts.columns = ['Status', 'Count']
            st.plotly_chart(px.bar(att_counts, x="Status", y="Count", color="Status", color_discrete_map={"✅ Safe": "#00cc96", "⚠️ Warning": "#ffa500", "🚨 Danger": "#ff4b4b"}, template="plotly_white"), use_container_width=True)

elif st.session_state.active_tab == "🔍 Search":
    back_button()
    search_input = st.text_input("Search Student (Name or Roll No)", value=st.session_state.search_query, placeholder="AID SE-01...")
    st.session_state.search_query = search_input
    
    search_results = df[df["Name"].str.contains(search_input, case=False) | df["Student_ID"].str.contains(search_input, case=False)] if search_input else filtered_df
    
    if not search_results.empty:
        student = search_results.iloc[0] if len(search_results) == 1 else search_results[search_results["Name"] == st.selectbox("Select Student", search_results["Name"].tolist())].iloc[0]
        st.markdown(f"<div class='profile-card'><h3>Profile: {student['Name']} ({student['Student_ID']})</h3>", unsafe_allow_html=True)
        p1, p2 = st.columns(2)
        with p1:
            st.info(f"**Dept:** {student['Department']} | **Year:** {student['Year']}")
            fig_radar = go.Figure(go.Scatterpolar(r=[student['Internal_Marks']/30*100, student['External_Marks']/70*100, student['Practical_Marks']/25*100], theta=['Internal', 'External', 'Practical'], fill='toself', line_color='#1e3c72'))
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False)
            st.plotly_chart(fig_radar, use_container_width=True)
        with p2:
            st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=student['Attendance_Pct'], title={'text': "Attendance %"}, gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#1e3c72"}, 'steps': [{'range': [0, 50], 'color': "#ff4b4b"}, {'range': [50, 75], 'color': "#ffa500"}, {'range': [75, 100], 'color': "#00cc96"}]})), use_container_width=True)
            st.metric("SGPA", student['SGPA'])
        st.markdown("</div>", unsafe_allow_html=True)
    else: st.error("No records found.")

elif st.session_state.active_tab == "🚨 Intervention":
    back_button()
    alert_df = df[(df["Attendance_Pct"] < 50) | (df["External_Marks"] < 28) | (df["SGPA"] < 5.0)]
    if alert_df.empty: st.success("No interventions needed.")
    else:
        for _, row in alert_df.iterrows():
            st.markdown(f"<div class='intervention-card'><h4 style='color:#ff4b4b;'>{row['Name']} ({row['Student_ID']})</h4><p>Dept: {row['Department']} | Year: {row['Year']}</p><p>Attendance: {row['Attendance_Pct']}% | End-Sem: {row['External_Marks']} | SGPA: {row['SGPA']}</p></div>", unsafe_allow_html=True)
            if st.button(f"Analyze {row['Name']}", key=f"btn_{row['Student_ID']}"):
                st.session_state.previous_tab = "🚨 Intervention"; st.session_state.active_tab = "🔍 Search"; st.session_state.search_query = row['Student_ID']; st.rerun()

st.markdown("---")
st.markdown(f"<p style='text-align: center; color: #888;'>EduInsight Dashboard v1.2 | {datetime.now().strftime('%Y-%m-%d')}</p>", unsafe_allow_html=True)
