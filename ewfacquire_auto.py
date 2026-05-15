#!/usr/bin/env python3
"""
Fully automated ewfacquire wrapper
Covers ALL acquisition prompts deterministically
with macOS-safe pre-flight checks and raw-read validation.

Author: Prince
"""

import pexpect
import datetime
import os
import sys
import time
import subprocess
import shutil

# =========================
# SAFETY CHECK – ROOT
# =========================

if os.geteuid() != 0:
    print("[-] Must be run with sudo/root.")
    sys.exit(1)

# =========================
# USER CONFIGURATION
# =========================

SOURCE_TYPE = "device"  # case-sensitive options: "device" for physical disk or "vmdk" for virtual disk image
EVIDENCE_DEVICE = "/dev/rdisk5"
VMDK_PATH = ""  # required when SOURCE_TYPE = "vmdk"

IMAGE_DIR = "/Users/princesharma/Library/CloudStorage/GoogleDrive-career.prince@gmail.com/My Drive/saks_drive/"

CASE_PREFIX = "CASE_1"
CASE_START_NUMBER = 1
EVIDENCE_NUMBER = "001"
EXAMINER_NAME = "Prince"
DESCRIPTION = "sakshi_hd"
NOTES = "testing1"

MEDIA_TYPE = "fixed"
MEDIA_CHARACTERISTICS = "physical"

EWF_FORMAT = "encase6"
COMPRESSION_METHOD = "deflate"
COMPRESSION_LEVEL = "fast"

START_OFFSET = "0"
BYTES_TO_ACQUIRE = ""
SEGMENT_SIZE = ""
BYTES_PER_SECTOR = ""
SECTORS_AT_ONCE = "8192"
ERROR_GRANULARITY = "4096"
RETRIES = "1"
WIPE_ON_ERROR = "no"

# =========================
# PRE-FLIGHT CHECKS (LEAN)
# =========================

def fail(msg):
    print(f"\n❌ ERROR: {msg}\n")
    sys.exit(1)

def raw_read_test(device):
    try:
        subprocess.check_call(
            ["dd", f"if={device}", "of=/dev/null", "bs=512", "count=1"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except subprocess.CalledProcessError:
        return False

today = datetime.date.today().strftime("%Y%m%d")
case_number = f"{CASE_PREFIX}_{CASE_START_NUMBER:03d}_{today}"

image_base = os.path.join(IMAGE_DIR, case_number)
log_file = os.path.join(IMAGE_DIR, f"{case_number}_ewfacquire.log")

os.makedirs(IMAGE_DIR, exist_ok=True)

print("[*] Performing pre-flight checks...")

acquisition_source = EVIDENCE_DEVICE
cleanup_raw_after_acquire = False

if SOURCE_TYPE == "device":
    # 1️⃣ Device node must exist
    if not os.path.exists(EVIDENCE_DEVICE):
        fail(f"Evidence device {EVIDENCE_DEVICE} not found.")

    # 2️⃣ diskutil must recognize the disk
    disk_device = EVIDENCE_DEVICE.replace("/dev/r", "/dev/")

    try:
        info = subprocess.check_output(
            ["diskutil", "info", disk_device],
            text=True
        )
    except subprocess.CalledProcessError:
        fail("diskutil could not read device info.")

    # 3️⃣ Disk must NOT be mounted
    if "Mounted: Yes" in info:
        fail("Evidence device is mounted. Unmount before acquisition.")

    # 4️⃣ RAW READ PROBE (CRITICAL)
    print("[*] Verifying raw read access...")

    if not raw_read_test(EVIDENCE_DEVICE):
        fail("Evidence device is not readable (not connected or not configured).")

    # 5️⃣ Disk size (informational only)
    size_gb = None

    for line in info.splitlines():
        if "Disk Size" in line:
            if "Bytes" in line:
                try:
                    bytes_part = line.split("Bytes")[0].split("(")[-1].strip()
                    size_bytes = int(bytes_part)
                    size_gb = size_bytes / (1024 ** 3)
                except Exception:
                    pass

            if size_gb is None:
                try:
                    gb_part = line.split(":")[1].strip().split(" ")[0]
                    size_gb = float(gb_part)
                except Exception:
                    pass
            break

    if size_gb is not None:
        print(f"[+] Evidence device detected: {size_gb:.2f} GB (unmounted)")
    else:
        print("[!] Warning: Could not parse disk size (continuing anyway)")
elif SOURCE_TYPE == "vmdk":
    if not VMDK_PATH.strip():
        fail("VMDK_PATH is required when SOURCE_TYPE is 'vmdk'.")
    if not os.path.isabs(VMDK_PATH):
        fail("VMDK_PATH must be an absolute path.")
    if not os.path.exists(VMDK_PATH):
        fail(f"VMDK source file {VMDK_PATH} not found.")
    if shutil.which("qemu-img") is None:
        fail("qemu-img not found. Install with: brew install qemu")

    vmdk_raw_output = os.path.join(IMAGE_DIR, f"{case_number}_vmdk_converted.raw")
    print(f"[*] Converting VMDK to RAW: {VMDK_PATH} -> {vmdk_raw_output}")
    try:
        subprocess.run(
            ["qemu-img", "convert", "-p", "-f", "vmdk", "-O", "raw", VMDK_PATH, vmdk_raw_output],
            check=True
        )
    except subprocess.CalledProcessError as exc:
        fail(f"VMDK to RAW conversion failed (exit code {exc.returncode}).")
    acquisition_source = vmdk_raw_output
    cleanup_raw_after_acquire = True
else:
    fail("SOURCE_TYPE must be 'device' or 'vmdk'.")

# =========================
# START ACQUISITION
# =========================

print(f"\n[+] Starting forensic acquisition for {case_number}\n")

child = pexpect.spawn(
    "ewfacquire",
    [acquisition_source],
    encoding="utf-8",
    timeout=None
)

child.logfile_read = sys.stdout
child.logfile = open(log_file, "w")

def expect_and_send(prompt, response):
    child.expect(prompt)
    child.sendline(response)

# =========================
# ALL REQUIRED INPUTS
# =========================

expect_and_send("Image path and filename", image_base)
expect_and_send("Case number", case_number)
expect_and_send("Description", DESCRIPTION)
expect_and_send("Evidence number", EVIDENCE_NUMBER)
expect_and_send("Examiner name", EXAMINER_NAME)
expect_and_send("Notes", NOTES)

expect_and_send("Media type", MEDIA_TYPE)
expect_and_send("Media characteristics", MEDIA_CHARACTERISTICS)

expect_and_send("Use EWF file format", EWF_FORMAT)
expect_and_send("Compression method", COMPRESSION_METHOD)
expect_and_send("Compression level", COMPRESSION_LEVEL)

expect_and_send("Start to acquire at offset", START_OFFSET)
expect_and_send("The number of bytes to acquire", BYTES_TO_ACQUIRE)

expect_and_send("Evidence segment file size", SEGMENT_SIZE)
expect_and_send("The number of bytes per sector", BYTES_PER_SECTOR)
expect_and_send("The number of sectors to read at once", SECTORS_AT_ONCE)
expect_and_send("The number of sectors to be used as error granularity", ERROR_GRANULARITY)
expect_and_send("The number of retries", RETRIES)
expect_and_send("Wipe sectors on read error", WIPE_ON_ERROR)

expect_and_send("Continue acquiry", "yes")

# =========================
# LIVE PROGRESS + HEARTBEAT
# =========================

last_output = time.time()

while True:
    try:
        line = child.readline()
        if line:
            print(line, end="")
            last_output = time.time()
        else:
            time.sleep(5)

        if time.time() - last_output > 60:
            print("[*] Acquisition in progress… still working.")
            last_output = time.time()

    except pexpect.EOF:
        break

child.wait()

print("\n[+] Acquisition completed. Starting hash verification...\n")

# =========================
# HASH VERIFICATION
# =========================

verify = pexpect.spawn(
    f"ewfverify {image_base}.E01",
    encoding="utf-8",
    timeout=None
)

verify.logfile_read = sys.stdout
verify_output = []

while True:
    try:
        line = verify.readline()
        if not line:
            break
        verify_output.append(line)
    except pexpect.EOF:
        break

verify.wait()

# =========================
# VERIFICATION RESULT
# =========================

verified = any(
    "verified" in line.lower() and "failed" not in line.lower()
    for line in verify_output
)

print("\n==============================")
if verified:
    print("✅ HASH VERIFIED")
    print("Evidence integrity confirmed.")
else:
    print("❌ HASH NOT VERIFIED")
    print("DO NOT USE THIS IMAGE.")
print("==============================\n")

if verified and cleanup_raw_after_acquire and os.path.exists(acquisition_source):
    try:
        os.remove(acquisition_source)
        print(f"[*] Removed intermediate RAW file: {acquisition_source}")
    except OSError:
        print(f"[!] Warning: Could not remove intermediate RAW file: {acquisition_source}")
elif not verified and cleanup_raw_after_acquire and os.path.exists(acquisition_source):
    print(f"[!] Intermediate RAW kept for troubleshooting: {acquisition_source}")
