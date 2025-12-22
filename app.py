import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import utils

# ====================== KONFIGURASI HALAMAN ======================
st.set_page_config(
    page_title="Salary Structure Calculator",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====================== CSS KUSTOM ======================
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        font-weight: bold;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
    }
</style>
""", unsafe_allow_html=True)

# ====================== HEADER ======================
st.markdown("""
<div class="main-header">
    <h1>💰 Salary Structure Calculator</h1>
    <p>Professional Compensation Analysis Tool</p>
</div>
""", unsafe_allow_html=True)

# ====================== SIDEBAR ======================
with st.sidebar:
    st.header("⚙️ Configuration")
    
    scenario_options = {
        1: "1. Salary Minimums & Maximums",
        2: "2. Lowest & Highest Midpoint", 
        3: "3. Midpoint Progression",
        4: "4. Salary Midpoints",
        5: "5. Market Rate"
    }
    
    scenario = st.selectbox("Select Scenario", options=list(scenario_options.keys()), format_func=lambda x: scenario_options[x])
    
    col1, col2 = st.columns(2)
    with col1:
        num_grades = st.number_input("Number of Grades", min_value=2, max_value=50, value=10, step=1)
    with col2:
        currency = st.text_input("Currency", value="$", max_chars=5)
    
    additional_params = {}
    if scenario == 2:
        st.subheader("📌 Additional Parameters")
        lowest_midpoint = st.number_input("Lowest Midpoint", value=20000.0, min_value=0.0, step=1000.0)
        highest_midpoint = st.number_input("Highest Midpoint", value=100000.0, min_value=0.0, step=1000.0)
        additional_params = {'lowest_midpoint': lowest_midpoint, 'highest_midpoint': highest_midpoint}
        
    elif scenario == 3:
        st.subheader("📌 Additional Parameters")
        lowest_midpoint = st.number_input("Lowest Midpoint", value=50000.0, min_value=0.0, step=1000.0)
        additional_params = {'lowest_midpoint': lowest_midpoint}
        
    elif scenario == 5:
        st.subheader("📌 Additional Parameters")
        target_percentile = st.selectbox("Target Percentile", [50, 60, 75, 90], index=0)
        additional_params = {'target_percentile': target_percentile}
    
    st.markdown("---")
    st.subheader("📁 Data Input")
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])
    
    if st.button("📥 Download Template Excel"):
        if scenario == 1:
            data = {
                'Salary Grade': utils.DEFAULT_GRADE_NAMES[:num_grades],
                'Minimum': [50000 + i*10000 for i in range(num_grades)],
                'Maximum': [70000 + i*14000 for i in range(num_grades)]
            }
        elif scenario == 2:
            data = {
                'Salary Grade': utils.DEFAULT_GRADE_NAMES[:num_grades],
                'Spread %': [30] * num_grades
            }
        elif scenario == 3:
            data = {
                'Salary Grade': utils.DEFAULT_GRADE_NAMES[:num_grades],
                'Midpoint Differential %': [0] + [10] * (num_grades - 1),
                'Spread %': [30] * num_grades
            }
        elif scenario == 4:
            base = 50000
            data = {
                'Salary Grade': utils.DEFAULT_GRADE_NAMES[:num_grades],
                'Midpoint': [base * (1.1 ** i) for i in range(num_grades)],
                'Spread %': [30] * num_grades
            }
        elif scenario == 5:
            base = 50000
            data = {
                'Salary Grade': utils.DEFAULT_GRADE_NAMES[:num_grades],
                'Market Rate': [base * (1.1 ** i) for i in range(num_grades)],
                'Spread %': [30] * num_grades
            }
        
        df_template = pd.DataFrame(data)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_template.to_excel(writer, index=False, sheet_name='Template')
        
        st.download_button(
            label="Download Template",
            data=output.getvalue(),
            file_name=f"template_scenario_{scenario}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    st.info("💡 **Tips:**\n1. Download template Excel\n2. Edit di Excel\n3. Upload kembali\n4. Calculate!")

# ====================== MAIN CONTENT ======================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Input Data", "📈 Results", "📉 Visualizations", "📥 Export"])

# Initialize session state
if 'result_df' not in st.session_state:
    st.session_state.result_df = None
if 'input_df' not in st.session_state:
    st.session_state.input_df = None

with tab1:
    st.header("Input Data")

    if uploaded_file is not None:
        if 'last_uploaded' not in st.session_state or st.session_state.last_uploaded != uploaded_file.name:
            df = pd.read_excel(uploaded_file)
            st.session_state.input_df = df
            st.session_state.last_uploaded = uploaded_file.name
            st.success(f"✅ File loaded! ({len(df)} rows)")
        else:
            df = st.session_state.input_df.copy()

        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, height=400)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save Changes", use_container_width=True):
                st.session_state.input_df = edited_df.copy()
                st.success("Changes saved!")
        with col2:
            if st.button("🔄 Reload Original", use_container_width=True):
                st.session_state.input_df = pd.read_excel(uploaded_file)
                st.session_state.last_uploaded = uploaded_file.name
                st.rerun()
    else:
        st.info("Please upload an Excel file or use template from sidebar.")

with tab2:
    st.header("Calculation Results")
    
    if st.button("🚀 Calculate Salary Structure", use_container_width=True):
        if st.session_state.input_df is None:
            st.error("❌ Please load or input data first!")
        else:
            with st.spinner("Calculating..."):
                try:
                    if scenario == 1:
                        result = utils.calculate_scenario_1(st.session_state.input_df)
                    elif scenario == 2:
                        result = utils.calculate_scenario_2(st.session_state.input_df, **additional_params)
                    elif scenario == 3:
                        result = utils.calculate_scenario_3(st.session_state.input_df, **additional_params)
                    elif scenario == 4:
                        result = utils.calculate_scenario_4(st.session_state.input_df)
                    elif scenario == 5:
                        result = utils.calculate_scenario_5(st.session_state.input_df, **additional_params)
                    
                    st.session_state.result_df = result
                    st.success("✅ Calculation complete!")
                    
                    st.dataframe(
                        result.style.format({
                            'Minimum': f'{currency}' + '{:,.0f}',
                            'Midpoint': f'{currency}' + '{:,.0f}',
                            'Maximum': f'{currency}' + '{:,.0f}',
                            'Range': f'{currency}' + '{:,.0f}',
                            'Spread %': '{:.1f}%',
                            'Mid Point Differential %': '{:.1f}%',
                            'Overlap %': '{:.1f}%'
                        }),
                        use_container_width=True,
                        height=400
                    )
                    
                except Exception as e:
                    st.error(f"❌ Calculation error: {str(e)}")
    
    if st.session_state.result_df is not None:
        st.subheader("Quick Statistics")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Avg Midpoint", f"{currency}{st.session_state.result_df['Midpoint'].mean():,.0f}")
        with col2:
            st.metric("Avg Spread", f"{st.session_state.result_df['Spread %'].mean():.1f}%")
        with col3:
            st.metric("Avg Overlap", f"{st.session_state.result_df['Overlap %'].mean():.1f}%")
        with col4:
            st.metric("Total Range", f"{currency}{st.session_state.result_df['Range'].sum():,.0f}")

        st.markdown("---")
        st.subheader("Next Steps")
        
        col_reset_a, col_reset_b = st.columns(2)
        with col_reset_a:
            if st.button("🔄 Recalculate", use_container_width=True):
                if 'result_df' in st.session_state:
                    del st.session_state.result_df
                st.rerun()
        
        with col_reset_b:
            if st.button("🗑️ Clear All", use_container_width=True):
                for key in ['result_df', 'input_df', 'last_uploaded']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

with tab3:
    st.header("Visualizations")
    
    if st.session_state.result_df is not None:
        df = st.session_state.result_df
        
        # Buat 4 visualisasi
        col1, col2 = st.columns(2)
        
        with col1:
            # 1. SALARY MIDPOINTS & PROGRESSION
            st.subheader("SALARY MIDPOINTS & PROGRESSION")
            fig1, ax1 = plt.subplots(figsize=(10, 6))
            
            grades = df['Salary Grade']
            midpoints = df['Midpoint']
            ax1.plot(grades, midpoints, color='gold', marker='o', linewidth=3, markersize=8, label='Midpoint')
            
            if 'Mid Point Differential %' in df.columns:
                ax2 = ax1.twinx()
                diff_pct = df['Mid Point Differential %']
                ax2.scatter(grades, diff_pct, color='green', s=150, alpha=0.7, label='Midpoint Differential %')
                ax2.set_ylabel('Midpoint Differential (%)', color='green')
                ax2.tick_params(axis='y', labelcolor='green')
                
                for i, (grade, diff) in enumerate(zip(grades, diff_pct)):
                    ax2.text(i, diff, f'{diff:.1f}%', ha='center', va='bottom', fontsize=8, color='darkgreen')
            
            ax1.set_xlabel('Grade')
            ax1.set_ylabel(f'Salary ({currency})', color='darkgoldenrod')
            ax1.tick_params(axis='x', rotation=45)
            ax1.grid(True, alpha=0.3, linestyle='--')
            
            for i, (grade, mp) in enumerate(zip(grades, midpoints)):
                ax1.text(i, mp, f'{currency}{mp:,.0f}', ha='center', va='bottom', fontsize=8, color='darkgoldenrod')
            
            st.pyplot(fig1)
            
            # 3. SALARY RANGES BY GRADE
            st.subheader("SALARY RANGES BY GRADE")
            fig3, ax3 = plt.subplots(figsize=(10, 8))
            
            y_pos = range(len(grades))
            for i, (grade, min_val, max_val) in enumerate(zip(grades, df['Minimum'], df['Maximum'])):
                ax3.barh(i, max_val - min_val, left=min_val, height=0.6, color='gold', alpha=0.8, edgecolor='darkgoldenrod')
                ax3.text(min_val, i, f'{currency}{min_val:,.0f}', ha='right', va='center', fontsize=8)
                ax3.text(max_val, i, f'{currency}{max_val:,.0f}', ha='left', va='center', fontsize=8)
            
            ax3.set_yticks(y_pos)
            ax3.set_yticklabels(grades)
            ax3.set_xlabel(f'Salary ({currency})')
            ax3.invert_yaxis()
            ax3.grid(True, alpha=0.3, linestyle='--', axis='x')
            
            st.pyplot(fig3)
        
        with col2:
            # 2. SALARY GRADES - SPREAD
            st.subheader("SALARY GRADES - SPREAD")
            fig2, ax2 = plt.subplots(figsize=(10, 6))
            
            y_pos = range(len(grades))
            ranges = df['Maximum'] - df['Minimum']
            
            ax2.barh(y_pos, ranges, left=df['Minimum'], color='gold', alpha=0.8, height=0.6, edgecolor='darkgoldenrod')
            
            if 'Spread %' in df.columns:
                spread_positions = df['Minimum'] + (ranges / 2)
                scatter = ax2.scatter(spread_positions, y_pos, s=150, color='green', alpha=0.7, label='Spread %')
                for i, (pos, spread) in enumerate(zip(spread_positions, df['Spread %'])):
                    ax2.text(pos, i, f'{spread:.1f}%', ha='center', va='center', fontsize=8, color='white')
            
            ax2.set_yticks(y_pos)
            ax2.set_yticklabels(grades)
            ax2.set_xlabel(f'Salary ({currency})')
            ax2.invert_yaxis()
            ax2.grid(True, alpha=0.3, linestyle='--', axis='x')
            
            st.pyplot(fig2)
            
            # 4. SALARY GRADES - OVERLAP
            st.subheader("SALARY GRADES - OVERLAP")
            fig4, ax4 = plt.subplots(figsize=(10, 8))
            
            ax4.barh(y_pos, ranges, left=df['Minimum'], color='gold', alpha=0.8, height=0.6, edgecolor='darkgoldenrod')
            
            if 'Overlap %' in df.columns:
                overlap_positions = df['Minimum'] + (ranges * 0.75)
                scatter = ax4.scatter(overlap_positions, y_pos, s=150, color='green', alpha=0.7, label='Overlap %')
                for i, (pos, overlap) in enumerate(zip(overlap_positions, df['Overlap %'])):
                    if overlap > 0:
                        ax4.text(pos, i, f'{overlap:.1f}%', ha='center', va='center', fontsize=8, color='white')
            
            ax4.set_yticks(y_pos)
            ax4.set_yticklabels(grades)
            ax4.set_xlabel(f'Salary ({currency})')
            ax4.invert_yaxis()
            ax4.grid(True, alpha=0.3, linestyle='--', axis='x')
            
            st.pyplot(fig4)
        
        # Download charts
        st.markdown("---")
        st.subheader("Download Charts")
        
        col_dl1, col_dl2, col_dl3, col_dl4 = st.columns(4)
        
        for col, fig, name in [(col_dl1, fig1, "midpoints"), (col_dl2, fig2, "spread"), 
                              (col_dl3, fig3, "ranges"), (col_dl4, fig4, "overlap")]:
            with col:
                buf = BytesIO()
                fig.savefig(buf, format="png", dpi=300, bbox_inches='tight')
                buf.seek(0)
                st.download_button(
                    label=f"📥 {name.title()}",
                    data=buf,
                    file_name=f"salary_{name}.png",
                    mime="image/png",
                    use_container_width=True
                )
    else:
        st.info("Please calculate results first in the Results tab")

with tab4:
    st.header("Export Results")
    
    if st.session_state.result_df is not None:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            csv = st.session_state.result_df.to_csv(index=False)
            st.download_button("📥 Download CSV", data=csv, file_name="salary_structure.csv", 
                             mime="text/csv", use_container_width=True)
        
        with col2:
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                st.session_state.result_df.to_excel(writer, sheet_name='Salary Structure', index=False)
                if st.session_state.input_df is not None:
                    st.session_state.input_df.to_excel(writer, sheet_name='Input Data', index=False)
            
            st.download_button("📊 Download Excel", data=output.getvalue(), 
                             file_name="salary_structure.xlsx", 
                             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             use_container_width=True)
        
        with col3:
            json_str = st.session_state.result_df.to_json(orient='records', indent=2)
            st.download_button("📄 Download JSON", data=json_str, file_name="salary_structure.json", 
                             mime="application/json", use_container_width=True)
    
    else:
        st.warning("No results to export. Please calculate first in Results tab.")

# ====================== FOOTER ======================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: gray;">
    <p>Salary Structure Calculator • Made with Streamlit • v1.0</p>
    <p>For professional use only</p>
</div>
""", unsafe_allow_html=True)