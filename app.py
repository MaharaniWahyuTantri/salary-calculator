import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from io import BytesIO
import base64
import time
import utils  # Import fungsi dari utils.py

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
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
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
    
    # Pilihan skenario
    scenario_options = {
        1: "1. Salary Minimums & Maximums",
        2: "2. Lowest & Highest Midpoint", 
        3: "3. Midpoint Progression",
        4: "4. Salary Midpoints",
        5: "5. Market Rate"
    }
    
    scenario = st.selectbox(
        "Select Scenario",
        options=list(scenario_options.keys()),
        format_func=lambda x: scenario_options[x]
    )
    
    # Input dasar
    col1, col2 = st.columns(2)
    with col1:
        num_grades = st.number_input("Number of Grades", min_value=2, max_value=50, value=10, step=1)
    with col2:
        currency = st.text_input("Currency", value="$", max_chars=5)
    
    # Parameter tambahan berdasarkan skenario
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
        st.info("P50 = Median market\nP60 = Above market\nP75 = Competitive\nP90 = Top of market")
    
    # Divider
    st.markdown("---")
    
    # Upload file
    st.subheader("📁 Data Input")
    uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])
    
    # Atau generate template
    if st.button("📥 Download Template CSV"):
        # Generate template berdasarkan skenario
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
        csv = df_template.to_csv(index=False)
        st.download_button(
            label="Click to Download",
            data=csv,
            file_name=f"template_scenario_{scenario}.csv",
            mime="text/csv"
        )
    
    st.markdown("---")
    st.info("💡 **Tips:**\n1. Download template\n2. Edit in Excel\n3. Upload back\n4. Calculate!")

# ====================== MAIN CONTENT ======================
# Tab untuk organisasi konten
tab1, tab2, tab3, tab4 = st.tabs(["📊 Input Data", "📈 Results", "📉 Visualizations", "📥 Export"])

# Initialize session state
if 'result_df' not in st.session_state:
    st.session_state.result_df = None
if 'input_df' not in st.session_state:
    st.session_state.input_df = None

with tab1:
    st.header("Input Data")

    if uploaded_file is not None:
        # Selalu baca file yang baru di-upload dan simpan ke session state
        if 'last_uploaded' not in st.session_state or st.session_state.last_uploaded != uploaded_file.name:
            df = pd.read_csv(uploaded_file)
            st.session_state.input_df = df
            st.session_state.last_uploaded = uploaded_file.name
            st.success(f"✅ File baru di-load! ({len(df)} baris)")
        else:
            # Gunakan data yang sudah ada di session state untuk diedit
            df = st.session_state.input_df.copy()

        # 1. Tampilkan data editor. Perubahan user langsung tersimpan di variabel `edited_df`.
        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True,
            height=400,
            key="data_editor" # Key penting untuk melacak widget
        )

        # 2. Tampilkan tombol "Save Changes"
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save Changes", type="secondary", use_container_width=True):
                # PERBAIKAN: Simpan dataframe hasil edit ke session state
                st.session_state.input_df = edited_df.copy()
                st.success("Perubahan berhasil disimpan ke memori!")
        with col2:
            # Tombol opsional untuk reload file asli
            if st.button("🔄 Muat Ulang File Asli", use_container_width=True):
                if uploaded_file is not None:
                    st.session_state.input_df = pd.read_csv(uploaded_file)
                    st.session_state.last_uploaded = uploaded_file.name
                    st.rerun() # Refresh halaman

    else:
        st.info("Silakan upload file CSV atau gunakan template di sidebar.")

with tab2:
    st.header("Calculation Results")
    
    if st.button("🚀 Calculate Salary Structure", type="primary", use_container_width=True):
        if st.session_state.input_df is None:
            st.error("❌ Please load or input data first!")
        else:
            with st.spinner("Calculating..."):
                try:
                    # Pilih fungsi berdasarkan skenario
                    if scenario == 1:
                        result = utils.calculate_scenario_1(st.session_state.input_df)
                    elif scenario == 2:
                        result = utils.calculate_scenario_2(
                            st.session_state.input_df,
                            **additional_params
                        )
                    elif scenario == 3:
                        result = utils.calculate_scenario_3(
                            st.session_state.input_df,
                            **additional_params
                        )
                    elif scenario == 4:
                        result = utils.calculate_scenario_4(st.session_state.input_df)
                    elif scenario == 5:
                        result = utils.calculate_scenario_5(
                            st.session_state.input_df,
                            **additional_params
                        )
                    
                    st.session_state.result_df = result
                    st.success("✅ Calculation complete!")
                    
                    # Tampilkan hasil
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
    
    # Tampilkan hasil jika sudah ada
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

        # TOMBOL RESET
        st.markdown("---")
        st.subheader("Lanjutkan atau Mulai Ulang")
        
        col_reset_a, col_reset_b = st.columns(2)
        with col_reset_a:
            if st.button("🔄 Hitung Ulang dengan Data Sama", use_container_width=True, type="secondary", key="recalc_tab2"):
                # Hanya hapus hasil, pertahankan data input
                if 'result_df' in st.session_state:
                    del st.session_state.result_df
                st.rerun()
        
        with col_reset_b:
            if st.button("🗑️ Hapus Semua & Mulai Baru", use_container_width=True, type="primary", key="clear_all_tab2"):
                # Hapus semua data
                for key in ['result_df', 'input_df', 'last_uploaded']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()


with tab3:
    st.header("Visualizations")
    
    if st.session_state.result_df is not None:
        # Pilih chart type
        chart_type = st.selectbox("Select Chart", ["Salary Ranges", "Midpoint Progression", "Spread Analysis", "Overlap Analysis"])
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if chart_type == "Salary Ranges":
            grades = st.session_state.result_df['Salary Grade']
            min_sal = st.session_state.result_df['Minimum']
            max_sal = st.session_state.result_df['Maximum']
            mid_sal = st.session_state.result_df['Midpoint']
            
            y_pos = np.arange(len(grades))
            ax.barh(y_pos, max_sal - min_sal, left=min_sal, color='lightblue', edgecolor='navy')
            ax.plot(mid_sal, y_pos, 'ro-', linewidth=2, markersize=8)
            ax.set_yticks(y_pos)
            ax.set_yticklabels(grades)
            ax.set_xlabel(f'Salary ({currency})')
            ax.set_title('Salary Ranges by Grade')
            ax.invert_yaxis()
            
        elif chart_type == "Midpoint Progression":
            grades = st.session_state.result_df['Salary Grade']
            midpoints = st.session_state.result_df['Midpoint']
            
            ax.plot(grades, midpoints, 'go-', linewidth=3, markersize=10)
            ax.set_xlabel('Grade')
            ax.set_ylabel(f'Salary ({currency})')
            ax.set_title('Midpoint Progression')
            ax.grid(True, alpha=0.3)
            ax.tick_params(axis='x', rotation=45)
            
        st.pyplot(fig)
        
        # Download chart
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=300)
        buf.seek(0)
        
        st.download_button(
            label="📥 Download Chart",
            data=buf,
            file_name=f"chart_{chart_type.lower().replace(' ', '_')}.png",
            mime="image/png"
        )
    else:
        st.info("Please calculate results first in the Results tab")

with tab4:
    st.header("Export Results")
    
    if st.session_state.result_df is not None:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Export to CSV
            csv = st.session_state.result_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name="salary_structure.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            # Export to Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                st.session_state.result_df.to_excel(writer, sheet_name='Salary Structure', index=False)
                if st.session_state.input_df is not None:
                    st.session_state.input_df.to_excel(writer, sheet_name='Input Data', index=False)
            excel_data = output.getvalue()
            
            st.download_button(
                label="📊 Download Excel",
                data=excel_data,
                file_name="salary_structure.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        with col3:
            # Export to JSON
            json_str = st.session_state.result_df.to_json(orient='records', indent=2)
            st.download_button(
                label="📄 Download JSON",
                data=json_str,
                file_name="salary_structure.json",
                mime="application/json",
                use_container_width=True
            )
        
        st.markdown("---")
        st.subheader("Share Results")
        
        # Preview data
        st.write("**Preview:**")
        st.write(st.session_state.result_df.head())
        
        # Tombol reset di dalam kondisi ADA hasil
        st.markdown("---")
        st.subheader("Aksi Selanjutnya")

        col_reset1, col_reset2, _ = st.columns([1, 1, 2])
        with col_reset1:
            if st.button("🔄 Hitung Ulang", use_container_width=True, type="secondary", key="reset1"):
                if 'result_df' in st.session_state:
                    del st.session_state.result_df
                st.rerun()
                st.info("Data input masih ada. Silakan tekan tombol '🚀 Calculate' lagi.")

        with col_reset2:
            if st.button("🆕 Mulai dari Awal", use_container_width=True, type="primary", key="reset2"):
                for key in ['result_df', 'input_df', 'last_uploaded']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
                st.success("Sesi direset. Silakan upload data baru.")
    
    else:
        # Kondisi TIDAK ADA hasil
        st.warning("Tidak ada hasil untuk di-export. Silakan hitung terlebih dahulu di tab **Results**.")
        
        # Tombol reset di dalam kondisi TIDAK ADA hasil
        st.markdown("---")
        st.subheader("Reset Data")
        
        if st.button("🧹 Hapus Semua Data & Mulai Baru", type="secondary", use_container_width=True, key="reset_global"):
            for key in ['result_df', 'input_df', 'last_uploaded']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
# ====================== FOOTER ======================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: gray; padding: 20px;">
    <p>Salary Structure Calculator • Made with Streamlit • v1.0</p>
    <p>For professional use only</p>
</div>
""", unsafe_allow_html=True)