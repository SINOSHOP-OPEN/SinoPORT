# -*- coding: utf-8 -*-
"""桩测 run_filming.bat：把 FreeCAD 换成桩 exe，验证流程与提示语。
坑（见记忆）：桩是 .bat 时，调用它必须加 call，否则父批处理会在那一行后直接结束。"""
import os
import re
import subprocess
import sys

SRC = r"D:\SinoSir\SinoPORT\20261019_开源仓库\SINOPORT_参赛版\run_filming.bat"
TMP = r"C:\Users\Administrator\AppData\Local\Temp\fcstub"
STUB = os.path.join(TMP, "fakecad.bat")
TEST = os.path.join(TMP, "test_run_filming.bat")

os.makedirs(TMP, exist_ok=True)

# 造桩 exe 目录结构：把桩放到 %LOCALAPPDATA%\Programs\... 不可行，改写变量
txt = open(SRC, encoding="ascii").read()
txt = txt.replace(
    'set "FCEXE=%LOCALAPPDATA%\\Programs\\FreeCAD 1.1\\bin\\freecadcmd.exe"',
    'set "FCEXE=%FCEXE_STUB%"',
)
# 坑：桩是 .bat，必须加 call，否则父批处理在此行后结束
txt, n = re.subn(r'(?m)^"%FCEXE%" "%SCRIPT%"', r'call "%FCEXE%" "%SCRIPT%"', txt)
assert n == 1, "替换调用行失败 n=%d" % n

# 坑：脚本路径是相对仓库根的，桩测试目录没有 src/model -> 造一个
spec_dir = os.path.join(TMP, "src", "model")
os.makedirs(spec_dir, exist_ok=True)
open(os.path.join(spec_dir, "build_pyramid_r6.py"), "w").close()

open(TEST, "w", encoding="ascii", newline="\r\n").write(txt)

env = dict(os.environ)
env["FCEXE_STUB"] = STUB

r = subprocess.run(["cmd", "/c", TEST], cwd=TMP,
                   stdin=subprocess.DEVNULL, capture_output=True, env=env)
out = r.stdout.decode("gbk", "replace")
err = r.stderr.decode("gbk", "replace")

checks = [
    ("rc == 0", r.returncode == 0),
    ("stderr 为空", err.strip() == ""),
    ("有 HOW TO CUT 提示块", "HOW TO CUT" in out),
    ("点名 building foam 触发词", "building foam ..." in out),
    ("提示按 Ctrl+C", "Ctrl+C" in out),
    ("提示输入 Y 结束", "type  Y" in out),
    ("解释 Terminate batch job", "Terminate batch job" in out),
    ("跑了 FreeCAD(桩)", "STUB_END" in out),
    ("跑到收尾", "run ended" in out),
    ("无 'was unexpected'", "was unexpected" not in out),
    ("无乱码", "\ufffd" not in out),
]

print("=== run_filming.bat 桩测 ===")
bad = 0
for name, ok in checks:
    print(("PASS  " if ok else "FAIL  ") + name)
    bad += 0 if ok else 1
print("--- 桩测 %d/%d ---" % (len(checks) - bad, len(checks)))
print("--- stdout ---")
print(out)
if err.strip():
    print("--- stderr ---")
    print(err)
sys.exit(1 if bad else 0)
