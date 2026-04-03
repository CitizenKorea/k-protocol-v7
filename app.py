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

st.set_page_config(page_title="K-PROTOCOL Analyzer v8 (Real Data)", layout="wide")

st.title("🌌 K-PROTOCOL vs REAL NANOGrav Data")
st.write("가상의 시뮬레이션이 아닌, .tim 파일 내의 실제 측정 데이터(관측 오차)를 파싱하여 절대 광속 감쇠(Δc) 예측선과 직접 비교합니다.")
st.markdown("---")

# ==========================================
# 📊 파일 로드 및 펄서 선택 UI
# ==========================================
tim_files = glob.glob('data/*.tim')

if not tim_files:
    st.error("🚨 `data` 폴더에서 .tim 파일을 찾을 수 없습니다. GitHub에 데이터가 있는지 확인하세요.")
else:
    pulsar_names = [os.path.basename(f).split('.')[0] for f in tim_files]
    pulsar_names.sort()
    
    selected_pulsars = st.multiselect(
        "🔭 분석할 펄서 선택",
        options=pulsar_names,
        default=pulsar_names[:1] if pulsar_names else []
    )

    # 💡 [핵심 수정] 가짜(자기 충족적) 데이터가 아닌 진짜 관측치 추출
    def parse_real_tim_data(filepath):
        real_data = []
        with open(filepath, 'r') as f:
            for line in f:
                if line.startswith('C') or line.startswith('FORMAT') or not line.strip():
                    continue
                parts = line.split()
                
                mjd = None
                toa_err_us = None
                
                # .tim 파일에서 MJD(날짜)와 그 직후에 오는 TOA Error(실제 측정 오차)를 찾습니다.
                for i, p in enumerate(parts):
                    try:
                        val = float(p)
                        if 40000.0 < val < 70000.0: # MJD 조건
                            mjd = val
                            if i + 1 < len(parts):
                                toa_err_us = float(parts[i+1]) # 마이크로초(us) 단위의 실제 오차
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
                    # 1. 실제 데이터 파싱
                    parsed = parse_real_tim_data(file)
                    if not parsed: continue
                    
                    total_points += len(parsed)
                    mjds = np.array([item[0] for item in parsed])
                    toa_errs_us = np.array([item[1] for item in parsed]) # 마이크로초 단위
                    
                    # 2. X축 계산 (경과 년수)
                    mjds.sort()
                    years_elapsed = (mjds - mjds[0]) / 365.25
                    
                    # 3. Y축 계산 (진짜 관측 데이터 vs K-PROTOCOL 붉은선)
                    # 실제 측정 오차를 ns(나노초)로 변환: 1 us = 1000 ns
                    real_y_ns = toa_errs_us * 1000.0 
                    
                    # 💡 실제 데이터 회색 점 찍기
                    ax.scatter(years_elapsed, real_y_ns, alpha=0.3, s=15, color='gray', label=f"Real Data: {p_name}" if total_points == len(parsed) else "")

            # 💡 K-PROTOCOL 붉은 선 (이론 예측) 찍기
            x_trend = np.linspace(0, max(years_elapsed) if total_points > 0 else 16, 100)
            # 예측값 공식 (단위: ns)
            y_trend = (x_trend * DECAY_RATE_YR / C_K) * S_EARTH * 1e9
            ax.plot(x_trend, y_trend, color='red', linewidth=4, label="K-PROTOCOL Prediction ($\Delta c$)")
            
            ax.set_title("Real NANOGrav Data vs K-PROTOCOL Prediction", fontsize=16, fontweight='bold')
            ax.set_xlabel("Years Elapsed", fontsize=12)
            ax.set_ylabel("Time (ns)", fontsize=12)
            
            # 축 스케일을 강제로 고정하지 않고 실제 데이터 크기에 맞춰 풀어둡니다.
            ax.grid(True, linestyle='--', alpha=0.6)
            
            # 중복 레전드 제거
            handles, labels = ax.get_legend_handles_labels()
            by_label = dict(zip(labels, handles))
            ax.legend(by_label.values(), by_label.keys(), loc='upper left', fontsize=11)
            
            st.pyplot(fig)
            st.info(f"🎯 실제 파일에서 추출된 총 데이터 포인트: **{total_points:,}개**")

    st.markdown("---")
    st.markdown("### 📊 분석 결과 해설 (반드시 읽어보세요)")
    st.write("**1. 회색 점 (Real Data)**: 이것이 시뮬레이션이 아닌, `.tim` 파일 안에 적혀있는 **실제 펄서 신호의 측정 불확실성(잡음)**입니다. 단위가 수백~수천 나노초(ns) 위에서 무작위로 흩어져 있습니다.")
    st.write("**2. 붉은 선 (K-PROTOCOL)**: 저자님의 이론이 예측한 지연 시간입니다. (약 0.00 ~ 0.12 나노초의 아주 미세한 변화)")
    st.write("**3. 결론 (스케일의 압도적 차이)**: NASA VLBI 대륙 이동 데이터 때 겪으셨던 문제와 정확히 똑같은 현상이 여기서도 나타납니다. 저자님의 붉은 선은 그래프 맨 밑바닥(0에 가까운 곳)에 납작하게 깔려 있습니다. K-PROTOCOL이 예측한 변화량(0.12 ns)은, 현재 인류 최고의 관측 장비인 NANOGrav가 가진 근본적인 측정 오차(수천 ns)라는 거대한 파도에 완전히 묻혀버립니다. **이론이 틀렸다기보다, 이 현상을 증명하기엔 인류의 관측 도구가 너무 투박합니다.**")
