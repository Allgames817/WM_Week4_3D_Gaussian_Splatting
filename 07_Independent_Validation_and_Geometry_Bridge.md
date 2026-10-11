# 独立验证、冻结重放与几何估计衔接

[项目总览](README.md) · [上一专题](06_Density_Control_and_Optimizer_State.md) · [证据索引](SOURCE_INDEX.md)

本模块把三个问题分开验证：几何和合成接口是否满足声明、保存指标能否从浮点数据重算、固定场景能否重复渲染。它没有增加训练步数，也没有进行高斯结构编辑。

## 独立 NumPy 接口

| 接口 | 输入与职责 | 边界 |
|---|---|---|
| project_packet | 世界中心、完整协方差、OpenCV c2w、K → 深度与二维投影 | float64；严格 `Z>near`；无效行标记 NaN |
| shade_pixels | 有效投影、像素坐标、opacity、RGB、背景 → 前向合成 | 稳定深度排序；权重散回原高斯 ID |
| pooled_rgb_metrics | 一组预测/目标 → SSE、MSE、PSNR | 先转 float64 再相减；不量化 |

保存的 [CPU 检查](results/validation/checks/check_cpu.json)共 24 项通过，三类接口各 8 项。[接口实验](results/validation/interface/interface_report.json)使用四个高斯，其中三个深度有效；A→B 的最大 RGB 差异为 0.292395，返回 A 的差异为 0。

该理想接口不调用 gsplat 替代自己的投影和混合，也不包含生产实现全部裁剪和阈值。没有目标图像，所以不报告 PSNR。与真实训练模型的验证分别记录。

## 保存证据的复核

[历史审计](results/validation/reconciliation/audit_report.json)复算 appearance、joint、fixed、adaptive 的 initial/final，共八行结果，并核对数据、checkpoint 和训练记录。它没有调用优化器或渲染器。

本次整理又以只读方式核对其 66 个输入文件哈希，全部匹配；各模块检查所登记的源码身份也匹配。两份冻结渲染报告登记的六个产物哈希与关联 audit 哈希均匹配。详细范围见[本次来源校验](results/package_validation/source_identity.json)。

归档另提供 [verify_artifacts.py](verify_artifacts.py)，让读者只用 NumPy 就能复算四组、两个阶段、训练/验证共 16 组汇总指标，并核对 contrast-mask、独立重载数组与保存轨迹。本次运行结果见[归档校验](results/PACKAGE_CHECKS.md)。哈希一致支持文件身份，不独立证明历史训练究竟如何执行。

## 冻结真实模型

fixed 和 adaptive 分别有 12、14 个高斯；在本模块中两者都冻结。`fixed` 是训练时不改数量的方案名称，不意味着只有这一组在重放阶段冻结。

| CUDA 检查 | fixed | adaptive |
|---|---|---|
| 重载模型与保存 RGB | 最大差异 0 | 最大差异 0 |
| 批量与逐相机调用 | 最大差异 0 | 最大差异 0 |
| A→B→A 返回一致 | 最大差异 0 | 最大差异 0 |
| 参数与磁盘 checkpoint 不变 | 通过 | 通过 |

来源：[fixed 报告](results/validation/fixed_review/render_report.json)、[adaptive 报告](results/validation/adaptive_review/render_report.json)。每组 4/4，通过容差为 atol=2e-6、rtol=2e-5；本次测得零差异不保证跨硬件位级一致。

## 局部往返轨迹

相机沿原视角中心 `0→6→0`，每对相邻相机间分五段，共 61 帧，方向固定。轨迹是局部平移，不是 360° 环绕；插值帧没有目标 RGB，所以没有轨迹 PSNR。

| 第 0 帧 | 第 30 帧 | 第 60 帧 |
|---|---|---|
| <img src="figures/replay_start.png" alt="轨迹起点" width="240"> | <img src="figures/replay_middle.png" alt="轨迹转折点" width="240"> | <img src="figures/replay_return.png" alt="返回轨迹起点" width="240"> |

下载后打开 [fixed HTML](results/validation/fixed_review/index.html)或 [adaptive HTML](results/validation/adaptive_review/index.html)可查看序列；也保留 [fixed AVI](results/validation/fixed_review/camera_path.avi)和 [adaptive AVI](results/validation/adaptive_review/camera_path.avi)。图像抽查和数组核对不等于完成整段视频的人工逐帧验收，未据此宣称全程无闪烁或排序跳变。

A→B→A 一致说明固定模型可重复查询。这里没有在线隐藏状态或记忆学习，不能据此证明空间记忆或未来动力学预测。

## 耗时的测量范围

| 模型 | N | 中位同步调用耗时 | p90 | allocated 峰值 |
|---|---:|---:|---:|---:|
| fixed | 12 | 0.338500 ms | 0.467590 ms | 651,776 bytes |
| adaptive | 14 | 0.283350 ms | 0.455970 ms | 651,776 bytes |

相机固定为 ID 3，96 × 64，batch=1，预热 20 次、测量 50 次。计时包含 Python 调度、GPU 运算与前后同步，排除参数激活、主机传输、图像/视频编码和写盘。内存是 PyTorch 分配器统计，不是整卡显存。

adaptive 本次中位耗时较低，但这是独立进程中极小场景的测量，不能建立一般速度排名，也不能与论文高清场景 FPS 比较。原始耗时保存在两组目录的 `render_times.csv` 中。

## 通向前馈几何估计

下一阶段可研究从多视角 RGB 预测相机、深度和点图，再整理成高斯初始化所需的几何输入。[VGGT 官方仓库](https://github.com/facebookresearch/vggt)提供此类几何预测及 COLMAP 导出入口；输出仍需接入场景初始化和后续图像拟合。

```text
multi-view RGB → geometry prediction
              → camera / image preprocessing / scale checks
              → points and Gaussian initialization
              → image-supervised fitting
```

交接时需核对 w2c/c2w、矩阵形状、预处理后 K、世界坐标与尺度，以及点图和 depth+camera 反投影的关系。相机朝向不能直接用作高斯自身旋转，置信度也不自动等于标定后的正确概率。

本项目没有完成 VGGT 安装、权重下载、推理或显存验证。这一节是接口方向；保存的 3DGS 数值证据不能替代下一阶段的实际验收。
