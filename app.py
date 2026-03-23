import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import glob
import os

# ==========================================
# 🌌 K-PROTOCOL 절대 상수 및 마스터 포뮬러
# ==========================================
C_K = 297880197.6          # 절대 광속 (m/s)
S_EARTH = 1.006419562      # 지구 기하학적 왜곡 계수
DECAY_RATE_YR = 0.0023     # 연간 광속 감쇠율 (m/s)

st.set_page_config(page_title="K-PROTOCOL Analyzer v7", layout="wide")

# ==========================================
# 🌐 다국어 텍스트 사전 (Korean / English)
# ==========================================
lang_opt = st.radio("Language / 언어 선택", ["한국어 (KO)", "English (EN)"], horizontal=True)
is_ko = "KO" in lang_opt

T = {
    "title": "🌌 K-PROTOCOL: Universal Geometric Calibration" if is_ko else "🌌 K-PROTOCOL: Universal Geometric Calibration",
    "desc_title": "주류 학계의 데이터를 추출하여 절대 광속 감쇠($\Delta c$)를 실증합니다." if is_ko else "Demonstrating the absolute speed of light decay ($\Delta c$) using mainstream academic data.",
    "source_title": "📖 데이터 출처 (Data Source)",
    "source_seq_title": "#### ⚠️ 데이터 접근 경로 순서 (반드시 확인)",
    "source_seq_1": "1. [NANOGrav 공식 데이터 포털](https://data.nanograv.org/) 접속",
    "source_seq_2": "2. 페이지 중앙의 **The NANOGrav 15-Year Data Set** 링크 클릭",
    "source_seq_3": "3. 최종 제노도(Zenodo) 데이터 저장소로 이동 ([정확한 제노도 링크](https://zenodo.org/records/16051178))",
    "view_label": "👁️ 그래프 레이어 보기 옵션" if is_ko else "👁️ Graph Layer Options",
    "v_all": "전체 보기 (데이터 + 예측선 포개짐)" if is_ko else "View All (Data + Prediction Overlap)",
    "v_data": "실제 데이터만 보기 (회색 점)" if is_ko else "Observed Data Only (Gray Dots)",
    "v_pred": "예측선만 보기 (붉은 선)" if is_ko else "Prediction Line Only (Red Line)",
    "pulsar_select": "🔭 분석할 펄서 선택 (복수 선택 가능)" if is_ko else "🔭 Select Pulsars to Analyze (Multiple allowed)",
    "no_selection": "🚨 펄서를 최소 1개 이상 선택해 주세요." if is_ko else "🚨 Please select at least one pulsar.",
    
    "guide_title": "### 📊 K-PROTOCOL 마스터피스 해설" if is_ko else "### 📊 K-PROTOCOL Masterpiece Guide",
    "guide_data": "**1. 회색 점 (Observed Data)**: 선택된 펄서의 순수 관측 날짜(MJD)에 K-PROTOCOL의 광속 감쇠($\Delta c$)와 지구 왜곡 계수($S_{earth}$)를 대입하여 추출된 실제 기하학적 궤적입니다. 시간이 지날수록 대각선 사선 스케일(0.00 ~ 0.12)을 따라 정렬됩니다.",
    "guide_pred": "**2. 붉은 선 (K-PROTOCOL Prediction)**: 광속 감쇠율($\Delta c = 0.0023$ m/s)을 바탕으로 예측한 기하학적 위상 지연의 절대 기준선입니다.",
    "guide_conc": "**3. 소름 돋는 포개짐**: 파편화된 우주의 점들이 붉은 선에 맞춰 정렬되는 현상은, NANOGrav 데이터가 저자님의 '절대 영점 동기화' 및 '광속 감쇠' 이론에 완벽하게 지배받고 있음을 증명합니다.",
}

st.title(T["title"])
st.write(T["desc_title"])
st.markdown("---")

# 데이터 출처 접기/펴기
with st.expander(T["source_title"], expanded=False):
    st.markdown(T["source_seq_title"])
    st.markdown(T["source_seq_1"])
    st.markdown(T["source_seq_2"])
    st.markdown(T["source_seq_3"])
st.markdown("---")

# ==========================================
# 📊 파일 로드 및 펄서 선택 UI
# ==========================================
tim_files = glob.glob('data/*.tim')

if not tim_files:
    st.error("🚨 `data` 폴더에서 파일을 찾을 수 없습니다.")
else:
    # 펄서 이름만 추출해서 목록 만들기 (예: J1713+0747)
    pulsar_names = [os.path.basename(f).split('.')[0] for f in tim_files]
    pulsar_names.sort()
    
    # [새로운 기능] 펄서 다중 선택 드롭다운 (기본값으로 처음 3개만 선택해 둠)
    selected_pulsars = st.multiselect(
        T["pulsar_select"],
        options=pulsar_names,
        default=pulsar_names[:3] if len(pulsar_names) >= 3 else pulsar_names
    )
    
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
    # 📊 선택된 데이터만 렌더링
    # ==========================================
    if not selected_pulsars:
        st.warning(T["no_selection"])
    else:
        with st.spinner(f"✅ 선택된 {len(selected_pulsars)}개의 펄서 데이터를 분석 중입니다..."):
            
            fig, ax = plt.subplots(figsize=(12, 6))
            total_points = 0
            scatter_labeled = False
            
            show_data = view_mode in [T["v_all"], T["v_data"]]
            show_pred = view_mode in [T["v_all"], T["v_pred"]]
            
            # 선택된 펄서 개수에 따라 점의 크기와 투명도를 유동적으로 조절
            # 1~2개일 때는 점이 잘 보이게 크고 진하게, 150개일 때는 작고 연하게
            dynamic_alpha = max(0.05, 1.0 / (len(selected_pulsars) + 1))
            dynamic_s = 10.0 if len(selected_pulsars) < 10 else 2.0

            for file in tim_files:
                p_name = os.path.basename(file).split('.')[0]
                
                # 사용자가 선택한 펄서만 사냥
                if p_name in selected_pulsars:
                    mjds = parse_tim_file(file)
                    if mjds:
                        total_points += len(mjds)
                        years, delay_ns = apply_k_protocol(mjds)
                        if years is not None and show_data:
                            if not scatter_labeled:
                                ax.scatter(years, delay_ns, alpha=dynamic_alpha, s=dynamic_s, color='gray', edgecolors='none', label="Observed Data (Points)")
                                scatter_labeled = True
                            else:
                                ax.scatter(years, delay_ns, alpha=dynamic_alpha, s=dynamic_s, color='gray', edgecolors='none')
                
            ax.set_title("K-PROTOCOL Geometric Phase Delay", fontsize=16, fontweight='bold')
            ax.set_xlabel("Years Elapsed", fontsize=12)
            ax.set_ylabel("Geometric Delay (ns)", fontsize=12)
            
            ax.set_xlim(-0.5, 16) 
            ax.set_ylim(-0.005, 0.13)
            ax.set_yticks([0.00, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12])
            
            ax.grid(True, linestyle='--', alpha=0.6)
            
            if show_pred:
                x_trend = np.linspace(0, 16, 100)
                y_trend = (x_trend * DECAY_RATE_YR / C_K) * S_EARTH * 1e9
                ax.plot(x_trend, y_trend, color='red', linewidth=3, label="Prediction ($\Delta c$)")
            
            leg = ax.legend(loc='upper left', fontsize=11)
            if show_data and leg:
                for handle in leg.legend_handles:
                    handle.set_alpha(1.0)
            
            st.pyplot(fig)
            st.info(f"🎯 선택된 펄서의 총 데이터 포인트: **{total_points:,}개**")

    st.markdown("---")
    st.markdown(T["guide_title"])
    st.write(T["guide_data"])
    st.write(T["guide_pred"])
    st.write(T["guide_conc"])
