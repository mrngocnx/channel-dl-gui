#!/usr/bin/env python3
"""Channel DL v3.3 — Thâu Hương Pháp Bảo | By Ngọc NX"""

import os, sys, json, threading, queue, subprocess, urllib.request
from pathlib import Path
from datetime import datetime
from tkinter import filedialog
import customtkinter as ctk

APP_NAME, APP_VER = "🎬 Thâu Hương Pháp Bảo", "3.3"
APP_SIZE = "960x720"
THEME = "dark"
DEFAULT_OUTPUT = str(Path.home() / "Downloads" / "thau-huong")
ctk.set_appearance_mode(THEME)
ctk.set_default_color_theme("green")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        # Căn giữa màn hình
        sw = self.winfo_screenwidth(); sh = self.winfo_screenheight()
        w, h = 960, 720
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.minsize(800, 600)
        self.title(f"{APP_NAME} v{APP_VER}")
        try:
            ip = os.path.join(getattr(sys, '_MEIPASS', '.'), 'icon.ico')
            if os.path.exists(ip): self.iconbitmap(ip)
        except: pass
        self.after_id = None
        self.log_q = queue.Queue()
        self._build()
        self._poll_log()
        self._log("Sẵn sàng 🐲", "ok")

    def _build(self):
        # Menu
        mb = ctk.CTkFrame(self, height=30, fg_color="transparent")
        mb.pack(fill="x", padx=10, pady=(8,0))
        ctk.CTkButton(mb, text="☀ Sáng" if THEME=="dark" else "🌙 Tối", width=70, height=24,
                      font=ctk.CTkFont(size=11), command=self._toggle_theme).pack(side="right")
        ctk.CTkLabel(mb, text=f"{APP_NAME} v{APP_VER} — By Ngọc NX",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")

        m = ctk.CTkFrame(self); m.pack(fill="both", expand=True, padx=14, pady=(4,14))
        ctk.CTkLabel(m, text="Dán link kênh → Thám Thính → Tải toàn bộ video chất lượng cao",
                     font=ctk.CTkFont(size=13)).pack(pady=(0,10))

        # URL
        uf = ctk.CTkFrame(m); uf.pack(fill="x", pady=(0,8))
        r = ctk.CTkFrame(uf, fg_color="transparent"); r.pack(fill="x", padx=10, pady=(8,8))
        self.url_var = ctk.StringVar()
        ctk.CTkEntry(r, textvariable=self.url_var, placeholder_text="https://youtube.com/@tenkenh").pack(side="left", fill="x", expand=True, padx=(0,6))
        ctk.CTkButton(r, text="📋", width=38, command=self._paste).pack(side="left", padx=(0,4))
        ctk.CTkButton(r, text="✕", width=38, fg_color="gray30", command=lambda: self.url_var.set("")).pack(side="left")

        # Output + Buttons
        of = ctk.CTkFrame(m); of.pack(fill="x", pady=(0,8))
        g = ctk.CTkFrame(of, fg_color="transparent"); g.pack(fill="x", padx=10, pady=(8,8))
        self.out_var = ctk.StringVar(value=DEFAULT_OUTPUT)
        ctk.CTkEntry(g, textvariable=self.out_var).pack(side="left", fill="x", expand=True, padx=(0,6))
        ctk.CTkButton(g, text="📂 Chọn", width=80, command=self._pick).pack(side="left", padx=(0,12))
        self.btn_scan = ctk.CTkButton(g, text="🔍 Thám Thính", width=130, fg_color="#2B5E9E", command=self._scan)
        self.btn_scan.pack(side="left", padx=(0,6))
        self.btn_dl = ctk.CTkButton(g, text="⬇️ Tải Tất Cả", width=140, state="disabled", command=self._download)
        self.btn_dl.pack(side="left")

        # Progress
        pf = ctk.CTkFrame(m); pf.pack(fill="x", pady=(0,8))
        self.pbar = ctk.CTkProgressBar(pf); self.pbar.pack(fill="x", padx=10, pady=(8,2)); self.pbar.set(0)
        self.plabel = ctk.CTkLabel(pf, text="⏳ Chờ lệnh...", font=ctk.CTkFont(size=12))
        self.plabel.pack(anchor="w", padx=10, pady=(0,6))

        # Log
        lf = ctk.CTkFrame(m); lf.pack(fill="both", expand=True)
        lh = ctk.CTkFrame(lf, fg_color="transparent", height=28); lh.pack(fill="x", pady=(4,0))
        ctk.CTkLabel(lh, text="📜 Nhật Ký", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        ctk.CTkButton(lh, text="🗑️", width=40, height=22, font=ctk.CTkFont(size=10),
                       command=self._clear_log).pack(side="right")
        self.log = ctk.CTkTextbox(lf, font=ctk.CTkFont(family="Consolas", size=12))
        self.log.pack(fill="both", expand=True, pady=(4,0))
        self.log.bind("<Key>", lambda e: "break")

        self.status = ctk.CTkLabel(self, text="Sẵn sàng 🐲", anchor="w", fg_color="gray15",
                                    font=ctk.CTkFont(size=11))
        self.status.pack(side="bottom", fill="x")

    # ─── Helpers ───
    def _log(self, msg, level="info"):
        p = {"info":"◆","ok":"✓","warn":"⚠","err":"✗","title":"━"}.get(level," ")
        self.log_q.put(f"[{datetime.now().strftime('%H:%M:%S')}] {p} {msg}")

    def _poll_log(self):
        while True:
            try: self.log.insert("end", self.log_q.get_nowait()+"\n"); self.log.see("end")
            except queue.Empty: break
        self.after_id = self.after(100, self._poll_log)

    def _clear_log(self):
        self.log.delete("1.0", "end"); self._log("📋 Đã xóa", "info")

    def _toggle_theme(self):
        new = "light" if ctk.get_appearance_mode() == "Dark" else "dark"
        ctk.set_appearance_mode(new)

    def _paste(self):
        try:
            t = self.clipboard_get()
            if t: self.url_var.set(t.strip())
        except: pass

    def _pick(self):
        d = filedialog.askdirectory()
        if d: self.out_var.set(d)

    def _set_state(self, working=False):
        s = "disabled" if working else "normal"
        self.btn_scan.configure(state=s)
        self.btn_dl.configure(state="disabled" if working else "normal")

    def _progress(self, pct, text=""):
        self.pbar.set(pct/100); self.plabel.configure(text=text)

    # ─── Scan ───
    def _scan(self):
        url = self.url_var.get().strip()
        if not url: return self._log("Nhập link kênh!", "warn")
        self._set_state(True); self._progress(0, "🔍 Đang thám thính...")
        self._log("━━━ THÁM THÍNH ━━━", "title"); self._log(f"📍 {url}")

        def run():
            try:
                import yt_dlp
                with yt_dlp.YoutubeDL({"quiet":True,"extract_flat":"in_playlist","ignoreerrors":True,"playlistend":None}) as y:
                    info = y.extract_info(url, download=False)
                entries = [e for e in (info.get('entries',[info]) if info else []) if e and not e.get('is_live')]
                if not entries: raise Exception("Không có video nào!")
                self._log(f"🏛️ {info.get('channel','?')}", "ok")
                self._log(f"💎 {len(entries)} video (đã lọc live)", "ok")
                for i,v in enumerate(entries,1):
                    t = v.get('title','?'); d = v.get('duration',0)
                    if d:
                        d=int(d); m,s=divmod(d,60); h=0
                        if m>=60: h,m=divmod(m,60)
                        ts = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
                        self._log(f"  {i:3d}. {t}  [{ts}]")
                    else: self._log(f"  {i:3d}. {t}")
                self.after(0, lambda: (self._set_state(False), self._progress(100, f"✅ {len(entries)} video — Nhấn Tải Tất Cả")))
            except Exception as e:
                self._log(f"❌ {e}", "err")
                self.after(0, lambda: (self._set_state(False), self._progress(0, "❌ Thất bại")))
        threading.Thread(target=run, daemon=True).start()

    # ─── Download ───
    def _download(self):
        url = self.url_var.get().strip()
        out = os.path.abspath(self.out_var.get().strip() or DEFAULT_OUTPUT)
        vdir = os.path.join(out, 'videos')
        tdir = os.path.join(out, 'thumbs')
        os.makedirs(vdir, exist_ok=True); os.makedirs(tdir, exist_ok=True)

        self._set_state(True); self._progress(0, "📥 Đang tải...")
        self._log("━━━ TẢI VIDEO ━━━", "title")
        self._log(f"📍 {url}"); self._log(f"📂 {out}")

        def run():
            try:
                import yt_dlp
                ydl_opts = {
                    'paths': {'home': out},
                    'outtmpl': {'default': 'videos/%(title).100s.%(ext)s',
                                'thumbnail': 'thumbs/%(title).100s.%(ext)s'},
                    'format': 'bestvideo+bestaudio/best',
                    'merge_output_format': 'mp4',
                    'remux_video': 'mp4',  # TikTok cần remux
                    'writethumbnail': True, 'embedthumbnail': False,
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

                    # Dọn sạch videos/: chỉ giữ .mp4, rename ảnh sang .jpg
                    import imghdr
                    for f in os.listdir(vdir):
                        fp = os.path.join(vdir, f)
                        if not f.lower().endswith('.mp4'):
                            try:
                                img_type = imghdr.what(fp)
                                if img_type:
                                    os.rename(fp, os.path.join(vdir, os.path.splitext(f)[0] + '.jpg'))
                                else:
                                    os.remove(fp)
                            except:
                                try: os.remove(fp)
                                except: pass
                # Avatar
                try:
                    with yt_dlp.YoutubeDL({"quiet":True,"extract_flat":True,"playlistend":1}) as y:
                        av = y.extract_info(url, download=False)
                    if av:
                        if av.get('entries'): av = av['entries'][0]
                        thumbs = av.get('thumbnails') or []
                        if thumbs:
                            av_url = thumbs[-1].get('url','')
                            if av_url: urllib.request.urlretrieve(av_url, os.path.join(out, 'avatar.jpg'))
                except: pass

                self.after(0, lambda: (self._set_state(False), self._progress(100, "✅ Hoàn tất!")))
            except Exception as e:
                self._log(f"❌ {e}", "err")
                self.after(0, lambda: (self._set_state(False), self._progress(0, "❌ Thất bại")))
        threading.Thread(target=run, daemon=True).start()

    def _hook(self, d):
        if d['status'] == 'downloading':
            try:
                p = float(d.get('_percent_str','0%').replace('%',''))
                self.after(0, lambda pp=p: self._progress(pp, f"📥 {d.get('filename','?')[:40]} {pp:.0f}%"))
            except: pass
        elif d['status'] == 'finished':
            self._log(f"✅ {os.path.basename(d.get('filename','?'))}")
        elif d['status'] == 'error':
            self._log(f"⚠️ Lỗi: {d.get('error','?')}", "warn")

    def on_closing(self):
        if self.after_id: self.after_cancel(self.after_id)
        self.destroy()

if __name__ == "__main__":
    a = App()
    a.protocol("WM_DELETE_WINDOW", a.on_closing)
    a.mainloop()
