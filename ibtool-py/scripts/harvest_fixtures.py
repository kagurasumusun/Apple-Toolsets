#!/usr/bin/env python3
"""Apple 純正 ibtool の全出力を大量取得してローカルフィクスチャ化"""
import sys, time, os, hashlib, base64
sys.path.insert(0, "/home/user/scripts")
from upterm_shell import UptermShell

LOCAL = "/home/user/ibtool-py/fixtures"
os.makedirs(f"{LOCAL}/input", exist_ok=True)
os.makedirs(f"{LOCAL}/golden", exist_ok=True)
os.makedirs(f"{LOCAL}/meta", exist_ok=True)


def step(u, label, cmd, timeout=30):
    """bash -c 経由で zsh の履歴展開/autocorrect/p10k から完全に隔離"""
    marker = f"M{int(time.time()*1e6)%100000000}"
    # bash -c '...' で 1 行スクリプトを実行
    inner = cmd.replace("'", "'\\''")
    wrapped = f"bash -c '{inner} 2>&1; echo __E=$?__; printf \"\\n__MARK_{marker}__\\n\"'"
    u.recv_available_clean()
    u.sendline(wrapped)
    text = u.recv_until_clean(f"__MARK_{marker}\n__".encode(), timeout=timeout)
    e = ""
    for line in text.splitlines():
        if line.startswith("__E="):
            e = line
            break
    return label, e, text


with UptermShell(verbose=False) as u:
    time.sleep(1.5)
    u.recv_available_clean()

    # 1) あらゆる xib / storyboard を /tmp/ibtests にコピー
    cmd_setup = r"""
set +e
rm -rf /tmp/ibtests; mkdir -p /tmp/ibtests
cd /Applications/Xcode_26.5.app/Contents/Developer/Platforms
echo '--- iOS xib ---'
for f in $(find iPhoneOS.platform/Developer/Library/Xcode/Templates -name '*.xib' 2>/dev/null | head -8); do
  base=$(basename "$f" | sed 's/___FILEBASENAME___/__/g')
  cp "$f" "/tmp/ibtests/ios_${base}"
done
echo '--- iOS storyboard ---'
for f in $(find iPhoneOS.platform/Developer/Library/Xcode/Templates -name '*.storyboard' 2>/dev/null | head -8); do
  base=$(basename "$f" | sed 's/___FILEBASENAME___/__/g')
  cp "$f" "/tmp/ibtests/ios_${base}"
done
echo '--- tvOS xib ---'
for f in $(find AppleTVOS.platform/Developer/Library/Xcode/Templates -name '*.xib' 2>/dev/null | head -5); do
  base=$(basename "$f" | sed 's/___FILEBASENAME___/__/g')
  cp "$f" "/tmp/ibtests/tvos_${base}"
done
echo '--- tvOS storyboard ---'
for f in $(find AppleTVOS.platform/Developer/Library/Xcode/Templates -name '*.storyboard' 2>/dev/null | head -5); do
  base=$(basename "$f" | sed 's/___FILEBASENAME___/__/g')
  cp "$f" "/tmp/ibtests/tvos_${base}"
done
echo '--- macOS xib ---'
for f in $(find MacOSX.platform/Developer/Library/Xcode/Templates -name '*.xib' 2>/dev/null | head -5); do
  base=$(basename "$f" | sed 's/___FILEBASENAME___/__/g')
  cp "$f" "/tmp/ibtests/mac_${base}"
done
echo '--- watchOS xib (rare) ---'
for f in $(find WatchOS.platform/Developer/Library/Xcode/Templates -name '*.xib' 2>/dev/null | head -5); do
  base=$(basename "$f" | sed 's/___FILEBASENAME___/__/g')
  cp "$f" "/tmp/ibtests/watchos_${base}"
done
echo '--- visionOS xib (rare) ---'
for f in $(find XROS.platform/Developer/Library/Xcode/Templates -name '*.xib' 2>/dev/null | head -5); do
  base=$(basename "$f" | sed 's/___FILEBASENAME___/__/g')
  cp "$f" "/tmp/ibtests/xros_${base}"
done
ls /tmp/ibtests/ | wc -l
ls /tmp/ibtests/ | head -40
"""
    lab, e, text = step(u, "setup", cmd_setup, timeout=60)
    print("--- setup ---")
    print(text[:4000])
    print("...")
    print(e)
    print()
