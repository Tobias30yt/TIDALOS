#!/usr/bin/env python3
"""Boot a TIDALOS ISO in a diskless QEMU VM and collect screenshots and serial logs."""
import argparse
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("iso", type=Path)
    parser.add_argument("--firmware", choices=("bios", "uefi"), default="bios")
    parser.add_argument("--seconds", type=int, default=180)
    parser.add_argument("--output", type=Path, default=Path("dist/boot-test"))
    args = parser.parse_args()
    if not args.iso.is_file():
        parser.error("ISO does not exist")
    args.output.mkdir(parents=True, exist_ok=True)
    output = args.output.resolve()
    (output / "status.json").write_text(json.dumps({"phase": "starting", "firmware": args.firmware}))
    with tempfile.TemporaryDirectory(prefix="tidalos-qemu-") as directory:
        monitor = str(Path(directory) / "qmp.sock")
        serial = str(Path(directory) / "serial.sock")
        command = ["qemu-system-x86_64", "-m", "3072", "-smp", "2", "-accel", "kvm" if os.access("/dev/kvm", os.R_OK | os.W_OK) else "tcg", "-cdrom", str(args.iso.resolve()), "-boot", "d", "-display", "none", "-vga", "std", "-nic", "user,model=virtio-net-pci", "-chardev", f"socket,id=serial,path={serial},server=on,wait=off,logfile={output / 'serial.log'}", "-serial", "chardev:serial", "-qmp", f"unix:{monitor},server=on,wait=off", "-no-reboot"]
        if args.firmware == "uefi":
            code = next((p for p in [Path("/usr/share/OVMF/OVMF_CODE_4M.fd"), Path("/usr/share/OVMF/OVMF_CODE.fd")] if p.exists()), None)
            if code is None:
                parser.error("OVMF firmware is not installed")
            variables = code.with_name(code.name.replace("CODE", "VARS"))
            writable = Path(directory) / "vars.fd"
            shutil.copyfile(variables, writable)
            command += ["-drive", f"if=pflash,format=raw,readonly=on,file={code}", "-drive", f"if=pflash,format=raw,file={writable}"]
        (output / "command.json").write_text(json.dumps(command, indent=2))
        with (output / "qemu.log").open("w") as log:
            process = subprocess.Popen(command, stdout=log, stderr=log)
            try:
                for _ in range(100):
                    if Path(monitor).exists():
                        break
                    if process.poll() is not None:
                        raise RuntimeError((output / "qemu.log").read_text())
                    time.sleep(0.1)
                connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                connection.settimeout(10)
                connection.connect(monitor)
                stream = connection.makefile("rwb")
                stream.readline()

                def qmp(name, arguments=None):
                    stream.write((json.dumps({"execute": name, "arguments": arguments or {}}) + "\n").encode())
                    stream.flush()
                    while True:
                        result = json.loads(stream.readline())
                        if "error" in result:
                            raise RuntimeError(result)
                        if "return" in result:
                            return result["return"]

                qmp("qmp_capabilities")
                print(f"Booting {args.firmware} VM ({command[command.index('-accel')+1]})", flush=True)
                elapsed = 0
                while elapsed < args.seconds:
                    time.sleep(min(30, args.seconds - elapsed))
                    elapsed += min(30, args.seconds - elapsed)
                    if process.poll() is not None:
                        raise RuntimeError("VM exited before inspection completed")
                    qmp("screendump", {"filename": str(output / f"screen-{elapsed:03d}.ppm")})
                    print(f"Captured screen at {elapsed}s", flush=True)
                status = qmp("query-status")
                (output / "status.json").write_text(json.dumps(status, indent=2))
                qmp("quit")
                stream.close()
                connection.close()
                process.wait(timeout=10)
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
    print("Capture complete. Inspect screenshots and serial.log to determine boot success; process status alone is not a desktop test.")


if __name__ == "__main__":
    main()
