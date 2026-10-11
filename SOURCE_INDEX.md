# 来源与证据索引

[项目总览](README.md) · [归档校验](results/PACKAGE_CHECKS.md)

公开说明按技术主题组织。原始实验位于本地 `Daily/Week4_Day1` 至 `Daily/Week4_Day7`；旧目录名、JSON 的 day 字段、绝对路径、源码指纹与时间戳保留原值，用于追溯，不作为阅读顺序。

| 展示主题 | 原目录 | 归档证据 |
|---|---|---|
| 表示与渲染入口 | Week4_Day1 | [渲染](results/renderer_entry/experiment/render_report.json)、[环境](results/renderer_entry/checks/env_report.json) |
| 高斯形状 | Week4_Day2 | [参数实验](results/gaussian_parameters/experiment/experiment_report.json)、[形状统计](results/gaussian_parameters/experiment/shape_stats.csv) |
| 相机投影 | Week4_Day3 | [实验记录](results/projection/experiment/experiment_report.json)、[投影统计](results/projection/experiment/projection_stats.csv) |
| 遮挡合成 | Week4_Day4 | [实验报告](results/compositing/experiment/experiment_report.json)、[独立逐像素核对](results/compositing/verified_metrics.json) |
| 多视角拟合 | Week4_Day5 | [合成场景](results/dataset/dataset_manifest.json)、[appearance](results/training/appearance/training_report.json)、[joint](results/training/joint/training_report.json) |
| 结构控制 | Week4_Day6 | [fixed](results/density_control/fixed/training_report.json)、[adaptive](results/density_control/adaptive/training_report.json)、[强制编辑](results/density_control/edit_audit/audit_report.json) |
| 独立验证 | Week4_Day7 | [接口](results/validation/interface/interface_report.json)、[指标审计](results/validation/reconciliation/audit_report.json)、[冻结渲染](results/validation/adaptive_review/render_report.json) |

## 版本选择

- 原 README 多数仍是学习包发放时的说明，包含“TODO 未完成”“尚未运行”等文字。公开总结依据实际保存的检查、训练、重载与数值产物，不复制这些过期状态。
- 实际包版本以运行报告为准：torch 2.4.1+cu124，gsplat 1.5.3+pt24cu124；原训练说明里的 torch 2.4.0 不作为实测环境。
- 投影采用当前 `outputs/day3`。其中 `presentation_updates` 说明白底 SVG 从原 NPZ 重导出；报告保留原数值运行版本及旧 SVG 哈希，不将样式更新写成重新计算。
- 强制编辑采用 `edit_audit_pathfix_20261012_015255`，归档为 `results/density_control/edit_audit`。较早重复目录不重复收录。
- 环境门槛、投影样式和路径修正之前的备份仍在原工作区。本展示包选取当前通过记录，不把通过状态解释为实验历史从未遇到问题。

## 文件身份

[source_manifest.json](results/source_manifest.json)对每个复制文件记录源路径、目标路径、字节数、SHA-256 和用途。精选图是源图的字节级副本，原 JSON、CSV、NPZ、HTML、AVI 也未改写。`documentation_inputs_not_distributed` 记录原说明和源码的身份，不表示这些文件已随包分发。

[本次来源核对](results/package_validation/source_identity.json)包括历史检查登记的源码、审计列出的 66 个输入、两组冻结报告登记的六个产物，以及 audit 关联哈希。核对发生于 2026-10-12；这不等于重跑历史 CPU/CUDA 检查或训练。

## 分发范围

与上一项目一样，本仓库定位为结果展示和证据归档。随包包含本地自建合成场景 `scene.npz`，用于给浮点预测提供一致的目标、划分和背景；它包含初始化参数，不包含 teacher 参数。强制编辑的 NPZ 也保留对应参数快照。

完整训练源码、Torch checkpoint、缓存、环境安装脚本、空白学习模板与重复运行未收录，见[排除说明](results/excluded_files.json)。原报告里的 checkpoint 或源码路径是历史输入位置，不是本仓库可执行路径。公开复核脚本只依赖本包文件，不需要访问原工作区。

哈希保证当前归档与整理输入一致，不能证明缺少历史身份记录的文件从未被修改。保存的浮点图像可复算指标，不能用来重新渲染任意新相机；61 帧轨迹是已有输出，也不是实时模型。
