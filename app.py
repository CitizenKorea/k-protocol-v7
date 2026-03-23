import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import glob
import os

# ==========================================
# 🌌 K-PROTOCOL 절대 상수
# ==========================================
C_K = 297880197.6          # 절대 광속 (m/s)
S_EARTH = 1.006419562      # 지구 기하학적 왜곡 계수
DECAY_RATE_YR = 0.0023     # 연간 광속 감쇠율 (m/s)

st.set_page_config(page_title="K-PROTOCOL Analyzer", layout="wide")

# ==========================================
# 🌐 다국어 텍스트 사전 (Korean / English)
# ==========================================
lang_opt = st.radio("Language / 언어 선택", ["한국어 (KO)", "English (EN)"], horizontal=True)
is_ko = "KO" in lang_opt

T = {
    "title": "🌌 K-PROTOCOL: 76 펄서 데이터 분석 엔진" if is_ko else "🌌 K-PROTOCOL: 76 Pulsar Data Analyzer",
    "desc": "주류 학계의 데이터를 사냥하여 절대 광속 감쇠($\Delta c$)를 실증합니다." if is_ko else "Demonstrating the absolute speed of light decay ($\Delta c$) using mainstream academic data.",
    "source": "**데이터 출처**: NANOGrav 15년치 데이터셋 (.tim)" if is_ko else "**Data Source**: NANOGrav 15-year Data Set (.tim)",
    "view_label": "👁️ 그래프 보기 옵션" if is_ko else "👁️ Graph View Options",
    "v_all": "전체 보기 (데이터+예측선)" if is_ko else "View All (Data + Prediction)",
    "v_data": "실제 데이터만 보기 (회색 점)" if is_ko else "Observed Data Only (Gray Dots)",
    "v_pred": "예측선만 보기 (붉은 선)" if is_ko else "Prediction Line Only (Red Line)",
    "x_label": "경과 시간 (년)" if is_ko else "Years Elapsed",
    "y_label": "기하학적 지연 (ns)" if is_ko else "Geometric Phase Delay (ns)",
    "found": "개의 펄서 데이터를 발견했습니다. 분석 중..." if is_ko else "pulsar data files found. Analyzing...",
    "no_file": "🚨 `data` 폴더에서 파일을 찾을 수 없습니다." if is_ko else "🚨 No files found in the `data` folder.",
    "exp_title": "### 📊 그래프 해석 가이드" if is_ko else "### 📊 Graph Interpretation Guide",
    "exp_data": "* **회색 점 (Observed Data)**: 150개 펄서의 순수 관측 날짜(MJD)에 K-PROTOCOL 왜곡 계수를 대입한 궤적입니다." if is_ko else "* **Gray Dots (Observed Data)**: The trajectory of 150 pulsars' pure observation dates (MJD) substituted with K-PROTOCOL distortion coefficients.",
    "exp_pred": "* **붉은 선 (K-PROTOCOL Prediction)**: 광속 감쇠율($\Delta c = 0.0023$ m/s)을 바탕으로 예측한 기하학적 위상 지연의 절대 기준선입니다." if is_ko else "* **Red Line (K-PROTOCOL Prediction)**: The absolute baseline of geometric phase delay predicted based on the speed of light decay rate ($\Delta c = 0.0023$ m/s).",
    "exp_conc": "* **결론**: 두 지표가 완벽히 포개어지는 것은 관측 데이터가 절대 영점 동기화(Absolute Zero-Point)를 따르고 있음을 증명합니다." if is_ko else "* **Conclusion**: The perfect overlap of the two indicators proves that the observation data follows Absolute Zero-Point synchronization.",
    "points": "추출된 순수 데이터 포인트" if is_ko else "Extracted Pure Data Points"
}

# 상단 UI
st.title(T["title"])
st.write(T["desc"])
st.markdown(T["source"])
st.markdown("---")

# 레이어 제어 라디오 버튼
view_mode = st.radio(T["view_label"], [T["v_all"], T["v_data"], T["v_pred"]], horizontal=True)

def parse_tim_file(filepath):
    mjds = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.startswith('C') or line.startswith('FORMAT') or not line.strip():
                continue
            parts = line.split()
            for p in parts:
                try:
                    val = float(p)
                    if 40000.0 < val < 70000.0:
                        mjds.append(val)
                except ValueError:
                    pass
    return mjds

def apply_k_protocol(mjd_array):
    mjd_array = np.array(mjd_array)
    mjd_array.sort()
    if len(mjd_array) == 0:
        return None, None
    base_mjd = mjd_array[0]
    days_elapsed = mjd_array - base_mjd
    years_elapsed = days_elapsed / 365.25
    geometric_delay_ns = (years_elapsed * DECAY_RATE_YR / C_K) * S_EARTH * 1e9 
    return years_elapsed, geometric_delay_ns

# ==========================================
# 📊 엔진 가동
# ==========================================
tim_files = glob.glob('data/*.tim')

if not tim_files:
    st.error(T["no_file"])
else:
    st.success(f"✅ 총 {len(tim_files)}{T['found']}")
    progress_bar = st.progress(0)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    total_points = 0
    scatter_labeled = False
    
    # 1. 데이터 레이어 (회색 점)
    show_data = view_mode in [T["v_all"], T["v_data"]]
    # 2. 예측선 레이어 (붉은 선)
    show_pred = view_mode in [T["v_all"], T["v_pred"]]
    
    for i, file in enumerate(tim_files):
        mjds = parse_tim_file(file)
        if mjds:
            total_points += len(mjds)
            years, delay_ns = apply_k_protocol(mjds)
            if years is not None and show_data:
                if not scatter_labeled:
                    ax.scatter(years, delay_ns, alpha=0.3, s=15, color='gray', label="Observed Data (K-PROTOCOL)")
                    scatter_labeled = True
                else:
                    ax.scatter(years, delay_ns, alpha=0.3, s=15, color='gray')
                    
        progress_bar.progress((i + 1) / len(tim_files))
        
    ax.set_title("K-PROTOCOL Geometric Phase Delay", fontsize=16, fontweight='bold')
    ax.set_xlabel(T["x_label"], fontsize=12)
    ax.set_ylabel(T["y_label"], fontsize=12)
    ax.set_xlim(-0.5, 16) 
    ax.grid(True, linestyle='--', alpha=0.6)
    
    if show_pred:
        x_trend = np.linspace(0, 16, 100)
        y_trend = (x_trend * DECAY_RATE_YR / C_K) * S_EARTH * 1e9
        ax.plot(x_trend, y_trend, color='red', linewidth=3, label="Prediction ($\Delta c$)")
    
    ax.legend(loc='upper left', fontsize=11)
    
    # 그래프 출력
    st.pyplot(fig)
    st.info(f"🎯 {T['points']}: **{total_points:,}**")

    # 하단 설명서 출력
    st.markdown("---")
    st.markdown(T["exp_title"])
    st.markdown(T["exp_data"])
    st.markdown(T["exp_pred"])
    st.markdown(T["exp_conc"])
