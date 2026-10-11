# 方法、实现与数据来源

[项目总览](README.md) · [本地证据索引](SOURCE_INDEX.md)

外部资料用于解释方法与实现入口；本仓库的数字、图像和结论范围以本地实验产物为依据。未使用论文图片或论文指标充当本机结果。

| 来源 | 用途 |
|---|---|
| [3D Gaussian Splatting 原论文 v1](https://arxiv.org/abs/2308.04079v1) | 显式高斯、协方差优化、可见性感知渲染与密度控制的概念来源 |
| [作者项目页](https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/) | 原方法与官方材料入口 |
| [gsplat v1.5.3](https://github.com/nerfstudio-project/gsplat/tree/v1.5.3) | 本地实际使用的渲染库版本 |
| [渲染入口 rendering.py](https://github.com/nerfstudio-project/gsplat/blob/v1.5.3/gsplat/rendering.py) | 相机、直接 RGB 与光栅化选项 |
| [几何参考 _torch_impl.py](https://github.com/nerfstudio-project/gsplat/blob/v1.5.3/gsplat/cuda/_torch_impl.py) | 四元数、协方差与投影的源码阅读入口 |
| [CUDA 包装接口](https://github.com/nerfstudio-project/gsplat/blob/v1.5.3/gsplat/cuda/_wrapper.py) | 投影、tile 与像素合成接口 |
| [DefaultStrategy](https://github.com/nerfstudio-project/gsplat/blob/v1.5.3/gsplat/strategy/default.py) / [行操作](https://github.com/nerfstudio-project/gsplat/blob/v1.5.3/gsplat/strategy/ops.py) | 增删与参数、优化器状态管理的阅读参考 |
| [PyTorch 2.4 CUDA 语义](https://docs.pytorch.org/docs/2.4/notes/cuda.html#asynchronous-execution) | 理解保存报告中的同步计时范围 |
| [VGGT 官方仓库](https://github.com/facebookresearch/vggt) / [论文 v1](https://arxiv.org/abs/2503.11651v1) | 下一阶段前馈几何输出与接口方向 |

## 本地实验与上游方法的关系

本地使用小型手工/合成场景、直接 RGB、固定相机、确定性视角顺序、RGB MSE 和有限结构编辑。没有复制原论文全部训练设置，也没有复现其真实场景质量和实时性能基准。

教学 NumPy 合成与生产 gsplat 的阈值、裁剪和排序路径有区别；独立用例通过不表示所有场景逐值相等。VGGT 只作为方向与接口参考，main 分支会变化，本包没有固定或验证下一阶段的实际运行环境。

## 数据与图像

训练目标由本机 gsplat 渲染器生成，场景清单见 [dataset_manifest.json](results/dataset/dataset_manifest.json)。`scene.npz` 的 SHA-256：

```text
51d579640f0ecc5b28906eff9f0f716b90042eda0539d4e0fdc22fce04185af5
```

切片、椭圆、混合图、预测图和轨迹均来自本地实验。精选图保留原始像素/向量文件；目标图、预测图及误差图有不同语义，不以相似外观替代指标核对。上游代码和论文的权利归各自权利人，本展示包不重新授予第三方材料许可。

2026-10-12 整理时核对了论文页面、gsplat 固定版本仓库及 VGGT 官方仓库入口；详细接口解释还依据原工作区的契约和已保存实验记录，没有声称重新审计全部上游源码。
