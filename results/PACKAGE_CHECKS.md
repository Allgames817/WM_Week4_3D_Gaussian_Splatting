# 归档与指标校验

[项目总览](../README.md) · [来源索引](../SOURCE_INDEX.md)

整理日期：2026-10-12（Asia/Shanghai）。本次检查归档身份、文档链接和保存浮点结果，没有重新训练、重新渲染或重新运行原 CPU/CUDA 验收。

## 历史数值验收

| 模块 | CPU 通过数 | 另行 GPU / CUDA 对照 | 证据目录 |
|---|---:|---:|---|
| 表示与入口 | 8 | 4；CUDA 模式总计 12，含 CPU 重测 | [renderer_entry](renderer_entry/checks) |
| 高斯参数 | 18 | 3 | [gaussian_parameters](gaussian_parameters/checks) |
| 相机投影 | 24 | 3 | [projection](projection/checks) |
| 遮挡合成 | 24 | 4 | [compositing](compositing/checks) |
| 多视角拟合 | 24 | 4 | [training](training/checks) |
| 结构控制 | 24 | 4 | [density_control](density_control/checks) |
| 独立接口与冻结模型 | 24 | fixed / adaptive 各 4 | [CPU](validation/checks)、[fixed](validation/fixed_review/render_report.json)、[adaptive](validation/adaptive_review/render_report.json) |

计数是具名用例，不是独立实验或重复种子数量。历史检查的版本身份与本次源文件核对见 [source_identity.json](package_validation/source_identity.json)。

## 本次归档复核

使用 [verify_artifacts.py](../verify_artifacts.py)执行标准库检查及 NumPy 浮点复算，结果记录在 [artifact_audit.json](package_validation/artifact_audit.json)。检查内容包括：

- 767 个复制文件的 SHA-256 和字节数、JSON 可解析性、本地 Markdown/HTML 文件链接。
- 四组实验 × initial/final × train/val，共 16 组 SSE、MSE、PSNR、最大误差和 target-contrast 区域指标。
- 指标同时与保存 metrics、训练报告和独立历史审计比较；浮点先转 float64，再做差与汇总。
- 四组独立重载 RGB 与对应 final 数组一致，配对实验的共同起点图像一致。
- 两组轨迹各 61 帧文件齐全，浮点起点/返回一致，起点与对应 final 视角 0 匹配；登记的 AVI、NPZ、耗时 CSV 哈希和 audit 关联匹配。

没有通过 PNG 反算指标，也没有加载 Torch checkpoint。原始场景和全部复算输入已在包内；无需本机 `Daily` 路径、CUDA 或 gsplat。

## 可复查命令

```powershell
python verify_artifacts.py
python verify_artifacts.py --recompute-metrics
```

第二条需要 NumPy。本地已有环境可用 `H:\anaconda3\envs\wm_gsplat\python.exe` 执行，读者也可使用自己的 Python 3.10+ 环境。只有输出 `status: PASS` 才表示该次检查通过。

包大小和最大文件的数值以检查运行时为准；输出报告首次写入时尚不计入自身大小，之后只读检查会把该报告纳入统计。哈希校验只绑定复制产物，新增说明和校验报告由本次整理生成。

## 校验边界

本次通过说明归档内结果可以复算、文件与登记身份一致，并不重新证明历史 GPU 执行过程、真实几何精度、全部输入正确性或完整轨迹的视觉质量。源码身份核查只覆盖历史报告实际登记的文件，未登记的文件不自动获得相同保证。
