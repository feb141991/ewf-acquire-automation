ß
#!/usr/bin/env python3
import pexpect
import datetime
import os
import sys

# =========================
# USER CONFIGURATION
# =========================

EVIDENCE_DEVICE = "/dev/rdisk4"
IMAGE_DIR = "/Users/C/F_Images"

CASE_PREFIX = "CASE"
CASE_START_NUMBER = 1
EVIDENCE_NUMBER = "001"
EXAMINER_NAME = "Prince"
DESCRIPTION = "sakshi_hd"
NOTES = "testing"

SEGMENT_SIZE = "2G"
COMPRESSION_METHOD = "deflate"
COMPRESSION_LEVEL = "fast"

BYTES_PER_SECTOR = "512"
BLOCK_SIZE = "4096"
ERROR_GRANULARITY = "4096"
RETRIES = "2"
ZERO_ON_ERROR = "no"

# =========================
# AUTO-GENERATED VALUES
# =========================

today = datetime.date.today().strftime("%Y%m%d")
case_number = f"{CASE_PREFIX}_{CASE_START_NUMBER:03d}_{today}"
image_path = os.path.join(IMAGE_DIR, f"{case_number}.E01")
log_file = f"{case_number}_ewfacquire.log"

# =========================
# START ACQUISITION
# =========================

print(f"\n[+] Starting forensic acquisition for {case_number}\n")

child = pexpect.spawn(
    f"sudo ewfacquire {EVIDENCE_DEVICE}",
    encoding="utf-8",
    timeout=None
)

child.logfile = open(log_file, "w")

def expect_and_send(prompt, response):
    child.expect(prompt)
    child.sendline(response)

expect_and_send("Image path and filename:", image_path)
expect_and_send("Case number:", case_number)
expect_and_send("Description:", DESCRIPTION)
expect_and_send("Evidence number:", EVIDENCE_NUMBER)
expect_and_send("Examiner name:", EXAMINER_NAME)
expect_and_send("Notes:", NOTES)

expect_and_send("Use EWF file format", "encase6")
expect_and_send("Compression method", COMPRESSION_METHOD)
expect_and_send("Compression level", COMPRESSION_LEVEL)
expect_and_send("Start to acquire at offset", "0")
expect_and_send("Evidence segment file size", SEGMENT_SIZE)
expect_and_send("The number of bytes per sector", BYTES_PER_SECTOR)
expect_and_send("The number of sectors to read at once", BLOCK_SIZE)
expect_and_send("The number of sectors to be used as error granularity", ERROR_GRANULARITY)
expect_and_send("The number of retries when a read error occurs", RETRIES)
expect_and_send("Wipe sectors on read error", ZERO_ON_ERROR)
expect_and_send("Continue acquiry with these values", "yes")

child.wait()

print("\n[+] Acquisition completed. Starting hash verification...\n")

# =========================
# HASH VERIFICATION
# =========================

verify = pexpect.spawn(
    f"ewfverify {image_path}",
    encoding="utf-8",
    timeout=None
)

verify_output = []
verify.logfile_read = sys.stdout

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
