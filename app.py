import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import glob
import os

C_K = 297880197.6          
S_EARTH = 1.006419562      
DECAY_RATE_YR = 0.0023     

st.set_page_config(page_title="K-PROTOCOL Analyzer v8 (Real Data)", layout="wide")

st.title("🌌 K-PROTOCOL vs REAL NANOGrav Data")
st.markdown("---")

tim_files = glob.glob('data/*.tim')

if not tim_files:
    st.error("🚨 `data` 폴더에서 .tim 파일을 찾을 수 없습니다.")
else:
    pulsar_names = [os.path.basename(f).split('.')[0] for f in tim_files]
    pulsar_names.sort()
    
    selected_pulsars = st.multiselect(
        "🔭 분석할 펄서 선택",
        options=pulsar_names,
        default=pulsar_names[:1] if pulsar_names else []
    )

    # 💡 돋보기(줌) 슬라이더 추가
    zoom_level = st.slider("🔍 Y축 돋보기 (최대 나노초 설정)", min_value=0.5, max_value=35000.0, value=35000.0, step=10.0, help="숫자를 1.0 가까이 줄이면 바닥에 붙어있던 붉은 선의 진짜 위치가 보입니다.")

    def parse_real_tim_data(filepath):
        real_data = []
        with open(filepath, 'r') as f:
            for line in f:
                if line.startswith('C') or line.startswith('FORMAT') or not line.strip():
                    continue
                parts = line.split()
                mjd = None
                toa_err_us = None
                for i, p in enumerate(parts):
                    try:
                        val = float(p)
                        if 40000.0 < val < 70000.0:
                            mjd = val
                            if i + 1 < len(parts):
                                toa_err_us = float(parts[i+1]) 
                            break
                    except ValueError:
                        pass
                if mjd and toa_err_us is not None:
                    real_data.append((mjd, toa_err_us))
        return real_data

    if not selected_pulsars:
        st.warning("🚨 펄서를 최소 1개 이상 선택해 주세요.")
    else:
        with st.spinner("✅ 실제 파일에서 우주 데이터를 뜯어내는 중..."):
            fig, ax = plt.subplots(figsize=(12, 6))
            total_points = 0
            
            for file in tim_files:
                p_name = os.path.basename(file).split('.')[0]
                if p_name in selected_pulsars:
                    parsed = parse_real_tim_data(file)
                    if not parsed: continue
                    total_points += len(parsed)
                    mjds = np.array([item[0] for item in parsed])
                    toa_errs_us = np.array([item[1] for item in parsed]) 
                    
                    mjds.sort()
                    years_elapsed = (mjds - mjds[0]) / 365.25
                    real_y_ns = toa_errs_us * 1000.0 
                    
                    ax.scatter(years_elapsed, real_y_ns, alpha=0.3, s=15, color='gray', label=f"Real Data: {p_name}" if total_points == len(parsed) else "")

            x_trend = np.linspace(0, max(years_elapsed) if total_points > 0 else 16, 100)
            y_trend = (x_trend * DECAY_RATE_YR / C_K) * S_EARTH * 1e9
            ax.plot(x_trend, y_trend, color='red', linewidth=4, label="K-PROTOCOL Prediction ($\Delta c$)")
            
            # 💡 슬라이더 값으로 Y축 천장 높이 강제 고정
            ax.set_ylim(-0.05, zoom_level)
            
            ax.set_title("Real NANOGrav Data vs K-PROTOCOL Prediction", fontsize=16, fontweight='bold')
            ax.set_xlabel("Years Elapsed", fontsize=12)
            ax.set_ylabel("Time (ns)", fontsize=12)
            ax.grid(True, linestyle='--', alpha=0.6)
            
            handles, labels = ax.get_legend_handles_labels()
            by_label = dict(zip(labels, handles))
            ax.legend(by_label.values(), by_label.keys(), loc='upper left', fontsize=11)
            
            st.pyplot(fig)
            st.info(f"🎯 실제 파일에서 추출된 총 데이터 포인트: **{total_points:,}개**")
