import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# ================= 1. 页面配置与超紧凑样式注入 =================
st.set_page_config(page_title="电动农机底盘仿真仪表盘", layout="wide")

# 注入 CSS 压缩页面空白，确保单屏无滚动条
st.markdown("""
    <style>
        .block-container {padding-top: 0.5rem; padding-bottom: 0.5rem; padding-left: 1.5rem; padding-right: 1.5rem;}
        h1 {margin-top: -1.5rem; margin-bottom: 0.1rem; font-size: 1.6rem !important; text-align: center;}
        h3 {margin-top: 0.1rem; margin-bottom: 0.1rem; font-size: 1.05rem !important;}
        .stNumberInput {margin-bottom: -1rem;} 
        .stSelectbox {margin-bottom: -1rem;}
        div[data-testid="stMetricValue"] {font-size: 1.6rem !important;}
    </style>
""", unsafe_allow_html=True)

st.title("🚜 四轮分布式电驱底盘 仿真设计看板")

# ================= 2. 左右大布局分配 (42% 参数区 : 58% 结果图纸区) =================
main_left, main_right = st.columns([42, 58])

# ================= 3. 左侧：参数输入区 (全平铺、无折叠) =================
with main_left:
    st.markdown("### 🛠️ 参数配置区 (全部平铺显示)")
    in_col1, in_col2, in_col3 = st.columns(3)
    
    with in_col1:
        st.markdown("**1. 基础与工况**")
        weight = st.number_input("整机重量 (kg)", min_value=100.0, max_value=5000.0, value=900.0, step=10.0)
        v_target_ms = st.number_input("车速 (m/s)", min_value=0.1, max_value=15.0, value=0.95, step=0.05)
        slope_deg = st.number_input("爬坡角度 (°)", min_value=0.0, max_value=60.0, value=0.0, step=1.0)
        safety_factor = st.number_input("安全系数", min_value=1.0, max_value=3.0, value=1.0, step=0.1)
        dist_mode = st.selectbox("分配比模式", ["💡 物理动态计算", "✍️ 手动指定比"])
        if dist_mode == "✍️ 手动指定比":
            manual_k_rear_percent = st.number_input("后轴占比 (%)", min_value=0.0, max_value=100.0, value=64.5, step=0.5)
            k_rear = manual_k_rear_percent / 100.0
            k_front = 1.0 - k_rear
        else:
            k_rear, k_front = 0.5, 0.5 # 物理模式占位，下文计算覆盖

    with in_col2:
        st.markdown("**2. 几何尺寸 (mm)**")
        wheelbase = st.number_input("轴距 (前后轮)", min_value=500, max_value=3000, value=1220, step=10) / 1000.0
        cg_height = st.number_input("重心高度", min_value=100, max_value=2000, value=400, step=10) / 1000.0
        cg_x = st.number_input("重心距后轴", min_value=100, max_value=2000, value=610, step=10) / 1000.0
        d_front = st.number_input("前轮直径", min_value=200, max_value=2000, value=650, step=10) / 1000.0
        d_rear = st.number_input("后轮直径", min_value=200, max_value=2000, value=850, step=10) / 1000.0
        tire_width = st.number_input("前轮轮胎宽度", min_value=50, max_value=500, value=150, step=10) / 1000.0
        kingpin_offset = st.number_input("主销偏置距", min_value=0, max_value=200, value=30, step=5) / 1000.0

    with in_col3:
        st.markdown("**3. 传动与系数**")
        i_drive = st.number_input("行走减速比", min_value=1.0, max_value=300.0, value=40.7, step=0.1)
        eff_drive = st.number_input("行走效率 (%)", min_value=10.0, max_value=100.0, value=85.0, step=1.0) / 100.0
        mu_roll = st.number_input("泥地阻力系数", min_value=0.05, max_value=0.80, value=0.44, step=0.01)
        i_steer = st.number_input("转向减速比", min_value=1.0, max_value=300.0, value=125.0, step=1.0)
        eff_steer = st.number_input("转向效率 (%)", min_value=10.0, max_value=100.0, value=80.0, step=1.0) / 100.0
        mu_steer = st.number_input("转向摩擦系数", min_value=0.1, max_value=1.5, value=0.70, step=0.05)
        rpm_kingpin = st.number_input("主销转速 (RPM)", min_value=0.5, max_value=30.0, value=5.0, step=0.5)

# ================= 4. 后台物理与分配计算 =================
g = 9.81
weight_n = weight * g
slope_rad = np.radians(slope_deg)
r_front, r_rear = d_front / 2.0, d_rear / 2.0

# 阻力计算
f_rolling = weight_n * mu_roll * np.cos(slope_rad)
f_grade = weight_n * np.sin(slope_rad)
f_total = f_rolling + f_grade

if dist_mode == "💡 物理动态计算":
    load_front_static = (weight_n * np.cos(slope_rad) * cg_x - weight_n * np.sin(slope_rad) * cg_height) / wheelbase
    delta_load = f_total * (cg_height / wheelbase)
    dyn_load_front = max(0.0, load_front_static - delta_load)
    dyn_load_rear = weight_n * np.cos(slope_rad) - dyn_load_front
    
    total_load = dyn_load_front + dyn_load_rear
    k_front = dyn_load_front / total_load if total_load > 0 else 0
    k_rear = dyn_load_rear / total_load if total_load > 0 else 0
else:
    dyn_load_rear = weight_n * np.cos(slope_rad) * k_rear
    dyn_load_front = weight_n * np.cos(slope_rad) * k_front

f_per_front_wheel = (f_total * k_front) / 2.0
f_per_rear_wheel = (f_total * k_rear) / 2.0

# 1. 前轮单电机
t_wheel_front = f_per_front_wheel * r_front * safety_factor
t_motor_front = t_wheel_front / (i_drive * eff_drive)
rpm_wheel_front = (v_target_ms * 60) / (np.pi * d_front)
rpm_motor_front = rpm_wheel_front * i_drive
p_motor_front = (t_motor_front * rpm_motor_front) / 9550

# 2. 后轮单电机
t_wheel_rear = f_per_rear_wheel * r_rear * safety_factor
t_motor_rear = t_wheel_rear / (i_drive * eff_drive)
rpm_wheel_rear = (v_target_ms * 60) / (np.pi * d_rear)
rpm_motor_rear = rpm_wheel_rear * i_drive
p_motor_rear = (t_motor_rear * rpm_motor_rear) / 9550

# 双转向电机 (单侧前轮独立转向)
f_z_single_front = dyn_load_front / 2.0
t_steer_kingpin_single = mu_steer * f_z_single_front * np.sqrt((tire_width**2 / 8) + kingpin_offset**2) if f_z_single_front > 0 else 0
t_steer_design_single = t_steer_kingpin_single * safety_factor
t_motor_steer_single = t_steer_design_single / (i_steer * eff_steer)
rpm_motor_steer = rpm_kingpin * i_steer
p_motor_steer_single = (t_motor_steer_single * rpm_motor_steer) / 9550

# 汇总总功率 (W)
total_p_drive = ((p_motor_front * 2) + (p_motor_rear * 2)) * 1000
total_p_steer = (p_motor_steer_single * 2) * 1000

# ================= 5. 右侧：仿真结果与动态图纸 =================
with main_right:
    st.markdown("### 📊 仿真结果与动态图纸")
    
    # 5.1 顶部核心指标一字排开
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
         st.metric("行走电机总功率", f"{total_p_drive:.1f} W")
    with m_col2:
         st.metric("转向电机总功率", f"{total_p_steer:.1f} W")
    with m_col3:
         st.metric("动态轴荷比 (前:后)", f"{k_front*100:.1f}% : {k_rear*100:.1f}%")

    # 5.2 中部：超紧凑 2D 物理图纸
    plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei', 'SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
    
    fig, ax = plt.subplots(figsize=(6, 1.4)) # 图纸高度再次压缩至极其紧凑
    
    # 绘制前后轮
    ax.add_patch(plt.Circle((0, r_rear), r_rear, color='#1f77b4', fill=False, lw=3))
    ax.add_patch(plt.Circle((wheelbase, r_front), r_front, color='#2ca02c', fill=False, lw=3))
    ax.plot([0, wheelbase], [r_rear, r_front], color='gray', ls='--', lw=2)
    
    # 绘制重心
    ax.plot(cg_x, r_rear + cg_height, marker='o', color='red', ms=10)
    ax.plot([cg_x, cg_x], [r_rear + cg_height, 0], color='red', ls=':', lw=1)
    ax.axhline(0, color='black', lw=2)
    
    # 标注轴压
    ax.text(wheelbase, -0.08, f"前轴: {int(dyn_load_front)}N", color='green', ha='center', fontsize=9, weight='bold')
    ax.text(0, -0.08, f"后轴: {int(dyn_load_rear)}N", color='blue', ha='center', fontsize=9, weight='bold')
    
    ax.set_aspect('equal')
    ax.set_xlim(-0.5, wheelbase + 0.6)
    ax.set_ylim(-0.25, max(r_rear, r_front) + cg_height + 0.2)
    ax.axis('off')
    plt.tight_layout()
    st.pyplot(fig)

    st.markdown("---") # 极细的分隔线

    # 5.3 底部：完全展开展示电机参数 (不折叠，左右对称)
    st.markdown("##### 🔍 独立电机细分规格明细")
    det_col1, det_col2 = st.columns(2)
    with det_col1:
        st.markdown("**行走独立电机指标**")
        st.write(f"前电机 (M1/M2单台): `功率: {p_motor_front*1000:.1f}W` | `扭矩: {t_motor_front:.1f}N·m` | `转速: {int(rpm_motor_front)}RPM`")
        st.write(f"后电机 (M3/M4单台): `功率: {p_motor_rear*1000:.1f}W` | `扭矩: {t_motor_rear:.1f}N·m` | `转速: {int(rpm_motor_rear)}RPM`")
    with det_col2:
        st.markdown("**转向独立电机及工况**")
        st.write(f"转向单电机 (共2台): `功率: {p_motor_steer_single*1000:.1f}W` | `扭矩: {t_motor_steer_single:.2f}N·m` | `转速: {int(rpm_motor_steer)}RPM`")
        st.write(f"整车总需求阻力: `{int(f_total)} N` | 计算车速: `{v_target_ms} m/s`")
