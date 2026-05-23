# 🎬 Thâu Hương Pháp Bảo

**Pháp bảo thu phục video từ toàn bộ động phủ — Lưu Ảnh Các (YouTube) / Đấu Chấm Các (TikTok)**

Tự động chọn chất lượng cao nhất (best video + best audio → MP4). Chỉ cần tọa độ động phủ, pháp bảo sẽ lo phần còn lại.

## Tính năng

- ✅ Tự động nhận diện tông môn — Lưu Ảnh Các hay Đấu Chấm Các
- ✅ Chọn **chất lượng cao nhất** tự động (đỉnh cấp linh phẩm)
- ✅ **Ấn lưu** — không thu lại video đã có
- ✅ **Khắc ấn** — nhúng thumbnail + metadata vào file
- ✅ Hạn mức pháp bảo, lọc niên đại
- ✅ Progress bar + nhật ký tu luyện real-time
- ✅ Thu công bất cứ lúc nào

## Cài đặt & Chạy

### Yêu cầu
- Python 3.8+
- FFmpeg (tải từ [ffmpeg.org](https://ffmpeg.org/) — hợp nhất âm thanh hình ảnh)
- Tkinter (có sẵn khi cài Python)

### Cách dùng (bản source)

```bash
git clone https://github.com/ngocxn/channel-dl-gui
cd channel-dl-gui
pip install -r requirements.txt
python app.py
```

### Build standalone (không cần Python)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "ThauHuongPhapBao" app.py
```

File exe ở thư mục `dist/`.

## Hướng dẫn

1. **🗺️ Dán tọa độ động phủ** — link kênh YouTube (`@tenkenh`) hoặc TikTok (`@username`)
2. **⚙️ Chỉnh pháp khí** — hạn mức, niên đại, kho chứa
3. **🔍 Thám Thính** — dò xét động phủ trước
4. **⬇️ Thu Phục** — pháp bảo vận hành, theo dõi tiến độ

## Download

Tải bản build sẵn từ [Releases](https://github.com/ngocxn/channel-dl-gui/releases).

---

*Linh thú AI — Ngân Nguyệt 🐲*
