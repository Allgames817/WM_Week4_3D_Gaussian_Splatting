# 精选图说明

[项目总览](../README.md) · [来源清单](../results/source_manifest.json)

所有精选图都是原实验输出的字节级副本，没有改变显示范围或误差倍率。

| 文件组 | 内容与解释 |
|---|---|
| renderer_rgb | 三个手工高斯的入口渲染 |
| gaussian_* | 世界空间响应的 XY 切片；不包含相机或遮挡 |
| projection_* | 当前白背景 SVG 投影展示，保留原 NPZ 数值 |
| composite_* | 固定二维足迹下，交换深度标签前后的颜色 |
| validation_target | 保留验证视角 1 的合成目标 |
| initial / appearance / joint / fixed / adaptive prediction | 同一视角不同阶段或条件的预测 |
| adaptive_error | `[0,1]` 范围内未放大的绝对 RGB 误差 |
| replay_* | adaptive 局部往返轨迹第 0 / 30 / 60 帧 |

训练图像为 96 × 64，网页放大只为浏览；世界切片和投影实验另有自己的网格。完整路径与哈希见来源清单，图像指标从浮点 NPZ 计算。
