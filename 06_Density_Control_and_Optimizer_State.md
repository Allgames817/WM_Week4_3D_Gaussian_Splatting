# 受控增密、裁剪与 Adam 状态迁移

[项目总览](README.md) · [上一专题](05_Multi_View_Fitting_and_Evaluation.md) · [下一专题：独立验证](07_Independent_Validation_and_Geometry_Bridge.md)

增密改变显式场景的参数行数，也改变优化器需要维护的状态。本项目实现有限预算的确定性策略，以固定数量续训作为配对对照；它不是完整 DefaultStrategy 或原论文密度控制的复现。

## 结构操作的含义

| 操作 | 参数行变化 | 本地规则 |
|---|---|---|
| clone | 保留父行，追加一个副本；净增 1 | 原样复制五组原始参数 |
| split | 删除父行，追加两个子行；净增 1 | 沿最长局部轴的世界方向对称偏移，尺度除以 1.6 |
| prune | 删除所选行；净减 1 | 优先选择 opacity 较低的候选，保留最小数量 |

split 位移为父高斯最大尺度的一半，颜色和 opacity 继承父值。没有 alpha、体积或积分补偿，因此这些操作不会普遍保持图像不变。

## 选择规则与预算

先处理低 opacity 裁剪，再从未被裁剪、有有效投影且梯度统计超过阈值的高斯中选择增密候选。选中父行按尺度分为 clone 或 split。平局使用原始行号，预算按净新增行数计算。

| 配置 | 值 |
|---|---:|
| grow_threshold | 0.0002 |
| small_scale | 0.12 |
| prune_threshold | 0.005 |
| max_points / min_points | 32 / 4 |
| 每窗口 max_new / max_prune | 2 / 2 |
| 检查时刻 | 追加第 50、100、150、200、250 步之后 |

有效投影不等于无遮挡；梯度统计也不是 NeRF 的体密度。验证视角既不参与梯度，也不参与结构选择。

## 参数与 Adam 必须一起更新

五组参数共享相同的 `source_index` 和 `is_new`：它们确保同一行仍然指向同一个高斯。保留行的 `exp_avg`、`exp_avg_sq` 按源索引迁移，新行的两类矩清零；每个参数组的标量 step 保留，学习率和其他配置不变。

新行虽然矩为零，却共享已有参数组的 step，不能说它们从独立 Adam 的第 0 步重新开始。编辑后还要替换参数组引用、删除旧 Parameter 对应状态，并重新前向构建计算图。新建空 Adam 会丢掉旧行历史，不符合这次对照设计。

保存的 [CPU 检查](results/density_control/checks/check_cpu.json)为 24/24，覆盖选择、行编辑和状态迁移；[CUDA 检查](results/density_control/checks/check_cuda.json)另有 4 项，覆盖编辑后的渲染、梯度、更新与重载。

## 配对续训结果

fixed 和 adaptive 都从同一个 joint checkpoint 及 Adam 状态开始，各追加 300 步，总计 900 步。相机顺序、数据、损失与 LAST 规则一致，起始 RGB 最大差异为 0。

| 方案 | 最终 N | Val MSE | Val PSNR | Val 对比区域 MSE |
|---|---:|---:|---:|---:|
| 共同起点 joint | 12 | 4.37484701e-6 | 53.5904 dB | 1.09442810e-5 |
| fixed | 12 | 4.42021577e-6 | 53.5456 dB | 1.09632368e-5 |
| adaptive | 14 | 1.77948648e-6 | 57.4971 dB | 4.33892701e-6 |

adaptive 相比 fixed 的验证 MSE 低 59.74%，PSNR 高 3.9515 dB。fixed 相比共同起点略退化约 1.04%，说明追加步数不保证验证误差单调下降。相同步数也不是相同算力，不能将该表解释为等计算预算基准。

## 编辑瞬间与后续收益

五个窗口中只有一个实际发生编辑：追加第 50 步，父行 7、11 被分裂为四个子行，高斯数 12→14。全程 clone=0、split=2 个父行、prune=0。

| adaptive 时刻 | N | Val MSE |
|---|---:|---:|
| 第 50 步编辑前 | 12 | 4.31416947e-6 |
| 第 50 步编辑后 | 14 | 1.29954459e-4 |
| 第 100 步编辑前 | 14 | 2.69219663e-6 |
| 第 300 步最终 | 14 | 1.77948648e-6 |

编辑瞬间误差约增至 30 倍，之后继续优化才恢复并改善。结论是“这次受控分裂加后续优化有益”，不是“增加高斯一定立即变好”。来源：[事件记录](results/density_control/adaptive/events.json)、[阶段指标](results/density_control/adaptive/metrics_history.csv)。

## 强制编辑是另一种实验

独立审计在同一已拟合起点分别强制执行 noop、clone、split、prune，之后不训练：

| 分支 | N | Val MSE | 与起点 RGB 最大变化 |
|---|---:|---:|---:|
| noop | 12 | 4.37484701e-6 | 0 |
| clone | 13 | 2.26402835e-4 | 0.214020 |
| split | 13 | 8.01663271e-5 | 0.134495 |
| prune | 11 | 5.08562997e-4 | 0.445501 |

[强制编辑报告](results/density_control/edit_audit/audit_report.json)证明这些结构操作会改变图像，不证明它们在训练中触发或带来收益。clone/prune 在实际续训中均未触发，因此本例没有它们的训练收益证据。重载一致性由 [fixed](results/density_control/fixed_reload/evaluation_report.json)与 [adaptive](results/density_control/adaptive_reload/evaluation_report.json)的独立报告支持。
