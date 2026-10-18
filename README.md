# 🌌 AetherOS Mobile

> **A premium, fluid mobile operating system shell with glassmorphism, clean squircle icons, dynamic island, and cloud CI/CD builds.**

[![Build AetherOS Bootable Image](https://github.com/RD7890/AetherOS-Mobile/actions/workflows/build-os.yml/badge.svg)](https://github.com/RD7890/AetherOS-Mobile/actions/workflows/build-os.yml)
[![Release](https://img.shields.io/github/v/release/RD7890/AetherOS-Mobile?color=00F0FF&label=Release)](https://github.com/RD7890/AetherOS-Mobile/releases)
[![Platform](https://img.shields.io/badge/Platform-ARM64%20%7C%20x86__64-7C4DFF)](https://github.com/RD7890/AetherOS-Mobile)

---

## ✨ Features

- **🏝️ Dynamic Island:** Contextual top pill with live audio waveform visualizers, active call timers, and battery notifications.
- **🎨 Glassmorphic Squircle Icons:** Clean, modern vector icons for Phone, Messages, Browser, Files, Music, Settings, Terminal, Weather, Clock, Gallery, Notes, and Calculator.
- **⚡ 60 FPS Spring Physics:** Smooth cubic-bezier transitions when launching, minimizing, or switching apps.
- **🎛️ Pull-Down Control Center:** Fast access to Wi-Fi, Bluetooth, Dark Mode, Flashlight, Brightness, and Volume sliders.
- **💻 Embedded Terminal App:** Directly execute bash and system commands inside a matrix-styled OLED terminal.
- **☁️ Zero Local Compilation:** GitHub Actions builds the bootable hybrid ISO entirely in the cloud and automatically publishes releases.

---

## 📱 Running on Phone via Termux:X11

You can run AetherOS directly on your Android phone using **Termux** and **Termux:X11** with full direct touch support:

```bash
# Clone the repository
git clone https://github.com/RD7890/AetherOS-Mobile.git
cd AetherOS-Mobile

# Launch AetherOS
./scripts/run_local.sh
```

Switch to your **Termux:X11** app to interact with the mobile interface!

---

## 🛠️ Architecture

```
AetherOS-Mobile/
├── .github/workflows/
│   └── build-os.yml         # Cloud builder for bootable hybrid ISO releases
├── src/
│   └── aether_os.py         # Master 60fps mobile shell & window compositor
├── scripts/
│   └── run_local.sh         # Termux:X11 direct launch script
└── README.md
```

---

## 🚀 Cloud Build (GitHub Actions)

Every push to `main` automatically triggers GitHub Actions to:
1. Spin up a multi-core cloud runner.
2. Package the kernel, initramfs, and AetherOS environment.
3. Generate `AetherOS-Mobile-x86_64.iso`.
4. Publish a downloadable release artifact ready for QEMU or bare-metal booting.
