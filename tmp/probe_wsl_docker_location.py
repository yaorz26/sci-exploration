"""只读排查：WSL 发行版虚拟磁盘与 Docker 数据的实际落盘位置。

只读操作：读取注册表 Lxss 键与若干已知路径的存在性/体积，不启动 WSL、不启动 Docker、不改任何设置。
"""
import json
import os
import shutil
import winreg


def drive_free(path):
    drive = os.path.splitdrive(os.path.abspath(path))[0] + os.sep
    try:
        usage = shutil.disk_usage(drive)
        return "%s free %.1f GiB / total %.1f GiB" % (drive, usage.free / 2**30, usage.total / 2**30)
    except Exception as exc:  # noqa: BLE001
        return "%s <error: %s>" % (drive, exc)


def human(size):
    return "%.2f GiB" % (size / 2**30)


print("=== 1. WSL 发行版位置（注册表 HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Lxss） ===")
try:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Lxss") as key:
        index = 0
        while True:
            try:
                guid = winreg.EnumKey(key, index)
            except OSError:
                break
            index += 1
            with winreg.OpenKey(key, guid) as sub:
                info = {}
                for value_name in ("DistroName", "BasePath", "State", "Version", "Flags"):
                    try:
                        info[value_name] = winreg.QueryValueEx(sub, value_name)[0]
                    except OSError:
                        info[value_name] = None
                base = info.get("BasePath") or ""
                local = base.replace("\\\\?\\", "").replace("\\", os.sep) if base else ""
                vhdx = os.path.join(local, "ext4.vhdx") if local else ""
                print("- distro=%s state=%s version=%s" % (info.get("DistroName"), info.get("State"), info.get("Version")))
                print("  BasePath=%s" % base)
                if vhdx and os.path.exists(vhdx):
                    print("  ext4.vhdx=%s  size=%s  所在盘: %s" % (vhdx, human(os.path.getsize(vhdx)), drive_free(vhdx)))
                else:
                    print("  ext4.vhdx 未在预期路径找到: %s" % vhdx)
except OSError as exc:
    print("读取注册表失败: %s" % exc)

print("\n=== 2. Docker Desktop 数据位置（已知候选路径，只判存在性） ===")
local_appdata = os.environ.get("LOCALAPPDATA", "")
appdata = os.environ.get("APPDATA", "")
candidates = [
    os.path.join(local_appdata, "Docker", "wsl"),
    os.path.join(local_appdata, "Docker", "wsl", "data"),
    os.path.join(local_appdata, "Docker", "wsl", "distro"),
    os.path.join(local_appdata, "Docker", "wsl", "main"),
]
for path in candidates:
    exists = os.path.isdir(path)
    print("- %s  exists=%s" % (path, exists))
    if exists:
        for root, _dirs, files in os.walk(path):
            for name in files:
                if name.lower().endswith((".vhdx", ".vhd")):
                    full = os.path.join(root, name)
                    print("    %s  size=%s  %s" % (full, human(os.path.getsize(full)), drive_free(full)))
            break

settings = os.path.join(appdata, "Docker", "settings-store.json")
print("- %s  exists=%s" % (settings, os.path.isfile(settings)))
if os.path.isfile(settings):
    try:
        with open(settings, encoding="utf-8") as fh:
            data = json.load(fh)
        keys = ("DataFolder", "dataFolder", "WslEngineDataFolder", "DiskSizeMiB", "DiskSizeGiB")
        for key in keys:
            if key in data:
                print("    %s = %r" % (key, data[key]))
    except Exception as exc:  # noqa: BLE001
        print("    解析失败: %s" % exc)

print("\n=== 3. 盘容量 ===")
for drive in ("C:\\", "D:\\"):
    print("- %s" % drive_free(drive))
