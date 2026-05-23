#!/usr/bin/env python3
"""
Channel DL GUI v1.0
Tải toàn bộ video từ kênh YouTube / TikTok với giao diện trực quan.
"""

import os
import re
import sys
import json
import subprocess
import threading
import queue
from pathlib import Path
from datetime import datetime
from tkinter import filedialog, messagebox

import customtkinter as ctk

# ─────────────────────────── CONFIG ───────────────────────────
APP_NAME     = "🎬 Channel Downloader"
APP_VERSION  = "1.0"
APP_GEOMETRY = "780x680"
THEME        = "dark"
COLOR_THEME  = "green"

DEFAULT_OUTPUT = str(Path.home() / "Downloads" / "channel-dl")

ctk.set_appearance_mode(THEME)
ctk.set_default_color_theme(COLOR_THEME)


# ─────────────────────────── HELPERS ───────────────────────────
def get_ytdlp_cmd():
    """Trả về command list để chạy yt-dlp — hoạt động cả với PyInstaller bundle"""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        ytdlp_main = os.path.join(sys._MEIPASS, 'yt_dlp', '__main__.py')
        if os.path.exists(ytdlp_main):
            return [sys.executable, ytdlp_main]
        return ['yt-dlp']
    return [sys.executable, '-m', 'yt_dlp']


def get_ffmpeg_path():
    """Tìm ffmpeg, ưu tiên bundled trong PyInstaller"""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        for name in ('ffmpeg.exe', 'ffmpeg'):
            path = os.path.join(sys._MEIPASS, name)
            if os.path.exists(path):
                return path
    # Tìm trong PATH (Linux/macOS)
    try:
        which = subprocess.run(['which', 'ffmpeg'], capture_output=True, text=True, timeout=3)
        if which.returncode == 0 and which.stdout.strip():
            return which.stdout.strip()
    except Exception:
        pass
    # Windows — kiểm tra cùng thư mục exe
    if sys.platform == 'win32':
        local = os.path.join(os.path.dirname(sys.executable), 'ffmpeg.exe')
        if os.path.exists(local):
            return local
    return None


# ─────────────────────────── MAIN APP ───────────────────────────
class ChannelDLApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry(APP_GEOMETRY)
        self.minsize(680, 580)
        self.resizable(True, True)

        self.download_thread: threading.Thread | None = None
        self.process: subprocess.Popen | None = None
        self.running = False
        self.log_queue = queue.Queue()
        self.after_id = None

        self._build_ui()
        self._start_log_consumer()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ─────────────────────────── UI BUILD ───────────────────────────
    def _build_ui(self):
        main = ctk.CTkFrame(self)
        main.pack(fill="both", expand=True, padx=14, pady=14)

        # Header
        header = ctk.CTkLabel(main, text=f"{APP_NAME} v{APP_VERSION}",
                               font=ctk.CTkFont(size=22, weight="bold"))
        header.pack(pady=(0, 6))
        ctk.CTkLabel(main, text="Tải video từ toàn bộ kênh YouTube / TikTok — chất lượng cao nhất",
                      font=ctk.CTkFont(size=13)).pack(pady=(0, 14))

        # ── URL ──
        uf = ctk.CTkFrame(main)
        uf.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(uf, text="🔗 URL Kênh", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 4))
        row = ctk.CTkFrame(uf, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=(0, 10))

        self.url_var = ctk.StringVar()
        self.url_entry = ctk.CTkEntry(row, textvariable=self.url_var,
                                       placeholder_text="https://www.youtube.com/@tenkenh hoặc https://www.tiktok.com/@username")
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(row, text="📋", width=38, command=self._paste_url).pack(side="left", padx=(0, 4))
        ctk.CTkButton(row, text="✕", width=38, fg_color="gray30", hover_color="gray20",
                       command=lambda: self.url_var.set("")).pack(side="left")

        # ── Options ──
        of = ctk.CTkFrame(main)
        of.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(of, text="⚙️  Tùy chọn", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 6))

        g = ctk.CTkFrame(of, fg_color="transparent")
        g.pack(fill="x", padx=10, pady=(0, 4))

        ctk.CTkLabel(g, text="🔢 Giới hạn video:").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=4)
        self.limit_var = ctk.StringVar(value="0")
        ctk.CTkEntry(g, textvariable=self.limit_var, width=70, placeholder_text="0 = all").grid(row=0, column=1, sticky="w", padx=(0, 20), pady=4)

        ctk.CTkLabel(g, text="📅 Từ ngày:").grid(row=0, column=2, sticky="w", padx=(0, 6), pady=4)
        self.date_var = ctk.StringVar()
        ctk.CTkEntry(g, textvariable=self.date_var, width=120, placeholder_text="YYYYMMDD (tùy chọn)").grid(row=0, column=3, sticky="w", pady=4)

        ctk.CTkLabel(g, text="📂 Lưu vào:").grid(row=1, column=0, sticky="w", padx=(0, 6), pady=4)
        self.output_var = ctk.StringVar(value=DEFAULT_OUTPUT)
        self.output_entry = ctk.CTkEntry(g, textvariable=self.output_var)
        self.output_entry.grid(row=1, column=1, columnspan=2, sticky="ew", padx=(0, 6), pady=4)
        g.columnconfigure(1, weight=1)
        ctk.CTkButton(g, text="📂 Chọn", width=80, command=self._browse_output).grid(row=1, column=3, sticky="w", pady=4)

        # Checkboxes
        cf = ctk.CTkFrame(of, fg_color="transparent")
        cf.pack(fill="x", padx=10, pady=(0, 10))

        self.archive_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(cf, text="Bỏ qua video đã tải (archive)", variable=self.archive_var).pack(side="left", padx=(0, 20))
        self.metadata_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(cf, text="Nhúng thumbnail + metadata", variable=self.metadata_var).pack(side="left")

        # ── Buttons ──
        bf = ctk.CTkFrame(main)
        bf.pack(fill="x", pady=(0, 10))

        self.analyze_btn = ctk.CTkButton(bf, text="🔍 Phân tích kênh", command=self._analyze, width=140,
                                          fg_color="#2B5E9E", hover_color="#1D4A7A")
        self.analyze_btn.pack(side="left", padx=(0, 8))

        self.download_btn = ctk.CTkButton(bf, text="⬇️  Tải xuống", command=self._start_download, width=140)
        self.download_btn.pack(side="left", padx=(0, 8))

        self.stop_btn = ctk.CTkButton(bf, text="■ Dừng", width=80, fg_color="#B33", hover_color="#922",
                                       state="disabled", command=self._stop_download)
        self.stop_btn.pack(side="left")

        # ── Progress ──
        pf = ctk.CTkFrame(main)
        pf.pack(fill="x", pady=(0, 10))
        self.progress_bar = ctk.CTkProgressBar(pf)
        self.progress_bar.pack(fill="x", padx=10, pady=(10, 2))
        self.progress_bar.set(0)
        self.prog_label = ctk.CTkLabel(pf, text="⏳ Chờ thao tác...", font=ctk.CTkFont(size=12))
        self.prog_label.pack(anchor="w", padx=10, pady=(0, 10))

        # ── Log ──
        ctk.CTkLabel(main, text="📋 Nhật ký:", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w")
        self.log_text = ctk.CTkTextbox(main, height=180, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_text.pack(fill="both", expand=True, pady=(4, 0))

        # Status bar
        self.status_var = ctk.StringVar(value="Sẵn sàng ✅")
        self.status_bar = ctk.CTkLabel(self, textvariable=self.status_var, font=ctk.CTkFont(size=11),
                                        anchor="w", fg_color="gray15")
        self.status_bar.pack(side="bottom", fill="x", padx=0, pady=0)

    # ─────────────────────────── ACTIONS ───────────────────────────
    def _paste_url(self):
        try:
            text = self.clipboard_get()
            if text:
                self.url_var.set(text.strip())
        except Exception:
            pass

    def _browse_output(self):
        d = filedialog.askdirectory(title="Chọn thư mục lưu video")
        if d:
            self.output_var.set(d)

    def _log(self, msg, level="info"):
        prefix = {"info": "◆", "ok": "✓", "warn": "⚠", "err": "✗", "title": "━"}.get(level, " ")
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_queue.put(f"[{ts}] {prefix} {msg}")

    def _log_direct(self, msg):
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.update_idletasks()

    def _start_log_consumer(self):
        def poll():
            try:
                while True:
                    self._log_direct(self.log_queue.get_nowait())
            except queue.Empty:
                pass
            self.after_id = self.after(100, poll)

    def _set_buttons(self, state):
        s = {"idle": {"download": "normal", "analyze": "normal", "stop": "disabled"},
             "working": {"download": "disabled", "analyze": "disabled", "stop": "normal"}}.get(state, {})
        self.download_btn.configure(state=s.get("download", "normal"))
        self.analyze_btn.configure(state=s.get("analyze", "normal"))
        self.stop_btn.configure(state=s.get("stop", "disabled"))

    def _set_progress(self, pct, text=""):
        self.progress_bar.set(pct / 100.0)
        if text:
            self.prog_label.configure(text=text)
        self.update_idletasks()

    def _on_close(self):
        if self.running and not messagebox.askokcancel("Đang tải", "Tiến trình đang chạy. Thoát sẽ dừng tải. Tiếp tục?"):
            return
        if self.running:
            self._stop_download()
        self.quit()
        self.destroy()

    # ─────────────────────────── ANALYZE ───────────────────────────
    def _analyze(self):
        url = self.url_var.get().strip()
        if not url:
            self._log("Nhập URL kênh trước!", "warn")
            return

        self._set_buttons("working")
        self._set_progress(0, "🔍 Đang phân tích kênh...")
        self._log("─── Phân tích kênh ───", "title")
        self._log(f"URL: {url}")

        def run():
            try:
                limit = self.limit_var.get().strip() or "0"
                limit_num = 5
                ytdlp_cmd = get_ytdlp_cmd()
                args = ytdlp_cmd + [
                    "--flat-playlist", "--dump-json",
                    "--playlist-end", str(limit_num),
                    url
                ]
                result = subprocess.run(args, capture_output=True, text=True, timeout=30)

                if result.returncode != 0:
                    err = result.stderr.strip() or "Không thể phân tích kênh"
                    self._log(err, "err")
                    self.after(0, lambda: self._set_buttons("idle"))
                    self.after(0, lambda: self._set_progress(0, "❌ Phân tích thất bại"))
                    return

                lines = [l for l in result.stdout.strip().split("\n") if l]
                if not lines:
                    self._log("Không tìm thấy video nào!", "warn")
                    self.after(0, lambda: self._set_buttons("idle"))
                    return

                first = json.loads(lines[0])
                channel = first.get("channel", first.get("uploader", "N/A"))

                total = limit if limit != "0" else "?"
                if limit == "0":
                    last = json.loads(lines[-1])
                    total = last.get("playlist_count") or last.get("n_entries") or f">={len(lines)}"

                self._log(f"📺 Kênh: {channel}", "ok")
                self._log(f"🔢 Video: {total} (xem thử {len(lines)})", "ok")

                for l in lines[:10]:
                    v = json.loads(l)
                    title = v.get("title", "?")
                    dur = v.get("duration", 0)
                    m, s = divmod(dur, 60)
                    self._log(f"  ▸ {title}  [{m}:{s:02d}]")

                if len(lines) > 10:
                    self._log(f"  ... và {len(lines) - 10} video nữa")

                self.after(0, lambda: self._set_progress(100, f"✅ Tìm thấy {total} video trên kênh {channel}"))

            except subprocess.TimeoutExpired:
                self._log("Phân tích timeout (30s)", "err")
            except Exception as e:
                self._log(f"Lỗi: {e}", "err")
            finally:
                self.after(0, lambda: self._set_buttons("idle"))
                if not self.running:
                    self.after(0, lambda: self._set_progress(0, "⏳ Chờ thao tác..."))

        threading.Thread(target=run, daemon=True).start()

    # ─────────────────────────── DOWNLOAD ───────────────────────────
    def _start_download(self):
        url = self.url_var.get().strip()
        if not url:
            self._log("Nhập URL kênh trước!", "warn")
            return

        self.running = True
        self._set_buttons("working")
        self._set_progress(0, "🚀 Đang chuẩn bị...")
        self.log_text.delete("0.0", "end")
        self._log("─── Bắt đầu tải ───", "title")

        t = threading.Thread(target=self._download_worker, args=(url,), daemon=True)
        t.start()

    def _download_worker(self, url):
        try:
            output_dir = self.output_var.get().strip() or DEFAULT_OUTPUT
            limit = self.limit_var.get().strip() or "0"
            date_after = self.date_var.get().strip()
            use_archive = self.archive_var.get()
            embed_meta = self.metadata_var.get()

            ytdlp_cmd = get_ytdlp_cmd()
            args = ytdlp_cmd + [
                "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
                "--merge-output-format", "mp4",
                "--no-overwrites", "--continue",
                "--retries", "10", "--retry-sleep", "5",
                "--progress-template", "download:%(progress._percent_str)s|%(progress._speed_str)s|%(progress._eta_str)s|%(info.title)s",
                "--newline",
                "-o", os.path.join(output_dir, "%(channel)s", "%(title)s [%(id)s].%(ext)s"),
            ]

            ffmpeg = get_ffmpeg_path()
            if ffmpeg:
                args.extend(["--ffmpeg-location", ffmpeg])

            if use_archive:
                args.extend(["--download-archive", os.path.join(output_dir, ".archive.txt")])

            if embed_meta:
                args.extend(["--write-thumbnail", "--embed-thumbnail", "--embed-metadata",
                             "--convert-thumbnails", "jpg"])

            args.extend(["--playlist-end", str(int(limit)) if limit != "0" else "-1"])

            if date_after:
                args.extend(["--dateafter", date_after])

            if "tiktok.com" in url.lower():
                args.extend(["--extractor-args", "tiktok:api_hostname=api16-normal-c-useast1a.tiktokv.com"])

            args.append(url)

            self._log(f"📂 Lưu vào: {output_dir}")
            self._log(f"🔢 Giới hạn: {'Không giới hạn' if limit == '0' else limit}")
            self._log(f"📦 Archive: {'BẬT' if use_archive else 'TẮT'}")
            self.after(0, lambda: self._set_progress(5, "🔄 Đang analyse kênh..."))

            os.makedirs(output_dir, exist_ok=True)

            self.process = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1
            )

            video_count = 0
            for line in iter(self.process.stdout.readline, ""):
                if not self.running:
                    self.process.terminate()
                    break

                line = line.strip()
                if not line:
                    continue

                if line.startswith("[download]") and "|" in line:
                    try:
                        parts = line.split("|")
                        if len(parts) >= 3:
                            pct = float(parts[0].replace("[download]", "").strip().rstrip("%"))
                            speed = parts[1].strip() if len(parts) > 1 else "?"
                            eta = parts[2].strip() if len(parts) > 2 else "?"
                            prog = f"⬇️ {pct:.1f}%  ⚡ {speed}  ⏱ {eta}"
                            self.after(0, lambda p=pct, t=prog: self._set_progress(p, t))
                            continue
                    except (ValueError, IndexError):
                        pass

                if "[download] 100%" in line:
                    video_count += 1
                    self._log(f"✅ #{video_count}: Tải xong", "ok")
                    continue

                if line.startswith("[channel]"):
                    self._log(line, "info")
                    continue

                if "ERROR:" in line or "Warning:" in line:
                    self._log(line, "warn")
                    continue

                if any(line.startswith(p) for p in ("[download]", "[info]", "[youtube]", "[tiktok]")):
                    self._log(line, "info")
                    continue

            self.process.wait()

            if not self.running:
                self._log("⏹ Đã dừng bởi người dùng", "warn")
                self.after(0, lambda: self._set_progress(0, "⏹ Đã dừng"))
            else:
                self._log(f"✅ Hoàn tất! Tổng số video: {video_count}", "ok")
                self.after(0, lambda: self._set_progress(100, "✅ Hoàn tất!"))

                if os.path.exists(output_dir):
                    if sys.platform == 'win32':
                        total_bytes = sum(
                            os.path.getsize(os.path.join(dp, f))
                            for dp, _, fn in os.walk(output_dir) for f in fn
                        )
                        if total_bytes > 1073741824:
                            total_size = f"{total_bytes / 1073741824:.1f} GB"
                        elif total_bytes > 1048576:
                            total_size = f"{total_bytes / 1048576:.1f} MB"
                        else:
                            total_size = f"{total_bytes / 1024:.1f} KB"
                    else:
                        total_size = subprocess.run(
                            ["du", "-sh", output_dir], capture_output=True, text=True
                        ).stdout.strip().split()[0]
                    self._log(f"💾 Dung lượng: {total_size}", "ok")

        except Exception as e:
            self._log(f"Lỗi: {e}", "err")
            self.after(0, lambda: self._set_progress(0, "❌ Lỗi"))
        finally:
            self.running = False
            self.process = None
            self.after(0, lambda: self._set_buttons("idle"))

    def _stop_download(self):
        self.running = False
        if self.process:
            try:
                self.process.terminate()
                self._log("Đang dừng...", "warn")
            except Exception:
                pass
        self._set_buttons("idle")
        self._set_progress(0, "⏹ Đã dừng")


# ─────────────────────────── MAIN ───────────────────────────
if __name__ == "__main__":
    app = ChannelDLApp()
    app.mainloop()
