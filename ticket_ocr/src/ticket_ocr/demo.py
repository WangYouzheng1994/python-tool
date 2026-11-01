"""直接识别项目 test_file 中的图片，提取总累计，不提供 HTTP。

处理顺序：定位图片 → 准备一次 CPU 引擎 → 逐图解码识别 → 写入独立 JSON。
面向 Python 入门阅读：函数负责各处理阶段，main 负责编排，类似 Java 的入口方法。
RapidOCR 只是当前 Demo 候选引擎；默认禁止模型下载，不上传图片。
终端仅显示摘要，但本地 JSON 含完整识别文字，仍须按敏感数据保管和清理。
"""

import argparse
from contextlib import redirect_stderr, redirect_stdout
import json
import os
from pathlib import Path
import sys
from tempfile import mkdtemp
from time import perf_counter
from typing import Any

from ticket_ocr.fields import extract_total_accumulated


# parents 从 0 开始：demo.py → ticket_ocr（0）→ src（1）→ 项目根目录（2）。
# 以源码位置定位模型，避免工作目录改变后找错文件；Path 类似 Java 的 java.nio.file.Path。
PROJECT_DIR = Path(__file__).resolve().parents[2]
MODEL_DIR = PROJECT_DIR / "models"
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tif", ".tiff"}
MAX_IMAGE_BYTES = 20 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000


class DemoError(Exception):
    """可安全显示的固定错误信息。"""


class DemoArgumentParser(argparse.ArgumentParser):
    """参数错误不回显可能包含敏感路径的原始消息。"""

    def error(self, message: str) -> None:
        self.exit(2, "错误：命令行参数无效；请使用 --help 查看用法。\n")


def prepare_engine(allow_download: bool) -> Any:
    """检查模型与字典并构建 CPU 引擎，只有 allow_download 为真才允许下载。

    这里依赖 RapidOCR 3.10.0 的内部配置/API，升级依赖时须重新核对并运行测试，
    不能把内部接口当成长期稳定契约。Any 表示此处暂不约束第三方动态对象的类型，
    不代表返回值可以任意使用；调用方仍依赖引擎可调用的约定。
    """
    # 延迟导入：仅在真正识别时加载 OCR 依赖；查看 --help 不必初始化这些库。
    # Python 的函数内 import 同样使用模块缓存，并非每次调用都重新执行整个模块。
    import rapidocr
    from rapidocr.inference_engine.base import FileInfo, InferSession
    from rapidocr.utils.download_file import DownloadFile, DownloadFileInput
    from rapidocr.utils.log import logger
    from rapidocr.utils.parse_parameters import ParseParams

    cfg = ParseParams.load(Path(rapidocr.__file__).parent / "config.yaml")
    params: dict[str, Any] = {
        "Global.model_root_dir": str(MODEL_DIR),
        "Global.log_level": "critical",
    }
    # 关闭配置中这些硬件加速 provider，使用当前 ONNX Runtime 的 CPU 路径。
    for provider in ("cuda", "dml", "cann", "coreml"):
        params[f"EngineConfig.onnxruntime.use_{provider}"] = False
    # Det 检测文字框，Cls 判断文字方向，Rec 识别文字；Rec 还需字符字典。
    # required 保存 (本地路径, 下载地址, 可选校验和)，先收集再统一检查。
    required = []
    for section in ("Det", "Cls", "Rec"):
        task = cfg[section]
        info = InferSession.get_model_url(
            FileInfo(task.engine_type, task.ocr_version, task.task_type,
                     task.lang_type, task.model_type)
        )
        model = MODEL_DIR / Path(info["model_dir"]).name
        required.append((model, info["model_dir"], info.get("SHA256")))
        params[f"{section}.model_path"] = str(model)
        if section == "Rec":
            # 元数据内置字典时无需读取该文件；否则必须提供本地字典，避免回退下载。
            from rapidocr.ch_ppocr_rec.main import DEFAULT_DICT_URL

            url = info.get("dict_url") or DEFAULT_DICT_URL
            dictionary = MODEL_DIR / Path(url).name
            required.append((dictionary, url, None))
            params["Rec.rec_keys_path"] = str(dictionary)
    # 不把缺失文件交给引擎自行处理：显式路径加前置检查，防止默认流程隐式联网。
    # 当前 Demo 保守地要求字典文件也存在，即使某些模型已内置字典。
    if not allow_download and any(not path.is_file() for path, _, _ in required):
        raise DemoError("缺少本地模型或字典；请准备 models/，或显式使用 --allow-download。")
    for path, url, checksum in required:
        if allow_download:
            DownloadFile.run(DownloadFileInput(url, path, logger, checksum, verbose=False))
        if not path.is_file() or path.stat().st_size == 0:
            raise DemoError("本地模型或字典无效，请重新准备 models/。")
    return rapidocr.RapidOCR(params=params)


def load_image(path: Path) -> Any:
    """校验本地单帧图片，返回方向归一化、白底、BGR 排列的 NumPy 数组。

    Any 用于隔离第三方数组类型，使模块导入时不必先加载 NumPy/Pillow；
    实际返回的是 ndarray，而非图片路径或 URL。
    """
    from PIL import Image, ImageOps
    import numpy as np

    if not path.is_file() or not 0 < path.stat().st_size <= MAX_IMAGE_BYTES:
        raise DemoError("图片不存在、不是普通文件、为空或超过 20 MiB。")
    # with 类似 Java 的 try-with-resources：退出代码块时关闭原图文件，异常时也会关闭。
    # Pillow 可延迟解码，因此在文件仍打开时完成转换，返回独立数组。
    with Image.open(path) as image:
        if image.format not in {"PNG", "JPEG", "BMP", "WEBP", "TIFF"}:
            raise DemoError("不支持的图片格式；请使用 PNG/JPEG/BMP/WEBP/TIFF。")
        if image.width * image.height > MAX_IMAGE_PIXELS:
            raise DemoError("图片超过 4000 万像素。")
        if getattr(image, "n_frames", 1) != 1:
            raise DemoError("仅支持单帧图片。")
        # 坐标对应 EXIF 方向归一化后的图片，而非原始存储方向。
        normalized = ImageOps.exif_transpose(image)
        # 透明区域先合成白底，避免直接丢弃 alpha 后出现黑底或隐藏颜色干扰识别。
        if normalized.mode in {"RGBA", "LA"} or "transparency" in normalized.info:
            rgba = normalized.convert("RGBA")
            background = Image.new("RGBA", rgba.size, "white")
            normalized = Image.alpha_composite(background, rgba)
        # RapidOCR 数组输入采用 BGR；提前解码避免引擎将字符串解释为 URL。
        # 数组轴为 [行(y), 列(x), 通道]；[:, :, ::-1] 只反转 RGB 通道，不翻转坐标。
        # copy() 生成独立、连续的数组，避免负步长视图带来的下游兼容性问题。
        return np.array(normalized.convert("RGB"))[:, :, ::-1].copy()


def convert_result(result: Any, total_seconds: float) -> dict[str, Any]:
    """将引擎结果适配为 JSON 可序列化的 dict/list/str/float，空结果保留空列表。

    result 的 Any 对应第三方结果对象；此函数是隔离其属性结构的适配边界，
    类似将 Java SDK 的返回对象转换为自己的 DTO。坐标只转数值类型，不缩放或换轴。
    """
    texts = result.txts
    items = []
    if texts is not None and len(texts):
        if result.boxes is None or result.scores is None:
            raise ValueError("incomplete result")
        if not len(texts) == len(result.boxes) == len(result.scores):
            raise ValueError("inconsistent result")
        # 普通 zip 会静默截断到最短序列；strict=True 在长度不一致时抛错，避免丢结果。
        # 显式转为内置类型，因为 NumPy 标量/数组不一定能直接交给 json.dumps。
        for text, box, score in zip(texts, result.boxes, result.scores, strict=True):
            items.append({"text": str(text), "box": [[float(v) for v in p] for p in box],
                          "confidence": float(score)})
    return {"items": items, "total_accumulated": extract_total_accumulated(items),
            "engine_seconds": float(result.elapse),
            "total_seconds": total_seconds}


def main(argv: list[str] | None = None) -> int:
    """无参数识别项目 test_file 顶层图片，也兼容显式单图路径。"""
    parser = DemoArgumentParser(description="识别 test_file 中的图片（默认禁止模型下载）")
    parser.add_argument("image", nargs="?", help="可选：显式本地单帧图片路径")
    parser.add_argument("--output", help="单图 JSON 输出路径；不覆盖已有文件")
    parser.add_argument("--allow-download", action="store_true",
                        help="允许模型及字典外网下载到 models/；不上传图片")
    args = parser.parse_args(argv)
    if args.output and args.image is None:
        parser.error("--output requires image")
    try:
        if args.image is not None:
            images = [Path(args.image).expanduser().resolve()]
        else:
            input_dir = PROJECT_DIR / "test_file"
            if not input_dir.is_dir():
                raise DemoError("请把图片放到项目 test_file/ 目录，再直接运行。")
            images = sorted(
                (p for p in input_dir.iterdir()
                 if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES),
                key=lambda p: p.name,
            )
            if not images:
                raise DemoError("test_file/ 顶层没有支持的图片。")
        # 一批图片只初始化一次；禁止将第三方日志或完整识别内容输出到终端。
        with open(os.devnull, "w") as sink, redirect_stdout(sink), redirect_stderr(sink):
            engine = prepare_engine(args.allow_download)
        if args.output:
            output_paths = [Path(args.output).expanduser().resolve()]
            if output_paths[0].exists():
                raise DemoError("输出文件已存在，请换一个路径；不会覆盖已有文件。")
            output_paths[0].parent.mkdir(parents=True, exist_ok=True)
        else:
            output_dir = PROJECT_DIR / ".ocr-output"
            output_dir.mkdir(parents=True, exist_ok=True)
            # 每次运行独立目录，序号与排序后的输入对应，不使用票据文件名。
            run_dir = Path(mkdtemp(prefix="run-", dir=output_dir))
            output_paths = [run_dir / f"{i:04d}.json" for i in range(1, len(images) + 1)]
    except DemoError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1
    except Exception:
        print("错误：模型加载或目录准备失败，请检查本地环境。", file=sys.stderr)
        return 1

    failed = 0
    for index, (image_path, output_path) in enumerate(zip(images, output_paths, strict=True), 1):
        started = perf_counter()
        try:
            with open(os.devnull, "w") as sink, redirect_stdout(sink), redirect_stderr(sink):
                image = load_image(image_path)
                payload = convert_result(engine(image), perf_counter() - started)
            serialized = json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False)
            # 排他创建也防止并发覆盖或输出与原图/硬链接指向同一文件。
            with output_path.open("x", encoding="utf-8") as output:
                output.write(serialized + "\n")
        except DemoError as exc:
            failed += 1
            print(f"第 {index} 张失败：{exc}", file=sys.stderr)
        except Exception:
            failed += 1
            print(f"第 {index} 张失败：图片读取、识别或结果写入失败。", file=sys.stderr)
        else:
            print(f"第 {index} 张：{len(payload['items'])} 条；"
                  f"耗时 {payload['total_seconds']:.3f}s。")
    print(f"处理结束：成功 {len(images) - failed} 张，失败 {failed} 张。")
    if len(images) > failed:
        print("结果位于 .ocr-output/" + run_dir.name + "/。" if not args.output
              else "结果已写入指定 JSON。")
    return 1 if failed else 0
