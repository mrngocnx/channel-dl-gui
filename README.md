# 🎬 Channel Downloader GUI

Tải toàn bộ video từ kênh **YouTube** / **TikTok** với giao diện trực quan.

Tự động chọn chất lượng cao nhất (best video + best audio → MP4).

## Tính năng

- ✅ Giao diện CustomTkinter — đẹp, dark mode, responsive
- ✅ Hỗ trợ YouTube + TikTok
- ✅ Chọn chất lượng cao nhất tự động
- ✅ Giới hạn số lượng video
- ✅ Lọc theo ngày
- ✅ Bỏ qua video đã tải (archive)
- ✅ Nhúng thumbnail + metadata vào file
- ✅ Progress bar real-time
- ✅ Resume nếu bị gián đoạn
- ✅ Dừng bất cứ lúc nào

## Cài đặt & Chạy

### Yêu cầu
- Python 3.8+
- FFmpeg (tải từ [ffmpeg.org](https://ffmpeg.org/) — cần để merge video+audio)

### Cách chạy

```bash
# Clone repo
git clone https://github.com/ngocxn/channel-dl-gui
cd channel-dl-gui

# Cài dependencies
pip install -r requirements.txt

# Chạy
python app.py
```

### Build standalone (không cần Python)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon icon.ico --name "ChannelDL" app.py
```

File exe sẽ ở thư mục `dist/`.

## Hướng dẫn sử dụng

1. **Dán URL kênh** — YouTube (`@tenkenh`) hoặc TikTok (`@username`)
2. **Tùy chọn** — giới hạn số video, lọc ngày, chọn thư mục
3. **Phân tích kênh** — xem trước thông tin kênh
4. **Tải xuống** — bắt đầu tải, progress bar + log real-time

## Download

Tải bản build sẵn từ [Releases](https://github.com/ngocxn/channel-dl-gui/releases).
