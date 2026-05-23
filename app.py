#!/usr/bin/env python3
"""
Channel DL — Tu Tiên Downloader v1.0
Pháp bảo thu phục video toàn bộ động phủ YouTube / TikTok.
"""

import os, re, sys, json, threading, queue
from pathlib import Path
from datetime import datetime
from tkinter import filedialog

import customtkinter as ctk

# ─── CẤU HÌNH ───
APP_NAME     = "🎬 Thâu Hương Pháp Bảo"
APP_VERSION  = "1.0"
APP_GEOMETRY = "780x680"
THEME        = "dark"
COLOR_THEME  = "green"
DEFAULT_OUTPUT = str(Path.home() / "Downloads" / "thau-huong")

ctk.set_appearance_mode(THEME)
ctk.set_default_color_theme(COLOR_THEME)

def get_ytdlp_cmd():
    return ['yt-dlp']

def _detect_platform(url):
    if 'youtube.com' in url.lower() or 'youtu.be' in url.lower():
        return '📺 YouTube'
    elif 'tiktok.com' in url.lower():
        return '🎵 TikTok'
    return None

class ChannelDLApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry(APP_GEOMETRY)
        self.minsize(680, 580)
        self.running = False
        self.after_id = None
        self.log_queue = queue.Queue()
        self.video_list = []  # danh sách video đã thám thính

        self._build_ui()
        self._khoi_dong_log()
        self._ghi_log("Pháp bảo sẵn sàng 🐲", "ok")

    # ─── GIAO DIỆN ───
    def _build_ui(self):
        main = ctk.CTkFrame(self)
        main.pack(fill="both", expand=True, padx=14, pady=14)

        ctk.CTkLabel(main, text=f"{APP_NAME} v{APP_VERSION}",
                      font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(0, 6))
        ctk.CTkLabel(main, text="Dán link kênh → Thám Thính → Xác nhận tải toàn bộ video chất lượng cao nhất",
                      font=ctk.CTkFont(size=13)).pack(pady=(0, 14))

        # ── URL ──
        uf = ctk.CTkFrame(main)
        uf.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(uf, text="🗺️ Link Kênh",
                      font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 4))
        row = ctk.CTkFrame(uf, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=(0, 10))
        self.url_var = ctk.StringVar()
        self.url_entry = ctk.CTkEntry(row, textvariable=self.url_var,
                                       placeholder_text="https://www.youtube.com/@tenkenh")
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(row, text="📋", width=38, command=self._dan).pack(side="left", padx=(0, 4))
        ctk.CTkButton(row, text="✕", width=38, fg_color="gray30",
                       command=lambda: self.url_var.set("")).pack(side="left")

        # ── Kho chứa ──
        of = ctk.CTkFrame(main)
        of.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(of, text="📂  Kho Chứa",
                      font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 6))
        g = ctk.CTkFrame(of, fg_color="transparent")
        g.pack(fill="x", padx=10, pady=(0, 10))
        self.output_var = ctk.StringVar(value=DEFAULT_OUTPUT)
        self.output_entry = ctk.CTkEntry(g, textvariable=self.output_var)
        self.output_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(g, text="📂 Chọn Thư Mục", width=100, command=self._chi_duong).pack(side="left")

        # ── Nút ──
        bf = ctk.CTkFrame(main)
        bf.pack(fill="x", pady=(0, 10))
        self.analyze_btn = ctk.CTkButton(bf, text="🔍 Thám Thính", command=self._tham_thinh,
                                          width=140, fg_color="#2B5E9E")
        self.analyze_btn.pack(side="left", padx=(0, 8))
        self.download_btn = ctk.CTkButton(bf, text="⬇️  Xác Nhận Tải Tất Cả", command=self._bat_dau_thu,
                                          width=180, state="disabled")
        self.download_btn.pack(side="left", padx=(0, 8))
        self.stop_btn = ctk.CTkButton(bf, text="■ Dừng", width=80, fg_color="#B33",
                                       state="disabled", command=self._thu_cong)
        self.stop_btn.pack(side="left")

        # ── Tiến độ ──
        pf = ctk.CTkFrame(main)
        pf.pack(fill="x", pady=(0, 10))
        self.progress_bar = ctk.CTkProgressBar(pf)
        self.progress_bar.pack(fill="x", padx=10, pady=(10, 2))
        self.progress_bar.set(0)
        self.prog_label = ctk.CTkLabel(pf, text="⏳ Chờ lệnh...", font=ctk.CTkFont(size=12))
        self.prog_label.pack(anchor="w", padx=10, pady=(0, 10))

        # ── Log ──
        ctk.CTkLabel(main, text="📜 Nhật Ký:", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w")
        self.log_text = ctk.CTkTextbox(main, height=200, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_text.pack(fill="both", expand=True, pady=(4, 0))

        self.status_var = ctk.StringVar(value="Sẵn sàng 🐲")
        self.status_bar = ctk.CTkLabel(self, textvariable=self.status_var, font=ctk.CTkFont(size=11),
                                        anchor="w", fg_color="gray15")
        self.status_bar.pack(side="bottom", fill="x")

    # ─── THAO TÁC ───
    def _dan(self):
        try:
            t = self.clipboard_get()
            if t: self.url_var.set(t.strip())
        except: pass

    def _chi_duong(self):
        d = filedialog.askdirectory()
        if d: self.output_var.set(d)

    def _ghi_log(self, msg, level="info"):
        p = {"info":"◆","ok":"✓","warn":"⚠","err":"✗","title":"━"}.get(level," ")
        self.log_queue.put(f"[{datetime.now().strftime('%H:%M:%S')}] {p} {msg}")

    def _ghi_log_truc_tiep(self, msg):
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.update_idletasks()

    def _khoi_dong_log(self):
        def poll():
            while True:
                try: self._ghi_log_truc_tiep(self.log_queue.get_nowait())
                except queue.Empty: break
            self.after_id = self.after(100, poll)
        poll()

    def _set_nut(self, state):
        if state == "idle":
            self.analyze_btn.configure(state="normal")
            self.download_btn.configure(state="disabled")
            self.stop_btn.configure(state="disabled")
        elif state == "working":
            self.analyze_btn.configure(state="disabled")
            self.download_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
        elif state == "ready":
            self.analyze_btn.configure(state="normal")
            self.download_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")

    def _set_tien_do(self, pct, text=""):
        self.progress_bar.set(pct / 100)
        self.prog_label.configure(text=text)

    # ─── THÁM THÍNH ───
    def _tham_thinh(self):
        url = self.url_var.get().strip()
        if not url:
            self._ghi_log("Nhập link kênh trước!", "warn"); return

        tm = _detect_platform(url)
        self._set_nut("working")
        self._set_tien_do(0, "🔍 Đang thám thính...")
        self._ghi_log("━━━ THÁM THÍNH ━━━", "title")
        self._ghi_log(f"📍 {url}")
        if tm: self._ghi_log(f"🏯 {tm}", "ok")

        self.video_list = []

        def run():
            try:
                import yt_dlp
            except ImportError:
                self._ghi_log("yt-dlp chưa được cài, đang tải...", "warn")
                import subprocess, sys
                subprocess.run([sys.executable, '-m', 'pip', 'install', 'yt-dlp'], capture_output=True)
                import yt_dlp
            
            try:
                ydl_opts = {
                    'quiet': True,
                    'extract_flat': 'in_playlist',
                    'ignoreerrors': True,
                    'playlistend': None,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    try:
                        info = ydl.extract_info(url, download=False)
                    except Exception as e:
                        self._ghi_log(f"Lỗi: {e}", "err")
                        self.after(0, lambda: self._set_nut("idle"))
                        self.after(0, lambda: self._set_tien_do(0, "❌ Thám thính thất bại"))
                        return

                entries = info.get('entries', [info]) if info else []
                entries = [e for e in entries if e and not e.get('is_live', False) and not e.get('live_status', '') == 'is_live']
                channel = info.get('channel', info.get('uploader', 'Vô Danh'))
                total = len(entries)

                self.video_list = entries
                self._ghi_log(f"🏛️ Chủ: {channel}", "ok")
                self._ghi_log(f"💎 Tổng cộng: {total} video (đã lọc livestream)", "ok")
                self._ghi_log(f"📋 Danh sách {total} video:", "info")

                for i, v in enumerate(entries, 1):
                    t = v.get("title","?")
                    d = v.get("duration",0)
                    if d:
                        m,s = divmod(d,60); h=0
                        if m>=60: h,m=divmod(m,60)
                        ts = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
                        self._ghi_log(f"  {i:3d}. {t}  [{ts}]")
                    else:
                        self._ghi_log(f"  {i:3d}. {t}")

                self.after(0, lambda: self._set_nut("ready"))
                self.after(0, lambda: self._set_tien_do(100, f"✅ {len(entries)}/{total} video — Nhấn Xác Nhận để tải"))
                self.after(0, lambda: self.status_var.set(f"✅ {len(entries)} video — sẵn sàng tải"))

            except Exception as e:
                self._ghi_log(f"Lỗi: {e}", "err")
                self.after(0, lambda: self._set_nut("idle"))
                self.after(0, lambda: self._set_tien_do(0, "❌ Thám thính thất bại"))

        threading.Thread(target=run, daemon=True).start()

    # ─── THU PHỤC (TẢI ALL) ───
    def _bat_dau_thu(self):
        url = self.url_var.get().strip()
        output = self.output_var.get().strip() or DEFAULT_OUTPUT
        Path(output).mkdir(parents=True, exist_ok=True)

        self.running = True
        self._set_nut("working")
        self._set_tien_do(5, "🚀 Đang khởi động pháp bảo...")
        self._ghi_log("━━━ THU PHỤC ━━━", "title")
        self._ghi_log(f"📍 {url}")
        self._ghi_log(f"📂 {output}")

        def run():
            try:
                import yt_dlp
            except ImportError:
                self._ghi_log("yt-dlp chưa được cài, đang tải...", "warn")
                import subprocess, sys
                subprocess.run([sys.executable, '-m', 'pip', 'install', 'yt-dlp'], capture_output=True)
                import yt_dlp
            
            try:
                video_dir = os.path.join(output, 'videos')
                thumb_dir = os.path.join(output, 'thumbs')
                Path(video_dir).mkdir(parents=True, exist_ok=True)
                Path(thumb_dir).mkdir(parents=True, exist_ok=True)
                
                ydl_opts = {
                    'outtmpl': {'default': os.path.join(video_dir, '%(title).100s.%(ext)s'),
                                'thumbnail': os.path.join(thumb_dir, '%(title).100s.%(ext)s')},
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    'merge_output_format': 'mp4',
                    'writethumbnail': True,
                    'embedthumbnail': False,
                    'embedmetadata': True,
                    'addmetadata': True,
                    'download_archive': os.path.join(output, 'archive.txt'),
                    'ignoreerrors': True,
                    'quiet': True,
                    'progress_hooks': [self._tien_trinh],
                    'match_filter': yt_dlp.utils.match_filter_func('!is_live'),
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    # Tải avatar kênh
                    try:
                        if info and 'channel_url' in info:
                            import urllib.request
                            avatar = ydl.extract_info(info['channel_url'], download=False)
                            if avatar and 'thumbnails' in avatar:
                                av_url = avatar['thumbnails'][-1].get('url', '')
                                if av_url:
                                    urllib.request.urlretrieve(av_url, os.path.join(output, 'avatar.jpg'))
                                    self._ghi_log(f"🖼️ Avatar kênh đã lưu: avatar.jpg", "ok")
                    except Exception:
                        pass

                self.after(0, lambda: self._set_tien_do(100, "✅ Đại Công Cáo Thành!"))
                self.after(0, lambda: self._set_nut("idle"))
                self.after(0, lambda: self.status_var.set("✅ Hoàn tất!"))

            except Exception as e:
                self._ghi_log(f"Lỗi: {e}", "err")
                self.after(0, lambda: self._set_tien_do(0, "❌ Thất bại"))
                self.after(0, lambda: self._set_nut("idle"))

        threading.Thread(target=run, daemon=True).start()

    def _tien_trinh(self, d):
        if d['status'] == 'downloading':
            pct = d.get('_percent_str', '0%').replace('%','')
            try: p = float(pct)
            except: p = 0
            self.after(0, lambda: self._set_tien_do(p, f"📥 {d.get('filename','?')[:50]}... {pct}%"))
        elif d['status'] == 'finished':
            self._ghi_log(f"✅ {d.get('filename','?')}")

    def _thu_cong(self):
        self.running = False
        self._set_nut("idle")
        self._set_tien_do(0, "⏹ Đã dừng")

    # ─── THOÁT ───
    def on_closing(self):
        if self.running:
            self._thu_cong()
        if self.after_id:
            self.after_cancel(self.after_id)
        self.destroy()

if __name__ == "__main__":
    app = ChannelDLApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
