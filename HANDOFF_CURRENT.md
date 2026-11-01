# Bàn giao DHH-learners — trạng thái ngày 2026-10-29

## Đọc trước khi tiếp tục

Bạn là AI tiếp tục dự án đang có trên máy người dùng. Trả lời bằng tiếng Việt, ngắn gọn, làm trực tiếp trong dự án. Đọc file này trước, sau đó đọc mã nguồn liên quan. `HANDOFF.md` là tài liệu nền ngày 2026-10-28; phần nói pea/bee/knee chưa có ảnh trong đó đã lỗi thời. Khi có khác biệt, ưu tiên trạng thái mới ghi ở đây và mã nguồn thực tế.

Thư mục dự án: `C:\Users\tuank\Projects\DHH-learners`.
Môi trường: Windows, PowerShell, Python trong `.venv`.

Yêu cầu gần nhất đã thực hiện: thay ba ảnh của bài **knee /n/** bằng bộ ảnh mới người dùng gửi; vẫn dùng cách trình bày và hoạt ảnh giống bài **me /m/**. Hiện người dùng yêu cầu file bàn giao này, chưa yêu cầu một tính năng tiếp theo cụ thể.

## 1. Hai app riêng biệt — tuyệt đối không mở nhầm

- **App cho người học**: `app/learner_app.py`, cổng **8502**. Đây là app người dùng muốn khi nói “mở app”, “app cho user luyện phát âm”.
- **Dev/prototype**: `app/streamlit_app.py`, cổng **8501**. Có phân tích, hiệu chuẩn, log, debug. Chỉ mở khi người dùng yêu cầu dev.
- Hai app dùng chung scoring trong `app/fricative/`, nhưng giao diện phải tách biệt.
- Người dùng muốn mở app trong **trình duyệt mặc định trên máy của họ**, không chỉ trong browser pane của AI.

URL người học:

- `http://localhost:8502/?word=knee` — bài vừa sửa gần nhất.
- Các bài khác: `?word=see`, `she`, `fee`, `pea`, `bee`, `me`, `cheat`.
- Kiểm tra riêng một bước: `http://localhost:8502/?word=knee&step=2&hold=1`.

## 2. Quyền và cách làm việc người dùng đã xác nhận

- Người dùng đã nói cho phép chủ động can thiệp **dự án đang làm**: chỉnh code, thêm/thay ảnh, chạy lại app, mở browser. Không hỏi lại xác nhận các thao tác thường lệ đó.
- Vẫn tuân thủ quyền sandbox của môi trường. Đọc ảnh ổ D: và mở browser/khởi động app nền trước đây cần `require_escalated`; dùng cơ chế cấp quyền của công cụ khi cần, không cố vượt qua.
- Quyền sửa dự án không tự mở rộng thành quyền thay đổi thiết lập bảo mật hệ thống, công khai dữ liệu hay xóa dữ liệu riêng.
- Với /n/, yêu cầu chính xác là **“tương tự như m, giống cái m mọi thứ nha, k làm khác”**. Giữ player, thời gian, kiểu hiệu ứng, check cards, pause/jump/speed giống /m/; chỉ thay nội dung và tọa độ theo ảnh /n/.
- Dùng hình người dùng cung cấp. Không tự vẽ lại ảnh hoặc thay phong cách khi chưa được yêu cầu.
- Khi nói “ảnh động” trong công việc này, đó là **ba ảnh chạy lặp/chuyển mờ, kèm hiệu ứng vector trên ảnh**, không phải video chuyển động cơ miệng thật hay file GIF đã xuất.

## 3. Trạng thái bài học hiện tại

- **see /s/**: một ảnh `mouth_s.jpg`, hoạt ảnh spotlight/marks theo `Motion`, tips, hình rắn và mắt.
- **she /ʃ/**: ảnh `mouth_sh.jpg` và tips; không có chuỗi nhiều ảnh.
- **fee /f/**: ảnh `mouth_f.jpg` và tips; không có chuỗi nhiều ảnh.
- **me /m/**: mẫu chuẩn để làm /n/. Ba ảnh `me_1.jpg`, `me_2.jpg`, `me_3.jpg`, mỗi bước **4–5–4 giây**. Có ring, arrow, airflow, throat vibration, ba check cards EN/ZH/pinyin dưới mỗi bước.
- **pea /p/**: `pea_1.png`, `pea_2.png`, `pea_3.png`, **4–3–4 giây**. Khép môi → bật hơi → ee. Hiện hiển thị nguyên ảnh có chữ/check cards tích hợp sẵn; `checks=()` và không thêm overlay shapes. Không được mô tả là giống hoàn toàn cấu hình /m/.
- **bee /b/**: `bee_1.png`, `bee_2.png`, `bee_3.png`, **4–3–4 giây**. Khép môi → mở nhẹ → ee. Cấu hình tương tự pea: nguyên ảnh, `checks=()`, không thêm overlay shapes.
- **knee /n/**: ba ảnh **mới nhất** `knee_1.png`, `knee_2.png`, `knee_3.png`, **4–5–4 giây**, check cards và overlay giống cơ chế me. Chi tiết ở mục 4.
- **cheat /tʃ/**: chưa điền bộ ảnh hướng dẫn trong `LESSONS`; các phần thiếu dùng placeholder theo hệ thống hiện có.
- Các hình nghĩa từ, hình biểu tượng âm và nghĩa tiếng Hoa còn thiếu ở nhiều bài. Không coi bài học đã hoàn chỉnh chỉ vì đã có ảnh miệng.
- `knee` vẫn không highlight chữ nào: cách xử lý k câm chưa được người dùng quyết định.

## 4. Bộ ảnh /n/ mới nhất và cách tích hợp

Đã sao chép vào `app/learner/assets/` theo thứ tự:

1. `D:\SCIENCE RESEARCH\SPECTROGRAM\Step 1_ Tongue contact for _n_-1.png` → `knee_1.png`.
2. `D:\SCIENCE RESEARCH\SPECTROGRAM\Step 2_ _n_ Sound and Nasal Airflow-2.png` → `knee_2.png`.
3. `D:\SCIENCE RESEARCH\SPECTROGRAM\Step 3_ Open into ee—knee-3.png` → `knee_3.png`.

**Không dùng lại bộ cũ** `n 1.png`, `n2.png`, `n3.png`. Các file đích knee đã được ghi đè bằng bộ mới.

Nội dung:

- Bước 1: đầu lưỡi chạm lợi sau răng trên, môi hơi mở, đặt tay lên cổ.
- Bước 2: giữ đầu lưỡi ở trên, luồng khí qua mũi, phát tiếng nnn và cảm nhận rung.
- Bước 3: nhả đầu lưỡi, luồng khí qua miệng, giữ giọng khi chuyển sang ee/knee.

`Step` được thêm trường tùy chọn `display_height: int | None = None` ở cuối dataclass. Cả ba bước knee đặt `display_height=922` để chỉ hiện phần trên của ảnh, ẩn các check cards đã in trong ảnh; ba check cards được dựng thành HTML bên dưới như me.

Trong `mouth_steps()` (`app/learner/motion.py`):

```python
width, height = Image.open(lesson.steps[0].image).size
height = lesson.steps[0].display_height or height
```

CSS của player nhiều ảnh có `object-position: top`, kết hợp `object-fit: cover` và tỷ lệ stage. Đây là crop bằng giao diện; file PNG gốc trong assets vẫn đầy đủ. Các bài không đặt `display_height` dùng chiều cao ảnh nguyên bản. Giả định hiện tại: ba ảnh một bài có cùng kích thước và cùng vùng hiển thị.

Tọa độ overlay đã chỉnh theo bộ mới trong `LESSONS["knee"]`:

- Bước 1: ring đầu lưỡi `(678,254)`, mũi tên nâng lưỡi từ `(635,320)`, ring bàn tay `(1095,760)`.
- Bước 2: airflow đi lên qua khoang mũi, ring mũi `(715,176)`, ring đầu lưỡi `(678,254)`, wave cổ `(980,655)` và `(1220,655)`.
- Bước 3: airflow qua miệng, ring nhả đầu lưỡi `(642,480)`, wave cổ ở cùng hai vị trí bước 2.
- Tọa độ là pixel của ảnh nguồn, không phải tọa độ màn hình. Khi đổi ảnh cần căn lại shapes.

## 5. File quan trọng

- `app/learner_app.py`: entry của người học, chọn bài bằng query param `word`; nhánh `lesson.steps` gọi `mouth_steps()`.
- `app/learner/lessons.py`: dataclass `Lesson`, `Step`, `Motion`; toàn bộ nội dung bài, asset paths, thời gian, checks, tọa độ hiệu ứng.
- `app/learner/motion.py`: Streamlit components v2, JS/CSS của animation; `mouth_motion()` cho một ảnh/spotlight, `mouth_steps()` cho nhiều ảnh.
- `app/learner/screen.py`: bố cục, style, `_image_uri()` đọc ảnh thành data URI. Hàm này có `lru_cache`, nên ghi đè file ảnh cùng tên cần restart để xóa cache.
- `app/learner/mic.py`: nút thu âm người học.
- `app/learner/result.py`: gọi scoring và dựng kết quả; bản ghi thay panel thu âm, nút Record again để quay lại.
- `app/learner/tongue.py`: minh họa kết quả /s/ và /ʃ/.
- `app/fricative/`: audio, segmentation, scoring, recogniser, GOP, calibration, log.
- `app/tests/test_learner_lessons.py`: kiểm tra nội dung/assets bài học.
- `app/METHOD_NOTES.md`: lịch sử phương pháp và bằng chứng scoring; đọc khi chỉnh scoring.
- `HANDOFF.md`: tài liệu nền cũ, còn hữu ích về scoring và môi trường nhưng trạng thái nội dung đã lỗi thời một phần.

## 6. Chạy và mở app

Chạy foreground trong PowerShell từ thư mục dự án:

```powershell
Set-Location 'C:\Users\tuank\Projects\DHH-learners\app'
..\.venv\Scripts\python.exe -m streamlit run learner_app.py --server.port 8502 --server.headless true
```

Chạy nền, không mở cửa sổ terminal thừa:

```powershell
Start-Process -FilePath 'C:\Users\tuank\Projects\DHH-learners\.venv\Scripts\python.exe' -ArgumentList '-m streamlit run learner_app.py --server.port 8502 --server.headless true' -WorkingDirectory 'C:\Users\tuank\Projects\DHH-learners\app' -WindowStyle Hidden
Start-Process 'http://localhost:8502/?word=knee'
```

Khi sửa helper module/ảnh, **restart server 8502**, không chỉ refresh. Trước khi dừng process, xác định listener và kiểm tra đó đúng là app người học; chỉ dừng process liên quan, không kill toàn bộ Python hoặc các app khác.

```powershell
Get-NetTCPConnection -LocalPort 8502 -State Listen -ErrorAction SilentlyContinue
```

Health URL: `http://localhost:8502/_stcore/health`. Sandbox từng chặn socket localhost; lỗi “socket forbidden by access permissions” không đủ kết luận app đã hỏng. Nếu cần kiểm tra ngoài sandbox, dùng escalation đúng quy định.

App đã được khởi động lại và lệnh mở browser đã thành công sau lần thay ảnh n gần nhất. **Không suy ra process vẫn chạy ở phiên tiếp theo**; kiểm tra lại. Trước đây assistant từng mở nhầm cổng 8501 và tuyên bố app mở khi chưa xác minh nội dung; tránh lặp lại.

## 7. Kiểm tra đã làm và giới hạn xác minh

Lệnh gần nhất, từ root dự án:

```powershell
.\.venv\Scripts\python.exe -m pytest app\tests\test_learner_lessons.py -q
```

Kết quả sau thay bộ n mới: **18 passed**.

Giới hạn quan trọng:

- Các test này xác nhận asset tồn tại và một số cấu trúc bài; không chứng minh animation thực tế hiển thị đúng trên browser.
- Trong các lượt thêm pea/bee/knee ở chat này, chưa chụp và kiểm tra giao diện từng bước bằng browser sau thay đổi. Vị trí overlay n được căn dựa trên ảnh đính kèm, chưa được xác nhận bằng screenshot runtime.
- Chưa thử microphone thật cho những thay đổi ảnh này; không có chỉnh sửa scoring trong các lượt đó.
- Nếu cần tiếp tục xác minh, mở knee với `step=1/2/3&hold=1`, kiểm tra ảnh/crop/check cards/overlay rồi thử play, pause, tốc độ 0.5× và vòng lặp; so sánh me để bảo đảm cùng cách trình bày.
- Chưa có yêu cầu xuất GIF/video độc lập. Không tuyên bố đã tạo GIF.

## 8. Scoring và môi trường nền (không sửa trong lượt ảnh)

Theo tài liệu bàn giao trước:

- Fricatives /s ʃ f/: pipeline đo âm học, calibration, recogniser và reconcile.
- /p b m n tʃ/: GOP dựa trên wav2vec2 khi có model; fallback âm học khi thiếu model.
- Model/checkpoint lớn có thể nằm ở `app/assets/model/w2v_phone`; hãy kiểm tra thực tế trước khi báo có/không. Không lặp thông tin cũ từ ngày cài repo rằng model chắc chắn chưa có.
- Các ngưỡng là thử nghiệm; chưa xác thực trên trẻ em hoặc người DHH. Vấn đề /b/ bị nghe thành /m/ vẫn là ghi chú chưa giải quyết trong tài liệu cũ.
- Windows từng chặn binary pandas 3.x bằng Smart App Control; tài liệu cũ ghi pandas 2.3.3 đang dùng được. Không tắt chính sách bảo mật để chữa dependency.
- D1 samples không được phân phối trong repo; test phụ thuộc dữ liệu có thể thiếu. Phân biệt lỗi thiếu dữ liệu với regression bằng cách đọc lỗi thực tế.
- `app/logs/audio` có giọng nói riêng của người dùng: không tự tải lên, commit hoặc chia sẻ.
- Repo ban đầu tải ZIP do Git thiếu. Không giả định có `.git`, remote hoặc commit history. Các thay đổi hiện là file local; chưa có push/PR trong chuỗi công việc này.

## 9. Nguồn ảnh pea/bee để tra cứu nếu cần

Pea:

1. `D:\SCIENCE RESEARCH\SPECTROGRAM\English _p__ Lips closed, voice off-1.png`.
2. `C:\Users\tuank\Downloads\Release _p_ with a short puff-2.png`.
3. `C:\Users\tuank\Downloads\Frame 3_ Say ee — pea-3.png`.

Bee:

1. `D:\SCIENCE RESEARCH\SPECTROGRAM\B Step 1_ Low Relaxed Tongue-1.png`.
2. `C:\Users\tuank\Downloads\Step 2_ Gentle tongue release-2.png`.
3. `C:\Users\tuank\Downloads\Step 3_ Ee-Bee Low Tongue Guide-3.png`.

Assets đã sao chép vào dự án; chạy app không phụ thuộc các đường dẫn nguồn trên ổ D:/Downloads.

## 10. Cách tiếp tục từ đây

1. Đọc file này và những module cần thiết; không bắt người dùng kể lại toàn bộ dự án.
2. Nếu người dùng chỉ yêu cầu mở app: kiểm tra/chạy learner trên 8502 và mở trình duyệt mặc định của họ.
3. Nếu người dùng gửi bộ ảnh mới: gắn đúng bài, đúng thứ tự; giữ cơ chế họ chỉ định, căn overlay theo hình mới, restart và kiểm tra thực tế.
4. Với knee, bộ ảnh trong mục 4 là bộ đang được dùng. Không hoàn nguyên theo tài liệu cũ.
5. Các tính năng chưa có (cheat, hình nghĩa từ, Map/star rules, kiểm chứng scoring...) là việc có thể làm sau, không phải yêu cầu mới đã được chốt. Tiếp tục theo chỉ dẫn tiếp theo của người dùng.
