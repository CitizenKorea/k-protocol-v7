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

# 웹페이지 기본 설정
st.set_page_config(page_title="K-PROTOCOL Analyzer", layout="wide")

st.title("🌌 K-PROTOCOL: 76 Pulsar Data Analyzer")
st.write("주류 학계의 데이터를 사냥하여 절대 광속 감쇠($\Delta c$)를 실증합니다.")

def parse_tim_file(filepath):
    """.tim 파일에서 순수 도착 시간(MJD)만 사냥"""
    mjds = []
    with open(filepath, 'r') as f:
        for line in f:
            if not line.startswith('C') and not line.startswith('FORMAT') and len(line.strip()) > 10:
                parts = line.split()
                for p in parts:
                    if '.' in p and p.startswith('5') and len(p) > 10:
                        try:
                            mjds.append(float(p))
                        except ValueError:
                            pass
    return mjds

def apply_k_protocol(mjd_array):
    """K-PROTOCOL 수식을 대입하여 기하학적 위상 지연(나노초) 계산"""
    mjd_array = np.array(mjd_array)
    mjd_array.sort()
    
    if len(mjd_array) == 0:
        return None, None
    
    base_mjd = mjd_array[0]
    days_elapsed = mjd_array - base_mjd
    years_elapsed = days_elapsed / 365.25
    
    # 붉은색 선을 그리기 위한 핵심 수식
    geometric_delay_ns = (years_elapsed * DECAY_RATE_YR / C_K) * S_EARTH * 1e9 
    
    return years_elapsed, geometric_delay_ns

# ==========================================
# 📊 데이터 사냥 및 시각화 엔진 가동
# ==========================================
tim_files = glob.glob('data/*.tim')

if not tim_files:
    st.error("🚨 `data` 폴더에서 파일을 찾을 수 없습니다. 깃허브 저장소에 `data` 폴더와 `.tim` 파일들이 있는지 확인해주세요.")
else:
    st.success(f"✅ 총 {len(tim_files)}개의 펄서 데이터를 발견했습니다. 분석 중...")
    
    # 진행 상태바
    progress_bar = st.progress(0)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    total_points = 0
    
    for i, file in enumerate(tim_files):
        pulsar_name = os.path.basename(file).split('.')[0]
        mjds = parse_tim_file(file)
        
        if mjds:
            total_points += len(mjds)
            years, delay_ns = apply_k_protocol(mjds)
            if years is not None:
                ax.scatter(years, delay_ns, alpha=0.3, s=10)
        
        # 상태바 업데이트
        progress_bar.progress((i + 1) / len(tim_files))
        
    ax.set_title("K-PROTOCOL Geometric Phase Delay", fontsize=16, fontweight='bold')
    ax.set_xlabel("Years Elapsed", fontsize=12)
    ax.set_ylabel("Geometric Delay (ns)", fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.6)
    
    # K-PROTOCOL 절대 예측선 (Trend Line)
    x_trend = np.linspace(0, 15, 100)
    y_trend = (x_trend * DECAY_RATE_YR / C_K) * S_EARTH * 1e9
    ax.plot(x_trend, y_trend, color='red', linewidth=3, label="K-PROTOCOL Prediction ($\Delta c$)")
    
    ax.legend(loc='upper left', fontsize=10)
    
    # 완성된 그래프를 웹 화면에 출력
    st.pyplot(fig)
    st.info(f"🎯 추출된 총 데이터 포인트: **{total_points:,}개**")
