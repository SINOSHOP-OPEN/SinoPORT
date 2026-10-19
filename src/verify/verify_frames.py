# -*- coding: utf-8 -*-
"""帧序列连续性判定  (2026-10-18)

为什么单独一个文件
================================================================
r1 的 GROUP-9B 片首轮编码只得了 868 帧（应为 912），`encode_film.py`
的 VERIFY 只查分辨率 / 像素格式 / 帧率 —— 868 帧全部 PASS 被当成
成片交付。缺陷在于：它只数「有多少帧」，不查「帧号是否连续」。

本文件查两件事，缺一即 BLOCKED：
  1 帧号从 1 起严格 +1，无跳号
  2 帧数 = 时长 x FPS（缺帧会导致末段黑屏或音画不齐）

Run:  python -B verify_frames.py <frame_dir> [expected_frames]
      python -B verify_frames.py <frame_dir> [expected] --zero-based
"""
import glob
import os
import re
import sys


def main():
    if len(sys.argv) < 2:
        print("usage: verify_frames.py <frame_dir> [expected]")
        return 2
    d = sys.argv[1]
    exp = int(sys.argv[2]) if len(sys.argv) > 2 else None
    # 【2026-10-19】部分渲染脚本（R5/F3 系列、岸边 r3）用 0-based 帧号，
    # 与本脚本原定的 1-based 约定不同。开关只改「起始帧号」这一项判据，
    # 连续性与帧数判据不变 —— 故不影响既有片的回归结果。
    zero_based = "--zero-based" in sys.argv

    files = glob.glob(os.path.join(d, "f*.png"))
    if not files:
        print("BLOCKED: 目录无帧：%s" % d)
        return 2

    nums = []
    for f in files:
        m = re.search(r"f(\d+)\.png$", os.path.basename(f))
        if m:
            nums.append(int(m.group(1)))
    nums.sort()

    print("目录：%s" % d)
    print("帧文件数：%d" % len(files))
    if not nums:
        print("BLOCKED: 帧名不符合 fNNNNN.png 规范")
        return 2
    print("帧号范围：%d ~ %d" % (nums[0], nums[-1]))

    ok = True

    # ---- 1 起止 ----
    _first = 0 if zero_based else 1
    if nums[0] != _first:
        print("FAIL  首帧应为 f%05d.png，实测 f%05d.png" % (_first, nums[0]))
        ok = False
    else:
        print("PASS  首帧 f%05d.png%s"
              % (_first, "（0-based）" if zero_based else ""))

    # ---- 2 连续性 ----
    missing = []
    for a, b in zip(nums[:-1], nums[1:]):
        if b != a + 1:
            for k in range(a + 1, b):
                missing.append(k)
    if missing:
        print("FAIL  帧号不连续，缺 %d 帧：%s%s"
              % (len(missing), missing[:20],
                 " ..." if len(missing) > 20 else ""))
        ok = False
    else:
        print("PASS  帧号连续，零缺失")

    # ---- 3 期望帧数 ----
    if exp is not None:
        if len(nums) != exp:
            print("FAIL  帧数 %d != 期望 %d" % (len(nums), exp))
            ok = False
        else:
            print("PASS  帧数 %d = 期望 %d" % (len(nums), exp))
    else:
        print("INFO  未给期望帧数，跳过帧数判定")

    print("VERIFY:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
