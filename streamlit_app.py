import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# ================= 1. 页面配置与 CSS 样式注入 =================
st.set_page_config(page_title="4WID 农机底盘校核看板", layout="wide", page_icon="🚜")

st.markdown("""
    <style>
        header {visibility: hidden; height: 0px !important;}
        footer {visibility: hidden;}
        .block-container {padding-top: 1.0rem !important; padding-bottom: 0.2rem !important; padding-left: 1.5rem; padding-right: 1.5rem;}
        
        .panel-card {
            background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px;
            padding: 12px 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); margin-bottom: 12px;
        }
        .section-title { font-size: 1rem; font-weight: 700; color: #1e293b; border-bottom: 2px solid #3b82f6; padding-bottom: 6px; margin-bottom: 12px; }
        
        .status-badge-ok { background-color: #dcfce7; color: #166534; padding: 3px 8px; border-radius: 4px; font-weight: 600; font-size: 0.75rem;}
        .status-badge-err { background-color: #fee2e2; color: #991b1b; padding: 3px 8px; border-radius: 4px; font-weight: 600; font-size: 0.75rem;}
        
        .styled-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; text-align: left; }
        .styled-table th { background-color: #f8fafc; color: #475569; padding: 8px; border-bottom: 2px solid #cbd5e1; }
        .styled-table td { padding: 6px 8px; border-bottom: 1px solid #f1f5f9; color: #334155; }
        
        .stNumberInput {margin-bottom: -0.5rem !important; margin-top: -4px !important;}
        label {font-size: 0.75rem !important; color: #475569 !important;}
    </style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center; margin-top: -20px; margin-bottom: 15px; font-size: 1.6rem; color: #0f172a;'>🚜 4WID 高速插秧机底盘综合校核看板</h2>", unsafe_allow_html=True)


# ================= 2. 核心计算逻辑封装 (解耦) =================
def calculate_dynamics(p: dict) -> dict:
    """底盘动力学与电机需求计算引擎"""
    res = {}
    g = 9.81
    G_N = p['weight'] * g

    # 4.1 动态轴荷
    Q_front_static = G_N * p['cg_x'] / p['wheelbase']
    Q_rear_static = G_N - Q_front_static
    F_total_est = (Q_front_static * p['f2']) + (Q_rear_static * p['f1']) + p['fc_float']
    delta_Q = F_total_est * (p['cg_height'] / p['wheelbase'])

    res['Qd2'] = max(0.0, Q_front_static - delta_Q)  # 前轴动态载荷
    res['Qd1'] = G_N - res['Qd2']                    # 后轴动态载荷
    
    # 翘头警告
    res['is_wheelie'] = res['Qd2'] == 0

    # 4.2 阻力与附着力极限
    Pd_total = (res['Qd2'] * p['f2']) + (res['Qd1'] * p['f1']) + p['fc_float']
    res['P_max2'] = res['Qd2'] * p['phi2']
    res['P_max1'] = res['Qd1'] * p['phi1']

    # 4.3 最优扭矩分配
    sum_phi = (res['Qd1'] * p['phi1']) + (res['Qd2'] * p['phi2'])
    ratio_rear = (res['Qd1'] * p['phi1']) / sum_phi if sum_phi > 0 else 0.5
    ratio_front = 1.0 - ratio_rear

    res['Pd1_req'] = Pd_total * ratio_rear
    res['Pd2_req'] = Pd_total * ratio_front

    # 行走电机参数计算 (单轮)
    r1, r2 = p['d_rear'] / 2.0, p['d_front'] / 2.0
    res['T_rear'] = (res['Pd1_req'] / 2.0) * r1 * p['sf'] / (p['i_drive'] * p['eff_drive'])
    res['T_front'] = (res['Pd2_req'] / 2.0) * r2 * p['sf'] / (p['i_drive'] * p['eff_drive'])
    
    res['rpm_rear'] = (p['v_target'] * 60 / (np.pi * p['d_rear'])) * p['i_drive']
    res['rpm_front'] = (p['v_target'] * 60 / (np.pi * p['d_front'])) * p['i_drive']
    
    res['P_kw_rear'] = (res['T_rear'] * res['rpm_rear']) / 9550
    res['P_kw_front'] = (res['T_front'] * res['rpm_front']) / 9550

    # 4.4 转向电机参数计算 (单侧)
    f_z_single_front = res['Qd2'] / 2.0
    t_kingpin = p['mu_steer'] * f_z_single_front * np.sqrt((p['tire_width']**2 / 8) + p['kp_offset']**2) if f_z_single_front > 0 else 0
    res['t_steer_design'] = t_kingpin * p['sf']
    res['t_motor_steer'] = res['t_steer_design'] / (p['i_steer'] * p['eff_steer'])
    res['rpm_steer'] = p['rpm_kingpin'] * p['i_steer']
    res['P_kw_steer'] = (res['t_motor_steer'] * res['rpm_steer']) / 9550
    
    return res


# ================= 3. 图纸渲染封装 =================
def draw_chassis_diagram(p: dict, res: dict):
    """绘制底盘动态受力简图"""
    plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei', 'SimHei', 'Microsoft YaHei', 'Arial']
    plt.rcParams['axes.unicode_minus'] = False
    
    fig, ax = plt.subplots(figsize=(7.0, 1.5), dpi=150)
    r1, r2 = p['d_rear']/2, p['d_front']/2
    wb, cg_x, cg_h = p['wheelbase'], p['cg_x'], p['cg_height']
    
    # 绘制车轮与底盘
    ax.add_patch(plt.Circle((0, r1), r1, facecolor='#e0f2fe', edgecolor='#0284c7', lw=1.5, alpha=0.9))
    ax.add_patch(plt.Circle((wb, r2), r2, facecolor='#dcfce7', edgecolor='#16a34a', lw=1.5, alpha=0.9))
    ax.plot([0, wb], [r1, r2], color='#475569', lw=4.0, solid_capstyle='round')
    
    # 绘制地面 (带一点阴影效果)
    ax.plot([-r1-0.2, wb+r2+0.2], [0, 0], color='#1e293b', lw=1.5)
    ax.fill_between([-r1-0.2, wb+r2+0.2], -0.05, 0, color='#94a3b8', alpha=0.2)
    
    # 质心标志
    cg_y = r1 + cg_h
    ax.plot(cg_x, cg_y, marker='o', color='#ef4444', ms=8, zorder=5)
    ax.plot(cg_x, cg_y, marker='+', color='white', ms=6, zorder=6)
    ax.plot([cg_x, cg_x], [cg_y, 0], color='#ef4444', ls='--', lw=1)
    
    # 注释
    ax.text(0, r1 + r1 + 0.05, f"后轴 Qd1\n{int(res['Qd1'])} N", color='#0284c7', ha='center', fontsize=8, weight='bold')
    ax.text(wb, r2 + r2 + 0.05, f"前轴 Qd2\n{int(res['Qd2'])} N", color='#16a34a', ha='center', fontsize=8, weight='bold')
    if res['is_wheelie']:
        ax.text(wb/2, cg_y, "⚠️ 警告：前轮已离地！", color='red', ha='center', weight='bold')

    ax.set_aspect('equal')
    ax.axis('off')
    plt.tight_layout()
    return fig


# ================= 4. 前端布局与交互 =================
col_params, col_analysis = st.columns([32, 68], gap="medium")

with col_params:
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🛠️ 1. 整机与环境参数</div>', unsafe_allow_html=True)
    
    # 使用字典收集参数
    params = {}
    p1, p2 = st.columns(2)
    with p1:
        params['weight'] = st.number_input("整机质量 G (kg)", value=900.0, step=10.0)
        params['v_target'] = st.number_input("设计速度 v (m/s)", value=0.95, step=0.05)
        params['cg_x'] = st.number_input("重心距后轴 Lg (mm)", value=427, step=10) / 1000.0
        params['cg_height'] = st.number_input("重心高度 Hg (mm)", value=400, step=10) / 1000.0
        params['fc_float'] = st.number_input("浮船阻力 Fc (N)", value=600.0, step=50.0)
        params['sf'] = st.number_input("安全系数 S", min_value=1.0, value=1.0, step=0.1)
    with p2:
        params['wheelbase'] = st.number_input("轴距 L (mm)", value=1220, step=10) / 1000.0
        params['d_front'] = st.number_input("前轮径 D2 (mm)", value=650, step=10) / 1000.0
        params['d_rear'] = st.number_input("后轮径 D1 (mm)", value=850, step=10) / 1000.0
        params['i_drive'] = st.number_input("行走减速比 i", value=40.7, step=0.1)
        params['eff_drive'] = st.number_input("行走效率 η (%)", value=85.0) / 100.0
        
    st.markdown("<div style='margin-top:10px; margin-bottom:5px; font-size:0.85rem; font-weight:bold; color:#1e293b;'>🌍 2. 地面系数 (水田工况)</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        params['f2'] = st.number_input("前轮滚阻系数 f2", value=0.28, step=0.01)
        params['phi2'] = st.number_input("前轮附着系数 φ2", value=0.65, step=0.01)
    with c2:
        params['f1'] = st.number_input("后轮滚阻系数 f1", value=0.35, step=0.01)
        params['phi1'] = st.number_input("后轮附着系数 φ1", value=0.80, step=0.01)
        
    st.markdown("<div style='margin-top:10px; margin-bottom:5px; font-size:0.85rem; font-weight:bold; color:#1e293b;'>🔄 3. 独立线控转向 (EPS)</div>", unsafe_allow_html=True)
    s1, s2 = st.columns(2)
    with s1:
        params['tire_width'] = st.number_input("轮胎宽度 B (mm)", value=150, step=10) / 1000.0
        params['kp_offset'] = st.number_input("主销偏置 e (mm)", value=30, step=5) / 1000.0
        params['mu_steer'] = st.number_input("原地转向摩擦 μ", value=0.70, step=0.05)
    with s2:
        params['i_steer'] = st.number_input("转向减速比", value=125.0, step=1.0)
        params['eff_steer'] = st.number_input("转向效率 (%)", value=80.0) / 100.0
        params['rpm_kingpin'] = st.number_input("主销目标转速 (RPM)", value=5.0, step=0.5)
        
    st.markdown('</div>', unsafe_allow_html=True)

# 触发计算
res = calculate_dynamics(params)

# 状态判定
slip_f_msg, badge_f = ("打滑警告!", "status-badge-err") if res['Pd2_req'] > res['P_max2'] else ("附着正常", "status-badge-ok")
slip_r_msg, badge_r = ("打滑警告!", "status-badge-err") if res['Pd1_req'] > res['P_max1'] else ("附着正常", "status-badge-ok")


with col_analysis:
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📈 动力学状态图纸与轴荷监控</div>', unsafe_allow_html=True)
    
    # 渲染图纸
    fig = draw_chassis_diagram(params, res)
    st.pyplot(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 新增：KPI 指标行
    total_drive_power = (res['P_kw_front'] * 2 + res['P_kw_rear'] * 2) * 1000
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("全车驱动总功率", f"{total_drive_power:.0f} W")
    m2.metric("整车总推力需求", f"{res['Pd1_req'] + res['Pd2_req']:.0f} N")
    m3.metric("后轴附着利用率", f"{(res['Pd1_req']/res['P_max1'])*100:.1f} %" if res['P_max1']>0 else "N/A")
    m4.metric("前轴附着利用率", f"{(res['Pd2_req']/res['P_max2'])*100:.1f} %" if res['P_max2']>0 else "N/A")

    # 综合校核报告表
    st.markdown('<div class="panel-card" style="margin-top: 10px;">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">✅ 电机输出规格选型明细 (单台参数)</div>', unsafe_allow_html=True)
    
    table_html = f"""
    <table class="styled-table">
        <thead>
            <tr>
                <th>电机类别与位置</th>
                <th>需求推力/阻力</th>
                <th>打滑校核</th>
                <th>额定功率 (W)</th>
                <th>轮端/主销需求扭矩</th>
                <th>电机输出扭矩</th>
                <th>电机目标转速</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td style="color:#16a34a; font-weight:600;">前轮驱动 (M1/M2)</td>
                <td>{res['Pd2_req']/2:.0f} N</td>
                <td><span class="{badge_f}">{slip_f_msg}</span></td>
                <td style="font-weight:600;">{res['P_kw_front']*1000:.1f} W</td>
                <td>{(res['Pd2_req']/2)*(params['d_front']/2):.1f} N·m</td>
                <td>{res['T_front']:.1f} N·m</td>
                <td>{int(res['rpm_front'])} RPM</td>
            </tr>
            <tr>
                <td style="color:#0284c7; font-weight:600;">后轮驱动 (M3/M4)</td>
                <td>{res['Pd1_req']/2:.0f} N</td>
                <td><span class="{badge_r}">{slip_r_msg}</span></td>
                <td style="font-weight:600;">{res['P_kw_rear']*1000:.1f} W</td>
                <td>{(res['Pd1_req']/2)*(params['d_rear']/2):.1f} N·m</td>
                <td>{res['T_rear']:.1f} N·m</td>
                <td>{int(res['rpm_rear'])} RPM</td>
            </tr>
            <tr style="background-color: #f8fafc;">
                <td style="color:#d97706; font-weight:600;">前轮转向 (共2台)</td>
                <td>-</td>
                <td><span style="color:#94a3b8;">N/A</span></td>
                <td style="font-weight:600;">{res['P_kw_steer']*1000:.1f} W</td>
                <td>{res['t_steer_design']:.1f} N·m</td>
                <td>{res['t_motor_steer']:.2f} N·m</td>
                <td>{int(res['rpm_steer'])} RPM</td>
            </tr>
        </tbody>
    </table>
    """
    st.markdown(table_html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ================= 5. 底部：核心理论计算公式库 =================
with st.expander("📚 团队研发参考：底盘核心理论计算公式库 (基于车辆地面力学)"):
    f_c1, f_c2 = st.columns(2)
    with f_c1:
        st.markdown("**1. 动态轴荷转移公式**")
        st.latex(r"Q_{d2} (前轴) = G \cdot \frac{L_g}{L} - \Delta Q")
        st.latex(r"Q_{d1} (后轴) = G - Q_{d2}")
        st.latex(r"\text{其中抬头力矩转移量：} \Delta Q = F_{total} \cdot \frac{H_g}{L}")
        
        st.markdown("**2. 水田总需求阻力**")
        st.latex(r"P_{d\_total} = (Q_{d2} \cdot f_2) + (Q_{d1} \cdot f_1) + F_c")
        
        st.markdown("**3. 电机选型功率计算**")
        st.latex(r"P (kW) = \frac{T \cdot n}{9550}")
    with f_c2:
        st.markdown("**4. 《手册》最优附着扭矩分配比例**")
        st.latex(r"\frac{P_{d1}}{P_{d2}} \approx \frac{Q_{d1} \cdot \varphi_1}{Q_{d2} \cdot \varphi_2}")
        st.caption("指导 VCU 开发：根据前后轮当前的垂直载荷和附着极限，实时按比例下发力矩上限指令，可保证整机牵引效率最高且不打滑。")
        
        st.markdown("**5. 原地转向阻力矩公式 (最恶劣工况)**")
        st.latex(r"M_{steer} = \mu_{s} \cdot \frac{Q_{d2}}{2} \cdot \sqrt{\frac{B^2}{8} + e^2}")
        st.caption("注：动态轴荷 $Q_{d2}$ 变轻时，转向扭矩需求会自动减小。")
