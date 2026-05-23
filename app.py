#!/usr/bin/env python3
"""
Channel DL v3.2 — Thâu Hương Pháp Bảo
Download toàn bộ video từ kênh YouTube/TikTok
"""

import os, sys, json, threading, queue, subprocess, urllib.request, time, shutil
from pathlib import Path
from datetime import datetime
from tkinter import filedialog
import customtkinter as ctk

APP_NAME     = "🎬 Thâu Hương Pháp Bảo"
APP_VERSION  = "3.2"
APP_GEOMETRY = "780x680"
THEME        = "dark"
COLOR_THEME  = "green"
DEFAULT_OUTPUT = str(Path.home() / "Downloads" / "thau-huong")
ctk.set_appearance_mode(THEME)
ctk.set_default_color_theme(COLOR_THEME)

def get_ytdlp():
    """Tìm yt-dlp.exe: ưu tiên bundle, fallback PATH"""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        exe = os.path.join(sys._MEIPASS, 'yt-dlp.exe')
        if os.path.exists(exe): return exe
    return shutil.which('yt-dlp') or 'yt-dlp'

YTDLP = get_ytdlp()

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry(APP_GEOMETRY)
        self.minsize(680, 580)
        try:
            ip = os.path.join(getattr(sys, '_MEIPASS', '.'), 'icon.ico')
            if os.path.exists(ip): self.iconbitmap(ip)
        except: pass
        self.proc = None
        self.running = False
        self.paused = False
        self.log_q = queue.Queue()
        self.after_id = None
        self._build()
        self._poll_log()
        self._log("Sẵn sàng 🐲", "ok")

    def _build(self):
        m = ctk.CTkFrame(self); m.pack(fill="both", expand=True, padx=14, pady=14)
        ctk.CTkLabel(m, text=f"{APP_NAME} v{APP_VERSION} — By Ngọc NX",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(0,6))
        ctk.CTkLabel(m, text="Dán link kênh → Thám Thính → Tải toàn bộ video chất lượng cao nhất",
                     font=ctk.CTkFont(size=13)).pack(pady=(0,14))

        # URL
        uf = ctk.CTkFrame(m); uf.pack(fill="x", pady=(0,10))
        ctk.CTkLabel(uf, text="🗺️ Link Kênh", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10,4))
        r = ctk.CTkFrame(uf, fg_color="transparent"); r.pack(fill="x", padx=10, pady=(0,10))
        self.url_var = ctk.StringVar()
        ctk.CTkEntry(r, textvariable=self.url_var, placeholder_text="https://youtube.com/@tenkenh").pack(side="left", fill="x", expand=True, padx=(0,6))
        ctk.CTkButton(r, text="📋", width=38, command=self._paste).pack(side="left", padx=(0,4))
        ctk.CTkButton(r, text="✕", width=38, fg_color="gray30", command=lambda: self.url_var.set("")).pack(side="left")

        # Output
        of = ctk.CTkFrame(m); of.pack(fill="x", pady=(0,10))
        ctk.CTkLabel(of, text="📂 Kho Chứa", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10,6))
        g = ctk.CTkFrame(of, fg_color="transparent"); g.pack(fill="x", padx=10, pady=(0,10))
        self.out_var = ctk.StringVar(value=DEFAULT_OUTPUT)
        ctk.CTkEntry(g, textvariable=self.out_var).pack(side="left", fill="x", expand=True, padx=(0,6))
        ctk.CTkButton(g, text="📂 Chọn", width=80, command=lambda: self.out_var.set(filedialog.askdirectory() or self.out_var.get())).pack(side="left")

        # Buttons
        bf = ctk.CTkFrame(m); bf.pack(fill="x", pady=(0,10))
        self.btn_scan  = ctk.CTkButton(bf, text="🔍 Thám Thính", width=130, fg_color="#2B5E9E", command=self._scan)
        self.btn_scan.pack(side="left", padx=(0,6))
        self.btn_dl    = ctk.CTkButton(bf, text="⬇️ Tải Tất Cả", width=130, state="disabled", command=self._download)
        self.btn_dl.pack(side="left", padx=(0,6))
        self.btn_pause = ctk.CTkButton(bf, text="⏸ Tạm Dừng", width=100, fg_color="#E67E22", state="disabled", command=self._pause)
        self.btn_pause.pack(side="left", padx=(0,6))
        self.btn_stop  = ctk.CTkButton(bf, text="⏹ Dừng", width=80, fg_color="#B33", state="disabled", command=self._stop)
        self.btn_stop.pack(side="left")

        # Progress
        pf = ctk.CTkFrame(m); pf.pack(fill="x", pady=(0,10))
        self.pbar = ctk.CTkProgressBar(pf); self.pbar.pack(fill="x", padx=10, pady=(10,2)); self.pbar.set(0)
        self.plabel = ctk.CTkLabel(pf, text="⏳ Chờ lệnh...", font=ctk.CTkFont(size=12))
        self.plabel.pack(anchor="w", padx=10, pady=(0,10))

        # Log
        lf = ctk.CTkFrame(m); lf.pack(fill="both", expand=True, pady=(4,0))
        lh = ctk.CTkFrame(lf, fg_color="transparent", height=30); lh.pack(fill="x")
        ctk.CTkLabel(lh, text="📜 Nhật Ký", font=ctk.CTkFont(13,"bold")).pack(side="left")
        ctk.CTkButton(lh, text="🗑️ Xóa", width=60, height=22, font=ctk.CTkFont(size=10), command=self._clear_log).pack(side="right", padx=(0,4))
        self.log = ctk.CTkTextbox(lf, height=180, font=ctk.CTkFont(family="Consolas", size=12))
        self.log.pack(fill="both", expand=True, pady=(4,0))
        self.log.bind("<Key>", lambda e: "break")

        self.status = ctk.CTkLabel(self, text="Sẵn sàng 🐲", anchor="w", fg_color="gray15", font=ctk.CTkFont(size=11))
        self.status.pack(side="bottom", fill="x")

    # ─── HELPERS ───
    def _log(self, msg, level="info"):
        p = {"info":"◆","ok":"✓","warn":"⚠","err":"✗","title":"━"}.get(level, " ")
        self.log_q.put(f"[{datetime.now().strftime('%H:%M:%S')}] {p} {msg}")

    def _poll_log(self):
        while True:
            try: self.log.insert("end", self.log_q.get_nowait() + "\n"); self.log.see("end")
            except queue.Empty: break
        self.after_id = self.after(100, self._poll_log)

    def _clear_log(self):
        self.log.delete("1.0", "end")
        self._log("📋 Đã xóa nhật ký", "info")

    def _set_btn(self, state):
        s = {"idle":    ("normal","disabled","disabled","disabled"),
             "ready":   ("normal","normal","disabled","disabled"),
             "working": ("disabled","disabled","normal","normal"),
             "paused":  ("disabled","disabled","disabled","normal")}
        b = s.get(state, s["idle"])
        self.btn_scan.configure(state=b[0])
        self.btn_dl.configure(state=b[1])
        self.btn_pause.configure(state=b[2], text="▶ Tiếp Tục" if state=="paused" else "⏸ Tạm Dừng")
        self.btn_stop.configure(state=b[3])

    def _progress(self, pct, text=""):
        self.pbar.set(pct/100)
        self.plabel.configure(text=text)

    def _paste(self):
        try:
            t = self.clipboard_get()
            if t: self.url_var.set(t.strip())
        except: pass

    def _scan(self):
        url = self.url_var.get().strip()
        if not url: return self._log("Nhập link kênh!", "warn")
        self._set_btn("working"); self._progress(0, "🔍 Đang thám thính...")
        self._log("━━━ THÁM THÍNH ━━━", "title"); self._log(f"📍 {url}")

        def run():
            try:
                import yt_dlp
                with yt_dlp.YoutubeDL({"quiet":True,"extract_flat":"in_playlist","ignoreerrors":True,"playlistend":None}) as y:
                    info = y.extract_info(url, download=False)
                entries = [e for e in (info.get('entries',[info]) if info else []) if e and not e.get('is_live')]
                if not entries: raise Exception("Không tìm thấy video nào!")
                self._log(f"🏛️ {info.get('channel','?')}", "ok")
                self._log(f"💎 {len(entries)} video (đã lọc livestream)", "ok")
                for i,v in enumerate(entries,1):
                    t = v.get('title','?')
                    d = v.get('duration',0)
                    if d:
                        d=int(d); m,s=divmod(d,60); h=0
                        if m>=60: h,m=divmod(m,60)
                        ts = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
                        self._log(f"  {i:3d}. {t}  [{ts}]")
                    else: self._log(f"  {i:3d}. {t}")
                self.after(0, lambda:self._set_btn("ready"))
                self.after(0, lambda:self._progress(100, f"✅ {len(entries)} video — Nhấn Tải Tất Cả"))
            except Exception as e:
                self._log(f"❌ {e}", "err")
                self.after(0, lambda:self._set_btn("idle"))
                self.after(0, lambda:self._progress(0, "❌ Thám thính thất bại"))
        threading.Thread(target=run, daemon=True).start()

    # ─── DOWNLOAD ───
    def _download(self):
        url = self.url_var.get().strip()
        out = self.out_var.get().strip() or DEFAULT_OUTPUT
        video_dir = os.path.join(out, 'videos')
        thumb_dir = os.path.join(out, 'thumbs')
        Path(video_dir).mkdir(parents=True, exist_ok=True)
        Path(thumb_dir).mkdir(parents=True, exist_ok=True)

        self.running = True; self.paused = False
        self._set_btn("working"); self._progress(0, "📥 Đang tải...")
        self._log("━━━ TẢI VIDEO ━━━", "title")
        self._log(f"📍 {url}")
        self._log(f"📂 {out}")

        cmd = [YTDLP,
            '--paths', f'home:{out}',
            '--paths', 'video:videos',
            '--paths', 'thumbnail:thumbs',
            '-o', '%(title).100s.%(ext)s',
            '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            '--merge-output-format', 'mp4',
            '--write-thumbnail', '--no-embed-thumbnail',
            '--embed-metadata',
            '--download-archive', os.path.join(out, 'archive.txt'),
            '--ignore-errors', '--no-playlist-reverse',
            '--match-filter', '!is_live',
            '--no-progress', '--newline',
            '--extractor-retries', '10',
            '--sleep-requests', '0.5',
            '--sleep-interval', '3',
            '--max-sleep-interval', '8',
            url]

        def run():
            try:
                self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                for line in iter(self.proc.stdout.readline, ''):
                    if not self.running:
                        self.proc.kill(); break
                    while self.paused and self.running:
                        time.sleep(0.5)
                    if '[download]' in line and '%' in line:
                        try:
                            pct = float(line.split('%')[0].split()[-1])
                            self.after(0, lambda p=pct: self._progress(p, f"📥 Đang tải... {p:.0f}%"))
                        except: pass
                    elif 'Destination' in line or 'has already been downloaded' in line:
                        self._log(f"  {line.strip()[:90]}")
                    elif 'ERROR' in line:
                        self._log(f"  ⚠️ {line.strip()[:90]}", "warn")

                self.proc.wait()
                # Dọn ảnh trùng khỏi videos/
                try:
                    for f in os.listdir(video_dir):
                        if not f.lower().endswith(('.mp4','.mkv','.avi','.mov','.webm','.flv','.wmv')):
                            os.remove(os.path.join(video_dir, f))
                except: pass
                # Avatar
                try:
                    a = subprocess.run([YTDLP, '--print', '%(thumbnail)s', '--flat-playlist', '--playlist-end', '1', url],
                                       capture_output=True, text=True, timeout=15)
                    av = a.stdout.strip()
                    if av.startswith('http'):
                        urllib.request.urlretrieve(av, os.path.join(out, 'avatar.jpg'))
                        self._log("🖼️ Avatar: avatar.jpg", "ok")
                except: pass
                self.after(0, lambda: self._progress(100, "✅ Hoàn tất!"))
                self.after(0, lambda: self._set_btn("idle"))
            except Exception as e:
                self._log(f"❌ {e}", "err")
                self.after(0, lambda: self._set_btn("idle"))
        threading.Thread(target=run, daemon=True).start()

    def _pause(self):
        if self.paused:
            self.paused = False
            self._set_btn("working")
            self._log("▶ Tiếp tục", "ok")
        else:
            self.paused = True
            self._set_btn("paused")
            self._log("⏸ Đã tạm dừng", "warn")

    def _stop(self):
        self.running = False; self.paused = False
        try:
            if self.proc and self.proc.poll() is None:
                self.proc.kill()
                self.proc.wait(timeout=5)
        except: pass
        self._set_btn("idle"); self._progress(0, "⏹ Đã dừng")
        self._log("⏹ Đã dừng tải", "warn")

    def on_closing(self):
        self.running = False
        try:
            if self.proc and self.proc.poll() is None: self.proc.kill()
        except: pass
        if self.after_id: self.after_cancel(self.after_id)
        self.destroy()

if __name__ == "__main__":
    a = App()
    a.protocol("WM_DELETE_WINDOW", a.on_closing)
    a.mainloop()
