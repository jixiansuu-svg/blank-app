import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# ================= 1. 页面配置与看板级 UI 样式注入 =================
st.set_page_config(page_title="4WID 农机底盘校核看板", layout="wide")

st.markdown("""
    <style>
        /* 隐藏无用元素，极致压缩边距以实现单屏 */
        header {visibility: hidden; height: 0px !important;}
        footer {visibility: hidden;}
        .block-container {padding-top: 1.2rem !important; padding-bottom: 0.2rem !important; padding-left: 1.5rem; padding-right: 1.5rem;}
        
        /* 看板卡片样式 */
        .panel-card {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 10px 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.04);
            margin-bottom: 8px;
        }
        .section-title { font-size: 0.95rem; font-weight: 700; color: #1e293b; border-bottom: 2px solid #3b82f6; padding-bottom: 4px; margin-bottom: 8px; }
        
        /* 状态指示牌 */
        .status-badge-ok { background-color: #dcfce7; color: #166534; padding: 2px 6px; border-radius: 4px; font-weight: 600; font-size: 0.8rem;}
        .status-badge-err { background-color: #fee2e2; color: #991b1b; padding: 2px 6px; border-radius: 4px; font-weight: 600; font-size: 0.8rem;}
        
        /* 高档数据表格 */
        .styled-table { width: 100%; border-collapse: collapse; font-size: 0.82rem; text-align: left; }
        .styled-table th { background-color: #f8fafc; color: #475569; padding: 6px 8px; border-bottom: 1.5px solid #cbd5e1; }
        .styled-table td { padding: 5px 8px; border-bottom: 1px solid #f1f5f9; color: #334155; }
        
        /* 紧凑输入框 */
        .stNumberInput {margin-bottom: -1.0rem !important; margin-top: -6px !important;}
        label {font-size: 0.75rem !important; color: #475569 !important;}
    </style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center; margin-top: -30px; margin-bottom: 10px; font-size: 1.6rem; color: #0f172a;'>🚜 4WID 高速插秧机底盘 设计与校核看板</h2>", unsafe_allow_html=True)

# ================= 2. 全局布局 (35% 参数区 : 65% 校核与视图区) =================
col_params, col_analysis = st.columns([35, 65])

# ================= 3. 左侧：手册级参数配置区 =================
with col_params:
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🛠️ 物理与环境参数输入 (参照手册)</div>', unsafe_allow_html=True)
    
    p1, p2 = st.columns(2)
    with p1:
        weight = st.number_input("整机总质量 G (kg)", value=900.0, step=10.0)
        v_target_ms = st.number_input("设计作业速度 (m/s)", value=0.95, step=0.05)
        cg_x = st.number_input("重心距后轴 Lg (mm)", value=427, step=10) / 1000.0
        cg_height = st.number_input("重心高度 Hg (mm)", value=400, step=10) / 1000.0
        fc_float = st.number_input("浮船滑行阻力 Fc (N)", value=600.0, step=50.0)
        
    with p2:
        wheelbase = st.number_input("轴距 L (mm)", value=1220, step=10) / 1000.0
        d_front = st.number_input("前轮直径 D2 (mm)", value=650, step=10) / 1000.0
        d_rear = st.number_input("后轮直径 D1 (mm)", value=850, step=10) / 1000.0
        i_drive = st.number_input("轮边减速比 i", value=40.7, step=0.1)
        eff_drive = st.number_input("传动效率 η (%)", value=85.0, step=1.0) / 100.0

    st.markdown("<div style='margin-top:15px; margin-bottom:5px; font-size:0.8rem; font-weight:bold; color:#475569;'>底盘地面力学系数 (参考手册P513)</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        f2 = st.number_input("前轮滚阻系数 fd2", value=0.28, step=0.01)
        phi2 = st.number_input("前轮附着系数 φ2", value=0.65, step=0.01)
    with c2:
        f1 = st.number_input("后轮滚阻系数 fd1", value=0.35, step=0.01)
        phi1 = st.number_input("后轮附着系数 φ1", value=0.80, step=0.01)
    st.markdown('</div>', unsafe_allow_html=True)

# ================= 4. 后台核心算法 (依据《农业机械设计手册》) =================
g = 9.81
G_N = weight * g

# 4.1 静态与动态轴荷计算 (考虑浮船阻力与滚阻造成的重心转移)
Q_front_static = G_N * cg_x / wheelbase
Q_rear_static = G_N - Q_front_static

# 初始估算总推力用于计算重心转移
F_total_est = (Q_front_static * f2) + (Q_rear_static * f1) + fc_float
delta_Q = F_total_est * (cg_height / wheelbase)

Qd2 = max(0.0, Q_front_static - delta_Q) # 前轴动态载荷
Qd1 = G_N - Qd2                          # 后轴动态载荷

# 4.2 真实阻力计算 (Fd = Q * f)
Fd2 = Qd2 * f2
Fd1 = Qd1 * f1
Pd_total = Fd2 + Fd1 + fc_float # 总需求推力

# 4.3 附着力极限校核 (最大不打滑牵引力)
P_max2 = Qd2 * phi2  # 前轴最大牵引力
P_max1 = Qd1 * phi1  # 后轴最大牵引力

# 4.4 最优扭矩分配算法 (手册推导：Pd1/Pd2 ≈ Qd1*φ1 / Qd2*φ2)
ratio_rear = (Qd1 * phi1) / ((Qd1 * phi1) + (Qd2 * phi2))
ratio_front = 1.0 - ratio_rear

Pd1_req = Pd_total * ratio_rear  # 后轴分配的目标推力
Pd2_req = Pd_total * ratio_front # 前轴分配的目标推力

# 4.5 电机参数计算 (单轮)
r1, r2 = d_rear / 2.0, d_front / 2.0
T_motor_rear = (Pd1_req / 2.0) * r1 / (i_drive * eff_drive)
T_motor_front = (Pd2_req / 2.0) * r2 / (i_drive * eff_drive)

rpm_motor_rear = (v_target_ms * 60 / (np.pi * d_rear)) * i_drive
rpm_motor_front = (v_target_ms * 60 / (np.pi * d_front)) * i_drive

P_kw_rear = (T_motor_rear * rpm_motor_rear) / 9550
P_kw_front = (T_motor_front * rpm_motor_front) / 9550

# 状态判定
slip_front_status = "打滑警告!" if Pd2_req > P_max2 else "附着正常"
slip_rear_status = "打滑警告!" if Pd1_req > P_max1 else "附着正常"
badge_f = "status-badge-err" if Pd2_req > P_max2 else "status-badge-ok"
badge_r = "status-badge-err" if Pd1_req > P_max1 else "status-badge-ok"

# ================= 5. 右侧：设计校核与视图区 =================
with col_analysis:
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📈 动力学状态图纸与轴荷监控</div>', unsafe_allow_html=True)
    
    # 5.1 紧凑图纸
    plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei', 'SimHei', 'Microsoft YaHei']
    plt.rcParams['axes.unicode_minus'] = False
    fig, ax = plt.subplots(figsize=(6.0, 1.15), dpi=120)
    
    ax.add_patch(plt.Circle((0, r1), r1, facecolor='#e1f5fe', edgecolor='#1f77b4', lw=1.5))
    ax.add_patch(plt.Circle((wheelbase, r2), r2, facecolor='#e8f5e9', edgecolor='#2ca02c', lw=1.5))
    ax.add_patch(plt.Circle((0, r1), 0.02, color='#334155'))
    ax.add_patch(plt.Circle((wheelbase, r2), 0.02, color='#334155'))
    
    # 车架与浮船示意线
    ax.plot([0, wheelbase], [r1, r2], color='#64748b', lw=3.0, solid_capstyle='round')
    ax.plot([-0.2, wheelbase+0.2], [-0.02, -0.02], color='#94a3b8', lw=2.0, ls='-.') # 浮船线
    
    # 重心
    ax.plot(cg_x, r1 + cg_height, marker='o', color='#ef4444', ms=6)
    ax.plot([cg_x, cg_x], [r1 + cg_height, 0], color='#ef4444', ls=':', lw=0.8)
    
    ax.axhline(0, color='#1e293b', lw=1.2)
    
    # 标注轴荷
    ax.text(0, r1 + 0.1, f"后轴荷 Qd1: {int(Qd1)}N", color='#1f77b4', ha='center', fontsize=7.5, weight='bold')
    ax.text(wheelbase, r2 + 0.1, f"前轴荷 Qd2: {int(Qd2)}N", color='#2ca02c', ha='center', fontsize=7.5, weight='bold')
    
    ax.set_aspect('equal')
    ax.set_xlim(-0.4, wheelbase + 0.4)
    ax.set_ylim(-0.15, max(r1, r2) + cg_height + 0.15)
    ax.axis('off')
    plt.tight_layout()
    
    _, plot_col, _ = st.columns([1, 8, 1])
    with plot_col:
        st.pyplot(fig, use_container_width=False)
    st.markdown('</div>', unsafe_allow_html=True)

    # 5.2 综合校核报告表
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">✅ 附着力校核与最优驱动匹配表</div>', unsafe_allow_html=True)
    
    table_html = f"""
    <table class="styled-table">
        <thead>
            <tr>
                <th style="width: 15%;">车轴位置</th>
                <th style="width: 17%;">设计目标推力 (N)</th>
                <th style="width: 17%;">极限附着力 (N)</th>
                <th style="width: 15%;">打滑校核状态</th>
                <th style="width: 18%;">单电机功率要求</th>
                <th style="width: 18%;">最优指令转速</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td style="color:#2ca02c; font-weight:600;">前轴 (含2电机)</td>
                <td>{Pd2_req:.0f} N <span style="font-size:0.7rem; color:#64748b;">({ratio_front*100:.1f}%)</span></td>
                <td>{P_max2:.0f} N</td>
                <td><span class="{badge_f}">{slip_front_status}</span></td>
                <td style="font-weight:600;">{P_kw_front*1000:.1f} W</td>
                <td>{int(rpm_motor_front)} RPM</td>
            </tr>
            <tr>
                <td style="color:#1f77b4; font-weight:600;">后轴 (含2电机)</td>
                <td>{Pd1_req:.0f} N <span style="font-size:0.7rem; color:#64748b;">({ratio_rear*100:.1f}%)</span></td>
                <td>{P_max1:.0f} N</td>
                <td><span class="{badge_r}">{slip_rear_status}</span></td>
                <td style="font-weight:600;">{P_kw_rear*1000:.1f} W</td>
                <td>{int(rpm_motor_rear)} RPM</td>
            </tr>
        </tbody>
    </table>
    """
    st.markdown(table_html, unsafe_allow_html=True)
    
    # 底部工程提示
    st.markdown(f"""
    <div style='margin-top: 8px; font-size:0.8rem; color:#475569; background-color:#f1f5f9; padding:6px 10px; border-radius:6px;'>
        <b>💡 设计师 / VCU电控师 指导意见：</b><br>
        1. <b>总推力需求</b>：克服滚阻与浮船阻力共计 <code>{Pd_total:.0f} N</code>。全车总机械输出功率需满足 <code>{(P_kw_front*2 + P_kw_rear*2)*1000:.1f} W</code>。<br>
        2. <b>防滑移与扭矩控制</b>：按照手册推导的最优附着比，VCU 应对后轮下发 <code>{ratio_rear*100:.1f}%</code> 的扭矩指令，前轮 <code>{ratio_front*100:.1f}%</code>。若前轮扭矩超限，将引发打滑。<br>
        3. <b>电子差速超前率 (Slip-ratio Matching)</b>：电控目标速度闭环中，后轮外缘线速度建议比前轮高 3%~6%（参考手册P514），以消除寄生功率。
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
