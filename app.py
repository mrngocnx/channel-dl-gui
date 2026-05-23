import os, re, sys, json, threading, queue, subprocess, urllib.request
from pathlib import Path
from datetime import datetime
from tkinter import filedialog

import customtkinter as ctk

APP_NAME     = "🎬 Thâu Hương Pháp Bảo"
APP_VERSION  = "2.7"
APP_GEOMETRY = "780x680"
THEME        = "dark"
COLOR_THEME  = "green"
DEFAULT_OUTPUT = str(Path.home() / "Downloads" / "thau-huong")

ctk.set_appearance_mode(THEME)
ctk.set_default_color_theme(COLOR_THEME)

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
        try:
            icon_path = os.path.join(getattr(sys, '_MEIPASS', '.'), 'icon.ico')
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except: pass
        self.running = False
        self.paused = False
        self.after_id = None
        self.log_queue = queue.Queue()
        self.video_list = []
        self.ytdlp_process = None
        self._build_ui()
        self._khoi_dong_log()
        self._ghi_log("Pháp bảo sẵn sàng 🐲", "ok")

    def _build_ui(self):
        main = ctk.CTkFrame(self)
        main.pack(fill="both", expand=True, padx=14, pady=14)

        ctk.CTkLabel(main, text=f"{APP_NAME} v{APP_VERSION} — By Ngọc NX",
                      font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(0, 6))
        ctk.CTkLabel(main, text="Dán link kênh → Thám Thính → Xác Nhận tải toàn bộ video",
                      font=ctk.CTkFont(size=13)).pack(pady=(0, 14))

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

        bf = ctk.CTkFrame(main)
        bf.pack(fill="x", pady=(0, 10))
        self.analyze_btn = ctk.CTkButton(bf, text="🔍 Thám Thính", command=self._tham_thinh,
                                          width=130, fg_color="#2B5E9E")
        self.analyze_btn.pack(side="left", padx=(0, 6))
        self.download_btn = ctk.CTkButton(bf, text="⬇️  Tải Tất Cả", command=self._bat_dau_tai,
                                          width=130)
        self.download_btn.pack(side="left", padx=(0, 6))
        self.pause_btn = ctk.CTkButton(bf, text="⏸ Tạm Dừng", command=self._tam_dung,
                                        width=100, fg_color="#E67E22", state="disabled")
        self.pause_btn.pack(side="left", padx=(0, 6))
        self.resume_btn = ctk.CTkButton(bf, text="▶ Tiếp Tục", command=self._tiep_tuc,
                                         width=100, fg_color="#27AE60", state="disabled")
        self.resume_btn.pack(side="left", padx=(0, 6))
        self.stop_btn = ctk.CTkButton(bf, text="⏹ Dừng", command=self._dung_tai,
                                       width=80, fg_color="#B33", state="disabled")
        self.stop_btn.pack(side="left")

        pf = ctk.CTkFrame(main)
        pf.pack(fill="x", pady=(0, 10))
        self.progress_bar = ctk.CTkProgressBar(pf)
        self.progress_bar.pack(fill="x", padx=10, pady=(10, 2))
        self.progress_bar.set(0)
        self.prog_label = ctk.CTkLabel(pf, text="⏳ Chờ lệnh...", font=ctk.CTkFont(size=12))
        self.prog_label.pack(anchor="w", padx=10, pady=(0, 10))

        log_frame = ctk.CTkFrame(main)
        log_frame.pack(fill="both", expand=True, pady=(4, 0))
        log_header = ctk.CTkFrame(log_frame, fg_color="transparent", height=30)
        log_header.pack(fill="x")
        ctk.CTkLabel(log_header, text="📜 Nhật Ký:", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        ctk.CTkButton(log_header, text="🗑️ Xóa", width=60, height=22, font=ctk.CTkFont(size=10),
                       command=self._xoa_nhat_ky).pack(side="right", padx=(0, 4))
        self.log_text = ctk.CTkTextbox(log_frame, height=180, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_text.pack(fill="both", expand=True, pady=(4, 0))
        self.log_text.bind("<Key>", lambda e: "break")

        self.status_var = ctk.StringVar(value="Sẵn sàng 🐲")
        self.status_bar = ctk.CTkLabel(self, textvariable=self.status_var, font=ctk.CTkFont(size=11),
                                        anchor="w", fg_color="gray15")
        self.status_bar.pack(side="bottom", fill="x")

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

    def _xoa_nhat_ky(self):
        self.log_text.delete("1.0", "end")
        self._ghi_log("📋 Nhật ký đã xóa", "info")

    def _set_ui_state(self, state):
        """idle, ready, working, paused"""
        self.analyze_btn.configure(state="normal" if state in ("idle","ready") else "disabled")
        self.download_btn.configure(state="normal" if state == "ready" else "disabled")
        self.pause_btn.configure(state="normal" if state == "working" else "disabled")
        self.resume_btn.configure(state="normal" if state == "paused" else "disabled")
        self.stop_btn.configure(state="normal" if state in ("working","paused") else "disabled")

    def _set_tien_do(self, pct, text=""):
        self.progress_bar.set(pct / 100)
        self.prog_label.configure(text=text)

    # ─── THÁM THÍNH ───
    def _tham_thinh(self):
        url = self.url_var.get().strip()
        if not url:
            self._ghi_log("Nhập link kênh trước!", "warn"); return
        tm = _detect_platform(url)
        self._set_ui_state("working")
        self._set_tien_do(0, "🔍 Đang thám thính...")
        self._ghi_log("━━━ THÁM THÍNH ━━━", "title")
        self._ghi_log(f"📍 {url}")
        if tm: self._ghi_log(f"🏯 {tm}", "ok")
        self.video_list = []

        def run():
            try:
                import yt_dlp
            except ImportError:
                self._ghi_log("Đang cài yt-dlp...", "warn")
                subprocess.run([sys.executable, '-m', 'pip', 'install', 'yt-dlp'], capture_output=True)
                import yt_dlp
            try:
                ydl_opts = {'quiet': True, 'extract_flat': 'in_playlist', 'ignoreerrors': True, 'playlistend': None}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                entries = info.get('entries', [info]) if info else []
                entries = [e for e in entries if e and not e.get('is_live', False) and e.get('live_status', '') != 'is_live']
                total = len(entries)
                self.video_list = entries
                self._ghi_log(f"🏛️ Chủ: {info.get('channel','?')}", "ok")
                self._ghi_log(f"💎 Tổng cộng: {total} video (đã lọc livestream)", "ok")
                for i, v in enumerate(entries, 1):
                    t = v.get("title","?")
                    d = v.get("duration",0)
                    if d:
                        d = int(d); m,s = divmod(d,60); h=0
                        if m>=60: h,m = divmod(m,60)
                        ts = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
                        self._ghi_log(f"  {i:3d}. {t}  [{ts}]")
                    else:
                        self._ghi_log(f"  {i:3d}. {t}")
                self.after(0, lambda: self._set_ui_state("ready"))
                self.after(0, lambda: self._set_tien_do(100, f"✅ {total} video — Nhấn Tải Tất Cả"))
            except Exception as e:
                self._ghi_log(f"Lỗi: {e}", "err")
                self.after(0, lambda: self._set_ui_state("idle"))
                self.after(0, lambda: self._set_tien_do(0, "❌ Thám thính thất bại"))
        threading.Thread(target=run, daemon=True).start()

    # ─── DOWNLOAD (subprocess) ───
    def _bat_dau_tai(self):
        url = self.url_var.get().strip()
        output = self.output_var.get().strip() or DEFAULT_OUTPUT
        video_dir = os.path.join(output, 'videos')
        thumb_dir = os.path.join(output, 'thumbs')
        Path(video_dir).mkdir(parents=True, exist_ok=True)
        Path(thumb_dir).mkdir(parents=True, exist_ok=True)

        self.running = True
        self.paused = False
        self._set_ui_state("working")
        self._set_tien_do(0, "📥 Đang tải...")
        self._ghi_log("━━━ TẢI VIDEO ━━━", "title")
        self._ghi_log(f"📍 {url}")
        self._ghi_log(f"📂 {output}")

        # Cookie từ Chrome (nếu có) giúp tăng trust, tránh bị chặn
        cookies_file = os.path.join(os.path.dirname(os.path.expanduser('~')), 'AppData', 'Local', 'Google', 'Chrome', 'User Data', 'Default', 'Network', 'Cookies')
        cmd = [
            'yt-dlp',
            '--paths', 'home:' + output,
            '--paths', 'video:videos',
            '--paths', 'thumbnail:thumbs',
            '-o', '%(title).100s.%(ext)s',
            '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            '--merge-output-format', 'mp4',
            '--write-thumbnail', '--no-embed-thumbnail',
            '--embed-metadata',
            '--download-archive', os.path.join(output, 'archive.txt'),
            '--ignore-errors', '--no-playlist-reverse',
            '--match-filter', '!is_live',
            '--no-progress', '--newline',
            '--compat-options', 'no-youtube-unavailable-videos',
            # Chống chặn YouTube
            '--extractor-retries', '10',        # Retry 10 lần nếu lỗi
            '--sleep-requests', '0.5',          # Delay 0.5s giữa mỗi request
            '--sleep-interval', '3',            # Nghỉ 3-8s giữa mỗi video
            '--max-sleep-interval', '8',
            '--retry-sleep-func', 'lambda n: 2 * n',  # Tăng dần thời gian retry
            url,
        ]

        def run():
            try:
                # Thử subprocess trước (dành cho user đã cài yt-dlp global)
                import subprocess
                try:
                    subprocess.run(['yt-dlp', '--version'], capture_output=True, timeout=5, check=True)
                    use_subprocess = True
                except:
                    use_subprocess = False
                    self._ghi_log("yt-dlp chưa cài, dùng module tích hợp sẵn", "info")

                if use_subprocess:
                    self.ytdlp_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                    for line in iter(self.ytdlp_process.stdout.readline, ''):
                        if not self.running:
                            self.ytdlp_process.kill()
                            break
                        while self.paused and self.running:
                            import time; time.sleep(0.5)
                        if '[download]' in line and '%' in line:
                            try:
                                pct = line.split('%')[0].split()[-1]
                                p = float(pct)
                                self.after(0, lambda pp=p: self._set_tien_do(pp, f"📥 Đang tải... {pp:.0f}%"))
                            except: pass
                        elif 'Destination' in line or 'has already' in line:
                            self._ghi_log(f"  {line.strip()[:90]}")
                    self.ytdlp_process.wait()
                else:
                    # Fallback: dùng module yt-dlp tích hợp
                    import yt_dlp
                    ydl_opts = {
                        'paths': {'home': output, 'video': 'videos', 'thumbnail': 'thumbs'},
                        'outtmpl': '%(title).100s.%(ext)s',
                        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                        'merge_output_format': 'mp4',
                        'writethumbnail': True, 'embedthumbnail': False,
                        'embedmetadata': True,
                        'download_archive': os.path.join(output, 'archive.txt'),
                        'ignoreerrors': True,
                        'match_filter': yt_dlp.utils.match_filter_func('!is_live'),
                        'extractor_retries': 10,
                        'sleep_interval': 3, 'max_sleep_interval': 8,
                        'progress_hooks': [self._tien_trinh],
                    }
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])

                # Dọn ảnh trùng
                try:
                    video_exts = ('.mp4','.mkv','.avi','.mov','.webm','.flv','.wmv')
                    for f in os.listdir(video_dir):
                        if not f.lower().endswith(video_exts):
                            os.remove(os.path.join(video_dir, f))
                except: pass

                # Avatar
                try:
                    src = url
                    if use_subprocess:
                        av_cmd = ['yt-dlp', '--print', '%(thumbnail)s', '--flat-playlist', '--playlist-end', '1', url]
                        av_r = subprocess.run(av_cmd, capture_output=True, text=True, timeout=15)
                        src = av_r.stdout.strip()
                    else:
                        with yt_dlp.YoutubeDL({'quiet':True,'extract_flat':True,'playlistend':1}) as y:
                            av_i = y.extract_info(url, download=False)
                            if av_i.get('entries'): av_i = av_i['entries'][0]
                            src = (av_i.get('thumbnails') or [{}])[-1].get('url','')
                    if src and src.startswith('http'):
                        urllib.request.urlretrieve(src, os.path.join(output, 'avatar.jpg'))
                        self._ghi_log(f"🖼️ Avatar kênh: avatar.jpg", "ok")
                except: pass

                self.after(0, lambda: self._set_tien_do(100, "✅ Hoàn tất!"))
                self.after(0, lambda: self._set_ui_state("idle"))
            except Exception as e:
                self._ghi_log(f"Lỗi: {e}", "err")
                self.after(0, lambda: self._set_ui_state("idle"))

        threading.Thread(target=run, daemon=True).start()

    def _tam_dung(self):
        self.paused = True
        self._set_ui_state("paused")
        self._ghi_log("⏸ Đã tạm dừng", "warn")
        self._set_tien_do(self.progress_bar.get()*100, "⏸ Tạm dừng")

    def _tiep_tuc(self):
        self.paused = False
        self._set_ui_state("working")
        self._ghi_log("▶ Tiếp tục tải...", "ok")

    def _dung_tai(self):
        self.running = False
        self.paused = False
        try:
            if self.ytdlp_process and self.ytdlp_process.poll() is None:
                self.ytdlp_process.kill()
                self.ytdlp_process.wait(timeout=5)
        except: pass
        self._set_ui_state("idle")
        self._set_tien_do(0, "⏹ Đã dừng")
        self._ghi_log("⏹ Đã dừng tải", "warn")

    def on_closing(self):
        try:
            if self.ytdlp_process and self.ytdlp_process.poll() is None:
                self.ytdlp_process.kill()
        except: pass
        if self.after_id:
            self.after_cancel(self.after_id)
        self.destroy()

if __name__ == "__main__":
    app = ChannelDLApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
