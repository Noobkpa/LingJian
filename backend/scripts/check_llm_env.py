"""检查当前解释器下 Qwen + transformers 依赖是否可用（与启动脚本使用的 Python 对齐排查）。"""
from __future__ import annotations

import sys


def main() -> int:
    print("executable:", sys.executable)
    print("version:", sys.version.split()[0])
    try:
        import transformers

        v = getattr(transformers, "__version__", "?")
        print("transformers:", v)
    except Exception as e:
        print("ERROR: import transformers:", e)
        return 1

    try:
        from transformers import BeamSearchScorer  # noqa: F401

        print("BeamSearchScorer: OK")
    except Exception as e:
        print("BeamSearchScorer: FAIL ->", e)
        print("  修复: pip install \"transformers>=4.38,<4.57\"")
        return 2

    try:
        import einops  # noqa: F401

        print("einops: OK")
    except Exception as e:
        print("einops: FAIL ->", e)
        return 3

    try:
        from transformers_stream_generator.main import (  # noqa: F401
            NewGenerationMixin,
            StreamGenerationConfig,
        )

        print("transformers_stream_generator: OK")
    except Exception as e:
        print("transformers_stream_generator: FAIL ->", e)
        return 4

    try:
        import tiktoken  # noqa: F401

        print("tiktoken: OK")
    except Exception as e:
        print("tiktoken: FAIL ->", e)
        return 5

    print("--- 全部通过：请用「同一解释器」启动 uvicorn ---")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
