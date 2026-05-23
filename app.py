#!/usr/bin/env python3
"""
Channel DL v1.1 — Thâu Hương Pháp Bảo | By Ngọc NX
Download video YouTube/TikTok — phân loại videos/thumbs
"""

import os, sys, json, threading, queue, subprocess, urllib.request, re
from pathlib import Path
from datetime import datetime
from tkinter import filedialog
import customtkinter as ctk

APP_NAME, APP_VER = "🎬 Thâu Hương Pháp Bảo", "1.1"
THEME = "dark"
COLOR = "green"
DEFAULT_OUTPUT = str(Path.home() / "Downloads" / "thau-huong")

ctk.set_appearance_mode(THEME)
ctk.set_default_color_theme(COLOR)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        # Center screen
        sw = self.winfo_screenwidth(); sh = self.winfo_screenheight()
        w, h = 960, 740
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.minsize(820, 640)
        self.title(f"{APP_NAME} v{APP_VER}")
        try:
            ip = os.path.join(getattr(sys, '_MEIPASS', '.'), 'icon.ico')
            if os.path.exists(ip): self.iconbitmap(ip)
        except: pass
        self.after_id = None
        self.log_q = queue.Queue()
        self._build()
        self._poll_log()
        self._log("Pháp bảo sẵn sàng 🐲", "ok")

    def _build(self):
        # Top bar
        tb = ctk.CTkFrame(self, height=38, corner_radius=0, fg_color="#1a1a2e")
        tb.pack(fill="x")
        ctk.CTkLabel(tb, text=f"🐉  {APP_NAME}  v{APP_VER}  —  By Ngọc NX",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(side="left", padx=16, pady=6)
        self.theme_btn = ctk.CTkButton(tb, text="☀️", width=40, height=26,
                                        font=ctk.CTkFont(size=13), fg_color="transparent",
                                        hover_color="#16213e", command=self._toggle)
        self.theme_btn.pack(side="right", padx=12)

        m = ctk.CTkFrame(self); m.pack(fill="both", expand=True, padx=16, pady=(8,14))

        # URL
        uf = ctk.CTkFrame(m, corner_radius=10); uf.pack(fill="x", pady=(0,10))
        ctk.CTkLabel(uf, text="🗺️  Link Kênh", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=12, pady=(10,4))
        r = ctk.CTkFrame(uf, fg_color="transparent"); r.pack(fill="x", padx=12, pady=(0,10))
        self.url_var = ctk.StringVar()
        ctk.CTkEntry(r, textvariable=self.url_var, placeholder_text="https://youtube.com/@tenkenh | https://tiktok.com/@...",
                     font=ctk.CTkFont(size=13)).pack(side="left", fill="x", expand=True, padx=(0,6))
        ctk.CTkButton(r, text="📋", width=36, command=self._paste, font=ctk.CTkFont(size=13)).pack(side="left", padx=(0,4))
        ctk.CTkButton(r, text="✕", width=36, fg_color="#c0392b", font=ctk.CTkFont(size=13),
                       command=lambda: self.url_var.set("")).pack(side="left")

        # Output + Actions
        of = ctk.CTkFrame(m, corner_radius=10); of.pack(fill="x", pady=(0,10))
        ctk.CTkLabel(of, text="📂  Kho Chứa", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=12, pady=(10,4))
        g = ctk.CTkFrame(of, fg_color="transparent"); g.pack(fill="x", padx=12, pady=(0,10))
        self.out_var = ctk.StringVar(value=DEFAULT_OUTPUT)
        ctk.CTkEntry(g, textvariable=self.out_var, font=ctk.CTkFont(size=12)).pack(side="left", fill="x", expand=True, padx=(0,6))
        ctk.CTkButton(g, text="📂 Chọn", width=70, command=self._pick, font=ctk.CTkFont(size=12)).pack(side="left", padx=(0,10))
        self.btn_scan = ctk.CTkButton(g, text="🔍  Thám Thính", width=130, fg_color="#2B5E9E",
                                       hover_color="#1D4A7A", font=ctk.CTkFont(size=13, weight="bold"), command=self._scan)
        self.btn_scan.pack(side="left", padx=(0,6))
        self.btn_dl = ctk.CTkButton(g, text="⬇️  Tải Tất Cả", width=140, state="disabled",
                                     fg_color="#27AE60", hover_color="#1E8449",
                                     font=ctk.CTkFont(size=13, weight="bold"), command=self._download)
        self.btn_dl.pack(side="left")

        # Progress
        pf = ctk.CTkFrame(m, corner_radius=8); pf.pack(fill="x", pady=(0,10))
        self.pbar = ctk.CTkProgressBar(pf, height=18, corner_radius=6,
                                        fg_color="#2a2a3e", progress_color="#27AE60")
        self.pbar.pack(fill="x", padx=12, pady=(10,2)); self.pbar.set(0)
        self.plabel = ctk.CTkLabel(pf, text="⏳  Chờ lệnh...", font=ctk.CTkFont(size=12))
        self.plabel.pack(anchor="w", padx=14, pady=(0,8))

        # Log
        lf = ctk.CTkFrame(m, corner_radius=10); lf.pack(fill="both", expand=True)
        lh = ctk.CTkFrame(lf, fg_color="transparent", height=30); lh.pack(fill="x", padx=8, pady=(4,0))
        ctk.CTkLabel(lh, text="📜  Nhật Ký", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=4)
        ctk.CTkButton(lh, text="🗑️ Xóa", width=50, height=22, font=ctk.CTkFont(size=10),
                       fg_color="#555", hover_color="#444", command=self._clear).pack(side="right", padx=4)
        self.log = ctk.CTkTextbox(lf, font=ctk.CTkFont(family="Consolas", size=12),
                                   fg_color="#0d0d1a", text_color="#e0e0e0")
        self.log.pack(fill="both", expand=True, pady=(0,8), padx=8)
        self.log.bind("<Key>", lambda e: "break")

        # Status
        self.status = ctk.CTkLabel(self, text="🐲  Sẵn sàng", anchor="w",
                                    fg_color="#1a1a2e", font=ctk.CTkFont(size=11))
        self.status.pack(side="bottom", fill="x", ipady=2)

    # ─── Helpers ───
    def _log(self, msg, level="info"):
        p = {"info":"◆","ok":"✓","warn":"⚠","err":"✗","title":"━"}.get(level," ")
        self.log_q.put(f"[{datetime.now().strftime('%H:%M:%S')}] {p} {msg}")

    def _poll_log(self):
        while True:
            try: self.log.insert("end", self.log_q.get_nowait()+"\n"); self.log.see("end")
            except queue.Empty: break
        self.after_id = self.after(100, self._poll_log)

    def _clear(self):
        self.log.delete("1.0", "end"); self._log("🗑️ Đã xóa", "info")

    def _toggle(self):
        new = "light" if ctk.get_appearance_mode() == "Dark" else "dark"
        ctk.set_appearance_mode(new)
        self.theme_btn.configure(text="🌙" if new=="dark" else "☀️")

    def _paste(self):
        try:
            t = self.clipboard_get()
            if t: self.url_var.set(t.strip())
        except: pass

    def _pick(self):
        d = filedialog.askdirectory()
        if d: self.out_var.set(d)

    def _state(self, busy=False):
        self.btn_scan.configure(state="disabled" if busy else "normal")
        self.btn_dl.configure(state="disabled" if busy else "normal")

    def _progress(self, pct, text=""):
        self.pbar.set(pct/100); self.plabel.configure(text=text)

    # ─── Thám thính ───
    def _scan(self):
        url = self.url_var.get().strip()
        if not url: return self._log("🔴 Nhập link kênh!", "err")
        self._state(True); self._progress(0, "🔍  Đang thám thính...")
        self._log("━━━  THÁM THÍNH  ━━━", "title"); self._log(f"📍 {url}")

        def run():
            try:
                import yt_dlp
                ydl = yt_dlp.YoutubeDL({"quiet":True,"extract_flat":"in_playlist","ignoreerrors":True,"playlistend":None})
                info = ydl.extract_info(url, download=False)
                entries = [e for e in (info.get('entries',[info]) or []) if e and not e.get('is_live')]
                if not entries: raise Exception("Không tìm thấy video nào!")
                self._log(f"🏛️  {info.get('channel','?')}", "ok")
                self._log(f"💎  {len(entries)} video (đã lọc live)", "ok")
                for i,v in enumerate(entries,1):
                    t = v.get('title','?'); d = v.get('duration',0)
                    if d:
                        d=int(d); m,s=divmod(d,60); h=0
                        if m>=60: h,m=divmod(m,60)
                        ts = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
                        self._log(f"  {i:3d}. {t}  [{ts}]")
                    else: self._log(f"  {i:3d}. {t}")
                self.after(0, lambda: (self._state(False), self._progress(100, f"✅  {len(entries)} video — Nhấn Tải Tất Cả")))
            except Exception as e:
                self._log(f"🔴  {e}", "err")
                self.after(0, lambda: (self._state(False), self._progress(0, "❌  Thất bại")))
        threading.Thread(target=run, daemon=True).start()

    # ─── Download ───
    def _download(self):
        url = self.url_var.get().strip()
        out = os.path.abspath(self.out_var.get().strip() or DEFAULT_OUTPUT)
        vdir = os.path.join(out, 'videos'); tdir = os.path.join(out, 'thumbs')
        os.makedirs(vdir, exist_ok=True); os.makedirs(tdir, exist_ok=True)

        # Phân biệt TikTok vs YouTube để chọn format
        is_tiktok = 'tiktok.com' in url.lower()

        self._state(True); self._progress(0, "📥  Đang tải...")
        self._log("━━━  TẢI VIDEO  ━━━", "title")
        self._log(f"📍 {url}"); self._log(f"📂 {out}")
        self._log(f"🎵 Nguồn: {'TikTok' if is_tiktok else 'YouTube'}", "info")

        def run():
            try:
                import yt_dlp
                # Format riêng cho từng nền tảng
                if is_tiktok:
                    fmt = 'bv*+ba/b'  # TikTok: 1 stream duy nhất
                else:
                    fmt = 'bv*+ba/b'  # YouTube: tách video+audio rồi merge

                ydl_opts = {
                    'paths': {'home': out},
                    'outtmpl': {'default': 'videos/%(title).100s.%(ext)s',
                                'thumbnail': 'thumbs/%(title).100s.%(ext)s'},
                    'format': fmt,
                    'merge_output_format': 'mp4',
                    'remux_video': 'mp4',
                    'writethumbnail': True,
                    'embedthumbnail': False,
                    'converttumbnails': 'jpg',
                    'embedmetadata': True, 'addmetadata': True,
                    'download_archive': os.path.join(out, 'archive.txt'),
                    'ignoreerrors': True, 'no_color': True,
                    'match_filter': yt_dlp.utils.match_filter_func('!is_live'),
                    'extractor_retries': 10,
                    'sleep_interval': 3, 'max_sleep_interval': 8,
                    'progress_hooks': [self._hook],
                }
                with yt_dlp.YoutubeDL(ydl_opts) as y:
                    y.download([url])

                # Cleanup: xóa ảnh không đúng khỏi videos/, rename sang .jpg
                from PIL import Image as PILImage
                for f in os.listdir(vdir):
                    fp = os.path.join(vdir, f)
                    if not f.lower().endswith('.mp4') and os.path.isfile(fp):
                        try:
                            PILImage.open(fp).verify()
                            # Là ảnh thật → rename .jpg trong thumbs/
                            new_name = os.path.splitext(f)[0] + '.jpg'
                            os.rename(fp, os.path.join(tdir, new_name))
                            self._log(f"🖼️  Đã chuyển {f} → thumbs/{new_name}", "info")
                        except:
                            try: os.remove(fp); self._log(f"🗑️  Đã xóa {f} (không phải ảnh)", "info")
                            except: pass

                # Avatar
                try:
                    with yt_dlp.YoutubeDL({"quiet":True,"extract_flat":True,"playlistend":1}) as y:
                        av = y.extract_info(url, download=False)
                    if av:
                        if av.get('entries'): av = av['entries'][0]
                        av_url = (av.get('thumbnails') or [{}])[-1].get('url','')
                        if av_url: urllib.request.urlretrieve(av_url, os.path.join(out, 'avatar.jpg'))
                except: pass

                self.after(0, lambda: (self._state(False), self._progress(100, "✅  Hoàn tất!")))
            except Exception as e:
                self._log(f"🔴  {e}", "err")
                self.after(0, lambda: (self._state(False), self._progress(0, "❌  Thất bại")))
        threading.Thread(target=run, daemon=True).start()

    def _hook(self, d):
        if d['status'] == 'downloading':
            try:
                p = float(d.get('_percent_str','0%').replace('%',''))
                self.after(0, lambda pp=p: self._progress(pp, f"📥 {pp:.0f}%"))
            except: pass
        elif d['status'] == 'finished':
            self._log(f"✅ {os.path.basename(d.get('filename','?'))}")
        elif d['status'] == 'error':
            self._log(f"⚠️ {d.get('error','?')}", "warn")

    def on_closing(self):
        if self.after_id: self.after_cancel(self.after_id)
        self.destroy()

if __name__ == "__main__":
    a = App()
    a.protocol("WM_DELETE_WINDOW", a.on_closing)
    a.mainloop()
