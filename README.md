# EWF Acquire Automation Tool

Automated forensic disk acquisition and verification tool using `ewfacquire` and `ewfverify`.

## 🔍 Overview
This project automates the acquisition of physical storage devices into **E01 (EnCase6)** format on macOS/Linux systems using `libewf`.

It is designed to:
- Reduce human error
- Enforce forensic best practices
- Provide reproducible, court-defensible imaging

## ⚙️ Features
- Physical disk acquisition (`/dev/rdisk`)
- Optional VMDK input conversion to RAW on macOS (via `qemu-img`)
- E01 (EnCase6) format
- Optimized performance parameters
- Automatic case naming
- Full interaction logging
- Post-acquisition hash verification
- Clear VERIFIED / NOT VERIFIED result

## 🧰 Requirements
- macOS or Linux
- Python 3.8+
- libewf
- pexpect
- qemu (only needed when `SOURCE_TYPE = "vmdk"`)

```bash
pip install -r requirements.txt
```

## 📁 Where is the code?
- Main automation script: `ewfacquire_auto.py`
- Dependency list: `requirements.txt`

## 🧪 VMDK support (macOS)
Set the following in `ewfacquire_auto.py`:
- `SOURCE_TYPE = "vmdk"`
- `VMDK_PATH = "/absolute/path/to/source.vmdk"`

The script converts VMDK to RAW using `qemu-img`, then acquires it into E01.
