# 显式高斯表示与渲染接口

[项目总览](README.md) · [下一专题：高斯形状](02_Gaussian_Parameters_and_Covariance.md)

从 NeRF 切换到 3DGS，仍然需要相机、图像和可微渲染。变化在于场景由可学习的高斯集合表达：每个元素直接拥有位置、形状、不透明度与颜色。坐标 MLP 的权重不能直接解释为这组高斯参数。

## 参数与激活边界

| 参数 | 形状 | 进入渲染器前的含义 |
|---|---|---|
| means | `(N,3)` | 世界空间中心 |
| quats | `(N,4)` | 高斯自身旋转，wxyz 顺序 |
| scales | `(N,3)` | 正的主轴标准差；原始 log_scales 通过 exp 转换 |
| opacities | `(N,)` | `[0,1]` 不透明度；原始 logits 通过 sigmoid 转换 |
| colors | `(N,3)` | 直接 RGB，不是球谐系数 |

入口合成实验直接传入已在合法范围内的 RGB，不再 sigmoid。多视角拟合则优化 `color_logits`，在渲染前做一次 sigmoid。**同一个颜色张量是原始参数还是已激活值，必须由接口明确。** 对尺度或 opacity 重复激活也会改变场景。

高斯自身旋转与相机旋转承担不同职责：前者决定椭球朝向，后者把世界坐标转换到相机坐标。两者即使都可用四元数表达，也不能交换使用。

## 相机契约

本项目实际渲染采用 OpenCV 相机局部坐标：x 向右、y 向下、z 向前。`viewmats` 表示 world-to-camera，内参 K 对应当前图像像素。若上游提供 camera-to-world，需要明确求逆；若图像 resize/crop，必须相应更新 K。

投影均值是连续像素坐标。逐像素教学合成使用 `(column+0.5,row+0.5)` 采样，不能重复增加偏移。上一项目 NeRF 的原整数像素契约需要在交接时显式转换，不能仅靠分辨率相同就认为一致。

## 最小渲染证明了什么

入口实验使用三个手工高斯。它将五类参数、相机、背景送入真实 gsplat，导出 RGB、总 alpha 与浮点数组，没有优化器更新。

<p align="center">
  <img src="figures/renderer_rgb.png" alt="三个手工高斯在黑色背景上的 RGB 渲染" width="288" height="192">
  <br>
  <sub>三个手工高斯的 RGB 渲染 · 原图 96 × 64，放大 3 倍展示</sub>
</p>

保存的 [CPU 报告](results/renderer_entry/checks/check_cpu.json)为 8/8；[CUDA 模式报告](results/renderer_entry/checks/check_cuda.json)为 12/12，其中重做 8 项 CPU 检查，新增 4 项 GPU 检查。不能把这两份报告当成 20 项不同检查。

该入口验证接口可运行以及指定输入的前向/反向性质；真实训练改善由[多视角拟合](05_Multi_View_Fitting_and_Evaluation.md)单独证明。入口图片本身不能证明完成了场景重建。

## 与 NeRF 的联系

| 问题 | 前一项目 NeRF | 本项目 3DGS |
|---|---|---|
| 场景参数 | 坐标与方向网络的权重 | 显式高斯参数集合 |
| 像素查询 | 沿世界射线采样并查询神经场 | 将高斯投影为屏幕足迹 |
| alpha 来源 | 密度与有限采样区间 | opacity 与二维高斯响应 |
| 可保留的接口 | 相机语义、RGB 监督、训练/验证隔离、指标口径 | 同左，但像素与布局仍需逐项检查 |
| 本例外观 | 方向相关网络分支 | 直接 RGB，无球谐外观分支 |

本项目实际训练使用固定 `gsplat v1.5.3` 的 CUDA 扩展。保存报告记录 Python 3.10.22、torch 2.4.1+cu124 和 gsplat 1.5.3+pt24cu124；部分原学习说明中的旧版本不作为实际运行依据。环境记录见[入口环境](results/renderer_entry/checks/env_report.json)，后续运行版本也分别保存在各报告中。

## 证据入口

[渲染报告](results/renderer_entry/experiment/render_report.json)记录最小输入与输出范围；[浮点渲染](results/renderer_entry/experiment/render_float.npz)保留数值；[方法来源](SOURCES.md)给出固定版本源码入口。本次整理未重新运行 GPU 渲染，历史文件与当前源文件的匹配情况见[校验记录](results/PACKAGE_CHECKS.md)。
