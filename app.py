#!/usr/bin/env python3
"""
Channel DL — Tu Tiên Downloader v1.0
Pháp bảo thu phục video toàn bộ động phủ YouTube / TikTok.
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

# ─────────────────────────── TU TIÊN CẤU HÌNH ───────────────────────────
APP_NAME     = "🎬 Thâu Hương Pháp Bảo"
APP_VERSION  = "1.0"
APP_GEOMETRY = "780x680"
THEME        = "dark"
COLOR_THEME  = "green"

DEFAULT_OUTPUT = str(Path.home() / "Downloads" / "thau-huong")

ctk.set_appearance_mode(THEME)
ctk.set_default_color_theme(COLOR_THEME)


# ─────────────────────────── LINH THÚ HỖ TRỢ ───────────────────────────
def get_ytdlp_cmd():
    """Gọi yt-dlp — linh phù vạn năng"""
    return ['yt-dlp']


def get_ffmpeg_path():
    """Tìm ffmpeg — pháp khí hợp nhất"""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        for name in ('ffmpeg.exe', 'ffmpeg'):
            path = os.path.join(sys._MEIPASS, name)
            if os.path.exists(path):
                return path
    try:
        which = subprocess.run(['which', 'ffmpeg'], capture_output=True, text=True, timeout=3)
        if which.returncode == 0 and which.stdout.strip():
            return which.stdout.strip()
    except Exception:
        pass
    if sys.platform == 'win32':
        local = os.path.join(os.path.dirname(sys.executable), 'ffmpeg.exe')
        if os.path.exists(local):
            return local
    return None


def _detect_platform(url):
    """Nhận diện tông môn từ tọa độ"""
    if 'youtube.com' in url.lower() or 'youtu.be' in url.lower():
        return 'Lưu Ảnh Các 📺'
    elif 'tiktok.com' in url.lower():
        return 'Đấu Chấm Các 🎵'
    return None


# ─────────────────────────── PHÁP BẢO CHÍNH ───────────────────────────
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

        self._xay_giao_dien()
        self._khoi_dong_log()
        self.protocol("WM_DELETE_WINDOW", self._thoat)

    # ─────────────────────────── XÂY DỰNG GIAO DIỆN ───────────────────────────
    def _xay_giao_dien(self):
        main = ctk.CTkFrame(self)
        main.pack(fill="both", expand=True, padx=14, pady=14)

        # ── Tiêu đề ──
        ctk.CTkLabel(main, text=f"{APP_NAME} v{APP_VERSION}",
                      font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(0, 6))
        ctk.CTkLabel(main, text="Chỉ cần tọa độ động phủ, pháp bảo sẽ thu phục toàn bộ video — Lưu Ảnh Các / Đấu Chấm Các",
                      font=ctk.CTkFont(size=13)).pack(pady=(0, 14))

        # ── Tọa độ ──
        uf = ctk.CTkFrame(main)
        uf.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(uf, text="🗺️ Tọa Độ Động Phủ",
                      font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 4))
        row = ctk.CTkFrame(uf, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=(0, 10))

        self.url_var = ctk.StringVar()
        self.url_entry = ctk.CTkEntry(row, textvariable=self.url_var,
                                       placeholder_text="https://www.youtube.com/@tenkenh hoặc tiktok.com/@username")
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(row, text="📋", width=38, command=self._dan).pack(side="left", padx=(0, 4))
        ctk.CTkButton(row, text="✕", width=38, fg_color="gray30", hover_color="gray20",
                       command=lambda: self.url_var.set("")).pack(side="left")

        # ── Pháp Khí ──
        of = ctk.CTkFrame(main)
        of.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(of, text="⚙️  Pháp Khí Tùy Chỉnh",
                      font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 6))

        g = ctk.CTkFrame(of, fg_color="transparent")
        g.pack(fill="x", padx=10, pady=(0, 4))

        ctk.CTkLabel(g, text="🔢 Hạn mức pháp bảo:").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=4)
        self.limit_var = ctk.StringVar(value="0")
        ctk.CTkEntry(g, textvariable=self.limit_var, width=70, placeholder_text="0 = vô hạn").grid(row=0, column=1, sticky="w", padx=(0, 20), pady=4)

        ctk.CTkLabel(g, text="📅 Từ niên đại:").grid(row=0, column=2, sticky="w", padx=(0, 6), pady=4)
        self.date_var = ctk.StringVar()
        ctk.CTkEntry(g, textvariable=self.date_var, width=120, placeholder_text="YYYYMMDD (không bắt buộc)").grid(row=0, column=3, sticky="w", pady=4)

        ctk.CTkLabel(g, text="🏛️ Kho chứa:").grid(row=1, column=0, sticky="w", padx=(0, 6), pady=4)
        self.output_var = ctk.StringVar(value=DEFAULT_OUTPUT)
        self.output_entry = ctk.CTkEntry(g, textvariable=self.output_var)
        self.output_entry.grid(row=1, column=1, columnspan=2, sticky="ew", padx=(0, 6), pady=4)
        g.columnconfigure(1, weight=1)
        ctk.CTkButton(g, text="📂 Chỉ Đường", width=80, command=self._chi_duong).grid(row=1, column=3, sticky="w", pady=4)

        # Checkbox
        cf = ctk.CTkFrame(of, fg_color="transparent")
        cf.pack(fill="x", padx=10, pady=(0, 10))

        self.archive_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(cf, text="Không thu lại video đã có (lưu ấn)", variable=self.archive_var).pack(side="left", padx=(0, 20))
        self.metadata_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(cf, text="Khắc ấn + thu nhỏ vào pháp bảo", variable=self.metadata_var).pack(side="left")

        # ── Nút lệnh ──
        bf = ctk.CTkFrame(main)
        bf.pack(fill="x", pady=(0, 10))

        self.analyze_btn = ctk.CTkButton(bf, text="🔍 Thám Thính", command=self._tham_thinh,
                                          width=140, fg_color="#2B5E9E", hover_color="#1D4A7A")
        self.analyze_btn.pack(side="left", padx=(0, 8))

        self.download_btn = ctk.CTkButton(bf, text="⬇️  Thu Phục", command=self._bat_dau_thu,
                                          width=140)
        self.download_btn.pack(side="left", padx=(0, 8))

        self.stop_btn = ctk.CTkButton(bf, text="■ Thu Công", width=80, fg_color="#B33",
                                       hover_color="#922", state="disabled", command=self._thu_cong)
        self.stop_btn.pack(side="left")

        # ── Tiến độ ──
        pf = ctk.CTkFrame(main)
        pf.pack(fill="x", pady=(0, 10))
        self.progress_bar = ctk.CTkProgressBar(pf)
        self.progress_bar.pack(fill="x", padx=10, pady=(10, 2))
        self.progress_bar.set(0)
        self.prog_label = ctk.CTkLabel(pf, text="⏳ Chờ lệnh...", font=ctk.CTkFont(size=12))
        self.prog_label.pack(anchor="w", padx=10, pady=(0, 10))

        # ── Nhật ký ──
        ctk.CTkLabel(main, text="📜 Nhật Ký Tu Luyện:", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w")
        self.log_text = ctk.CTkTextbox(main, height=180, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_text.pack(fill="both", expand=True, pady=(4, 0))

        # Thanh trạng thái
        self.status_var = ctk.StringVar(value="Pháp bảo sẵn sàng 🐲")
        self.status_bar = ctk.CTkLabel(self, textvariable=self.status_var, font=ctk.CTkFont(size=11),
                                        anchor="w", fg_color="gray15")
        self.status_bar.pack(side="bottom", fill="x", padx=0, pady=0)

    # ─────────────────────────── THAO TÁC ───────────────────────────
    def _dan(self):
        try:
            text = self.clipboard_get()
            if text:
                self.url_var.set(text.strip())
        except Exception:
            pass

    def _chi_duong(self):
        d = filedialog.askdirectory(title="Chỉ đường đến kho chứa")
        if d:
            self.output_var.set(d)

    def _ghi_log(self, msg, level="info"):
        prefix = {"info": "◆", "ok": "✓", "warn": "⚠", "err": "✗", "title": "━"}.get(level, " ")
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_queue.put(f"[{ts}] {prefix} {msg}")

    def _ghi_log_truc_tiep(self, msg):
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.update_idletasks()

    def _khoi_dong_log(self):
        def poll():
            try:
                while True:
                    self._ghi_log_truc_tiep(self.log_queue.get_nowait())
            except queue.Empty:
                pass
            self.after_id = self.after(100, poll)

    def _set_nut(self, state):
        s = {"idle": {"download": "normal", "analyze": "normal", "stop": "disabled"},
             "working": {"download": "disabled", "analyze": "disabled", "stop": "normal"}}.get(state, {})
        self.download_btn.configure(state=s.get("download", "normal"))
        self.analyze_btn.configure(state=s.get("analyze", "normal"))
        self.stop_btn.configure(state=s.get("stop", "disabled"))

    def _set_tien_do(self, pct, text=""):
        self.progress_bar.set(pct / 100.0)
        if text:
            self.prog_label.configure(text=text)
        self.update_idletasks()

    def _thoat(self):
        if self.running and not messagebox.askokcancel(
            "Đang tế luyện", "Pháp bảo đang vận hành. Thoát sẽ hủy công pháp. Tiếp tục?"
        ):
            return
        if self.running:
            self._thu_cong()
        self.quit()
        self.destroy()

    # ─────────────────────────── THÁM THÍNH ───────────────────────────
    def _tham_thinh(self):
        url = self.url_var.get().strip()
        if not url:
            self._ghi_log("Điền tọa độ động phủ trước!", "warn")
            return

        tông_môn = _detect_platform(url)
        self._set_nut("working")
        self._set_tien_do(0, "🔍 Đang thám thính...")
        self._ghi_log("━━━ Thám Thính Động Phủ ━━━", "title")
        self._ghi_log(f"🗺️ Tọa độ: {url}")
        if tông_môn:
            self._ghi_log(f"🏯 Tông môn: {tông_môn}", "ok")

        def run():
            try:
                limit_num = 5
                import yt_dlp
                ydl_opts = {
                    'quiet': True,
                    'extract_flat': True,
                    'dump_single_json': True,
                    'playlistend': limit_num,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    try:
                        info = ydl.extract_info(url, download=False)
                    except Exception as e:
                        self._ghi_log(str(e), "err")
                        self.after(0, lambda: self._set_nut("idle"))
                        self.after(0, lambda: self._set_tien_do(0, "❌ Thám thính thất bại"))
                        return
                
                entries = []
                if 'entries' in info:
                    entries = info['entries']
                else:
                    entries = [info]
                
                lines = [json.dumps(e) for e in entries if e]
                channel = info.get('channel', info.get('uploader', 'Vô Danh'))
                total = info.get('playlist_count', info.get('n_entries', len(entries)))

                if result.returncode != 0:
                    err = result.stderr.strip() or "Không thể dò la!"
                    self._ghi_log(err, "err")
                    self.after(0, lambda: self._set_nut("idle"))
                    self.after(0, lambda: self._set_tien_do(0, "❌ Thám thính thất bại"))
                    return

                lines = [l for l in result.stdout.strip().split("\n") if l]
                if not lines:
                    self._ghi_log("Động phủ trống rỗng, không có bảo vật nào!", "warn")
                    self.after(0, lambda: self._set_nut("idle"))
                    return

                first = json.loads(lines[0])
                channel = first.get("channel", first.get("uploader", "Vô Danh"))

                last = json.loads(lines[-1])
                total = last.get("playlist_count") or last.get("n_entries") or f">={len(lines)}"

                self._ghi_log(f"🏛️ Chủ động phủ: {channel}", "ok")
                self._ghi_log(f"💎 Pháp bảo: {total} cái (thám thính {len(lines)})", "ok")

                for v in entries[:10]:
                    if not v: continue
                    title = v.get("title", "Vô danh")
                    dur = v.get("duration", 0)
                    if dur:
                        m, s = divmod(dur, 60)
                        self._ghi_log(f"  ▸ {title}  [{m}:{s:02d}]")
                    else:
                        self._ghi_log(f"  ▸ {title}")

                if len(lines) > 10:
                    self._ghi_log(f"  ... và {len(lines) - 10} cái nữa")

                self.after(0, lambda: self._set_tien_do(100, f"✅ {total} pháp bảo tại {channel}"))

            except subprocess.TimeoutExpired:
                self._ghi_log("Thám thính quá lâu, động phủ có kết giới (timeout 30s)", "err")
            except Exception as e:
                self._ghi_log(f"Lỗi: {e}", "err")
            finally:
                self.after(0, lambda: self._set_nut("idle"))
                if not self.running:
                    self.after(0, lambda: self._set_tien_do(0, "⏳ Chờ lệnh..."))

        threading.Thread(target=run, daemon=True).start()

    # ─────────────────────────── THU PHỤC ───────────────────────────
    def _bat_dau_thu(self):
        url = self.url_var.get().strip()
        if not url:
            self._ghi_log("Điền tọa độ động phủ trước!", "warn")
            return

        self.running = True
        self._set_nut("working")
        self._set_tien_do(0, "🚀 Triển khai pháp bảo...")
        self.log_text.delete("0.0", "end")
        self._ghi_log("━━━ Bắt Đầu Thu Phục ━━━", "title")

        tông_môn = _detect_platform(url)
        if tông_môn:
            self._ghi_log(f"🏯 Nhắm tới: {tông_môn}", "ok")

        t = threading.Thread(target=self._thu_worker, args=(url,), daemon=True)
        t.start()

    def _thu_worker(self, url):
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

            self._ghi_log(f"🏛️ Kho chứa: {output_dir}")
            self._ghi_log(f"🔢 Hạn mức: {'Vô hạn' if limit == '0' else limit}")
            self._ghi_log(f"📦 Ấn lưu: {'BẬT (không lấy lại)' if use_archive else 'TẮT (lấy tất cả)'}")
            self.after(0, lambda: self._set_tien_do(5, "🔄 Đang khởi động pháp bảo..."))

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
                            self.after(0, lambda p=pct, t=prog: self._set_tien_do(p, t))
                            continue
                    except (ValueError, IndexError):
                        pass

                if "[download] 100%" in line:
                    video_count += 1
                    self._ghi_log(f"✅ #{video_count}: Thu phục thành công", "ok")
                    continue

                if "ERROR:" in line or "Warning:" in line:
                    self._ghi_log(line, "warn")
                    continue

                if any(line.startswith(p) for p in ("[download]", "[info]", "[youtube]", "[tiktok]")):
                    self._ghi_log(line, "info")
                    continue

            self.process.wait()

            if not self.running:
                self._ghi_log("⏹ Ta đã thu công (do ngươi ra lệnh)", "warn")
                self.after(0, lambda: self._set_tien_do(0, "⏹ Thu công"))
            else:
                self._ghi_log(f"🎉 Đại Công Cáo Thành! Thu được {video_count} pháp bảo!", "ok")
                self.after(0, lambda: self._set_tien_do(100, "✅ Đại Công Cáo Thành!"))

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
                    self._ghi_log(f"💾 Dung lượng: {total_size}", "ok")

        except Exception as e:
            self._ghi_log(f"Pháp bảo gặp sự cố: {e}", "err")
            self.after(0, lambda: self._set_tien_do(0, "❌ Thất bại"))
        finally:
            self.running = False
            self.process = None
            self.after(0, lambda: self._set_nut("idle"))

    def _thu_cong(self):
        self.running = False
        if self.process:
            try:
                self.process.terminate()
                self._ghi_log("Đang thu công...", "warn")
            except Exception:
                pass
        self._set_nut("idle")
        self._set_tien_do(0, "⏹ Đã thu công")


# ─────────────────────────── KHỞI ĐỘNG ───────────────────────────
if __name__ == "__main__":
    app = ChannelDLApp()
    app.mainloop()
