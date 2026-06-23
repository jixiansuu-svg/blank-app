import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# ================= 1. 页面配置与超紧凑 UI 样式注入 =================
st.set_page_config(page_title="电动农机底盘仿真仪表盘", layout="wide")

# 注入高档紧凑样式，彻底清除滚动条，隐藏 Streamlit 顶底白边
st.markdown("""
    <style>
        /* 隐藏 Streamlit 顶部 Header、底部 Footer 和菜单 */
        header {visibility: hidden; height: 0px !important;}
        footer {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        
        /* 紧凑页面整体边距 */
        .block-container {padding-top: 1.5rem !important; padding-bottom: 0.5rem !important; padding-left: 1.5rem; padding-right: 1.5rem;}
        
        /* 配置区卡片容器 */
        .config-card {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 10px 12px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.03);
        }
        
        /* 总览数据卡片 */
        .overview-container { display: flex; gap: 10px; margin-bottom: 5px; }
        .overview-card {
            flex: 1;
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 6px 10px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.02);
        }
        .overview-label { font-size: 0.78rem; color: #64748b; font-weight: 500; margin-bottom: 1px; }
        .overview-val { font-size: 1.3rem; font-weight: 700; color: #0f172a; }
        
        /* 高档数据表格样式 (超压缩) */
        .styled-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 2px;
            font-size: 0.8rem;
            text-align: left;
            border-radius: 6px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.01);
        }
        .styled-table th {
            background-color: #f1f5f9;
            color: #334155;
            font-weight: 600;
            padding: 4px 6px; /* 极致内边距 */
            border-bottom: 1.5px solid #cbd5e1;
        }
        .styled-table td {
            padding: 4px 6px;
            border-bottom: 1px solid #e2e8f0;
            color: #475569;
        }
        .styled-table tr:last-child td { border-bottom: none; }
        
        /* 压缩输入框、选择框与标题间距，杜绝滚动 */
        .stNumberInput {margin-bottom: -1.2rem !important; margin-top: -5px !important;} 
        .stSelectbox {margin-bottom: -1.2rem !important; margin-top: -5px !important;}
        label {font-size: 0.75rem !important; margin-bottom: 1px !important; color: #475569 !important;}
    </style>
""", unsafe_allow_html=True)

# 重新设计无遮挡标题
st.markdown("<h2 style='text-align: center; margin-top: -35px; margin-bottom: 8px; font-size: 1.7rem; color: #0f172a;'>🚜 四轮分布式电驱底盘 仿真设计中控台</h2>", unsafe_allow_html=True)

# ================= 2. 左右大布局分配 (38% 配置区 : 62% 仿真图纸与结果) =================
main_left, main_right = st.columns([38, 62])

# ================= 3. 左侧：配置区 =================
with main_left:
    st.markdown("<h4 style='margin-top:0px; margin-bottom:4px; font-size:1.1rem; color:#334155;'>🛠️ 参数配置区</h4>", unsafe_allow_html=True)
    
    st.markdown('<div class="config-card">', unsafe_allow_html=True)
    in_col1, in_col2 = st.columns(2)
    
    with in_col1:
        st.markdown("<span style='font-size:0.85rem; font-weight:bold; color:#0f172a;'>🚗 1. 车辆与工况</span>", unsafe_allow_html=True)
        weight = st.number_input("整机重量 (kg)", min_value=100.0, max_value=5000.0, value=900.0, step=10.0)
        v_target_ms = st.number_input("车辆速度 (m/s)", min_value=0.1, max_value=15.0, value=0.95, step=0.05)
        slope_deg = st.number_input("爬坡角度 (°)", min_value=0.0, max_value=60.0, value=0.0, step=1.0)
        safety_factor = st.number_input("动力安全系数", min_value=1.0, max_value=3.0, value=1.0, step=0.1)
        
        dist_mode = st.selectbox("轴荷分配模式", ["💡 物理动态计算", "✍️ 手动指定比"])
        if dist_mode == "✍️ 手动指定比":
            manual_k_rear_percent = st.number_input("后轴占比 (%)", min_value=0.0, max_value=100.0, value=64.5, step=0.5)
            k_rear = manual_k_rear_percent / 100.0
            k_front = 1.0 - k_rear
        else:
            k_rear, k_front = 0.5, 0.5 
            
        st.markdown("<div style='margin-top:12px;'><span style='font-size:0.85rem; font-weight:bold; color:#0f172a;'>📐 2. 几何尺寸 (mm)</span></div>", unsafe_allow_html=True)
        wheelbase = st.number_input("轴距 (前后轴)", min_value=500, max_value=3000, value=1220, step=10) / 1000.0
        cg_height = st.number_input("重心高度", min_value=100, max_value=2000, value=400, step=10) / 1000.0
        cg_x = st.number_input("重心距后轴 (50:50为610)", min_value=100, max_value=2000, value=610, step=10) / 1000.0

    with in_col2:
        st.markdown("<span style='font-size:0.85rem; font-weight:bold; color:#0f172a;'>⚙️ 3. 传动与效率</span>", unsafe_allow_html=True)
        i_drive = st.number_input("行走轮边减速比", min_value=1.0, max_value=300.0, value=40.7, step=0.1)
        eff_drive = st.number_input("行走传动效率 (%)", min_value=10.0, max_value=100.0, value=85.0, step=1.0) / 100.0
        mu_roll = st.number_input("泥地滚动阻力系数", min_value=0.05, max_value=0.80, value=0.44, step=0.01)
        
        st.markdown("<div style='margin-top:12px;'><span style='font-size:0.85rem; font-weight:bold; color:#0f172a;'>🔄 4. 转向与系统</span></div>", unsafe_allow_html=True)
        i_steer = st.number_input("转向机构总减速比", min_value=1.0, max_value=300.0, value=125.0, step=1.0)
        eff_steer = st.number_input("转向传动效率 (%)", min_value=10.0, max_value=100.0, value=80.0, step=1.0) / 100.0
        mu_steer = st.number_input("转向摩擦系数", min_value=0.1, max_value=1.5, value=0.70, step=0.05)
        rpm_kingpin = st.number_input("转向主销转速 (RPM)", min_value=0.5, max_value=30.0, value=5.0, step=0.5)
        
        d_front = st.number_input("前轮直径 (mm)", min_value=200, max_value=2000, value=650, step=10) / 1000.0
        d_rear = st.number_input("后轮直径 (mm)", min_value=200, max_value=2000, value=850, step=10) / 1000.0
        tire_width = st.number_input("前轮轮胎宽度 (mm)", min_value=50, max_value=500, value=150, step=10) / 1000.0
        kingpin_offset = st.number_input("主销偏置距 (mm)", min_value=0, max_value=200, value=30, step=5) / 1000.0

    st.markdown('</div>', unsafe_allow_html=True)

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

# 前后驱动电机参数
t_wheel_front = f_per_front_wheel * r_front * safety_factor
t_motor_front = t_wheel_front / (i_drive * eff_drive)
rpm_wheel_front = (v_target_ms * 60) / (np.pi * d_front)
rpm_motor_front = rpm_wheel_front * i_drive
p_motor_front = (t_motor_front * rpm_motor_front) / 9550

t_wheel_rear = f_per_rear_wheel * r_rear * safety_factor
t_motor_rear = t_wheel_rear / (i_drive * eff_drive)
rpm_wheel_rear = (v_target_ms * 60) / (np.pi * d_rear)
rpm_motor_rear = rpm_wheel_rear * i_drive
p_motor_rear = (t_motor_rear * rpm_motor_rear) / 9550

# 转向单电机 (共两台)
f_z_single_front = dyn_load_front / 2.0
t_steer_kingpin_single = mu_steer * f_z_single_front * np.sqrt((tire_width**2 / 8) + kingpin_offset**2) if f_z_single_front > 0 else 0
t_steer_design_single = t_steer_kingpin_single * safety_factor
t_motor_steer_single = t_steer_design_single / (i_steer * eff_steer)
rpm_motor_steer = rpm_kingpin * i_steer
p_motor_steer_single = (t_motor_steer_single * rpm_motor_steer) / 9550

# 汇总总功率 (W)
total_p_drive = ((p_motor_front * 2) + (p_motor_rear * 2)) * 1000
total_p_steer = (p_motor_steer_single * 2) * 1000

# ================= 5. 右侧：总览 + 示意图 (大幅度缩小) + 细分区 (完全浮出) =================
with main_right:
    st.markdown("<h4 style='margin-top:0px; margin-bottom:4px; font-size:1.1rem; color:#334155;'>📊 仿真结果与动态图纸</h4>", unsafe_allow_html=True)
    
    # 5.1 总览
    st.markdown(f"""
        <div class="overview-container">
            <div class="overview-card" style="border-left: 3px solid #1f77b4;">
                <div class="overview-label">行走电机总功率</div>
                <div class="overview-val">{total_p_drive:.1f} W</div>
            </div>
            <div class="overview-card" style="border-left: 3px solid #ff7f0e;">
                <div class="overview-label">转向电机总功率</div>
                <div class="overview-val">{total_p_steer:.1f} W</div>
            </div>
            <div class="overview-card" style="border-left: 3px solid #2ca02c;">
                <div class="overview-label">动态轴荷比 (前 : 后)</div>
                <div class="overview-val">{k_front*100:.1f}% : {k_rear*100:.1f}%</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 5.2 示意图：彻底缩小 50% 物理大小 (画布调为超扁平 3.0 × 0.8，DPI微调)
    plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei', 'SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 画布极度压缩：3.0英寸长，0.85英寸高 (极速扁平，杜绝纵向占地)
    fig, ax = plt.subplots(figsize=(3.0, 0.85), dpi=130) 
    
    # 实体车轮：线宽降至 1.0 (极致精简)
    rear_wheel = plt.Circle((0, r_rear), r_rear, facecolor='#e1f5fe', edgecolor='#1f77b4', lw=1.0)
    front_wheel = plt.Circle((wheelbase, r_front), r_front, facecolor='#e8f5e9', edgecolor='#2ca02c', lw=1.0)
    ax.add_patch(rear_wheel)
    ax.add_patch(front_wheel)
    
    # 微型轴心孔
    ax.add_patch(plt.Circle((0, r_rear), 0.015, color='#334155'))
    ax.add_patch(plt.Circle((wheelbase, r_front), 0.015, color='#334155'))
    
    # 精简底盘车架 (线宽降至 2.2)
    ax.plot([0, wheelbase], [r_rear, r_front], color='#64748b', lw=2.2, solid_capstyle='round')
    
    # 微型红重心 (ms 降至 5)
    ax.plot(cg_x, r_rear + cg_height, marker='o', color='#ef4444', ms=5)
    ax.plot([cg_x, cg_x], [r_rear + cg_height, 0], color='#ef4444', ls=':', lw=0.6)
    
    # 纤细地平线 (线宽降至 1.0)
    ax.axhline(0, color='#334155', lw=1.0)
    
    # 精密微型标注卡片 (字号降至 5.8，内边距 pad 降至 0.18，绝不与地平线冲突)
    ax.text(0, r_rear + 0.10, f"后轴: {int(dyn_load_rear)}N", color='#1f77b4', ha='center', fontsize=5.8, weight='bold',
            bbox=dict(boxstyle="round,pad=0.18", fc="#f0f9ff", ec="#1f77b4", lw=0.5))
    ax.text(wheelbase, r_front + 0.10, f"前轴: {int(dyn_load_front)}N", color='#2ca02c', ha='center', fontsize=5.8, weight='bold',
            bbox=dict(boxstyle="round,pad=0.18", fc="#f0fdf4", ec="#2ca02c", lw=0.5))
    
    ax.set_aspect('equal')
    ax.set_xlim(-0.4, wheelbase + 0.4)
    ax.set_ylim(-0.15, max(r_rear, r_front) + cg_height + 0.18)
    ax.axis('off')
    plt.tight_layout()
    
    # 🌟 关键：使用 columns 将缩小后的图纸在中央限制宽度陈列，阻止横向和纵向的强制拉伸
    _, plot_center_col, _ = st.columns([1.5, 7.0, 1.5])
    with plot_center_col:
        st.pyplot(fig, use_container_width=False) # 彻底关闭容器拉伸，保全 50% 缩小的黄金比例！

    # 5.3 细分区：高档工业表格 (由于上图缩减了一半高度，表格现已完美浮出，完全不被遮挡)
    st.markdown("<h4 style='margin-top:2px; margin-bottom:1px; font-size:0.95rem; color:#334155;'>🔍 独立电机细分规格明细</h4>", unsafe_allow_html=True)
    
    table_html = f"""
    <table class="styled-table">
        <thead>
            <tr>
                <th style="width: 32%;">电机位置与型号</th>
                <th style="width: 20%;">工作用途</th>
                <th style="width: 16%;">单台功率 (W)</th>
                <th style="width: 16%;">单台扭矩 (N·m)</th>
                <th style="width: 16%;">转速 (RPM)</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td style="color:#2ca02c; font-weight:600;">M1 (左前驱动) / M2 (右前驱动)</td>
                <td>行走轮边驱动</td>
                <td style="font-weight:600; color:#2ca02c;">{p_motor_front*1000:.1f} W</td>
                <td>{t_motor_front:.1f} N·m</td>
                <td>{int(rpm_motor_front)} RPM</td>
            </tr>
            <tr>
                <td style="color:#1f77b4; font-weight:600;">M3 (左后驱动) / M4 (右后驱动)</td>
                <td>行走轮边驱动</td>
                <td style="font-weight:600; color:#1f77b4;">{p_motor_rear*1000:.1f} W</td>
                <td>{t_motor_rear:.1f} N·m</td>
                <td>{int(rpm_motor_rear)} RPM</td>
            </tr>
            <tr>
                <td style="color:#ff7f0e; font-weight:600;">左转向电机 / 右转向电机 (共2台)</td>
                <td>独立线控转向</td>
                <td style="font-weight:600; color:#ff7f0e;">{p_motor_steer_single*1000:.1f} W</td>
                <td>{t_motor_steer_single:.2f} N·m</td>
                <td>{int(rpm_motor_steer)} RPM</td>
            </tr>
        </tbody>
    </table>
    """
    st.markdown(table_html, unsafe_allow_html=True)
    
    # 底部系统级参数 (最紧凑一格)
    st.markdown("<div style='margin-top: 3px; font-size:0.78rem; color:#475569;'>📦 <b>整车克服总推力需求</b>: <code style='font-size:0.75rem;'>"+str(int(f_total))+" N</code>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;🚀 <b>底盘设定仿真速度</b>: <code style='font-size:0.75rem;'>"+f"{v_target_ms:.2f} m/s"+"</code></div>", unsafe_allow_html=True)
