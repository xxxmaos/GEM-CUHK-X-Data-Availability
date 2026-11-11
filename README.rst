GEM / AdaDebate-X 数据可用性说明
================================

本仓库只收录论文数据声明清单所需的说明、官方链接、引用和来源核验信息。
不包含原始视频、采样帧、传感器数据、预测记录、日志、模型权重或论文正文。
创建日期：2026-11-11。新仓库与原项目均为私有仓库，链接需要获授权账号访问。

五项清单
--------

1. 正式名称与版本：CUHK-X — Small Model Track，HAR 训练发布包；本地下载元数据记录的固定修订为 ca37a2e9c6a06271309be03bbfbe16f29e40d8b4。这不是数据集“v2.0”；Version 2.0 是许可版本。
2. 官方入口：https://openaiotlab.github.io/CUHK-X/ ，官方数据浏览器 https://aiot-public-dataset-cuhk-x.cuhkaiot.com/ 。本地包对应的发布页为 https://huggingface.co/datasets/Kevin-Pal/CUHK-X_Small_Model_Track 。
3. 访问条件：依官方数据条款，访问前须取得所有者明确书面许可；申请联系 syjiang@ie.cuhk.edu.hk。页面可浏览不等于已经取得使用许可。此仓库不声称作者已完成授权申请。
4. 许可与限制：https://github.com/openaiotlab/CUHK-X/blob/main/LICENSE ，以及 https://huggingface.co/datasets/Kevin-Pal/CUHK-X_Small_Model_Track/blob/main/LICENSE 。CUHK-X License Version 2.0 的数据条款限定非商业研究并禁止全部或部分数据再分发。旧 README 中 MIT / CC BY 4.0 的说明与当前 LICENSE 不一致，不能据旧说明推断数据可以再分发。
5. 实际提供范围：本仓库仅提供这份数据声明文档包；原研究仓库包含研究代码、逐片段预测、汇总结果、配置及部分日志/报告。没有发现已提交的原始图像或视频；详情见 PROJECT_DATA_SCOPE.txt。

文件
----

* DATASET_INFO.txt：名称、精确下载修订、采用的任务与模态。
* ACCESS_AND_LICENSE.txt：官方入口、申请条件、许可链接及版本区分。
* PROJECT_DATA_SCOPE.txt：本仓库、原项目和本地数据目录的范围区别。
* dataset_reference.bib：官方论文引用。
* data_availability.tex：可用于稿件的英文数据声明（含中文注释）。
* provenance.json：下载修订、ETag、文件校验、原项目提交及来源链接。

原研究仓库：https://github.com/xxxmaos/AdaDebate-X-ConvNeXt
本说明仓库：https://github.com/xxxmaos/GEM-CUHK-X-Data-Availability
本仓库不是完整复现实验包，也不是数据集镜像。
