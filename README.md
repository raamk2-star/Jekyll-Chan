# Formula OCR → MathML / LaTeX

Paste a screenshot of any math formula and get **MathML or LaTeX** output ready to paste directly into Microsoft Word or PowerPoint.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue) ![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS-lightgrey) ![Offline](https://img.shields.io/badge/Runs-Offline-green)

---

## Features

- 📋 **Paste from clipboard** — snip a formula with your OS screenshot tool, Ctrl+V into the app
- 🔁 **Toggle MathML / LaTeX** output on the fly
- ⚡ **Auto-copy** — result is copied to clipboard immediately after recognition
- 🔌 **Fully offline** after first model download
- 🥰 Works on **Windows and macOS**

---

## Installation

### Windows

```bash
pip install "pix2tex[gui]" pillow latex2mathml
```

### macOS

```bash
brew install python python-tk
pip3 install "pix2tex[gui]" pillow latex2mathml
```

> **First run only** — download the model weights (~500 MB):
> ```bash
> python -c "from pix2tex.cli import LatexOCR; LatexOCR()"   # Windows
> python3 -c "from pix2tex.cli import LatexOCR; LatexOCR()"  # Mac
> ```

---

## Usage

```bash
python formula_ocr.py    # Windows
python3 formula_ocr.py   # macOS
```

1. Take a screenshot of a formula — `Win+Shift+S` (Windows) or `Cmd+Ctrl+Shift+4` (Mac)
2. Press `Ctrl+V` / `Cmd+V` in the app
3. MathML is recognised and **auto-copied** to your clipboard
4. In Word / PowerPoint: **Insert → Equation → Ctrl+V**

---

## Notes

- **macOS** requires Screen Recording permission for Terminal (`System Settings → Privacy & Security → Screen Recording`)
- Model is cached at `~/.cache/huggingface/` after first download — no internet needed afterwards
- Powered by [pix2tex](https://github.com/lukas-blecher/LaTeX-OCR) and [latex2mathml](https://github.com/roniemartinez/latex2mathml)

---
## Contact me if you need some help
- [Email](flyawaypencil480@gmail.com) for Jekyll Chan
- [LinkedIn](www.linkedin.com/in/jekyllchan) for Jekyll Chan

