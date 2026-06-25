import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# ================= 1. 页面配置与看板级 UI 样式注入 =================
st.set_page_config(page_title="4WID 农机底盘校核看板", layout="wide")

st.markdown("""
    <style>
        /* 隐藏无用元素，极致压缩边距 */
        header {visibility: hidden; height: 0px !important;}
        footer {visibility: hidden;}
        .block-container {padding-top: 1.0rem !important; padding-bottom: 0.2rem !important; padding-left: 1.5rem; padding-right: 1.5rem;}
        
        /* 看板卡片样式 */
        .panel-card {
            background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px;
            padding: 8px 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.04); margin-bottom: 8px;
        }
        .section-title { font-size: 0.95rem; font-weight: 700; color: #1e293b; border-bottom: 2px solid #3b82f6; padding-bottom: 4px; margin-bottom: 8px; }
        
        /* 状态指示牌 */
        .status-badge-ok { background-color: #dcfce7; color: #166534; padding: 2px 6px; border-radius: 4px; font-weight: 600; font-size: 0.75rem;}
        .status-badge-err { background-color: #fee2e2; color: #991b1b; padding: 2px 6px; border-radius: 4px; font-weight: 600; font-size: 0.75rem;}
        
        /* 高档数据表格 */
        .styled-table { width: 100%; border-collapse: collapse; font-size: 0.82rem; text-align: left; }
        .styled-table th { background-color: #f8fafc; color: #475569; padding: 5px 8px; border-bottom: 1.5px solid #cbd5e1; }
        .styled-table td { padding: 4px 8px; border-bottom: 1px solid #f1f5f9; color: #334155; }
        
        /* 紧凑输入框 */
        .stNumberInput {margin-bottom: -1.0rem !important; margin-top: -6px !important;}
        label {font-size: 0.72rem !important; color: #475569 !important;}
        
        /* 数学公式字体颜色 */
        .katex { font-size: 0.95em !important; color: #1e293b; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center; margin-top: -30px; margin-bottom: 5px; font-size: 1.6rem; color: #0f172a;'>🚜 4WID 高速插秧机底盘 综合校核看板 (含转向)</h2>", unsafe_allow_html=True)

# ================= 2. 全局布局 (33% 参数区 : 67% 校核与视图区) =================
col_params, col_analysis = st.columns([33, 67])

# ================= 3. 左侧：手册级参数配置区 =================
with col_params:
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🛠️ 1. 物理与环境参数输入</div>', unsafe_allow_html=True)
    
    p1, p2 = st.columns(2)
    with p1:
        weight = st.number_input("整机总质量 G (kg)", value=900.0, step=10.0)
        v_target_ms = st.number_input("设计速度 v (m/s)", value=0.95, step=0.05)
        cg_x = st.number_input("重心距后轴 Lg (mm)", value=427, step=10) / 1000.0
        cg_height = st.number_input("重心高度 Hg (mm)", value=400, step=10) / 1000.0
        fc_float = st.number_input("浮船滑行阻力 Fc (N)", value=600.0, step=50.0)
        sf = st.number_input("安全系数 S", min_value=1.0, value=1.0, step=0.1)
        
    with p2:
        wheelbase = st.number_input("轴距 L (mm)", value=1220, step=10) / 1000.0
        d_front = st.number_input("前轮直径 D2 (mm)", value=650, step=10) / 1000.0
        d_rear = st.number_input("后轮直径 D1 (mm)", value=850, step=10) / 1000.0
        i_drive = st.number_input("行走减速比 i", value=40.7, step=0.1)
        eff_drive = st.number_input("行走效率 η (%)", value=85.0, step=1.0) / 100.0
        
    st.markdown("<div style='margin-top:15px; margin-bottom:5px; font-size:0.8rem; font-weight:bold; color:#1e293b;'>🌍 2. 地面力学系数 (手册P513)</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        f2 = st.number_input("前轮滚阻系数 f2", value=0.28, step=0.01)
        phi2 = st.number_input("前轮附着系数 φ2", value=0.65, step=0.01)
    with c2:
        f1 = st.number_input("后轮滚阻系数 f1", value=0.35, step=0.01)
        phi1 = st.number_input("后轮附着系数 φ1", value=0.80, step=0.01)
        
    st.markdown("<div style='margin-top:15px; margin-bottom:5px; font-size:0.8rem; font-weight:bold; color:#1e293b;'>🔄 3. 独立线控转向系统 (EPS)</div>", unsafe_allow_html=True)
    s1, s2 = st.columns(2)
    with s1:
        tire_width = st.number_input("前轮胎宽度 B (mm)", value=150, step=10) / 1000.0
        kingpin_offset = st.number_input("主销偏置距 e (mm)", value=30, step=5) / 1000.0
        mu_steer = st.number_input("原地转向摩擦系数 μ", value=0.70, step=0.05)
    with s2:
        i_steer = st.number_input("转向减速比", value=125.0, step=1.0)
        eff_steer = st.number_input("转向效率 (%)", value=80.0, step=1.0) / 100.0
        rpm_kingpin = st.number_input("主销目标转速 (RPM)", value=5.0, step=0.5)
        
    st.markdown('</div>', unsafe_allow_html=True)

# ================= 4. 后台核心算法 (动力+转向) =================
g = 9.81
G_N = weight * g

# 4.1 行走：动态轴荷与重心转移
Q_front_static = G_N * cg_x / wheelbase
Q_rear_static = G_N - Q_front_static

F_total_est = (Q_front_static * f2) + (Q_rear_static * f1) + fc_float
delta_Q = F_total_est * (cg_height / wheelbase)

Qd2 = max(0.0, Q_front_static - delta_Q) # 前轴动态载荷
Qd1 = G_N - Qd2                          # 后轴动态载荷

# 4.2 行走：真实阻力与附着力
Fd2 = Qd2 * f2
Fd1 = Qd1 * f1
Pd_total = Fd2 + Fd1 + fc_float # 总需求推力

P_max2 = Qd2 * phi2  # 前轴极限附着力
P_max1 = Qd1 * phi1  # 后轴极限附着力

# 4.3 行走：最优扭矩分配
ratio_rear = (Qd1 * phi1) / ((Qd1 * phi1) + (Qd2 * phi2))
ratio_front = 1.0 - ratio_rear

Pd1_req = Pd_total * ratio_rear
Pd2_req = Pd_total * ratio_front

r1, r2 = d_rear / 2.0, d_front / 2.0
T_motor_rear = (Pd1_req / 2.0) * r1 * sf / (i_drive * eff_drive)
T_motor_front = (Pd2_req / 2.0) * r2 * sf / (i_drive * eff_drive)

rpm_motor_rear = (v_target_ms * 60 / (np.pi * d_rear)) * i_drive
rpm_motor_front = (v_target_ms * 60 / (np.pi * d_front)) * i_drive

P_kw_rear = (T_motor_rear * rpm_motor_rear) / 9550
P_kw_front = (T_motor_front * rpm_motor_front) / 9550

# 4.4 转向：独立EPS双电机计算
f_z_single_front = Qd2 / 2.0
t_steer_kingpin_single = mu_steer * f_z_single_front * np.sqrt((tire_width**2 / 8) + kingpin_offset**2) if f_z_single_front > 0 else 0
t_steer_design_single = t_steer_kingpin_single * sf
t_motor_steer_single = t_steer_design_single / (i_steer * eff_steer)
rpm_motor_steer = rpm_kingpin * i_steer
P_kw_steer_single = (t_motor_steer_single * rpm_motor_steer) / 9550

# 状态判定
slip_front_status = "打滑警告!" if Pd2_req > P_max2 else "附着正常"
slip_rear_status = "打滑警告!" if Pd1_req > P_max1 else "附着正常"
badge_f = "status-badge-err" if Pd2_req > P_max2 else "status-badge-ok"
badge_r = "status-badge-err" if Pd1_req > P_max1 else "status-badge-ok"

# ================= 5. 右侧：设计校核与图纸 =================
with col_analysis:
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📈 动力学状态图纸与轴荷监控</div>', unsafe_allow_html=True)
    
    # 5.1 紧凑图纸
    plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei', 'SimHei', 'Microsoft YaHei']
    plt.rcParams['axes.unicode_minus'] = False
    fig, ax = plt.subplots(figsize=(6.0, 1.1), dpi=120)
    
    ax.add_patch(plt.Circle((0, r1), r1, facecolor='#e1f5fe', edgecolor='#1f77b4', lw=1.5))
    ax.add_patch(plt.Circle((wheelbase, r2), r2, facecolor='#e8f5e9', edgecolor='#2ca02c', lw=1.5))
    ax.add_patch(plt.Circle((0, r1), 0.02, color='#334155'))
    ax.add_patch(plt.Circle((wheelbase, r2), 0.02, color='#334155'))
    ax.plot([0, wheelbase], [r1, r2], color='#64748b', lw=3.0, solid_capstyle='round')
    ax.plot([-0.2, wheelbase+0.2], [-0.02, -0.02], color='#94a3b8', lw=2.0, ls='-.') 
    ax.plot(cg_x, r1 + cg_height, marker='o', color='#ef4444', ms=6)
    ax.plot([cg_x, cg_x], [r1 + cg_height, 0], color='#ef4444', ls=':', lw=0.8)
    ax.axhline(0, color='#1e293b', lw=1.2)
    
    ax.text(0, r1 + 0.1, f"后轴动态载荷 Qd1: {int(Qd1)}N", color='#1f77b4', ha='center', fontsize=7.5, weight='bold')
    ax.text(wheelbase, r2 + 0.1, f"前轴动态载荷 Qd2: {int(Qd2)}N", color='#2ca02c', ha='center', fontsize=7.5, weight='bold')
    
    ax.set_aspect('equal')
    ax.set_xlim(-0.4, wheelbase + 0.4)
    ax.set_ylim(-0.15, max(r1, r2) + cg_height + 0.15)
    ax.axis('off')
    plt.tight_layout()
    
    _, plot_col, _ = st.columns([1, 8, 1])
    with plot_col:
        st.pyplot(fig, use_container_width=False)
    st.markdown('</div>', unsafe_allow_html=True)

    # 5.2 综合校核报告表 (含转向)
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">✅ 附着力校核与全车电机输出规格明细</div>', unsafe_allow_html=True)
    
    table_html = f"""
    <table class="styled-table">
        <thead>
            <tr>
                <th style="width: 25%;">电机类别与位置</th>
                <th style="width: 17%;">设计目标推力/阻力</th>
                <th style="width: 15%;">打滑校核状态</th>
                <th style="width: 15%;">单台电机功率</th>
                <th style="width: 14%;">单台电机扭矩</th>
                <th style="width: 14%;">转速指令</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td style="color:#2ca02c; font-weight:600;">前轮驱动电机 (M1/M2)</td>
                <td>{Pd2_req/2:.0f} N <span style="font-size:0.7rem;">/ 轮</span></td>
                <td><span class="{badge_f}">{slip_front_status}</span></td>
                <td style="font-weight:600; color:#2ca02c;">{P_kw_front*1000:.1f} W</td>
                <td>{T_motor_front:.1f} N·m</td>
                <td>{int(rpm_motor_front)} RPM</td>
            </tr>
            <tr>
                <td style="color:#1f77b4; font-weight:600;">后轮驱动电机 (M3/M4)</td>
                <td>{Pd1_req/2:.0f} N <span style="font-size:0.7rem;">/ 轮</span></td>
                <td><span class="{badge_r}">{slip_rear_status}</span></td>
                <td style="font-weight:600; color:#1f77b4;">{P_kw_rear*1000:.1f} W</td>
                <td>{T_motor_rear:.1f} N·m</td>
                <td>{int(rpm_motor_rear)} RPM</td>
            </tr>
            <tr style="background-color: #f8fafc;">
                <td style="color:#f59e0b; font-weight:600;">前轮转向电机 (共2台)</td>
                <td>{t_steer_design_single:.1f} N·m <span style="font-size:0.7rem;">/ 主销</span></td>
                <td><span style="color:#94a3b8;">-</span></td>
                <td style="font-weight:600; color:#f59e0b;">{P_kw_steer_single*1000:.1f} W</td>
                <td>{t_motor_steer_single:.2f} N·m</td>
                <td>{int(rpm_motor_steer)} RPM</td>
            </tr>
        </tbody>
    </table>
    """
    st.markdown(table_html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ================= 6. 底部：核心理论计算公式库 (支持折叠收纳) =================
with st.expander("📚 团队研发参考：底盘核心理论计算公式库 (基于车辆地面力学与《农业机械设计手册》)"):
    f_c1, f_c2 = st.columns(2)
    with f_c1:
        st.markdown("**1. 动态轴荷转移公式**")
        st.latex(r"Q_{d2} (前轴) = G \cdot \frac{L_g}{L} - \Delta Q")
        st.latex(r"Q_{d1} (后轴) = G - Q_{d2}")
        st.latex(r"\text{其中抬头力矩转移量：} \Delta Q = F_{total} \cdot \frac{H_g}{L}")
        
        st.markdown("**2. 水田总需求阻力**")
        st.latex(r"P_{d\_total} = (Q_{d2} \cdot f_2) + (Q_{d1} \cdot f_1) + F_c")
        st.caption("注：$F_c$ 为浮船壅泥滑行阻力，$f_1, f_2$ 为泥地滚阻系数。")
        
        st.markdown("**3. 电机选型功率计算**")
        st.latex(r"P (kW) = \frac{T \cdot n}{9550}")
        st.latex(r"T_{motor} = \frac{F_{wheel} \cdot R_{wheel}}{i \cdot \eta}")
        
    with f_c2:
        st.markdown("**4. 《手册》最优附着扭矩分配比例**")
        st.latex(r"\frac{P_{d1}}{P_{d2}} \approx \frac{Q_{d1} \cdot \varphi_1}{Q_{d2} \cdot \varphi_2}")
        st.caption("指导 VCU 开发：根据前后轮当前的垂直载荷和附着极限，实时按比例下发力矩上限指令，可保证整机牵引效率最高且不打滑。")
        
        st.markdown("**5. 原地转向阻力矩公式 (最恶劣工况)**")
        st.latex(r"M_{steer} = \mu_{s} \cdot \frac{Q_{d2}}{2} \cdot \sqrt{\frac{B^2}{8} + e^2}")
        st.caption("注：$B$ 为轮胎宽度，$e$ 为主销偏置距，$\mu_s$ 为原地转向摩擦系数。动态轴荷 $Q_{d2}$ 变轻时，转向扭矩需求会自动减小。")
