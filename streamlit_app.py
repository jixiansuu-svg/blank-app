import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# ================= 1. 页面基本布局 =================
st.set_page_config(page_title="四轮独立电动底盘可视化系统", layout="wide")
st.title("⚡ 4WD独立驱动 底盘可视化设计系统 (分布式驱动)")
st.markdown("支持精准数值输入。自动分别计算 **前侧独立电机**、**后侧独立电机** 以及 **转向电机** 的具体选型参数。")

# ================= 2. 侧边栏：精准数值输入 =================
st.sidebar.header("🚜 1. 基础物理与工况")
# 使用 number_input 替代 slider，支持直接键盘输入精确数值
weight = st.sidebar.number_input("整机重量 (kg)", min_value=100.0, max_value=5000.0, value=900.0, step=10.0)
slope_deg = st.sidebar.number_input("最大爬坡角度 (°)", min_value=0.0, max_value=60.0, value=15.0, step=1.0)
v_target_kmh = st.sidebar.number_input("目标最高车速 (km/h)", min_value=0.5, max_value=50.0, value=6.0, step=0.5)
safety_factor = st.sidebar.number_input("整机动力安全系数", min_value=1.0, max_value=3.0, value=1.3, step=0.1)
mu_roll = st.sidebar.number_input("烂泥地滚动阻力系数", min_value=0.05, max_value=0.80, value=0.30, step=0.01)

st.sidebar.header("📐 2. 底盘几何参数 (mm)")
wheelbase = st.sidebar.number_input("轴距 (前后轮中心距)", min_value=500, max_value=3000, value=1220, step=10) / 1000.0
cg_height = st.sidebar.number_input("重心高度", min_value=100, max_value=2000, value=600, step=10) / 1000.0
cg_x = st.sidebar.number_input("重心距后轴距离", min_value=100, max_value=2000, value=610, step=10) / 1000.0
d_front = st.sidebar.number_input("前轮直径", min_value=200, max_value=2000, value=650, step=10) / 1000.0
d_rear = st.sidebar.number_input("后轮直径", min_value=200, max_value=2000, value=950, step=10) / 1000.0

st.sidebar.header("⚙️ 3. 传动与转向参数")
st.sidebar.caption("提示：若采用轮毂电机直驱，行走减速比请设为 1")
i_drive = st.sidebar.number_input("行走系统总减速比", min_value=1.0, max_value=200.0, value=50.0, step=1.0)
eff_drive = st.sidebar.number_input("行走传动综合效率 (%)", min_value=10.0, max_value=100.0, value=85.0,
                                    step=1.0) / 100.0

i_steer = st.sidebar.number_input("转向机构总减速比", min_value=1.0, max_value=200.0, value=30.0, step=1.0)
eff_steer = st.sidebar.number_input("转向传动综合效率 (%)", min_value=10.0, max_value=100.0, value=80.0,
                                    step=1.0) / 100.0

tire_width = st.sidebar.number_input("前轮轮胎宽度 (mm)", min_value=50, max_value=500, value=150, step=10) / 1000.0
kingpin_offset = st.sidebar.number_input("主销偏置距 (mm)", min_value=0, max_value=200, value=30, step=5) / 1000.0

# ================= 3. 核心物理计算 =================
g = 9.81
weight_n = weight * g
slope_rad = np.radians(slope_deg)
v_target_ms = v_target_kmh / 3.6
r_front = d_front / 2.0
r_rear = d_rear / 2.0

# --- A. 动态轴荷转移 ---
load_front = (weight_n * np.cos(slope_rad) * cg_x - weight_n * np.sin(slope_rad) * cg_height) / wheelbase
load_rear = weight_n * np.cos(slope_rad) - load_front
if load_front < 0: load_front = 0  # 防止翘头

# --- B. 独立行走系统计算 (四轮独立) ---
f_rolling = weight_n * mu_roll * np.cos(slope_rad)
f_grade = weight_n * np.sin(slope_rad)
f_total = f_rolling + f_grade

# 假设推力在4个轮子上均匀分配 (每轮提供 1/4 推力)
f_per_wheel = f_total / 4.0

# 1. 前轮两台独立电机参数
t_wheel_front = f_per_wheel * r_front * safety_factor
t_motor_front = t_wheel_front / (i_drive * eff_drive)
rpm_wheel_front = (v_target_ms * 60) / (np.pi * d_front)
rpm_motor_front = rpm_wheel_front * i_drive
p_motor_front = (t_motor_front * rpm_motor_front) / 9550  # kW

# 2. 后轮两台独立电机参数
t_wheel_rear = f_per_wheel * r_rear * safety_factor
t_motor_rear = t_wheel_rear / (i_drive * eff_drive)
rpm_wheel_rear = (v_target_ms * 60) / (np.pi * d_rear)
rpm_motor_rear = rpm_wheel_rear * i_drive
p_motor_rear = (t_motor_rear * rpm_motor_rear) / 9550  # kW

# --- C. 转向系统计算 ---
mu_steer = 0.70  # 原地转向摩擦系数
f_z_single_front = load_front / 2.0
if f_z_single_front > 0:
    t_steer_kingpin = mu_steer * f_z_single_front * np.sqrt((tire_width ** 2 / 8) + kingpin_offset ** 2)
else:
    t_steer_kingpin = 0

t_steer_total = 2 * t_steer_kingpin * safety_factor  # 左右轮总转向柱扭矩
rpm_kingpin = 5.0  # 设定打方向的主销转速
rpm_motor_steer = rpm_kingpin * i_steer
t_motor_steer = t_steer_total / (i_steer * eff_steer)
p_motor_steer = (t_motor_steer * rpm_motor_steer) / 9550  # kW

# ================= 4. 前端排版展示 =================
col1, col2, col3 = st.columns([1.1, 1.1, 1.8])

with col1:
    st.success("⚙️ **四轮独立驱动系统 (Drive)**")
    st.metric("整机所需总推力 (包含爬坡/阻力)", f"{int(f_total)} N")
    st.markdown("---")

    st.markdown("🔵 **【前置独立电机】 (共 2 台)**")
    st.caption("基于前轮较小直径算出的各单台电机需求：")
    st.metric("单台前电机功率", f"{p_motor_front:.2f} kW")
    st.metric("单台前电机扭矩", f"{t_motor_front:.1f} N·m")
    st.metric("单台前电机转速", f"{int(rpm_motor_front)} RPM")

    st.markdown("---")
    st.markdown("🟢 **【后置独立电机】 (共 2 台)**")
    st.caption("基于后轮较大直径算出的各单台电机需求：")
    st.metric("单台后电机功率", f"{p_motor_rear:.2f} kW")
    st.metric("单台后电机扭矩", f"{t_motor_rear:.1f} N·m")
    st.metric("单台后电机转速", f"{int(rpm_motor_rear)} RPM")

with col2:
    st.info("🔄 **线控转向系统 (Steer)**")
    st.metric("当前动态前轴总载荷", f"{int(load_front)} N")
    st.metric("主销处转向总扭矩需求", f"{int(t_steer_total)} N·m")
    st.markdown("---")

    st.markdown("🟠 **【前轮转向电机】 (1 台)**")
    st.caption(f"已包含安全系数，基于效率 {eff_steer * 100}% 计算：")
    st.metric("转向电机功率", f"{p_motor_steer * 1000:.0f} W (瓦)")
    st.metric("转向电机输出扭矩", f"{t_motor_steer:.1f} N·m")
    st.metric("转向电机转速", f"{int(rpm_motor_steer)} RPM")

with col3:
    st.subheader("📐 底盘 2D 侧视简图 & 物理状态")
    # 设置支持中文显示
    plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei', 'SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False

    fig, ax = plt.subplots(figsize=(7, 4.5))

    # 画前后轮
    ax.add_patch(plt.Circle((0, r_rear), r_rear, color='#1f77b4', fill=False, lw=3, label='后轮'))
    ax.add_patch(plt.Circle((wheelbase, r_front), r_front, color='#2ca02c', fill=False, lw=3, label='前轮'))
    ax.plot([0, wheelbase], [r_rear, r_front], color='gray', ls='--', lw=2, label='底盘底板线')

    # 画重心
    ax.plot(cg_x, r_rear + cg_height, marker='o', color='red', ms=12, label='重心 (CG)')
    ax.plot([cg_x, cg_x], [r_rear + cg_height, 0], color='red', ls=':', lw=1)

    # 模拟坡面基准线
    ax.axhline(0, color='black', lw=2)

    # 注释轴荷
    ax.text(wheelbase, -0.15, f"前轴压: {int(load_front)}N", color='green', ha='center', fontsize=10, weight='bold')
    ax.text(0, -0.15, f"后轴压: {int(load_rear)}N", color='blue', ha='center', fontsize=10, weight='bold')

    if load_front == 0:
        ax.text(wheelbase / 2, max(r_rear, r_front), "⚠️ 警告：重心失稳，已向后翻车！", color='red', fontsize=14,
                fontweight='bold', ha='center')

    ax.set_aspect('equal')
    ax.set_xlim(-0.6, wheelbase + 0.8)
    ax.set_ylim(-0.3, max(r_rear, r_front) + cg_height + 0.4)
    ax.legend(loc='upper left', fontsize=9)
    ax.axis('off')
    st.pyplot(fig)

    st.markdown("---")
    st.markdown(f"**💡 工程师洞察 (基于当前参数)：**")
    st.markdown(
        f"- ⚠️ **转速差异**：由于后轮(直径{int(d_rear * 1000)}mm)比前轮(直径{int(d_front * 1000)}mm)大，在同等车速下，**前电机转速需达到 {int(rpm_motor_front)} RPM，而后电机仅需 {int(rpm_motor_rear)} RPM**。开发电控器时必须做**电子差速匹配**。")
    st.markdown(
        f"- ⚠️ **扭矩差异**：同样的推力要求下，大轮子产生的力臂更长，因此**后电机需要输出更大的扭矩 ({t_motor_rear:.1f} N·m) 才能推动车辆**。")
