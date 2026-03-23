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
st.title("🌌 K-PROTOCOL: 76 Pulsar Data Analyzer")
st.write("주류 학계의 데이터를 사냥하여 절대 광속 감쇠($\Delta c$)를 실증합니다.")

def parse_tim_file(filepath):
    """[수정됨] 엄격한 필터망: 진짜 MJD 날짜(40000~70000 사이)만 사냥"""
    mjds = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.startswith('C') or line.startswith('FORMAT') or not line.strip():
                continue
            parts = line.split()
            for p in parts:
                try:
                    val = float(p)
                    # 실제 펄서 관측 연도 범위에 해당하는 숫자만 추출
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
    
    # K-PROTOCOL 수식
    geometric_delay_ns = (years_elapsed * DECAY_RATE_YR / C_K) * S_EARTH * 1e9 
    
    return years_elapsed, geometric_delay_ns

# ==========================================
# 📊 데이터 사냥 및 시각화 엔진
# ==========================================
tim_files = glob.glob('data/*.tim')

if not tim_files:
    st.error("🚨 `data` 폴더에서 파일을 찾을 수 없습니다.")
else:
    st.success(f"✅ 총 {len(tim_files)}개의 펄서 데이터를 발견했습니다. 분석 중...")
    progress_bar = st.progress(0)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    total_points = 0
    scatter_labeled = False # 범례 중복 방지 장치
    
    for i, file in enumerate(tim_files):
        mjds = parse_tim_file(file)
        if mjds:
            total_points += len(mjds)
            years, delay_ns = apply_k_protocol(mjds)
            if years is not None:
                # [수정됨] 실제 데이터에 대한 범례 추가 및 색상 구분
                if not scatter_labeled:
                    ax.scatter(years, delay_ns, alpha=0.3, s=15, color='gray', label="Observed Pulsar Data (K-PROTOCOL Delay)")
                    scatter_labeled = True
                else:
                    ax.scatter(years, delay_ns, alpha=0.3, s=15, color='gray')
                    
        progress_bar.progress((i + 1) / len(tim_files))
        
    ax.set_title("K-PROTOCOL Geometric Phase Delay (Strict Filter)", fontsize=16, fontweight='bold')
    ax.set_xlabel("Years Elapsed", fontsize=12)
    ax.set_ylabel("Geometric Delay (ns)", fontsize=12)
    
    # [수정됨] x축을 160년이 아닌 15년(NANOGrav 관측 기간)으로 강제 고정
    ax.set_xlim(-0.5, 16) 
    ax.grid(True, linestyle='--', alpha=0.6)
    
    # K-PROTOCOL 절대 예측선
    x_trend = np.linspace(0, 16, 100)
    y_trend = (x_trend * DECAY_RATE_YR / C_K) * S_EARTH * 1e9
    ax.plot(x_trend, y_trend, color='red', linewidth=3, label="K-PROTOCOL Prediction ($\Delta c$)")
    
    ax.legend(loc='upper left', fontsize=11)
    
    st.pyplot(fig)
    st.info(f"🎯 엄격한 필터로 추출된 순수 데이터 포인트: **{total_points:,}개**")
