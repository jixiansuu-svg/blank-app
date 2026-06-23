import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# ================= 1. 页面配置与高档 UI 样式注入 =================
st.set_page_config(page_title="电动农机底盘仿真仪表盘", layout="wide")

# 注入高档工业风 CSS
st.markdown("""
    <style>
        /* 紧凑页面边距 */
        .block-container {padding-top: 1rem; padding-bottom: 1rem; padding-left: 2rem; padding-right: 2rem;}
        h1 {margin-top: -1.2rem; margin-bottom: 0.8rem; font-size: 2.2rem !important; color: #1e293b; font-weight: 700; text-align: center;}
        h3 {margin-top: 0rem; margin-bottom: 0.4rem; font-size: 1.3rem !important; color: #0f172a; font-weight: 600;}
        
        /* 配置区卡片容器 */
        .config-card {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 15px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        }
        
        /* 总览数据卡片 */
        .overview-container { display: flex; gap: 15px; margin-bottom: 10px; }
        .overview-card {
            flex: 1;
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 10px 15px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        }
        .overview-label { font-size: 0.85rem; color: #64748b; font-weight: 500; margin-bottom: 2px; }
        .overview-val { font-size: 1.5rem; font-weight: 700; color: #0f172a; }
        
        /* 高档数据表格样式 */
        .styled-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 5px;
            font-size: 0.88rem;
            text-align: left;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        }
        .styled-table th {
            background-color: #f1f5f9;
            color: #334155;
            font-weight: 600;
            padding: 10px 12px;
            border-bottom: 2px solid #cbd5e1;
        }
        .styled-table td {
            padding: 10px 12px;
            border-bottom: 1px solid #e2e8f0;
            color: #475569;
        }
        .styled-table tr:last-child td { border-bottom: none; }
        
        /* 压缩输入框间距 */
        .stNumberInput {margin-bottom: -0.6rem;} 
        .stSelectbox {margin-bottom: -0.6rem;}
    </style>
""", unsafe_allow_html=True)

st.title("🚜 四轮分布式电驱底盘 仿真设计中控台")

# ================= 2. 左右大布局分配 (40% 配置区 : 60% 仿真图纸与结果) =================
main_left, main_right = st.columns([40, 60])

# ================= 3. 左侧：配置区 (2列对齐平铺，美化紧凑) =================
with main_left:
    st.markdown("### 🛠️ 参数配置区")
    
    # 将输入框放入高档圆角背景卡片中
    st.markdown('<div class="config-card">', unsafe_allow_html=True)
    in_col1, in_col2 = st.columns(2)
    
    with in_col1:
        st.markdown("**🚗 1. 车辆与工况**")
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
            k_rear, k_front = 0.5, 0.5 # 占位
            
        st.markdown("<br>**📐 2. 几何尺寸 (mm)**", unsafe_allow_html=True)
        wheelbase = st.number_input("轴距 (前后轴)", min_value=500, max_value=3000, value=1220, step=10) / 1000.0
        cg_height = st.number_input("重心高度", min_value=100, max_value=2000, value=400, step=10) / 1000.0
        cg_x = st.number_input("重心距后轴 (50:50为610)", min_value=100, max_value=2000, value=610, step=10) / 1000.0

    with in_col2:
        st.markdown("**⚙️ 3. 传动与效率**")
        i_drive = st.number_input("行走轮边减速比", min_value=1.0, max_value=300.0, value=40.7, step=0.1)
        eff_drive = st.number_input("行走传动效率 (%)", min_value=10.0, max_value=100.0, value=85.0, step=1.0) / 100.0
        mu_roll = st.number_input("泥地阻力系数", min_value=0.05, max_value=0.80, value=0.44, step=0.01)
        
        st.markdown("<br>**🔄 4. 转向与系统**", unsafe_allow_html=True)
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

# 转向单电机 (共两台，单侧独立驱动)
f_z_single_front = dyn_load_front / 2.0
t_steer_kingpin_single = mu_steer * f_z_single_front * np.sqrt((tire_width**2 / 8) + kingpin_offset**2) if f_z_single_front > 0 else 0
t_steer_design_single = t_steer_kingpin_single * safety_factor
t_motor_steer_single = t_steer_design_single / (i_steer * eff_steer)
rpm_motor_steer = rpm_kingpin * i_steer
p_motor_steer_single = (t_motor_steer_single * rpm_motor_steer) / 9550

# 汇总总功率 (W)
total_p_drive = ((p_motor_front * 2) + (p_motor_rear * 2)) * 1000
total_p_steer = (p_motor_steer_single * 2) * 1000

# ================= 5. 右侧：总览 + 示意图 + 细分区 (极其美化、高度对称) =================
with main_right:
    st.markdown("### 📊 仿真结果与动态图纸")
    
    # 5.1 总览：精美 HTML 扁平数据卡片
    st.markdown(f"""
        <div class="overview-container">
            <div class="overview-card" style="border-left: 4px solid #1f77b4;">
                <div class="overview-label">行走电机总功率</div>
                <div class="overview-val">{total_p_drive:.1f} W</div>
            </div>
            <div class="overview-card" style="border-left: 4px solid #ff7f0e;">
                <div class="overview-label">转向电机总功率</div>
                <div class="overview-val">{total_p_steer:.1f} W</div>
            </div>
            <div class="overview-card" style="border-left: 4px solid #2ca02c;">
                <div class="overview-label">动态轴荷比 (前 : 后)</div>
                <div class="overview-val">{k_front*100:.1f}% : {k_rear*100:.1f}%</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 5.2 示意图：CAD级别精美 Matplotlib 绘图
    plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei', 'SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
    
    fig, ax = plt.subplots(figsize=(6, 2.0)) # 高度合理，居中
    
    # 绘制带 15% 透明度填充的实体轮胎 (高档感)
    rear_wheel = plt.Circle((0, r_rear), r_rear, facecolor='#e1f5fe', edgecolor='#1f77b4', lw=2.5)
    front_wheel = plt.Circle((wheelbase, r_front), r_front, facecolor='#e8f5e9', edgecolor='#2ca02c', lw=2.5)
    ax.add_patch(rear_wheel)
    ax.add_patch(front_wheel)
    
    # 绘制深灰色车轴中心孔
    ax.add_patch(plt.Circle((0, r_rear), 0.03, color='#334155'))
    ax.add_patch(plt.Circle((wheelbase, r_front), 0.03, color='#334155'))
    
    # 绘制实体底盘车架（由原先的虚线升级为粗实体灰钢架，极具CAD感）
    ax.plot([0, wheelbase], [r_rear, r_front], color='#64748b', lw=5.5, solid_capstyle='round')
    
    # 绘制重心 (CG) 红色指示点
    ax.plot(cg_x, r_rear + cg_height, marker='o', color='#ef4444', ms=12)
    ax.plot([cg_x, cg_x], [r_rear + cg_height, 0], color='#ef4444', ls=':', lw=1.5)
    
    # 绘制坚实的地平线 (完美支撑车轮)
    ax.axhline(0, color='#334155', lw=2.5)
    
    # 标注轴压文字（带圆角底色卡片包裹，完美防重叠，完美浮动在车轮上方空隙）
    ax.text(0, r_rear + 0.16, f"后轴: {int(dyn_load_rear)}N", color='#1f77b4', ha='center', fontsize=9.5, weight='bold',
            bbox=dict(boxstyle="round,pad=0.3", fc="#f0f9ff", ec="#1f77b4", lw=1))
    ax.text(wheelbase, r_front + 0.16, f"前轴: {int(dyn_load_front)}N", color='#2ca02c', ha='center', fontsize=9.5, weight='bold',
            bbox=dict(boxstyle="round,pad=0.3", fc="#f0fdf4", ec="#2ca02c", lw=1))
    
    ax.set_aspect('equal')
    ax.set_xlim(-0.5, wheelbase + 0.6)
    ax.set_ylim(-0.22, max(r_rear, r_front) + cg_height + 0.3)
    ax.axis('off')
    plt.tight_layout()
    st.pyplot(fig)

    # 5.3 细分区：高档工业表格，完美对齐
    st.markdown("### 🔍 独立电机细分规格明细")
    
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
                <td style="font-weight:600;">{p_motor_front*1000:.1f} W</td>
                <td>{t_motor_front:.1f} N·m</td>
                <td>{int(rpm_motor_front)} RPM</td>
            </tr>
            <tr>
                <td style="color:#1f77b4; font-weight:600;">M3 (左后驱动) / M4 (右后驱动)</td>
                <td>行走轮边驱动</td>
                <td style="font-weight:600;">{p_motor_rear*1000:.1f} W</td>
                <td>{t_motor_rear:.1f} N·m</td>
                <td>{int(rpm_motor_rear)} RPM</td>
            </tr>
            <tr>
                <td style="color:#ff7f0e; font-weight:600;">左转向电机 / 右转向电机 (共2台)</td>
                <td>独立线控转向</td>
                <td style="font-weight:600;">{p_motor_steer_single*1000:.1f} W</td>
                <td>{t_motor_steer_single:.2f} N·m</td>
                <td>{int(rpm_motor_steer)} RPM</td>
            </tr>
        </tbody>
    </table>
    """
    st.markdown(table_html, unsafe_allow_html=True)
    
    # 底部系统级参数，排列整齐
    st.markdown("<br>", unsafe_allow_html=True)
    sc1, sc2 = st.columns(2)
    with sc1:
        st.markdown(f"📦 **整车克服总推力需求**: `{int(f_total)} N`")
    with sc2:
        st.markdown(f"🚀 **底盘设定仿真速度**: `{v_target_ms:.2f} m/s`")
