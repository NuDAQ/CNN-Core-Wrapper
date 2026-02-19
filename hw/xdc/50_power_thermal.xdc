# ===========================
# io_activity.xdc  (Vivado XDC)
# 目标：仅为顶层 I/O 指定合理的平均切换率
# 条件：CLK_PERIOD=10ns (100 MHz)，一次推理≈80us
# 推导：IN_DUTY≈0.128；OUT_DUTY≈1.25e-4
# ===========================

# 时钟请继续用原有时序约束（XDC 里的 create_clock），
# 不要用 set_switching_activity 给时钟设频率

# ---------- 端口名（按你的 DUT 顶层端口命名；可保持不动） ----------
# 输入侧

# 输出侧

# 控制/状态/复位

# ---------- 数值（已经替你算好，直接用） ----------
# fclk = 100 MHz
# IN_DUTY = 0.128  -> 输入数据比特切换率 ≈ 0.5 * fclk * IN_DUTY = 6.4e6 /s
# OUT_DUTY = 1.25e-4 -> 输出数据比特切换率 ≈ 6.25e3 /s
# 每次推理边沿数~2 -> 2 * 12_500 = 25_000 /s

# input_ready：你给出"5周期切一次" -> 100MHz/5 = 20 MHz

# output_ready：TB 中常为1（always ready）

# start/done/idle/ready：保守估计

# 复位：基本不动

# ---------- 应用到端口 ----------



# 复位

# 兜底：任何仍未被标注的 I/O 给一个温和值，避免 I/O Activity=Low

set_switching_activity -toggle_rate 13.500 -static_probability 0.500 [get_ports ready]
set_switching_activity -toggle_rate 13.500 -static_probability 0.500 [get_ports input_data]
set_switching_activity -toggle_rate 0.007 -static_probability 0.196 [get_ports output_data]
set_switching_activity -toggle_rate 100.000 -static_probability 0.500 [get_ports clk]
set_switching_activity -toggle_rate 0.032 -static_probability 0.001 [get_ports idle]
set_switching_activity -toggle_rate 13.500 -static_probability 0.500 [get_ports input_valid]
set_switching_activity -toggle_rate 13.500 -static_probability 0.500 [get_ports start]
set_switching_activity -toggle_rate 13.500 -static_probability 0.500 [get_ports output_ready]
