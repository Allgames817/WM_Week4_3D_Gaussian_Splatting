# 实验结果归档

[项目总览](../README.md) · [证据索引](../SOURCE_INDEX.md) · [本次校验](PACKAGE_CHECKS.md)

各专题目录保留源 JSON、CSV、NPZ 和显示产物；历史报告里的 day、绝对路径、时间戳和源码哈希未改写。目录名按主题重组，文件内部仍可追溯原运行。

- `dataset`：本地合成场景，含目标、相机、固定划分与初始化。
- `training`：仅颜色/联合拟合的 initial、final、训练记录和独立重载。
- `density_control`：同起点续训、结构事件、优化器相关报告与强制编辑。
- `validation`：独立理想接口、历史浮点审计、两组冻结重放与 61 帧轨迹。
- `package_validation`：本次来源身份核对与归档复算结果，单独区别于历史运行。

`source_manifest.json` 描述复制文件；`excluded_files.json` 说明未分发内容。HTML 需下载后本地打开；GitHub 浏览文件不会执行其中脚本。Torch checkpoint 与完整训练代码不在本包，原报告中的相关路径仅作历史记录。
