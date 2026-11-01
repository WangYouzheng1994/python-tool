# 票据 OCR

知识手册唯一入口：[OCR 技术手册与成长学习路线总目录](docs/OCR_TECHNICAL_OVERVIEW.md)。按 `1-` 至 `9-` 递进阅读，涵盖基础、训练、OCR 制品、推理调优及从参数优化到微调训练的分阶段时间预算、官方教程与验收；运行说明仍以本文为准。

1. 把图片放在项目根目录 `test_file/`，在 PyCharm 用项目 `.venv/Scripts/python.exe` 直接运行 `src/ticket_ocr/__main__.py`，无需填写参数。也可选择模块 `ticket_ocr` 直接 Run / Debug；命令行使用 `uv run --no-sync python -m ticket_ocr`。默认输入、模型和结果目录均按源码定位，不受 IDE 工作目录影响。
2. 默认按文件名排序识别 `test_file/` 顶层图片，不递归子目录；支持 PNG/JPEG/BMP/WEBP/TIFF 单帧图片，最多 20 MiB、4000 万像素。一次启动只加载一个 CPU 引擎，逐图复用；单张失败继续处理后续图片。
3. 完整结果保存在 `.ocr-output/run-随机标识/0001.json` 等文件，序号对应输入排序；每次运行创建独立目录，不覆盖已有结果或原图。终端只显示序号、条数、耗时和汇总，不显示完整文字或原图路径。JSON 的 `items` 包含 `text`、四点 `box` 和 `confidence`，另有 `engine_seconds`、`total_seconds`；逐图总耗时包含解码和推理，不包含共享引擎初始化或写盘。坐标对应 EXIF 方向归一化后的图片，透明区域先合成白底。
4. 已从 ModelScope 的 RapidAI/RapidOCR 下载当前配置对应的 Det/Cls/Rec 模型和字典，保存在项目根目录 `models/`（约 30.30 MiB）。已实际识别本地 1 张图片，得到 75 条文字；再次默认运行也成功，无需下载。平时直接运行 `uv run --no-sync python -m ticket_ocr`；仅缺模型且明确允许下载时使用 `uv run --no-sync python -m ticket_ocr --allow-download`。图片不上传，默认禁止下载；当前验证不代表字段解析或数字准确率已验证。
5. 保留显式单图兼容：`uv run --no-sync python -m ticket_ocr test_file/your-image.png`。可选 `--output` 指定尚不存在的单图 JSON 路径；自定义目录不自动受 Git 忽略保护。成功退出 0，处理失败退出 1，参数错误退出 2。
6. 原图、模型和结果只留本机；`test_file/`、`models/`、`.ocr-output/` 已被 Git 忽略。完整 JSON 仍可能敏感，请自行管理访问和清理，不提交或分享真实票据与结果。
7. 现有环境为 Python 3.12.16、RapidOCR 3.10.0、onnxruntime 1.31.1，依赖由 `uv.lock` 锁定；RapidOCR 仅为当前候选实现，不代表生产选型。已有 `.venv` 无需重新初始化；首次恢复环境可使用 `uv sync --locked`，本次未安装或同步依赖。
8. JSON 增加 `total_accumulated` 列表：精确定位“总累计”（不匹配“总累计报表”），按上到下、左到右返回所有组，不相加。分框使用左标签、右侧同行数值，结合框高归一化的重叠比例和中心距离防串行；其他字段阻隔关联，数值框不复用。支持标签数值同框及相邻独立单位框，两种布局共用单位距离与文字阻隔检查；关联单位加入证据并参与低分检查，不伪造字符坐标。明确冒号分隔的异常值（如合成示例 `总累计:O123`）保留 `invalid` 项，不将字母猜成数字。
9. 每组包含 `value`（由 `Decimal` 直接生成的十进制字符串或 `null`）、`unit`、`status`、`label_box` 和原 OCR `evidence`（含 `item_index`、文字、框、OCR `confidence`）。`ok` 仅代表启发式解析通过；`missing`、`invalid`、`ambiguous`、`low_confidence` 均返回空值待确认，不补零、不猜数字、不换算单位。OCR 分数低于 0.9 时待确认，该分数不是字段关联置信度；合框只有整框证据。多个同行数字保守地报歧义，不强取最近值。字段名和状态仅用于本地 Demo，不是已确认 Java 接口契约。
10. 尚无 HTTP、Java 接口、URL 下载或其他字段解析；按用户要求不新增测试类。本轮用临时纯函数脚本验证合成数据，并用现有模型默认离线复跑样本；原图读取未呈现可辨认内容，不能声称目视核验或数字准确率验证完成。协作入口见 [AGENTS.md](AGENTS.md)，需求见 [requirements.md](docs/requirements.md)，实际验证见[交接](.agents/memory/handoff.md)。
