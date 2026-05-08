"""
Formula OCR → LaTeX / MathML
Paste a screenshot containing math formulas → get ready-to-copy LaTeX or MathML.
MathML can be pasted directly into Word/PowerPoint as a native equation.

Usage:
    python formula_ocr.py

Requirements:
    pip install pix2tex pillow latex2mathml
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageGrab
import threading
import sys

try:
    import latex2mathml.converter as _lmml
    _HAS_MATHML = True
except ImportError:
    _HAS_MATHML = False


# ── Colour palette ──────────────────────────────────────────────────────────
BG       = "#0f1117"
PANEL    = "#1a1d27"
BORDER   = "#2a2d3e"
ACCENT   = "#7c6af7"
ACCENT2  = "#a78bfa"
SUCCESS  = "#4ade80"
TEXT     = "#e2e8f0"
SUBTEXT  = "#94a3b8"
MONO     = ("Consolas", 12)
SANS     = ("Segoe UI", 10)
SANS_SM  = ("Segoe UI", 9)
TITLE    = ("Segoe UI Semibold", 11)


class FormulaOCRApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.model = None
        self.current_image: Image.Image | None = None
        self._setup_window()
        self._build_ui()
        self._load_model_async()
        # Global paste shortcut
        self.root.bind("<Control-v>", lambda _: self.paste_clipboard())
        self.root.bind("<Control-V>", lambda _: self.paste_clipboard())

    # ── Window ───────────────────────────────────────────────────────────────
    def _setup_window(self):
        self.root.title("Formula OCR  →  LaTeX")
        self.root.geometry("780x680")
        self.root.minsize(600, 500)
        self.root.configure(bg=BG)
        try:
            self.root.iconbitmap(default="")  # blank icon fallback
        except Exception:
            pass

    # ── UI ───────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Header ──
        hdr = tk.Frame(self.root, bg=BG, pady=18)
        hdr.pack(fill="x", padx=28)

        tk.Label(hdr, text="∫  Formula OCR", font=("Segoe UI Semibold", 16),
                 bg=BG, fg=ACCENT2).pack(side="left")

        self.status_var = tk.StringVar(value="⏳  Loading model…")
        tk.Label(hdr, textvariable=self.status_var, font=SANS_SM,
                 bg=BG, fg=SUBTEXT).pack(side="right", padx=4)

        # Output mode toggle
        self.mode_var = tk.StringVar(value="mathml")
        mode_frame = tk.Frame(hdr, bg=BG)
        mode_frame.pack(side="right", padx=12)
        for label, val in [("LaTeX", "latex"), ("MathML", "mathml")]:
            tk.Radiobutton(mode_frame, text=label, variable=self.mode_var,
                           value=val, bg=BG, fg=SUBTEXT,
                           selectcolor=BG, activebackground=BG,
                           activeforeground=ACCENT2,
                           font=SANS_SM).pack(side="left", padx=4)

        # ── Divider ──
        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x", padx=28)

        # ── Image drop zone ──
        self.drop_frame = tk.Frame(self.root, bg=PANEL, bd=0,
                                   highlightthickness=2,
                                   highlightbackground=BORDER,
                                   highlightcolor=ACCENT)
        self.drop_frame.pack(fill="x", padx=28, pady=(20, 0))

        self.image_label = tk.Label(
            self.drop_frame,
            text="📋  Ctrl+V  to paste screenshot  —  or  Open File  below",
            font=SANS, bg=PANEL, fg=SUBTEXT,
            pady=32, padx=20, cursor="hand2"
        )
        self.image_label.pack(fill="both")
        self.image_label.bind("<Button-1>", lambda _: self.open_file())

        # ── Buttons ──
        btn_row = tk.Frame(self.root, bg=BG)
        btn_row.pack(fill="x", padx=28, pady=12)

        self._btn(btn_row, "📂  Open File",      self.open_file,       PANEL,   TEXT   ).pack(side="left", padx=(0, 8))
        self._btn(btn_row, "📋  Paste (Ctrl+V)",  self.paste_clipboard, PANEL,   TEXT   ).pack(side="left", padx=(0, 8))
        self._btn(btn_row, "▶  Recognise",        self.recognise,       ACCENT,  "white").pack(side="left", padx=(0, 8))

        # ── Output ──
        tk.Label(self.root, text="LaTeX Output", font=TITLE,
                 bg=BG, fg=TEXT).pack(anchor="w", padx=28, pady=(8, 4))

        out_frame = tk.Frame(self.root, bg=PANEL, highlightthickness=1,
                             highlightbackground=BORDER)
        out_frame.pack(fill="both", expand=True, padx=28, pady=(0, 4))

        self.output_text = tk.Text(
            out_frame, font=MONO, bg=PANEL, fg=ACCENT2,
            insertbackground=ACCENT2, relief="flat",
            wrap="word", padx=14, pady=12,
            selectbackground=ACCENT, selectforeground="white"
        )
        self.output_text.pack(side="left", fill="both", expand=True)

        sb = ttk.Scrollbar(out_frame, command=self.output_text.yview)
        sb.pack(side="right", fill="y")
        self.output_text.config(yscrollcommand=sb.set)

        # ── Copy button + hint ──
        foot = tk.Frame(self.root, bg=BG)
        foot.pack(fill="x", padx=28, pady=(4, 18))

        self._btn(foot, "⎘  Copy Output", self.copy_latex, SUCCESS, "#0f1117",
                  font=("Segoe UI Semibold", 10)).pack(side="left")

        tk.Label(foot,
                 text="Word/PowerPoint: Insert → Equation → paste MathML directly",
                 font=SANS_SM, bg=BG, fg=SUBTEXT).pack(side="right")

    def _btn(self, parent, text, cmd, bg, fg, font=SANS, pady=7, padx=16):
        return tk.Button(
            parent, text=text, command=cmd,
            bg=bg, fg=fg, activebackground=ACCENT, activeforeground="white",
            font=font, relief="flat", cursor="hand2",
            pady=pady, padx=padx, bd=0
        )

    # ── Model loading ─────────────────────────────────────────────────────────
    def _load_model_async(self):
        def _load():
            try:
                from pix2tex.cli import LatexOCR  # type: ignore
                self.model = LatexOCR()
                self.root.after(0, lambda: self.status_var.set("✓  Model ready"))
            except ImportError:
                self.root.after(0, lambda: self.status_var.set(
                    "✗  pix2tex not found — run: pip install pix2tex"))
            except Exception as e:
                self.root.after(0, lambda: self.status_var.set(f"✗  {e}"))

        threading.Thread(target=_load, daemon=True).start()

    # ── Image input ───────────────────────────────────────────────────────────
    def paste_clipboard(self):
        try:
            img = ImageGrab.grabclipboard()
        except Exception as e:
            messagebox.showerror("Clipboard Error", str(e))
            return
        if img is None:
            messagebox.showwarning("Clipboard", "No image found in clipboard.\nTake a screenshot first.")
            return
        if isinstance(img, list):          # sometimes returns file paths
            try:
                img = Image.open(img[0])
            except Exception:
                messagebox.showwarning("Clipboard", "Could not open clipboard content as image.")
                return
        self._set_image(img)

    def open_file(self):
        path = filedialog.askopenfilename(
            title="Open formula image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.tiff *.gif"), ("All files", "*.*")]
        )
        if path:
            try:
                self._set_image(Image.open(path))
            except Exception as e:
                messagebox.showerror("Open Error", str(e))

    def _set_image(self, img: Image.Image):
        self.current_image = img.convert("RGB")
        # Thumbnail preview
        thumb = self.current_image.copy()
        thumb.thumbnail((740, 220), Image.LANCZOS)
        self._photo = ImageTk.PhotoImage(thumb)
        self.image_label.config(image=self._photo, text="", pady=0)
        # Auto-recognise
        self.recognise()

    # ── Recognition ───────────────────────────────────────────────────────────
    def recognise(self):
        if self.current_image is None:
            messagebox.showinfo("No Image", "Paste or open an image first.")
            return
        if self.model is None:
            messagebox.showinfo("Loading", "Model is still loading, please wait a moment.")
            return
        self.status_var.set("⏳  Recognising…")
        self.output_text.delete("1.0", tk.END)

        img_snap = self.current_image.copy()

        def _run():
            try:
                result: str = self.model(img_snap)
                self.root.after(0, lambda: self._show_result(result))
            except Exception as e:
                self.root.after(0, lambda: self.status_var.set(f"✗  Error: {e}"))

        threading.Thread(target=_run, daemon=True).start()

    def _show_result(self, latex: str):
        latex = latex.strip()
        mode = self.mode_var.get()

        if mode == "mathml":
            if not _HAS_MATHML:
                self.status_var.set("✗  latex2mathml not installed — run: pip install latex2mathml")
                output = latex
            else:
                try:
                    output = _lmml.convert(latex, display="block")
                    self.status_var.set("✓  Done  (MathML)")
                except Exception as e:
                    output = f"<!-- Conversion error: {e} -->\n{latex}"
                    self.status_var.set(f"✗  MathML conversion failed: {e}")
        else:
            output = latex
            self.status_var.set("✓  Done  (LaTeX)")

        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, output)
        self.copy_latex(silent=True)   # auto-copy

    # ── Copy ──────────────────────────────────────────────────────────────────
    def copy_latex(self, silent=False):
        latex = self.output_text.get("1.0", tk.END).strip()
        if not latex:
            if not silent:
                messagebox.showinfo("Empty", "Nothing to copy yet.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(latex)
        self.root.update()   # keep clipboard after app closes
        self.status_var.set("⎘  Copied to clipboard!")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()

    # Apply ttk scrollbar theme
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("Vertical.TScrollbar",
                    background=BORDER, troughcolor=PANEL,
                    arrowcolor=SUBTEXT, bordercolor=PANEL,
                    lightcolor=PANEL, darkcolor=PANEL)

    app = FormulaOCRApp(root)
    root.mainloop()
