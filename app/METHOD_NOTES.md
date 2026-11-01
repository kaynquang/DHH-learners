# Ghi chú phương pháp: những thay đổi so với bản đầu

Ghi lại mọi thay đổi trong các phiên làm việc gần đây, kèm lý do, tham số, bằng chứng từ log, và những gì còn dở.
Dùng làm nguyên liệu để viết phần Method / Limitations sau này. Ngày ghi: 2026-10-26.

Quy ước: **[ĐANG DÙNG]** = nằm trong luồng chạy hiện tại. **[ĐÃ THAY]** = từng làm, nay bị phương pháp khác thay (code có thể còn nằm lại).

---

## 0. Bản đầu (trước các thay đổi này)

- Chấm 14 từ (see, sip, sun, she, ship, shoe, fee, fan, food, pea, bee, me, knee, cheat) trên một thanh chọn "Target word".
- Fricative (/s/, /ʃ/, /f/): đo bằng Praat (CoG, relative amplitude, ...), ngưỡng cố định hoặc ngưỡng đã hiệu chỉnh theo giọng người học (trang Calibrate, 6 bản ghi see/she/fee).
- Stops /p/, /b/: đo VOT (burst → voicing đầu tiên), ngưỡng 30 ms.
- Nasal /m/, /n/: chỉ chấm được khi có phone recogniser (wav2vec2); không có thì app báo "cần recogniser".
- Affricate /tʃ/: đo rise time của tiếng xì (burst finder), hoặc probe trên đặc trưng wav2vec2.
- Thu âm bằng `st.audio_input` (phải bấm dừng). Calibration chỉ nằm trong `st.session_state`, mất khi tải lại.
- Recogniser (torch, transformers, checkpoint) chưa cài, nên mọi nhánh dùng recogniser đều không chạy.

---

## 1. Giao diện chọn âm **[ĐANG DÙNG]**

- "Target word" → **"Target sounds"**: 8 âm, mỗi âm một nút: /s/, /ʃ/, /f/, /p/, /b/, /m/, /n/, /tʃ/.
- Mỗi âm dùng một từ đại diện (từ đầu tiên của âm đó trong `config.py`): see, she, fee, pea, bee, me, knee, cheat. Dòng caption: "Say the word “…”".
- Lý do: các từ trùng âm (sip, sun, ship, shoe, fan, food) không thêm thông tin khi chấm phụ âm đầu.
- File: `app_pages/practice.py`.

## 2. Thu âm **[ĐANG DÙNG]**

- Thay `st.audio_input` bằng component Streamlit v2 tự viết (`views/autorecord.py`): bấm Record, **tự dừng sau 3 s** (`RECORD_SECONDS`), có nút **Stop** dừng sớm.
- Ghi bằng `MediaRecorder`, giải mã bằng `decodeAudioData`, đổi sang WAV 16-bit mono ngay trong trình duyệt, gửi base64 về Python.
- **Micro thô:** `getUserMedia({echoCancellation:false, noiseSuppression:false, autoGainControl:false})`.
  - Lý do (từ log): mặc định trình duyệt bật AGC và khử ồn. Bản thu bị clip (đỉnh sóng = 1.0), phần im lặng đầu bản bị xóa thành im lặng tuyệt đối (−120 dB), phụ âm /b/ yếu bị mất. Recogniser nghe "m" thay vì "b".
  - Sau khi tắt: đỉnh sóng 0.1–0.3, hết clip; nhưng nhiễu nền lộ ra (xem §7).
- Player: dạng sóng + vạch đỏ chạy ngang khi phát, bấm vào dạng sóng để nhảy tới đoạn đó (`playback()`).
  - Lỗi đã gặp: `getComputedStyle(parentElement)` lỗi vì `parentElement` của component là shadow root; sửa bằng đọc màu từ canvas.
- Dùng ở cả Practice và Calibrate. Đã bỏ player `st.audio` trùng lặp trên Practice.
- Chưa giải thích: nhiều bản ghi dài 0.7–2.2 s dù đặt 3 s (có thể do bấm Stop sớm, chưa kiểm tra).

## 3. Phone recogniser cài và chạy GPU **[ĐANG DÙNG]**

- Cài: torch 2.6.0+cu124, transformers 5.20.2, huggingface_hub (qua `uv pip`, venv `.venv`).
- Checkpoint: `facebook/wav2vec2-xlsr-53-espeak-cv-ft` (khoảng 1.2 GB, vào `assets/model/w2v_phone`, đầu vào 16 kHz, vocabulary IPA có cả ký hiệu thanh điệu như `u5`).
- GPU: RTX 3050 (4 GB VRAM). `phoneme_check._device()` chọn `cuda` nếu có, không thì `cpu`; model và tensor được đưa lên GPU, kết quả đưa về CPU.
- Tốc độ đo: khoảng 0.3 s mỗi bản ghi cho chấm GOP (53 bản trong 15 s, kể cả nạp model lần đầu).
- `requirements.txt`: ghi chú (comment) cách cài torch bản CUDA.

## 4. Hồ sơ hiệu chuẩn (profile) **[ĐANG DÙNG]**

- Calibration lưu ra đĩa: `profiles/<tên>.json` gồm `mu`, `sd`, `n_tokens` và thang đo của 6 bản (không lưu âm thanh).
- Sidebar: chọn profile, "Add profile" (tên tối đa 30 ký tự, chỉ chữ/số/khoảng trắng/`_`/`-`), "Delete this profile". Profile dùng lần cuối được nhớ (`profiles/_last.txt`) và nạp lại khi mở app.
- Calibrate xong thì lưu vào profile đang chọn; "No profile" thì chỉ dùng trong phiên.
- Biến môi trường `FRICATIVE_PROFILES` đổi thư mục (test dùng thư mục tạm).
- Chỉ áp dụng cho fricative (/s/, /ʃ/, /f/). Các âm khác dùng GOP, không cần hiệu chuẩn.
- Code: `fricative/calibrated.py` (`save_profile`, `load_profile`, `create_profile`, ...), `streamlit_app.py`.

## 5. Log để debug **[ĐANG DÙNG]**

- Mỗi bản ghi được chấm sẽ lưu: `logs/audio/<id>.wav` (âm thanh đúng như đã chấm) và `logs/entries/<id>.json`.
- `id` = md5(audio + từ mục tiêu). Chấm lại cùng bản ghi thì cập nhật mục cũ, giữ cờ và ghi chú của người học.
- Trường trong mỗi mục: thời gian, từ, âm mục tiêu, nguồn (Record/Upload/Sample), profile, `verdict` (nhãn, dấu, màu, âm nghe được, thông điệp), `details` (số đo, xác suất GOP, ...), `settings` (có recogniser không, có hiệu chuẩn không, ngưỡng), `flagged`, `note`.
- Cả các trường hợp **không chấm** ("Not scored" kèm lý do) cũng được ghi, vì đó là chỗ người học nói đúng mà app không nhận ra.
- Giao diện: dưới kết quả có nút **"Said it right but the result is wrong?"** (ghi chú + cờ), **Discard** (xóa bản ghi và không lưu lại), **Keep in log**; công tắc sidebar **"Save recordings to the log"** (mặc định bật). Trang **Log**: bảng, lọc "Only flagged" và theo âm, nghe lại, sửa ghi chú, xem JSON số đo, nút **Delete logs** (xóa các bản không cờ, hoặc xóa tất cả có ô xác nhận).
- Biến môi trường `FRICATIVE_LOGS` đổi thư mục (test dùng thư mục tạm).
- Code: `fricative/reclog.py`, `app_pages/log.py`.

---

## 6. Những gì log cho thấy (bằng chứng, theo thứ tự thời gian)

Dữ liệu: log hiện có 80 bản (26 cờ) lúc phân tích cuối, của một người nói, một micro, một phòng. Nhãn đúng/sai là do chính người nói tự ghi ("tôi nói đúng"), chưa có người thứ hai xác nhận.

1. **Micro mặc định làm méo:** clip, im lặng bị xóa, /b/ bị nghe thành /m/ (xem §2).
2. **Nền VOT sai khi im lặng bị xóa:** sàn nhiễu tính ở phân vị 5% = −120 dB, nên chút nhiễu đầu tiên bị coi là tiếng bật. Đã thử kẹp sàn không thấp hơn đỉnh 50 dB (`FLOOR_BELOW_PEAK_DB`, `stops.py`); 3 bản /b/ có VOT 130/72/384 ms rơi về 2/8/234 ms. Chỉnh theo rất ít bản, chưa kiểm chứng trên /p/ có tiếng bật yếu.
3. **Phòng ồn:** sau khi tắt khử ồn, nhiễu trong dải 1.5–7.5 kHz chỉ nhỏ hơn giọng khoảng 20 dB và kéo dài cả giây trước khi nói. Máy dò tiếng bật và probe `probability_p` cùng đọc nhầm đoạn đó (VOT 540–850 ms, probe luôn báo /p/ khoảng 99%). Trong 21 bản /b/ gần nhất chỉ 5 bản có VOT < 30 ms (tức luật VOT nói /b/).
4. **Giải mã phụ âm đầu ổn hơn đo tay:** recogniser giải mã đúng /b/ (bee → "b i"), /p/ (pea → "p"), /tʃ/ (cheat → "tʃ i t", "tɕ i", "dʒ i s") trong khi luật VOT và rise time sai.
5. **/b/ nghe thành /m/ hoặc /n/:** nhiều bản /b/ bị recogniser nghe là /m/ (xác suất 0.75–1.0). Lọc thông cao (100–400 Hz) trước recogniser không ổn định (có bản đổi, có bản không, làm hỏng "me"), nên **không dùng**. Phân biệt murmur/burst bằng số đo thấp/cao tần không tách được bản đúng và sai. Chưa biết đây là lỗi recogniser với giọng và micro này, hay /b/ thực sự bị mũi hóa.
6. **Phụ thuộc nguyên âm:** người học đọc "bu", "ba", ... vào mục tiêu "bee". Recogniser giải mã phụ âm đầu thành b/m/n/p gần như ngẫu nhiên với /u/ (nó chỉ được thử với "bee"/"pea"). Với /i/ ổn hơn (8 bản "b i" ra /b/ đúng, vài bản vẫn ra /m/).
7. **"cheat":** rise time đo ra tiếng xì dài 750–1650 ms (vô lý, là nhiễu), nên mọi bản bị chấm /ʃ/ ("nhầm ch thành sh"). Giải mã đúng /tʃ/ ở 5/8 bản.
8. **/n/:** hoạt động tốt (khoảng 99% theo ghi chú người dùng). **/m/:** lỗi khi đọc "mu" (recogniser giải mã trống) và có bản "me" ra /n/.

---

## 7. Chuỗi phương pháp đã thử cho /p/, /b/, /tʃ/ và vì sao thay

| Bước | Nội dung | Trạng thái |
|---|---|---|
| a | Nới VOT: `measure_vot(strict=False)` (không từ chối khi VOT > 120 ms), hiện cảnh báo | Vẫn dùng ở nhánh không có recogniser |
| b | Kẹp sàn VOT (`FLOOR_BELOW_PEAK_DB = 50`) | Vẫn dùng ở nhánh không có recogniser |
| c | Dùng phụ âm giải mã (`first_consonant`) làm quyết định chính: `classify_stop_heard` | **[ĐÃ THAY]** bởi GOP |
| d | Cổng (gate) không chặn p/b khi nghe ra M/N; chấm đỏ "You said /m/" thay vì "Not scored" | **[ĐÃ THAY]** |
| e | Kiểm tra nguyên âm phải là /i/ (`first_vowel`, `is_ee`), nguyên âm khác thì từ chối | **[ĐÃ THAY]** (GOP không phụ thuộc nguyên âm) |
| f | Thêm `dʒ`, `d͡ʒ`, `ʤ`, `ʧ` vào nhóm CH của gate; "cheat" dùng giải mã làm quyết định | Danh sách CH vẫn còn; quyết định **[ĐÃ THAY]** |
| g | **GOP** (§8) | **[ĐANG DÙNG]** |

Mã còn nằm lại chưa dùng trong luồng chính: `stops.classify_stop_heard`, `stops.classify_stop_probe`, `phoneme_check.first_vowel`, `phoneme_check.is_ee`, `phoneme_check.probability_p`, `phoneme_check.probability_ch`, `phoneme_check.nasal_reading`, `nasals.classify_nasal`. Nên dọn hoặc ghi rõ khi viết bài.

---

## 8. GOP (Goodness of Pronunciation) cho /p/ /b/ /m/ /n/ /tʃ/ **[ĐANG DÙNG]**

Mục tiêu: một cách chấm **không cần hiệu chuẩn theo giọng người học**, không phụ thuộc nguyên âm, và biết nói "không chắc".

**Ý tưởng.** Thay vì giải mã cả bản ghi rồi lấy phụ âm đầu (argmax), hỏi: trong khoảng 0.45 s đầu của lời nói, mỗi phụ âm ứng viên c có khả năng thế nào, theo sau là *một nguyên âm bất kỳ*?

**Thuật toán** (`fricative/gop.py`, `phoneme_check.log_posteriors`, `phoneme_check.vocabulary`):
1. Chạy wav2vec2-CTC trên cả bản ghi, lấy log xác suất mỗi 20 ms (frames × vocabulary). Âm thanh chuẩn hóa trung bình 0, độ lệch chuẩn 1.
2. Tìm khung lời nói đầu tiên: khung đầu có xác suất blank < 0.9 (`ACTIVE_BLANK_P`). Cắt từ 3 khung trước đó (`PRE_FRAMES`) và dài 22 khung (`WIDTH_FRAMES`, khoảng 0.45 s).
3. Với mỗi ứng viên c trong **tập dễ nhầm** và mỗi nguyên âm v trong vocabulary (nguyên âm đơn, không có thanh điệu), tính log-likelihood CTC của chuỗi `[c, v]` (thuật toán forward, tự cài bằng numpy). Gộp qua mọi v và mọi cách viết của c bằng logsumexp: `L(c)`.
4. Chuẩn hóa trong tập dễ nhầm: `P(c) = L(c) / Σ L(c')`. Đây là điểm GOP của âm mục tiêu.

**Tập dễ nhầm và cách viết (`CONFUSABLE`, `VARIANTS`):**
- /b/: b, p, m, d, v. /p/: p, b, m, t, f. /m/: m, n, b, p. /n/: n, m, d, t, l. /tʃ/: tʃ, ʃ, t, s, d.
- Cách viết: p ∈ {p, pʰ}; t ∈ {t, tʰ}; ʃ ∈ {ʃ, ɕ}; tʃ ∈ {tʃ, tɕ, dʒ, (t ʃ)}.

**Verdict** (ngưỡng tạm, chưa hiệu chuẩn trên dữ liệu công khai):
- P(đích) ≥ 0.80 → xanh (Correct).
- 0.50 ≤ P(đích) và đích là ứng viên cao nhất → vàng (Almost).
- Ứng viên khác cao nhất với P ≥ 0.60 → đỏ, "You said /x/" (x là âm nghe được).
- Còn lại → **không chấm** ("không chắc, hãy nói lại"), vẫn ghi vào log.
- Không có lời nói (không khung nào có blank < 0.9) → không chấm.

**Kết quả thử trên 53 bản ghi trong log** (chỉ là phân bố kết quả, không phải độ chính xác, vì nhãn đúng/sai chưa độc lập):

| Âm | Xanh | Vàng | Đỏ | Không chắc | Không có tiếng |
|---|---|---|---|---|---|
| /tʃ/ | 5 | 2 | 1 | 0 | 0 |
| /n/ | 4 | 1 | 1 | 2 | 1 |
| /m/ | 3 | 2 | 2 | 0 | 0 |
| /b/ | 7 | 0 | 12 | 2 | 0 |
| /p/ | 2 | 0 | 4 | 2 | 0 |

- 3 bản "bee" người dùng đánh dấu "báo /p/ nhầm" nay có P(b) = 0.98.
- "cheat": 7/8 bản có /tʃ/ là ứng viên cao nhất (trước đó gần như mọi bản bị chấm /ʃ/).
- Các bản /b/ bị nghe /m/ vẫn đỏ (P(b) 0.00–0.30): đây là giới hạn của recogniser với bản thu này, chưa phân biệt được "model sai" với "phát âm mũi hóa thật". Cần người nghe thứ hai.

**Tích hợp (`app_pages/practice.py`):**
- Nếu có recogniser và âm mục tiêu thuộc {b, p, m, n, tʃ}: dùng GOP; hiện xác suất của từng ứng viên dưới spectrogram.
- Fricative (s, ʃ, f): vẫn dùng pipeline cũ (đo Praat + hiệu chuẩn + `reconcile` với recogniser). Có cổng loại âm (gate): không nghe thấy phụ âm → không chấm; nghe ra loại khác (ví dụ stop thay vì fricative) → không chấm.
- Không có recogniser: dùng luật acoustic cũ (VOT cho p/b, rise time/probe cho tʃ, thông báo "cần recogniser" cho m/n).
- Test: `tests/test_gop.py` (12 test, không cần model: forward CTC, chuẩn hóa, vowel-agnostic, ngưỡng verdict).

**Vòng đánh giá sau khi dùng GOP (log 118 bản, 32 cờ; 60 bản từ 12:15 trở đi):**
- Ghi chú của người học cho thấy họ thử "bad", "bu", "bờ" (b + nguyên âm khác) trên mục tiêu /b/ và "mu" trên mục tiêu /m/. Các bản có nhãn rõ: "bee thì đúng" và "bad thì đúng" ra /b/ (P = 0.85 và 0.99); "bad bị nghe là m" (P(b) = 0.06), "bu và bờ" (P(b) = 0.20, top = m); "moon thì đúng" (P(m) = 0.97); "mu nhầm thành n" (P(m) = 0.10).
- Lỗi còn lại tập trung ở /b/ trước /a/, /u/, /ə/ (bị nghe là /m/) và /m/ trước /u/ (bị nghe là /n/). Đây là lỗi hệ thống của recogniser trên bản thu này, không phải lỗi ngưỡng.
- **Thử model thứ hai** `facebook/wav2vec2-lv-60-espeak-cv-ft` (cùng vocabulary): không tốt hơn (ví dụ "bee thì đúng" tụt từ P(b) 0.85 xuống 0.12; "bad bị nghe là m" vẫn 0.02), hai model chỉ đồng ý âm cao nhất ở 43/60 bản. Đồng ý trên "bad → m" cho thấy tín hiệu thật sự mơ hồ hoặc bị nhiễu, không chỉ là sai sót một model. Không dùng, đã xóa checkpoint. Ensemble hai model chỉ đổi lỗi thành "không chắc", chưa chứng minh có lợi.
- **Đã thêm công cụ gỡ lỗi:** trên trang Practice, với /b/ /p/ /m/ /n/ /tʃ/ hiện thêm (1) đồ thị xác suất từng ứng viên theo thời gian, vùng GOP được tô; (2) chuỗi phone mà recogniser giải mã (kèm thời điểm); (3) spectrogram có đánh dấu vùng phân tích. Log lưu thêm `decoded_phones`, `end_s`. Mục đích: xem /m/ hay /b/ nổi lên ở đâu trong từ, và có bị lấn bởi nhiễu đầu bản ghi không.

**Hạn chế đã biết của GOP:**
- Ngưỡng 0.8/0.5/0.6 là tạm, chưa tính từ tập có nhãn (nên dùng L2-ARCTIC hoặc tập tương tự), chưa đo FAR/FRR.
- Recogniser huấn luyện chủ yếu trên giọng người nghe bình thường; chưa đánh giá trên giọng người khiếm thính.
- Chỉ cắt cửa sổ cố định 0.45 s từ khung lời nói đầu tiên; nhiễu giải mã thành phụ âm ở đầu bản ghi sẽ kéo cả cửa sổ đi sai.
- Phụ thuộc xác suất blank < 0.9 để tìm lời nói; bản ghi cực nhỏ hoặc bị cắt đầu có thể bị bỏ.
- /b/ ↔ /m/ ↔ /n/ (đều khép môi/mũi) là cặp khó nhất trong dữ liệu hiện có.

---

## 8b. App người dùng (learner app) **[ĐANG DÙNG]**

- Entry riêng `learner_app.py` (port 8502), tách khỏi app Dev (`streamlit_app.py`, port 8501). Giao diện theo mockup `S mockup pdf.pdf` (thiết kế gốc trong `S - mockup.zip`); mã trong `learner/` (`lessons.py` nội dung, `screen.py` giao diện, `mic.py` nút thu, `result.py` chấm và hiện kết quả, `tongue.py` hình miệng).
- Mới chỉ màn luyện một từ. Nội dung đầy đủ chỉ có cho "see"; 7 từ còn lại để ô "to be added". Chưa có Map, luật cộng sao, nút sang từ kế.
- Thu: cùng cách như app Dev (micro thô, WAV tạo trong trình duyệt), tự dừng 3 s, Space để thu/dừng. Sau khi thu, nút mic được thay bằng kết quả; nút "Record again" đưa nút mic trở lại.
- **Chấm /s/, /ʃ/, /f/ dùng đúng quy trình của app Dev**, gom thành một hàm `fricative/pipeline.py::score_fricative`: cổng loại âm của recogniser → ranh giới tiếng xì → số đo → luật ngưỡng → (hiệu chuẩn nếu có) → kiểm tra tiếng xì bằng recogniser và `reconcile`. App người dùng nạp profile hiệu chuẩn dùng gần nhất, như app Dev khi mở lại. Đối chiếu trên 31 bản ghi fricative trong log: nhãn giống app Dev ở cả 31 bản. Việc kéo thanh trượt chỉnh ranh giới tiếng xì (có ở app Dev) không có ở app người dùng: không tìm được ranh giới thì không chấm.
- **Chấm /b/, /p/, /m/, /n/, /tʃ/ dùng GOP (§8).**
- Hình miệng + thanh trượt /ʃ/–/s/ (chỉ /s/ và /ʃ/): vị trí con trỏ lấy từ tỷ lệ /s/ so với /ʃ/ của mô hình hiệu chuẩn khi có hiệu chuẩn (cùng mô hình đưa ra nhãn đúng/sai nên hình khớp với nhãn), nếu không có thì từ trọng tâm tần số (CoG) của tiếng xì, vạch giữa là ngưỡng 4340 Hz của app Dev. Chỉ là hình minh họa âm thanh, không phải đo vị trí lưỡi. Hình bị ẩn nếu nó nằm lệch phía so với nhãn. Mốc 2000 Hz và 10400 Hz cho tư thế đầy đủ là tạm.
- **Ảnh miệng thành vòng lặp 3 bước** (`learner/motion.py`, nội dung ở `lessons.py::Motion`): vẫn dùng ảnh tĩnh (`mouth_s.jpg`), thêm lên trên một vùng sáng (phần còn lại tối đi), các dấu chuyển động (vòng nhấp nháy, mũi tên nhún, luồng khí chạy) và chữ Anh–Trung của bước đó; mỗi bước 3.6 s, lặp lại, có nút tạm dừng, nút số để nhảy bước, nút 0.5×. Lưỡi trong ảnh không chuyển động. Mới cấu hình cho /s/ ("see"): ① răng và môi, ② lưỡi (đầu lưỡi và phần trước lưỡi), ③ luồng khí và "không rung giọng". Ba bước này được đề xuất từ 4 ô nhắc, cần người có chuyên môn xác nhận. Toạ độ vùng sáng và dấu là điểm ảnh của ảnh đó; thêm âm khác thì khai báo `motions` cho bài của âm đó. `?step=2&hold=1` giữ nguyên một bước để kiểm tra.
- **Âm nói theo nhiều bước (/m/):** bài "me" dùng ba ảnh liên tiếp thay vì một ảnh (`lessons.py::Step`, `motion.py::mouth_steps`): ① Close your lips, ② Hum — mmm, ③ Open into ee — me. Mỗi bước có ảnh riêng (đã mang sẵn số bước và tiêu đề), 3 ô nhắc Anh–Trung–pinyin riêng, và thời gian hiện (4 s, 5 s, 4 s). Tự chạy lặp, có tạm dừng, nút 1/2/3 để nhảy bước, 0.5×; đổi ảnh bằng chuyển mờ nhanh, không morph vì ba ảnh không khớp tuyệt đối về vị trí. Ảnh bước ③ có lưỡi chưa đúng với /i:/ (thả lỏng); giữ nguyên ở giai đoạn dạy phụ âm, ghi chú để thay khi dạy nguyên âm. Test: `tests/test_learner_lessons.py`.
- **Hiệu ứng chuyển động lên ba ảnh của /m/** (`Step.shapes`): bước ① hai mũi tên đưa môi lại gần và vòng sáng ở bàn tay đặt lên cổ; bước ② luồng hơi chảy lên mũi và ra ngoài, vòng sáng ở mũi và môi, sóng rung tím ở cổ; bước ③ luồng hơi chảy ra qua miệng, vòng sáng ở môi, sóng rung ở cổ. Các dấu là vòng nhấp nháy, mũi tên nhún, nét đứt chạy theo đường hơi và sóng lan ra rồi mờ đi; tạm dừng thì chúng cũng dừng. Môi và lưỡi trong ảnh vẫn tĩnh. Toạ độ là điểm ảnh của từng ảnh (`lessons.py`), đã đặt lần đầu và đã kiểm trên ảnh chụp.
- **Nút chuyển giữa các âm** (không có trong mockup, theo yêu cầu): một hàng nút phía trên thẻ từ: mũi tên trước, một nút cho mỗi âm (/s/ /ʃ/ /f/ /p/ /b/ /m/ /n/ /tʃ/; âm đang mở được tô xanh), mũi tên sau; mũi tên bị khóa ở đầu và cuối danh sách. Chuyển sang âm khác thì mở bằng nút mic (xóa kết quả thu trước đó của hai âm) và đổi `?word=` trên địa chỉ. Mã: `NAV_CSS` trong `learner/screen.py`, hàm `go` trong `learner_app.py`.
- Dev vẫn còn bản sao riêng của quy trình này trong `app_pages/practice.py`; nên cho trang Dev gọi `score_fricative` để tránh hai bản lệch nhau.

---

## 8c. App người dùng: các quyết định ngày 2026-10-30 (để viết bài)

**a. Phản hồi bằng thị giác thay cho thính giác (ý tưởng cốt lõi của bài).** Nhận xét của người làm: app mới hiện nhãn, sao và thanh trượt, chưa thể hiện việc dùng spectrogram để thay phản hồi nghe cho người thiếu thính giác. Đã làm bản đầu cho /s/ và /ʃ/ (`learner/spectro.py`, `learner/mic.py`):
- *Hình sống khi đang nói*: chiều cao là cao độ tiếng xì (cao ở trên), chiều ngang là thời gian, độ đậm xanh là năng lượng (3 sắc, tính theo tiếng lớn nhất đã nghe nên không phụ thuộc bé nói to hay nhỏ).
- *Hình sau khi thu*: spectrogram đơn giản hoá (3 sắc, làm mịn, không số trên trục, chỉ lấy đoạn tiếng xì) vẽ trên ba dải xanh–vàng–đỏ; vạch đen và chấm cam đánh dấu CoG của bé.
- *Vùng đích lấy từ chính ngưỡng chấm điểm* (4340 Hz ± 300 Hz), nên hình và nhãn luôn khớp. Chưa dùng hình mẫu của giọng chuẩn: thư mục dự án chỉ có thống kê CMU ARCTIC đã trích (`assets/reference/arctic_patterns.json`: giọng bdl nam, slt nữ, 300 câu/giọng, nhãn MFA không kiểm tay), không còn âm thanh gốc. Từ đó có thể vẽ khoảng điển hình cho /s/ /ʃ/ /f/ (CoG trung vị /s/ ≈ 5279 Hz nam, 6311 Hz nữ; /ʃ/ ≈ 4260 và 4392 Hz) nhưng chưa làm. Chưa có hình cho /f/, /p/, /b/, /m/, /n/, /tʃ/ (không đo theo tần số: vùng đích phải là hình dạng đặc trưng, ví dụ khoảng lặng rồi tiếng nổ; cần quyết định).
- Mức "đơn giản hoá cho trẻ" là đề xuất, chưa có nguồn kiểm chứng cho trẻ khiếm thính.

**b. Cổng chất lượng khi luyện** (`fricative/noise.py::recording_quality`): trước khi chấm, bản thu bị từ chối (hiện thông báo, không chấm) nếu quá ồn, quá nhỏ hoặc quá to (sát mức tràn). Mức ồn nền lấy từ chính đoạn yên tĩnh nhất của bản thu (phân vị 10 của mức theo khung 25 ms) và mức giọng là phân vị 95. *Bài học về ngưỡng:* ngưỡng SNR đặt đầu tiên là 20 dB (lấy từ bước đo phòng). Log thực tế (`logs/quality.csv`, các lần thu thật) cho SNR 16 đến 24 dB trong phòng bình thường, nên ngưỡng 20 chặn nhầm bản thu tốt (người dùng đọc /ʃ/ vào trang /s/ bị báo "quá ồn"). Đã hạ ngưỡng chặn còn 12 dB. Mức "quá nhỏ" (−45 dBFS) là con số tự đặt, chưa kiểm chứng. Từ đó log còn ghi nhãn, CoG và âm nghe được cho mỗi lần thu để chỉnh ngưỡng theo dữ liệu.

**c. Luật sao** (do người làm quyết, `learner/stars.py`): vùng xanh = 3 sao; vùng vàng gần xanh = 2; vùng vàng gần đỏ = 1; đỏ = 0 sao và luyện lại. Điểm chia đôi vùng vàng (0,65 trên thang 0,5 đến 0,8) là lựa chọn của người làm code, chưa kiểm chứng. App giữ kết quả tốt nhất của từng bé trên từng từ; "đang học" sau lần thử đầu, "xong" ở 3 sao (mức 3 sao tự đặt). Map hiện sao và trạng thái thật.

**d. Phát hiện: hiệu chuẩn bằng chính âm đang học là sai về khái niệm.** Profile "test 1" (calibrate bằng see/she/fee mỗi từ 2 lần) có CoG 275 và 794 Hz cho "see", 335 và 420 Hz cho "fee", 3341 và 278 Hz cho "she": đoạn "tiếng xì" bị đo nhầm sang nền ồn hoặc nguyên âm (SNR lúc calibrate chỉ 13 đến 18 dB), nên chuẩn của người nói sai và điểm lệch theo. Nhưng còn một lỗi sâu hơn do người làm chỉ ra: với học sinh khiếm thính, chính /s/ /ʃ/ /f/ là âm đang học; bắt họ nói đúng để lấy làm chuẩn là vô lý, vì nếu họ chưa nói đúng thì app học luôn cái sai làm chuẩn, và điểm chỉ còn đo "có giống lần calibrate không". Hiệu chuẩn chỉ nên bù khác biệt thể chất (kích thước ống thanh quản, micro, phòng), đo bằng thứ không phụ thuộc phát âm âm đích.
- *Hướng đã chọn (đã làm trong app người dùng: `fricative/vtl.py`, `learner/sound_check.py`; test `tests/test_vtl.py`):* thu một nguyên âm kéo dài "aaa" hai lần; hệ số = F3 trung vị / 2625 Hz, giới hạn 0,85 đến 1,5, dịch ranh giới /s/–/ʃ/ (4340 Hz) và bề rộng vùng vàng (300 Hz) cho điểm số, các dải màu của hình và đường trượt; chấm /s/ /ʃ/ /f/ không còn dùng mô hình hiệu chuẩn từ see/she/fee. Phép đo F3 thử trên nguyên âm tổng hợp giọng nam/nữ/trẻ: lệch dưới 6%; trần formant phải theo cao độ giọng (5000 Hz dưới 160 Hz, 5500 Hz dưới 260 Hz, 7000 Hz trên đó), nếu để 5500 Hz cho giọng trẻ thì F3 bị đo thấp 600 đến 800 Hz. Chưa thử với giọng thật và chưa với trẻ em. Trang Calibrate của app Dev vẫn dùng cách see/she/fee (công cụ nghiên cứu).
- *Ý định ban đầu của mục này (giữ để đối chiếu):* thu một nguyên âm kéo dài "aaa" để suy ra hệ số tỉ lệ cho ngưỡng tần số (chuẩn hoá chiều dài ống thanh quản, VTLN), cộng đo ồn phòng; không còn bắt nói see/she/fee. Cơ sở: trong ARCTIC, điểm giữa của trung vị /s/ và /ʃ/ là ≈ 4770 Hz (nam) và ≈ 5350 Hz (nữ), tỉ lệ 1,12; tỉ lệ F3 của /a/ giữa nữ và nam theo bảng Peterson–Barney (nhớ từ tài liệu, chưa tra lại) cỡ 1,15: cùng bậc nên có thể co giãn ngưỡng theo hệ số này. Cần kiểm chứng trên giọng trẻ em, mà dữ liệu hiện có chỉ là người lớn.
- Chốt "CoG ≥ 2000 Hz" thêm vào bước calibrate see/she là sai hướng theo lập luận trên (chặn đúng những bé phát âm chưa chuẩn); sẽ bỏ cùng với bước see/she/fee.

**f. Phản hồi thời gian thực: từ spectrogram cuộn sang một chấm (người làm chọn thử, giữ cả hai để so).** Hình spectrogram cuộn lúc thu đã được làm trước (§8c.a). Người làm nhận xét hợp lý rằng nó không giúp được học sinh: (1) bé không biết nhìn vào đâu, (2) âm đầu của một từ như "see" chỉ kéo dài khoảng 0,2 s nên bé thấy hình khi âm đã hết, không kịp chỉnh, (3) hình sau khi thu đã đủ để xem lại. Phản hồi thời gian thực chỉ có ích khi bé kéo dài được âm (/s/ /ʃ/ /f/, /m/ /n/) và theo dõi một thứ đơn giản (nguyên tắc từ kiến thức chung, chưa tra tài liệu). Đã làm thành ba chế độ chọn được ngay trên màn hình (`learner/mic.py`, thanh "Live view" ở trang /s/ và /ʃ/):
- *Dot (mặc định):* một chấm di chuyển lên xuống theo độ cao tiếng xì hiện tại (trọng tâm tần số của phổ tức thời trong dải 1 đến 10 kHz, làm mượt, chỉ hiện khi có tiếng đủ lớn), màu xanh lá/vàng/đỏ theo dải đang đứng, có đuôi mờ ngắn; nhiệm vụ của bé: "giữ chấm trong vùng xanh". Dải đích là các dải của thanh trượt, lấy từ ngưỡng chấm điểm đã dịch theo kích thước giọng.
- *Game (thử, theo yêu cầu "tô sáng vùng đích"):* các thanh ngang theo từng hàng cao độ cho thấy năng lượng của bé; thanh nằm trong dải xanh có màu xanh, dải vàng màu vàng, dải đỏ màu đỏ; thanh tiến độ bên dưới đầy dần khi từ 60% năng lượng trở lên rơi vào dải xanh và tiếng đủ lớn (đủ 1 s tích lũy thì hiện 🎉). Chỉ tính thời gian ở trong vùng đích, không dạy bé hình dạng của âm. Chưa kiểm với giọng thật; ngưỡng 60% và mục tiêu 1 s là tự đặt.
- *Meter (cho /f/, `spectro.meter_levels`):* /f/ không nằm ở một dải cao độ mà là âm yếu (tiếng xì yếu hơn nguyên âm sau nó hơn 15 dB, ngưỡng chấm điểm −15 dB, lề 3 dB). Khi đang nói chưa có nguyên âm, nên mốc là mức "aaa" của chính bé lấy từ Sound Check (mặc định −28 dBFS khi chưa có). Một thanh dọc chạy theo độ mạnh hơi (RMS, dBFS): đỏ khi quá mạnh (trên mốc − 15 dB), vàng từ mốc − 18 đến mốc − 15 dB, xanh từ đó xuống tới sát nền ồn (tối đa mốc − 33 dB), xám khi quá nhẹ (có hơi, chưa có ma sát). Đo thử bằng nhiễu trắng ở −52, −44 và −30 dBFS: thanh xanh, và đỏ ở mức lớn. Hạn chế: mức tuyệt đối phụ thuộc khoảng cách và độ nhạy micro, nên có thể lệch nếu điều kiện khác lúc Sound Check. Chưa thử với giọng /f/ thật.
- *Picture:* spectrogram cuộn như bản đầu.
- *Off:* không có hình sống.
Chấm điểm vẫn theo cả từ; chưa có chế độ chấm một âm kéo dài đơn lẻ vì bộ chấm hiện tại đòi phụ âm đầu theo sau là nguyên âm. Hình sau khi thu cũng được sửa để khớp với hình sống: vẽ cả 3 s trên cùng trục thời gian, đoạn đã đo được khung giữa hai vạch và phần ngoài bị làm mờ, độ đậm lấy theo phần đã đo (trước đó hình cắt riêng đoạn tiếng xì và phóng to, nên không giống hình lúc thu). Một điểm còn mâu thuẫn: vạch CoG (số đo) và nhãn "You said /ʃ/" (do mô hình nhận dạng quyết, ghi đè số đo) có thể khác phía nhau trong cùng một lần thu; chưa xử lý. Mức "mượt" và độ nhạy của chấm chưa chỉnh với giọng thật.

**g. /f/ không được nhận (log ngày 2026-10-30, hồ sơ "kietto").** Bốn lần thu "fee" do người làm đánh dấu trong log Dev ("bình thường", "bthg", hai lần "mạnh"): ba lần không được chấm, một lần xanh. Hai lỗi độc lập: (1) *tiếng ù do hơi thổi vào micro*: "tiếng xì" tìm được dài 0,9 đến 1,3 s nhưng CoG chỉ 384 và 557 Hz, nên cổng "có tiếng xì không" (CoG < 1000 Hz) báo "No hiss found"; cắt dưới 150 Hz đưa CoG lên 3,5 đến 5 kHz. (2) *mô hình nhận dạng im lặng* trên một lần thu bình thường mà luật số đo cho vàng ("tiếng xì yếu hơn nguyên âm 16,3 dB"), nên bị bỏ ("không có /s ʃ f/ trong tiếng xì"); /f/ là âm yếu nên mô hình hay bỏ sót (nhận xét chung). Thử lọc tần thấp trên toàn bộ tín hiệu cho kết quả không đều (độ mạnh tương đối đổi từ −16,3 sang −19, −13 và −5,5 dB khi cắt 150, 300 và 500 Hz; ngưỡng −15 dB được đặt trên bản không lọc) và chỉ có 5 bản thu có thể thử lại, nên không lọc toàn bộ. Đã làm hai sửa nhỏ trong `fricative/pipeline.py`: (a) chỉ riêng cổng "có tiếng xì không" dùng bản đã cắt dưới 150 Hz (giọng trẻ bắt đầu từ khoảng 250 Hz); mọi số đo khác và mô hình nhận dạng vẫn dùng bản gốc. (b) với /f/, khi luật số đo cho /f/ mà mô hình không nghe ra gì thì hiện kết quả tối đa là vàng thay vì bỏ qua; không bao giờ xanh khi mô hình chưa xác nhận. Kết quả trên bốn bản thu đó: ba vàng, một xanh (trước: ba không chấm). Chưa kiểm tra tác động lên /s/ và /ʃ/ (không còn bản thu có nhãn để thử); các bản thu của app người dùng không lưu âm thanh.

**h. Gương môi bằng camera (thử, `learner/lipcam.py`; chỉ cho /m/ /p/ /b/).** Nơi cấu âm của /m/ /p/ /b/ là hai môi, và khác với lưỡi thì nhìn thấy được; âm thanh lại yếu ở việc phân biệt /m/ với /n/ lúc ngân (theo tài liệu: chuyển formant F2 sang nguyên âm là dấu hiệu chính, phần ù mũi yếu và không nhất quán; các nghiên cứu nhỏ, nhiều ngôn ngữ khác tiếng Anh). Cách làm: mô hình MediaPipe Face Landmarker (v0.10.21, tệp chép vào `app/static/mediapipe`, bật `enableStaticServing` trong `.streamlit/config.toml`, chạy được không cần mạng) đọc ảnh camera ngay trong trình duyệt; chỉ dùng khoảng cách môi trong trên và dưới chia cho chiều cao khuôn mặt (điểm 13, 14, 10, 152); ảnh không hiện ra, không gửi đi, không lưu, bé chỉ thấy một cái miệng hoạt hình mở và đóng theo môi và dòng "Lips together ✓ / Lips open". Chỉ chạy khi người dùng bật công tắc và bấm nút; có lời nhắc cần đồng ý của phụ huynh hoặc nhà trường. Không giúp được với /n/ (đầu lưỡi nằm sau răng) và /f/. Đã kiểm: thư viện và mô hình nạp được, camera mở được, báo "không thấy mặt" với hình thử của trình duyệt. Chưa kiểm với khuôn mặt thật: ngưỡng "môi khép" (khoảng hở dưới 0,03 chiều cao mặt) là đoán, cần chỉnh trên mặt trẻ em; độ chính xác theo ánh sáng, góc mặt, kính.

**e. Khác.** Màn Map "Sound Islands" theo mockup, vừa khít một màn hình (khung 1366 × 768 co giãn theo chiều cao cửa sổ). Bước Sound Check: bé mới chỉ vào danh sách khi bấm Save ở cuối, không trùng tên (không phân biệt hoa thường), hồ sơ đã lưu được cố định, thu lại phải qua một bước xác nhận, có nút xoá (có xác nhận). Khởi động nạp trước toàn bộ model (lần mở đầu 12 đến 15 s, các lần sau 1 đến 3,5 s). Tìm hiểu về lọc ồn: tài liệu cho thấy giảm ồn mạnh có thể làm méo giọng và làm nhận dạng kém đi (Kobashikawa 2019, SLaTE; arXiv 2512.17562); chưa có bài đo riêng lỗi /s/ sau khi lọc. Chưa lọc ồn trước khi chấm.

---

## 9. Thay đổi nhỏ khác

- `measure_vot(strict=False)`: không từ chối khi VOT > 120 ms (chỉ cảnh báo). Mặc định vẫn `strict=True` để test cũ còn đúng.
- Khi phép đo lỗi (/p/, /b/, /tʃ/), trang vẫn hiện spectrogram thay vì dừng trắng.
- `conftest.py`: `FRICATIVE_PROFILES` và `FRICATIVE_LOGS` trỏ thư mục tạm khi chạy test, để test không đụng dữ liệu thật.
- `test_app.py`: kiểm tra nhãn mới "Target sounds" và danh sách 8 âm `["/s/", "/ʃ/", "/f/", "/p/", "/b/", "/m/", "/n/", "/tʃ/"]`.
- Streamlit giữ module phụ (`views/…`, `fricative/…`) trong bộ nhớ: sửa module phụ cần **khởi động lại server** (trang trong `app_pages/` thì tự nạp lại).
- Test cũ: `test_app.py` và một phần `test_phoneme_check.py` fail vì thiếu bản ghi mẫu D1 (không phải do các thay đổi này); `test_stops.py` (21) và `test_gop.py` (12) pass.

---

## 10. Việc còn dở / hướng tiếp theo

1. **Hiệu chuẩn ngưỡng GOP** trên tập công khai có nhãn (L2-ARCTIC ...) và báo cáo độ chính xác theo người nói; kiểm tra trên giọng người khiếm thính.
2. ~~Kiểm tra chất lượng ghi âm trước khi chấm~~ — đã làm cho app người dùng (§8c.b); còn phải chỉnh ngưỡng bằng dữ liệu thật và làm cho app Dev.
3. **Người nghe thứ hai** gán nhãn các bản /b/ nghe ra /m/ để phân biệt lỗi model và lỗi phát âm.
4. **Cắt bản ghi quanh lời nói** (VAD) trước khi đưa vào model, thay cho cửa sổ cố định.
5. Áp dụng GOP cho fricative thay hoặc bổ trợ pipeline Praat/hiệu chuẩn.
6. Bỏ phiếu giữa nhiều cách đo (GOP, giải mã, đo tay) và chỉ báo xanh khi đồng ý.
7. Tìm hiểu vì sao nhiều bản ghi ngắn hơn 3 s.
8. Dọn mã đã bị thay (§7) hoặc đưa vào phụ lục.
9. Chạy lại toàn bộ test khi có đủ dữ liệu mẫu D1.

## 11. Gợi ý khi viết bài

- Phạm vi: chấm **phụ âm đầu** của 8 âm trong từ đơn; không nói rộng hơn dữ liệu.
- Kết quả đáng báo cáo: (1) tắt xử lý tự động của trình duyệt là điều kiện cần; (2) số đo acoustic cổ điển (VOT, rise time) hỏng trong phòng ồn; (3) GOP vowel-agnostic ổn định hơn nhưng /b/ ↔ /m/ vẫn khó.
- Nhãn hiện chỉ từ một người nói tự báo: ghi rõ là pilot, cần tách tập hiệu chuẩn ngưỡng và tập kiểm tra, và cần nhãn từ người nghe độc lập.

#### 8c.i  Lip mirror as a coach for /m/ (prototype, 2026-10-31)
The plain mirror only showed lips open/closed and gave no verdict. For /m/ it now also reads the microphone in the same page (loudness and share of
energy under 1 kHz, nothing stored) and puts the two together: /m/ = lips together while the voice hums; lips open while the voice sounds = another sound
(/n/ or a vowel), which is the m-versus-n cue the recording alone could not give in real time. Three boxes: lips together, hum while together, held 1 s
(a gap under 0.2 s does not break it). Guesses still to tune on real children: closed-lip limit 0.03, sound gate (room noise + 10 dB, else -50 dBFS),
low-pitch share 0.6. Not yet built: stars from the coach, /p/ and /b/ (burst and voicing before release), tests with a real face (only a fake camera
without a face was available, so the path with a face has not been run). The plain mirror stays for /p/ /b/ and behind the "Coach" switch for /m/.

#### 8c.j  "me" as /m/ then /iː/ (lip coach, prototype, 2026-10-31)
The coach continues past the hum: (1) lips together + hum for 0.5 s; (2) lips open while the sound goes on; (3) smile: lip width >= 1.15 x this child's own
closed-lip width and inner gap / face height < 0.08 (a small, wide mouth is /iː/, a tall one is "ah"); (4) hold sound + smile 1 s. If the sound stops for
0.8 s after step 2 the sequence starts again. The tongue (high and front for /iː/) cannot be seen; its trace is a high F2 (about 2.5-3 kHz, against about
1.1 kHz for "ah"), a live F2 dot is left for later and first for the Teacher view, because children's formants differ from adults' and are unmeasured here.
All three numbers are guesses, untested on a real face. Switch "Go on to ee" off to get the /m/-only coach.

#### 8c.k  A guided recorder for "me" (2026-10-31)
A fixed 3 s recording ended before a child had finished "mmm ... ee". For /m/ the recorder now knows the two sounds and follows the voice: it records from
the tap, lights "mmm" then "ee" as each is heard (0.4 s each), and stops 1.5 s after the child falls quiet (after at least 0.6 s of sound), or at 12 s,
or after 10 s of nothing. Sound gate: room noise + 10 dB (Sound Check), else -50 dBFS. Hum versus "ee": energy at 2-3.5 kHz relative to 0.1-1 kHz,
"ee" at -25 dB or more (a cheap stand-in for a high F2; a guess, untested on real voices, children's F2 is higher than adults'). The score itself
(GOP of /m/ on the recording) is unchanged. The grey line under the button shows the live numbers for tuning; to be hidden before real use.

#### 8c.l  Changes to the mechanism after 8c.k (2026-10-31): any vowel, a turn on request, a voice test, a shared button
1. **"Vowel" instead of "ee".** The fixed test for "ee" (energy at 2-3.5 kHz against 0.1-1 kHz at or above -25 dB) never fired for the user's voice. The guided
   recorder now compares with the child's own hum: after 0.4 s of hum it keeps the hum's level and its high/low ratio as a baseline, and any vowel counts when
   the ratio rises 8 dB above that baseline, or the sound is 6 dB louder than the hum, or the old absolute test is met. The target is only that the child
   moves on to a vowel; which vowel does not matter (the aim is the /m/, not the vowel). All three numbers are guesses.
2. **The sound test now needs a voice.** The lip mirror's first box lit before any hum: room noise and rumble are loud enough and sit below 1 kHz, and closed
   lips are the resting position. Noise above the gate was counted as hum, in the mirror and in the recorder. "Voiced" now also requires periodicity: the frame's
   best self-similarity at a pitch of 80-500 Hz (normalised autocorrelation) above 0.5; noise stays under it. The threshold is a guess, tested only on a fake
   microphone, and unknown for deaf children's voices, which may be less periodic.
3. **Nothing in the mirror starts or restarts by itself.** Earlier the sequence reset by itself (3 s after "well done", when the sound stopped, when the face was
   lost). Now a turn begins with Start and goes again only with Restart; a pause only shows a hint. This keeps each attempt a deliberate, countable act.
4. **One button for both.** "Record and mirror together" starts a mirror turn and the recorder with one press (the two are separate components on the same page
   and talk through a shared object, window.__lnMic). This puts the camera turn and the recording on the same moment, so they can later be compared.
5. **Layout (sky page, /m/ /p/ /b/ only).** A new look from the user's second sky mockup (sky, sun, clouds, sea strip, light cards, bigger word, glow on the record
   button and progress bar, switches in a row); the word card and the mouth card on top, the switches in a card, then the recorder and the mirror side by side.
   Pinyin is hidden in the tips there (the mockup has none). Not yet checked on phone widths.
6. **Open question (not built):** an assessment of /m/ that tells "dark m" from "light m". The meaning was not given. Reading under consideration: dark = a strong,
   low nasal murmur with the lips shut; light = a thin, brighter hum. No thresholds are set; they would need recordings of both made on purpose by the user.

#### 8c.m  A numbers-only log of camera and microphone (testing phase, allowed by the user, 2026-10-31)
Reason: the recorder and the lip mirror measured the sound separately and disagreed. Both now post, about ten times a second, what they measured to a small local
server (learner/camlog.py, 127.0.0.1:8503), which appends one JSON line per turn to app/logs/camera.jsonl. Both use epoch milliseconds, so a mirror turn and a
recorder turn can be laid on one time axis. mirror: lip gap and width (divided by face height), closed, stage, sound level, low-pitch share, voice test, voiced;
mic: level, voice test, high/low ratio, the milliseconds of "mmm" and of vowel counted, the reason it stopped (silence, max, nosound, tap). No picture of the face
and no sound is kept. The learner screen says so in its privacy note. Remove it when the testing phase ends.
First check of logs/quality.csv for "me" (14 recordings, 17:41-18:18 on 2026-10-31): 3 scored (red /n/, green /m/, yellow /m/); 5 refused as noisy (SNR 7.7-11.3 dB,
under the 12 dB limit); 2 refused as too loud (peak at the limit); 4 with no verdict ("Not sure which sound this was", "No speech was heard"). The recordings are
not kept, so the cause of the low SNR cannot be told; the guided recorder was in use. Open: whether the noise estimate is spoiled by recordings that are mostly hum.

#### 8c.n  First reading of camera.jsonl (2026-10-31, 18:25) and what it changed
Findings (one real session, real face, 15 turns): (1) The room was about -38 dB, the voice -22 to -30 dB; the gate came from Sound Check (-46 dB + 10 = -36 dB), so a steady
periodic hum of the room at -35 dB passed as "voice": the mirror reached stage 4 on room noise alone (turn 8: voiced on 36% of frames, stage 4), and the recorder never
heard 1.5 s of silence, so every recording ended at the 12 s limit. (2) The recorder counted only 175 ms of "mmm" in a turn where the mirror saw a 1.3 s hum and then the
lips opening: the hum was only allowed to count when its high/low ratio was under -25 dB, but this voice's hum was at about -21 dB and its vowel at -15 to -17 dB (only 4-6 dB
apart); the fixed limit that was thought to separate them did not. (3) The 8 dB jump needed for a vowel was therefore never reached.
Changes: the gate follows the room measured inside each recording (non-voice frames, +7 dB, in both the recorder and the mirror) instead of the Sound Check noise; any
voice counts as the hum for its first 0.4 s and becomes the baseline; a vowel is a rise of 4 dB in the high/low ratio above that baseline (or +6 dB louder); the voice
test limit is 0.6. The log now also keeps the energy in 7 bands (0.1-4.5 kHz) per frame to look for a better hum-versus-vowel feature. A replay of the logged frames under
the new rules (approximate: the logged ratio was smoothed the old way) gave an end 1.1 to 6.5 s before the 12 s limit in 3 of 4 turns, and a vowel found after the hum in all.
Caution: the 4 dB comes from one speaker and one session; it may fit that voice only. Not yet re-tested with a real voice after the change.

#### 8c.o  "I smiled and the app said I had not" (camera.jsonl, mirror turn 25, 2026-10-31 18:33) and the Dev page "Camera log"
Reading: at 6.4-7.3 s the lips were wide (width 0.295-0.31 against 0.19 closed, a ratio of 1.55) with a gap of 0.067-0.072, so the smile test was true, but the mirror stayed at
stage 2 because the sound test said "not a voice" on those frames although they were loud (-22 to -28 dB) and periodic (0.65-0.98). The cause was the room-following gate
of 8c.n: frames that were voice but just under the gate were counted as room, so the room estimate and the gate climbed together, from -29 to -18 dB within 2.5 s (a
runaway). A second, smaller cause: the smile limit on the lip gap (0.08) was passed at 7.7 s (0.086) by this speaker's "ee".
Changes: the room estimate takes only frames within 5 dB of itself (a voice, 10 dB or more above the room, can no longer move it); the gate is capped at -28 dB; the smile gap
limit is 0.10. Not yet checked on a real voice after the change.
The log is now readable in the Dev app, page "Camera log": the turns in a table (pick one), and for a picked turn the sound level with the gate, the voice test, the lips, the
stage of the mirror and the hum/vowel counted by each recorder turn that overlapped it, and the energy per band, all on one time axis. A mirror turn can hold several recordings.

Smile width limit lowered from 1.15 to 1.08 times the closed-lip width (2026-10-31), after the user asked for a looser test. In the user's logged turns the width in open frames was 1.36-1.58 times the closed width in a clear smile, 1.17-1.20 in a mild one and 1.0-1.1 in the weakest (turns 8, 16, 32 of camera.jsonl); the limit follows the mild one. Closed-to-slightly-open lips alone reach about 1.0-1.12, so a false pass on a barely open mouth is possible; the sound test and the gap limit (0.10) still have to hold at the same time.

The step "Open, keep the sound going" of the /m/ then /iː/ coach was removed at the user's request (2026-10-31): the lip mirror has three boxes (hum with lips together, smile with a small mouth, hold 1 s), and after 0.5 s of hum it waits for the smile directly.

#### 8c.p  The recorder's vowel box stayed grey while the mirror reached "done" (turns 55-57, 18:42)
In the log the hum and the vowel of this speaker differ little in the old features (high/low ratio -20 to -24 dB throughout; level -27 to -30 dB throughout), so the vowel was never
counted (ee 0 and 92 ms of the 400 needed). The per-band energies that the log keeps show what does differ: the energy at 300-600 Hz against that at 1-1.5 kHz is -4 to +2 dB in
the hum (lips shut, a nasal hum keeps more at 1 kHz) and +8 to +14 dB in the vowel (lips open). A vowel is now also counted when this ratio rises 6 dB above the child's own hum, and
the count decays twice as fast as it grows when the frame does not look like a vowel, so one odd frame does not stay counted. Replay on the logged frames of the 8 recorder turns with
bands: the vowel is found 0.4 to 4 s after the hum in all 8 (it was found in none of the two turns the user pointed at, now at 2.9 s and 2.5 s). The rule comes from one speaker
and one microphone; it is a physical story (open lips radiate 300-600 Hz and 3-4.5 kHz better than closed lips) but untested on children.

#### 8c.q  Both boxes green but the recording refused as "too noisy" (quality.csv 18:48:29, camera.jsonl turn 60)
The recorder (and the mirror) had both found the hum and the vowel, yet the score panel said "Too noisy". Cause: the quality check takes the 10th percentile of the clip's frames
as the room. The child held one note for the whole 12 s (the recorder only stopped at its 12 s limit; the vowel was counted from 1.3 s, the voice began 0.2 s after the tap), so
there was no quiet part: the 10th percentile was the voice, and the SNR came out at 8.3 dB, under the 12 dB limit, for a voice about 15 dB over the room (the recorder's own
estimate of the room: -39 dB; the voice -22 to -24 dB). Two changes: (1) the guided recorder stops 1.0 s after the vowel has been heard (it also stops on silence, 12 s or no sound,
as before); (2) it sends the room level it measured while recording in front of the WAV, and the quality check takes the quieter of that and the clip's own 10th percentile
(fricative/noise.py: recording_quality(sound, room_db); a test with a clip that is all voice). Ten of the 22 "me" lines in quality.csv between 17:41 and 18:48 were refused or
unscored; of these, the "noisy" ones (7.6-10.5 dB) may be of the same kind and could be rechecked once the recorder's room level exists in the log (it is in the log as the gate).
Still open: "Not sure which sound this was" (no verdict) in about one recording in four, and one red /n/ for a recording the user judged fine; the /m/ vs /n/ judgement has not been looked at yet.

#### 8c.r  "The hum ticks by itself" (camera.jsonl turns 63-68, 18:53:55-18:54:01)
In these turns the sound was already there on the first frame (level -23 to -25 dB, voice test 0.9-1.1, low-pitch share 0.99, lips closed) every time Restart or "together" was pressed
(five presses in 6 s), and the hum box ticked 0.5-0.6 s later, before any new hum had begun; the recorder did the same at 0.7 s after the tap (a steady sound that never changes: 0.9-1.1
voice test, high/low ratio -13 to -18 dB for 8 s). A hum going on when the turn begins, or a steady sound in the room, was therefore counted as a new hum. Change: in both the mirror and
the recorder, a hum counts only after a quiet moment of at least 0.3 s since the turn began (armed); until then the screen says "Be quiet for a moment, then hum" (wording and its Chinese
are mine, to be checked), and the log has an "armed" flag per frame. Cost: a child who starts humming within 0.3 s of the press is not credited until they pause and hum again.

Correction to 8c.r (2026-10-31, 18:57): the "quiet first" rule was switched off (ARM_QUIET_S = 0, in lipcam.py and mic.py; the code stays, a value above 0 turns it on). In the next log (turns 69-72)
the user hummed with closed lips for 15 s without a pause (level -22 dB, voice test about 0.95, lip gap 0.001), so nothing was ever "armed" and the app refused a real hum. The turns of 18:53:55
that were read as "the hum ticks by itself" were probably the same continuous hum across five Restart presses, i.e. correct ticks. A quiet-first rule cannot tell a real hum that was already going
from a steady sound in the room; what still protects against false hums is the voice test (periodicity 0.6) and the gate that follows the room (8c.n, 8c.o). Lesson: read the frames before the
press, and ask what the user was doing, before adding a rule.

#### 8c.s  One threshold, measured first (2026-10-31, after the user's choice "measure the room first, then hum")
Two thresholds had been in play and each failed in one direction: with the quiet-first rule (8c.r) a quiet room recorded nothing because a continuous hum never "armed"; with it off every steady
sound counted as a hum. Replaced, in the mirror and in the recorder, by a single threshold measured at the start of every turn (tap, Start, Restart, "together"): for 0.6 s the room is listened
to (the screen says "Wait, stay quiet"); the median level of that window plus 7 dB is the gate (floor -50 dBFS, ceiling -28 dBFS), fixed for the turn (no more following of the room during the turn).
If the window is louder than -32 dBFS (already humming, or a very noisy room) it starts again and the screen asks for quiet ("Please be quiet for a moment"); nothing counts until the room is known.
The measured room level also goes to the quality check (8c.q). The log has a flag "meas" (1 while the room is being measured) per frame. Cost: a child who hums within the first 0.6 s is asked to wait;
the numbers (0.6 s, -32 dB, +7 dB) are guesses from the user's room (-38 dB) and hum (-22 dB). The wording and its Chinese are mine, to be checked.

#### 8c.t  /n/ on the sky page: lips a little open, then hum (prototype, 2026-10-31)
Web search (2026-10-31): no study found that gives deaf children a real-time display for /n/ itself. Found: real-time spectral displays help deaf children learn consonants (Stark 1972, /ba/ /pa/); nasality work with
a nose accelerometer (Stevens, BBN) and a patent proposing tactile vibration instead of a screen; clinical nasalance (Nasometer) mostly on vowels; EPG and ultrasound show the alveolar contact (the "horseshoe" of
/t/ /d/ /n/) but need hardware, with small-sample evidence in deaf children; acoustically /m/ has a strong nasal resonance near 200 Hz with antiresonances near 1000, 1800 and 3000 Hz, while for /n/ F3 is evident and F2
and F4 are strongly attenuated (Macquarie University). Build: "knee" now uses the same layout, guided recorder (chips "nnn" then "ee") and lip coach as "me", with one difference in the lip rule: while humming, the lips
must be a little open (gap / face height above the closed limit 0.03 and under 0.12), the opposite of /m/; the width baseline for the smile is taken from these relaxed lips. The tongue cannot be seen and nothing about it is
claimed (the picture card keeps the content owner's checks: "Tongue tip up", "Lips slightly open"). Next: record about ten "mmm" and ten "nnn" with the mirror running and compare the per-band energies in the Camera log
(Dev app) to see whether any band separates the two sounds; only then add an acoustic condition. Wording ("Lips a little open, then hum" and its Chinese) is mine, to be checked.

#### 8c.u  /tʃ/ ("cheat"): what the literature gives, and the fine log to collect our own numbers (2026-10-31)
Search results (snippets only, full texts not read): Castleman & Diehl (ASA 1996) on English fricatives and affricates: preceding silence and frication duration discriminated /ʃ/ from /tʃ/ better than amplitude
rise time, which may owe its effect to the slope rather than the duration; a perception study with older listeners: /ʃ/ is taken for /tʃ/ when the frication rises slowly and the reverse when it rises fast, and
degraded hearing moves listeners towards frication duration as the main cue; an English study of children with and without cochlear implants measured frication duration, rise time and centroid frequency for
/tʃ/ /ʃ/ /s/ (PMC5831615): all groups separated the sounds in these three measures, the centroid being the stronger place cue for the normal-hearing children; Persian children with implants could not separate /ʃ/ and /tʃ/;
for English implant users, /s/ errors are most often [ʃ] and /tʃ/ is not fully acquired even 6 years after implantation. No source found for /tʃ/ -> /t/ in deaf children. Consequence for the design: the three
things to look at are the length of the hiss, the length of the silence before it (not available from a recording: the room is silent before the word anyway), the rise, and the centre of gravity of the hiss.
Build: every plain recording (any word except the guided "me" and "knee") now writes a fine log line ("mic-fine"): per screen frame (about 60 a second) the level and the energy in 8 bands up to 9 kHz; the Dev page
"Camera log" shows it with the room level, the start of the sound, the rise from the room to 90 % of the first peak, and the time until the low bands win over the high bands by 10 dB (the end of the hiss); the
numbers are rough, for looking, not thresholds. Next: about ten recordings each of "cheat", "sheet" (/ʃ/) and "teat" (/t/), then compare these measures; only then thresholds and a three-lamp display (pop, hiss, vowel).

#### 8c.v  /tʃ/ from CMU ARCTIC (bdl male, slt female; 2026-10-31): what separates it from /ʃ/ and /t/, without recording the user
Data: the public packages cmu_us_bdl_arctic and cmu_us_slt_arctic (festvox.org, 1132 sentences each, 16 kHz, with the package's own phone labels, 10 ms steps) were downloaded to C:\Users\tuank\Data\arctic_festvox
(outside the repo). The user's own ARCTIC folder on D: has the wavs of 8 voices but MFA TextGrids only for bdl /s/-/ʃ/ (no /tʃ/), so the package labels were used. Tokens: ch 218 + sh 325 + t about 2200 per voice.
Measures per token, on the 2.5-7.9 kHz band: steepest climb of the 5 ms envelope (dB per ms), length of the hiss (from 10 % to the last 10 % of the peak amplitude), 10-90 % rise time, centre of gravity 1-8 kHz.
(explore/pattern_lab/arctic_ch.py and arctic_ch_roc.py.)
Result, /tʃ/ against /ʃ/ (area under the ROC curve; balanced accuracy at the best limit): steepest climb 0.83 / 0.82 (bdl, limit 11.8 dB/ms) and 0.87 / 0.81 (slt, limit 3.8 dB/ms); hiss length 0.65-0.68; 10-90 % rise time
0.45-0.47 (no use, which fits the literature that the slope, not the duration of the rise, carries the cue). Medians of the steepest climb: ch 24.6 and 8.6, sh 4.3 and 2.7 dB/ms (bdl, slt). The best limit differs
between the two voices, so a fixed number is not enough; it has to be relative to the speaker or the recording (for instance against the climb of the child's own /ʃ/ in "she").
/tʃ/ against /t/: length of the hiss separates them, AUC 0.89-0.91, limit 56 ms (bdl) and 71 ms (slt): a /tʃ/ hiss is 95-110 ms (median), a /t/ release 34-39 ms. Centre of gravity helps less (AUC 0.67-0.68; ch 4.1-4.3 kHz, t 3.3-3.8 kHz).
Centre of gravity does not separate /tʃ/ from /ʃ/ (4.1 against 4.1 kHz; 4.3 against 4.4 kHz).
Caution: adult running speech, two voices, segment edges at 10 ms steps; the numbers are for choosing what to show, not final thresholds. The existing experimental model (app/fricative/affricate.py, an LDA on the
rise time and the steepest climb, leave-one-voice-out accuracy 0.80 on 8 ARCTIC voices) is consistent with this result.

#### 8c.w  /tʃ/ result: two lamps (the pop and the hiss), 2026-10-31
After a recording of "cheat" is scored (GOP), the result also shows two lamps, "t" and "sh" (learner/affricate_check.py, tests in tests/test_affricate_check.py), with a grey line of the numbers while testing.
Pop lamp: the steepest climb (dB per ms, 5 ms envelope, 2.5-7.9 kHz) of the first strong stretch of hiss: green from 10, yellow from 5, else red. Hiss lamp: its length (from 10 % of the peak amplitude to 15 dB below the peak):
green from 85 ms, yellow from 70 ms. Where the limits come from: ARCTIC words that start after a real pause (explore/pattern_lab/arctic_isolated.py; only slt, no /tʃ/ at all: /ʃ/ climbs at 2.5 dB/ms (IQR 2.0-2.8, n = 24) and /t/ at 28 (n = 14), hiss of /t/ 64.5 ms (IQR 49-78)) and
from the /tʃ/ of running speech (climb 8.6-24.6, hiss 95-108 ms). A first try that cut the ARCTIC tokens out and padded them with silence gave nothing useful (AUC 0.56): cutting the audio makes every onset abrupt and the vowel after it
lengthens every hiss, so such clips cannot stand in for isolated words. Two early recordings of "cheat" (26 Oct, flagged "ch heard as sh"): climb 1.6 and 1.7 dB/ms (red, gradual start, like /ʃ/), hiss 108 and 123 ms. The hiss finder first took the recorder's noise fade-in for hiss (771 ms);
it now starts at the first stretch within 30 dB of the loudest point of the recording. No limit has been checked on real isolated /tʃ/ from anyone; the first real recordings (the user's, then children's) are the test.

#### 8c.x  /tʃ/ live: the two lamps light up while the child speaks (2026-11-01)
The result-only lamps of 8c.w were not enough (the user asked for real-time feedback). The recorder of "cheat" now follows the hiss as it happens (learner/mic.py, startChGuide): an AudioWorklet filters the input to 2.5-7.9 kHz and sends
a 5 ms envelope every millisecond (and the whole-band level); after 0.6 s of listening to the room (the one threshold of the turn, as in 8c.s) the first stretch of hiss that stands 15 dB over the room is followed: the "t" lamp is
the steepest climb since its start (recomputed with every new millisecond, over the part of the rise within 20 dB of the peak so far, the same definition as the check after the recording), the "sh" lamp is its length so far (green the
moment it has lasted 85 ms; if it ends sooner, yellow from 70 ms, else red); the recording stops 1 s after the word has ended (or 8 s). The two lamps are the chips of the guided recorder, round and coloured. Without AudioWorklet it falls
back to a plain recording. The live turn is written to the camera log (src "mic-ch": room, the event, the band level every 4 ms) and shown in the Dev page.
Check with a fake microphone playing files: a synthetic hiss with a 2 ms rise: climb 28.3 dB/ms (offline check 22-36 depending on the 1 ms frame alignment), hiss 107 ms; a 80 ms fade-in: 2.0 dB/ms (offline 2.2), 96 ms; a 2 ms rise, 35 ms hiss: 34.6 dB/ms,
33 ms; the saved "cheat" of 26 Oct: 1.6 dB/ms, 107 ms (offline 1.6, 108). Bug found on the way: the first sample over the threshold was stored twice, which hid the steepest step (7.9 instead of 28 dB/ms).
The slope depends on where the 1 ms frames fall against the burst (22-36 for the same sound), which is fine against the limits 5 and 10 but is the reason not to read the number too closely. Not yet tried with a correct /tʃ/ from a person.

#### 8c.y  Web search (2026-11-01): the delay between the hiss and the vowel in deaf children, and the train picture
Searched in snippets only, full texts not read. (1) No study found that measures the gap between a fricative and the voicing of the next vowel in deaf or hard-of-hearing children. Related findings: older acoustic and EMG work on deaf adult speakers
found consonant-vowel formant transitions with a narrower range and slower rate, weak coarticulation, and difficulty coordinating articulation with phonation (sonicfield library, "acoustic and electromyographic investigation of consonant-vowel
transitions"); Croatian children with hearing loss spoke about 21 % (mild) to 43 % (deaf) slower with more variable segment durations (Horga, Mildner and Sindija, 2002); 8-10 year olds with severe hearing loss differed in vowel duration, VOT,
closure duration and consonant duration but not in burst duration; early identified preschoolers were closer to hearing children. Consequence: the time allowed between the end of the hiss and the start of the voice is not fixed at 0.3 s; it is 1.0 s
(TRAIN_BRIDGE_S in learner/mic.py), written to the log as "gap" so that it can be tightened from real children. (2) The "choo-choo train" cue for /tʃ/ is common in speech-therapy teaching material (Houston teaching-speech-sounds chapter;
Chicago Speech Therapy): /tʃ/ as /t/ and /ʃ/ in quick succession, "ch-ch-ch" repeated and getting faster; a tissue in front of the mouth puffs at each burst; the sneeze is the other usual picture. These are practitioner resources, not controlled
studies. (3) Real-time visual feedback for deaf children: Stark 1972 (spectral displays, /ba/ /pa/), SIM (Speech Illumina Mentor: animated characters and game, 6 of 7 profoundly deaf children improved vowel intelligibility by 13 % or more, small
conference sample), a Portuguese sibilant game with immediate visual feedback (classifier accuracy above 91 %, no child outcome in the snippet); and a vowel game engine paper (UTS) reports that children were frustrated by split-second lags: the picture
has to follow the sound at once.

#### 8c.z  /tʃ/ as a train (2026-11-01), replacing the two live lamps of 8c.x on the recorder
In the recorder of "cheat" a small scene is drawn (canvas): a station with a chimney, a rail, a train and a flag. The hiss from the chimney: after the hiss has held its peak for 25 ms (a slow fade-in reaches its peak late and looks steep at first), the
steepest climb decides: a burst (green or yellow) gives white (or grey) puffs rising from the chimney, a fade-in (red) one flat grey ribbon. The vowel: after the hiss the voice (loudness over the room + 7 dB and a pitch-repeat test above 0.6, as in 8c.n) is
followed; the train runs along the rail while the voice goes on (it needs 0.5 s to reach the flag, a stop of more than a quarter second slows it back down), the flag waves and "Well done" shows. If the voice has not started within 1.0 s of the end of the
hiss, the rail is drawn broken with a red cross and the train stays. The recording ends 1 s after the train arrives, or 1.5 s after the word has gone quiet, or at 8 s. After the recording the result still shows the two lamps "t" and "sh" and the numbers (8c.w).
Checked with a fake microphone playing synthetic words: a burst with a 110 ms hiss and a tone after it: puffs, train to the flag, "Well done" at 4 s (file time 2.5 s + 0.5 s of voice + the 1 s margin); a slow fade-in: ribbon, train runs; the voice 1.5 s late: puffs, rail broken
with a cross, no "Well done". Not tried with a person. The scene and its colours are drawn in code; no content of the owner is added; whether deaf children understand the train is not known and the picture should be shown to a teacher first.

#### 8c.aa  The train with the lip mirror (2026-11-01): option 1, the smile joins the "ee"
"cheat" now has the sky layout and the lip mirror (switch on the page, "Record and mirror together"). The two components share what the mirror sees through window.__lnLips: during the room listening of the turn (0.6 s, lips relaxed) the mirror takes the width of the
lips as the baseline; "spread" is the same test as the smile of "me" (width at least x1.08 of the baseline and an inner gap under 0.10 of the face height). With the mirror on and a face seen, the train of the recorder runs only while there is voice and the lips are spread
(otherwise the screen says "Smile wide" or "Make your mouth small", the wording of "me"; the state of the mirror says "Smile ✓" and "Lips relaxed", with "嘴唇放鬆" mine, to be checked); with no mirror or no face, the voice alone, as before. The "ch" part (the smoke) does not look at the lips yet.
The mirror turn is logged as for "me" with the ratio of the width to the baseline, and the recorder turn counts how long the voice came with spread lips and without (camSpread, camNoSpread in the event). Reason for stopping here: the content owner's cards say "Lips gently rounded"
for "ch" and "Lips slightly spread" for "ee", but how much the width of the lips changes in "ch" (rounding mostly shows as a small narrowing in a flat picture) is not known. Next step: about ten "cheat" turns with the mirror on, read the ratio at the moment of the hiss against the moment of the voice in the Dev page
"Camera log"; if the difference is clear, add "rounded" (a ratio under some limit) as a condition for white smoke.
Not tried with a real face (the fake camera of the browser has none); the train falls back to voice alone there, as it is meant to.

#### 8c.ab  /tʃ/: a ghost mouth that walks through the three steps (2026-11-01, prototype)
Request: guidance step by step as for "me" and "knee". For "cheat" the mirror now draws, behind the child's own mouth, a dashed ghost mouth that moves slowly (1.6 s a step) through the three steps of the lesson, with the titles of its picture cards:
"Get ready for ch" (lips narrower than relaxed, a rounded opening), "Release, ch" (narrow, a small gap), "Open into ee" (wide and flat). The child's mouth is drawn on the same scale (relaxed lips = 90, so a rounded mouth is narrower and a spread one wider);
the ghost turns green and the title gets a tick where the two agree (ratio within about 0.12 and gap within about 0.025 of the target). It starts when the room has been listened to and the relaxed width is known. It only shows: nothing waits for it, the train still follows
the sound and the spread lips only. The shapes (ratio 0.80 / 0.85 / 1.35, gap 0.09 / 0.025 / 0.035) and the agreement limits are guesses drawn to be seen, not measured; they are to be set from the "ratio" and "gap" in the log, as the camera cannot yet tell a rounded mouth reliably (8c.aa).
Checked: the drawing of both mouths in a test page for six states; not with a real face (the browser's fake camera has none), so the pacing against a real child's speech is not tried.

#### 8c.ac  /tʃ/: the three boxes and the ghost mouth together (2026-11-01)
As asked, "cheat" has both kinds of guide at once, in the mirror card: the three boxes of "me" and "knee" with a progress bar, and the ghost mouth behind the child's mouth. The boxes carry the three step titles of the lesson's picture cards ("Get ready for ch", "Release, ch", "Open into ee").
The recorder's train publishes what it has found (window.__lnTrain: the pop level, the hiss level, whether the hiss has ended, whether the voice has started, the progress of the train, the win) and the mirror reads it, so the two parts of the screen show the same turn.
Box 1 lights when the room has been listened to and the relaxed width of the lips is known. Box 2 lights when the hiss has ended with a burst (not red) and a long enough hiss (not red); if the hiss ended but the start was gradual or the hiss too short it turns red with an exclamation mark ("ch" that sounded like "sh" or "t"),
which is the verdict of the two lamps of 8c.w. Box 3 lights when the train has reached the flag (voice for 0.5 s with the lips spread). The bar follows the train. The ghost goes on when the child does (the "get ready" shape until the burst, the "release" shape until the voice begins, the "open into ee" shape after),
and falls back to the 1.6 s pace when the recorder is not running. The last state stays on the screen until Restart. Checked end to end with a browser whose face is a stub (the face detector replaced by a script that gives lip widths and gaps) and a synthetic word played into the microphone:
box 1 and the ghost "Get ready for ch" at the start; with the lips spread at the hiss and the voice, all three boxes, the full bar, the train at the flag and "Open into ee ✓". Not tried with a real face or a real child.

#### 8c.ad  /tʃ/: a written guide for each step (tongue, air, lips), 2026-11-01
The user said the release of "ch" is not tracked and asked for a more detailed guide ("where the tongue sits, where it pops"). The tongue cannot be seen by the camera and nothing in the app measures it; what is measured is its result in the sound (the burst and the hiss, boxes 2 and the "t" and "sh" lamps) and the lips (the camera). So the release can only be guided in words and
pictures, and judged by its sound. Under the three boxes the screen now shows, for the step the child is at, a short text in English with a Chinese line (learner/lipcam.py, CH_GHOST): step 1 tongue tip up on the bumpy ridge behind the top front teeth, the sides of the tongue touching the top side teeth, lips a little round, voice off, air kept in; step 2 the tongue tip drops away fast like a pop, a short quiet
"sh" of air through a small gap, voice still off, lips a little round; step 3 smile and open into "ee" without a stop, voice on and kept going. The wording is the assistant's, written at the user's request from the textbook placement of /tʃ/ and from the lesson's own picture cards (tongue tip up, soft palate raised, lips gently rounded, small gap, voice off); the English and Chinese must be checked by the content owner or a speech-language pathologist before children see it.
A low-tech check that the release is strong enough, found in practitioner material and not tried here: a thin tissue held in front of the mouth should puff forward at each burst.

#### 8c.ae  "Step 2, the release of ch, is not caught" (camera.jsonl turns 160-188, 00:36-01:02)
Reading the real turns: (1) the child began "ch" while the screen still said "Wait, stay quiet" (the first 0.6 s, when the room is listened to). In #164 and #166 a strong stretch of the 2.5-7.9 kHz band (peaks -31 and -27 dB, 1.2 s and 0.2 s long) lies inside that window: it was swallowed by the room measurement, and the event detector,
which only starts after the window, found nothing but weak blips later (peak -47 and -42 dB). (2) In a room with a high band that is already loud (roomHi -49 dB in #160) a real hiss peaked only 21 dB over the room (-28 dB) and was thrown away by the 25 dB limit for "a hiss, not a click". (3) When an event was found, the climb was mostly 1.4-2.5 dB/ms (a fade-in, "sh") with 9 of 12 attempts,
14.2 and 10.8 dB/ms (a burst) in two: the release itself was often not a burst.
Changes in learner/mic.py (startChGuide): the room level is the quiet quarter (25th percentile) of the window, not the median, so speech that begins inside the window does not raise it; at the end of the window everything it holds is played through the event detector (the window is not thrown away); the margins are
12 dB (start of an event) and 20 dB (a real hiss, not a click) instead of 15 and 25; floors of -80 dB (band) and -70 dB (whole) for the room, so that a microphone that is digitally silent does not turn every breath into an event. Checked with the fake microphone: a hiss at 0.85 s (inside the window) is caught (climb 36.6 dB/ms, hiss 107 ms); a hiss after the window as before (28.1, 107 ms).
Not changed and said so to the user: the tongue itself is not seen by anything in the app, so the release can only be guided by words (8c.ad) and judged by its sound.

#### 8c.af  "see" and "she": the hiss, then "ee", with the ghost mouth and the three boxes (2026-11-01)
As asked ("can s and sh also go on to the vowel"), "see" and "she" now have the sky layout, the lip mirror and a live guide of the same kind as "cheat" (learner/mic.py startFricGuide, learner/lipcam.py S_GHOST and SH_GHOST). Three boxes: "Get ready" (the lips of the sound: /s/ a small smile, teeth close; /ʃ/ lips a little round), "Hiss: sssss" or "Hiss: shh" (the hiss held in the target zone of the live dot for 0.5 s; the dot is
drawn at the same time as before), "Open into ee" (voice after the hiss within 1.0 s, with the lips spread when the mirror is on, for 0.5 s). The detail text under the boxes is the lesson's own check cards, English and Chinese as the content owner wrote them ("Teeth close, small smile", "Tongue tip down by lower teeth", "Front of tongue up a little",
"Voice off: no buzz" for /s/; "Round lips slightly", "Tongue up and back", "Keep air flowing" for /ʃ/); the box titles "Get ready" and "Hiss: shh", the ghost shapes (ratio 1.15 / gap 0.02 for /s/; 0.85 / 0.05 for /ʃ/; 1.35 / 0.035 for "ee") are the assistant's. The hiss is the 2.5-7.9 kHz band standing 12 dB over the room (the quiet quarter of the first 0.6 s), and counts as a hiss from 300 ms;
the part in the target zone is counted from the centre of gravity of each frame (the zones of 4340 Hz with the voice-size scale, as the dot). The live turn is logged as "mic-fric" (the hiss length, the time in the zone, the gap before the voice, the voice with and without spread lips) and shown on the Dev page.
Checked with a stub face and synthetic words (a 700 ms hiss at 2.6-3.8 kHz for "she", at 6-7.6 kHz for "see", then a tone): all three boxes light in order, the ghost goes on from "Get ready" to "Open into ee ✓", the bar fills. Not tried with a real face or a child; whether the camera tells a small smile from rounded lips in a flat picture is not known (needs a few turns of "see" and "she" with the mirror on).

Correction to 8c.af (2026-11-01, camera.jsonl turns 215 and 217 of "she"): the "Hiss: shh" box lit only after the hiss had ended, so a child who holds "shhhh" (turn 217: 6.2 s of hiss, 5.3 s of it in the target zone) never saw it. It now lights as soon as the hiss has been held in the zone for 0.4 s (it was 0.5 s, and only after the end), and the ghost mouth stays on the "Hiss" step until the voice
begins. Turn 215 held the hiss for 0.32 s: under the 0.4 s, so the box showed "not yet" (red with "!"), as designed. Checked with a stub face and a synthetic 2.5 s hiss in the "sh" zone: while the hiss is still going on, the screen shows "Hiss: shh ✓", boxes 1 and 2 lit and the dot in the green zone.

#### 8c.ag  The "ee" spread test lowered from x1.08 to x1.03 (2026-11-01, from the user's own turns)
The user asked for less spreading of the mouth for "ee". In the turns of "cheat" and "she" (camera.jsonl 144-225), at the moments with voice but no hiss (the whole band loud, the 2.5-7.9 kHz band not; 228 frames of the lip mirror at the same time), the width of the lips against the relaxed lips of the same turn was
10th / 25th / 50th / 75th / 90th percentile = 0.95 / 1.01 / 1.11 / 1.18 / 1.40; the share of these frames at or over the limit: x1.08 64 %, x1.05 69 %, x1.03 75 %, x1.00 79 %, x0.97 81 %. The inner gap (lips apart, over the face height) had the percentiles 0.056 / 0.062 / 0.071 / 0.087 / 0.126, so the limit of 0.10 failed on about 1 frame in 5 in one turn (#204: 81 % under 0.10).
The limit is now x1.03 (75 % of the frames pass; the user's ee is a small smile, not a wide one). It is the one constant for every "ee" in the app ("me", "knee", "cheat", "see", "she"). Cost: a mouth that is only slightly wider than the relaxed one now counts as spread, so the test no longer needs a real smile (the jitter of the relaxed width is about 0.02);
the voice is still needed, and the gap limit (0.10) is kept; raising it to 0.13 would let in 90 % of the frames instead of 80 %. Not changed because the user said "width" only.

#### 8c.ah  Two things in the "she" turns of 01:31-01:35 (2026-11-01)
(1) The delay between the end of the hiss and the voice (the user: "the VOT must be adjusted"): TRAIN_BRIDGE_S, the time allowed before the rail is shown broken, goes from 1.0 s to 1.5 s. The delays found in the user's real turns, over 300 ms: cheat 1660, 820, 586, 2491, 1063, 2910, 1181, 1441, 582, 766 ms; she 1075, 1105, 1034 ms. Part of each delay is the lip gate (the voice counts only with the lips spread, so the time spent spreading the lips is
included: 8 of these turns also have 100-1800 ms of voice with lips not spread). With 1.5 s, 11 of the 13 pass. The word "VOT" is used here for this delay (voice onset after the hiss), not the voice onset time of stops.
(2) The hiss of "she" is detected but is not in the target zone: turn 227 (hiss 4877 ms, 759 ms in the zone) and 229 (hiss 1292 ms, 40 ms in the zone). The scored recordings of the same minutes have centres of gravity of 6590, 5391 and 6909 Hz with the recogniser hearing "sh" (verdict yellow), while the "sh" zone of the live dot is below 4175 Hz (the adult
/ʃ/ of ARCTIC, 4.3-4.4 kHz, with the voice-size scale 1.03). The user's /ʃ/ sits where adult /s/ sits (ARCTIC /s/ 5.3-6.3 kHz), so the fixed zones do not fit this speaker or this microphone. Not changed yet: it needs a decision (a zone learned from the child's own sounds that the recogniser labels, or a manual shift).

#### 8c.ai  The hiss box follows the dot (2026-11-01)
The user: the dot clearly hears the "shhh" but the box of the step "Hiss: shh" does not; make them the same. The box used its own copy of the centre of gravity and counted only the time in the target zone (green); the dot used its own copy with a smoothing and showed three colours. Now the dot publishes what it shows (window.__lnDot: the centre of gravity and the colour) and the box reads it (learner/mic.py, startFricGuide):
the hiss counts as held while the dot is green (in the target zone) or yellow (next to it); when the dot is not running (the "Picture" or "Game" views, "Off") the box uses its own centre of gravity as before. The rows of the live log now carry the centre of gravity of the frame and the colour of the dot (fourth and fifth values), so that the next log shows what the child saw.
What the saved profile ("kietto") contains, for the record: the voice size from two "aaa" (F3 2713 Hz, scale 1.03) and the room noise (-46 dB), nothing from "see" or "she": the fixed zones of the dot (/ʃ/ under 4175 Hz, /s/ over 4796 Hz) are the adult ones moved by 3 %; the scored "she" recordings of 01:30-01:35 had centres of gravity of 5391-6909 Hz (8c.ah), outside the "sh" zone and in the red part of the dot.
Not yet decided: whether the zones should be learned from the child's own sounds. Also fixed: the Dev page "Camera log" had a syntax error since the "mic-fric" edit (two line breaks written as the characters backtick-n).

#### 8c.aj  "Still not" (camera.jsonl 232-243, "she", 01:42-01:46): the room taken from a window full of hiss, a quiet "ee", a long delay
Reading the turns (with the colour of the dot now in the log): #239 the hiss was held 1280 ms, all in the zone (the centre of gravity of the dot 3.1-4.2 kHz, p50 3993 Hz, green on 358 of 379 frames while the band was up): the box lit; but the voice began 1735 ms after the hiss, later than the 1.5 s allowed (the rail was drawn broken), and the level of the voice was only 3-8 dB over a room of -46 dB, under the +7 dB gate.
#243: the child hissed from the tap (hi band -38 dB from 0.2 s), so the quiet quarter of the 0.6 s window was the hiss itself: roomHi = -39 dB, the start threshold -27 dB was above the hiss (-28 to -42 dB), no event, while the dot was green on 1384 frames: the dot heard it, the box did not (the user's complaint). Changes (learner/mic.py, the guides of "cheat", "see" and "she"):
(1) the room of the hiss band is capped at -58 dB and the whole-band room at -40 dB when taken from the window; after the window, every 200 ms, the room falls to the quietest 200 ms seen (never rises), so a hiss that began at the tap is not lost and a quiet moment later corrects the estimate; (2) the retry "Please be quiet for a moment" is gone from these two guides (a loud hiss from the tap no longer sends the child round
the loop; the hum guides of "me" and "knee" keep it); (3) the voice of the "ee" after a hiss needs 4 dB over the room instead of 7 (the pitch-repeat test keeps noise out); (4) the delay allowed between the hiss and the voice is 2.0 s (was 1.5; the user's delays: 586-2910 ms).
A mistake of mine in the same hour: while adding the cap I put a comment in the middle of the line that set the phase, which commented out "phase = listen" in the guide of "see" and "she": for a few minutes that guide could not leave the listening of the room. Found by the test with synthetic words, repaired; the lines are now one statement each.
Checked with the fake microphone: "she" with a 700 ms hiss and a tone: hiss 702 ms, 685 in the zone, voice 508 ms, done; a 1.5 s hiss that begins inside the window: 1491 ms in the zone, voice 500 ms, done; "cheat" unchanged (28.1 dB/ms, 107 ms, voice 500 ms).

#### 8c.ak  A held "shhh" that turns into "ee" is scored by its hiss (2026-11-01, the user's remark)
The user: a child practising /ʃ/ prolongs it and turns it into "ee"; the machine refuses it as /ʃ/ because the end of the recording has changed, although the first part is right; whereas a quick "she" passes, so what is the app for? Evidence in quality.csv: the prolonged attempts of 01:26-01:30 were refused ("No consonant was heard at the start.", "No /s ʃ f/ sound was heard in the hiss.") while the quick ones were scored
("yellow, 5391-6909 Hz, sh"). The recogniser and the rules of the pipeline (fricative/pipeline.py) look at a whole word; they were never meant for a held sound that glides into a vowel. A first answer, cropping the recording to the first hiss and scoring the crop with the same pipeline, was tried on seven real ARCTIC /ʃ/ + /i/ made long
and dropped: the cropping end was unreliable (0.05-0.4 s) and the whole-recording path did not fail on these constructed words, so the failure of the user's own recordings could not be reproduced without their audio (the learner app keeps no audio).
Instead, for a guided recording of "see" or "she" the result is made from what the live guide found while the child spoke (learner/mic.py sends the summary with the recording: the length of the hiss, the time the dot was in the target zone or next to it, the gap before the voice, whether the "ee" was reached; learner/result.py: from_live): 0.8 s in the zone is green (3 stars with a long enough hold), 0.4 s yellow, less red, a hiss under 0.3 s "too short to measure" (so a quick "she" no longer passes); the line under the stars says how long the hiss and the part in the zone were, and whether the "ee" came.
The dot, the box and the result now say the same thing. Checked with a fake microphone: a 2.5 s hiss in the "sh" zone and a tone: all three boxes, the bar full, the result "Correct, You held /ʃ/", 3 stars, "2.5 s of hiss, 2.5 s in the green; then the ee".
Still open and not hidden: the zone of the dot weighs the spectrum by amplitude between 1 and 10 kHz, the scoring pipeline by power (Praat, power 2) over the whole spectrum, so the same hiss gives a lower centre of gravity on the dot (3.1-4.2 kHz in the log of 01:46) than in the score (5.4-6.9 kHz at 01:30); the zone limits (4175 and 4796 Hz) come from the power measure. The held-hiss result follows the dot, so it is as lenient as the dot. To settle with the zones.

#### 8c.al  The zones of the live dot, measured the dot's way on CMU ARCTIC (2026-11-01; the user's choice (c))
The dot and the scoring computed the centre of gravity differently: the scoring (Praat, power 2, the token's whole spectrum, "method B") and the dot (amplitude-weighted, 1-10 kHz, smoothed over frames, "method A"); the zone limits (4340 Hz +/- 300) came from B and were applied to A. Measured on 7104 ARCTIC tokens of four voices (bdl, rms male; slt, clb female; the labels of the festvox packages; the
analysis resamples to 48 kHz and reproduces the browser's analyser: Blackman window of 2048 samples, magnitudes smoothed 0.5, a frame every 16.7 ms, the centre of gravity smoothed 0.6/0.4; explore/pattern_lab/arctic_dot_cog.py, dot_cog_variants.py, dot_cog_zones.py, dot_cog_margins.py), middle 60 % of each token:
- method B: /s/ median 4828-6258 Hz, /ʃ/ 3956-4425 Hz, AUC 0.90-0.95 per voice (pooled 0.92, balanced accuracy 0.86 at 4790 Hz);
- method A as the dot had it (amplitude, 1-8 kHz, ARCTIC stops at 8 kHz): /s/ 4115-4969, /ʃ/ 3618-4161, AUC 0.71-0.89 (pooled 0.76, balanced accuracy 0.72 at 4360 Hz): the dot was a weaker judge, and its zone (4040-4640 before the voice scale) was misplaced for it;
- tried variants: power weights from 2 kHz: AUC 0.84-0.91 (pooled 0.86, balanced accuracy 0.79 at 4240 Hz); amplitude from 2 kHz 0.82-0.92 (pooled 0.85); power from 1 kHz 0.72-0.90 (0.78); power from 3 kHz is good for slt and clb (0.93-0.94) but breaks for rms (0.23).
Chosen: power-weighted centre of gravity between 2 and 8 kHz, limit 4240 Hz, yellow band +/- 300 Hz (before the voice-size scale), i.e. /ʃ/ zone under 3940 Hz and /s/ zone over 4540 Hz: 65 % of the /ʃ/ fall under 3940 (13 % of the /s/ do too), 59 % of the /s/ over 4540 (8 % of the /ʃ/ do), 27-28 % of both in the yellow band.
The midpoints differ by voice (bdl 3944, rms 4028, slt 4467, clb 4748 Hz): the voice-size scale (F3 of the "aaa" of Sound Check) is what is meant to carry that; it was not checked on these four voices. The picture after a recording and the scoring keep the old zones (method B). Code: learner/spectro.py zones(live=True), learner/mic.py (the dot and the guide of "see"/"she" use power weights), tests/test_spectro.py.
Limits of this: adult read speech in 16 kHz, so nothing above 8 kHz is measured (a live band of 2-8 kHz on a 48 kHz microphone is cut at the same place); the dot is still a weaker judge than the scoring (0.86 against 0.92), the live /s/ and /ʃ/ can be mistaken for each other about one time in four; the user's own /ʃ/ gave 3.1-4.2 kHz on the old dot and 5.4-6.9 kHz in the scoring; the new dot has not been run on a person yet.

#### 8c.am  The "ee" bar follows the voice at once (2026-11-01, the user: it runs with a delay, not real time; for "see" as well as "she")
Three delays were in the chain (learner/mic.py, learner/lipcam.py): (1) in the guide of "see" and "she" the voice counted only once the hiss had ended, and the hiss counts as ended 150 ms after it has fallen under the room: the vowel often begins before that, so the first 150 ms of the "ee" were lost; the voice now counts as soon as the hiss has been held in the zone long enough (0.4 s), or has ended;
(2) the bar was painted by the loop of the lip mirror, which waits for the face detector of each frame (MediaPipe on the CPU takes a good part of a frame) and so ran at a lower rate than the screen: the boxes and the bar now have a loop of their own, every screen frame, reading what the recorder publishes (window.__lnTrain); (3) the bar had a 0.08 s CSS transition: now 0.04 s.
Measured with a fake microphone (a synthetic hiss then a tone) and a stub face, by reading the width of the bar every 50 ms: for "she" the bar moved at the first sample after the voice began (5 %), and rose in steps of about 10 % every 50 ms to 100 % in 480 ms; for "see" the same (10 % to 100 % in 477 ms). The 480 ms is the time of voice the bar asks for (TRAIN_HOLD_VOICE_S = 0.5 s), not a lag: shorter would make the bar quicker, at the cost of a weaker test of the "ee".
The same code serves "see" and "she" (one guide for the two hisses) and "cheat" (the paint loop). Not measured with a real voice.

#### 8c.an  The snake of /s/ and /ʃ/ (2026-11-01, the user: "where is the snake of the s sound")
The snake of the content owner's word card (learner/lessons.py SNAKE_SVG) is a still picture. A second one is drawn live in the lip mirror card of "see" and "she" (learner/lipcam.py, canvas "snake"), by the assistant, not the content owner's: its shape, colours and flag are the assistant's own, to be reviewed.
It is drawn from the same numbers as the three boxes and the bar (window.__lnTrain from learner/mic.py, now with `need` = the 0.4 s of hiss in the zone) and the colour of the dot (window.__lnDot): the body grows to the middle while the hiss is held in the zone (inZone / need); the "ee" brings the head on to the flag, as far as the bar; at 100 % the flag turns green and the tongue flicks. Colour = the dot's (green, yellow, red); grey-green before anything is heard. One paint loop of its own, every screen frame (see 8c.am).
The count of the hiss in the zone only goes up, so the snake does not shrink when the dot leaves the zone (a shrinking snake would disagree with the box, which stays lit); it stops and turns red. It replaces nothing: the ghost mouth, the three boxes and the bar are kept. Checked with a fake microphone and a stub face (grows to the middle in the hiss, reaches the flag with "ee"), not with a real child.

#### 8c.ao  The ghost mouth in three steps for /p/ and /b/ (2026-11-01, the user: "make the ghost mouth in 3 steps like the other sounds for p and b")
"pea" and "bee" now have, in the lip mirror (learner/lipcam.py, P_GHOST / B_GHOST), what "cheat", "see" and "she" have: the dashed ghost mouth that moves through three steps, the three boxes titled with the steps, the words under them, the bar. The titles and the English words are those of the lesson's own picture cards (assets/pea_1-3.jpg, bee_1-3.jpg: "Close your lips", "Release a small puff" / "Release gently", "Say ee — pea" / "Say ee — bee"); the Chinese is the content owner's words from the check cards under the same pictures, joined with "；" by the assistant. The shapes of the ghost (lips together; lips parted a little; lips slightly spread) are the assistant's.
Camera only: nothing of the sound is read for these two. Box 1: lips seen together for PB_CLOSE_S = 0.3 s; box 2: the lips open after that; box 3 and the bar: the lips spread (the same test as the "ee" of "me": width >= x1.03 of this child's CLOSED lips, inner gap / face height < 0.10) and held PB_HOLD_S = 0.5 s; the spread must come after the opening, and a mouth wide open (gap 0.14) does not count. The ghost goes on with the child (closed -> parted -> spread).
Limits: the opened mouth and the "slightly spread" mouth are told apart only by the width (x1.03 is small, from the log of "me"), so a quick pop into "ee" passes through box 2 for a moment; the puff of /p/ and the voice of /b/ (the "Voice ON for ee" card) are NOT checked, so a child who does the three mouth shapes without a sound is still ticked. Checked with a stub face (the three steps tick in order, the bar fills in 0.5 s), not with a real face. To add, if wanted: the puff (a burst in the high band, as in "cheat") for /p/ and the voice for /b/ and "ee".

#### 8c.ap  "Smile", not "say ee", on every screen (2026-11-01, the user: for all the sounds, "smile" so that the child finds it easy)
Every word the child reads that told them to say "ee" now says "smile" (learner/lipcam.py, learner/mic.py, learner/result.py, learner_app.py): the third step of "cheat", "see", "she" ("Open into a smile"); of "pea" and "bee" ("Smile — pea", "Smile — bee"; the details "Smile and turn your voice on…", "…straight into a smile"); the toggle of "me"/"knee" ("Go on to a smile 接著微笑"); the guided recorder ("Now smile 接著微笑", the sound strip "mmm → smile"); the result of a held hiss ("; then the smile"); the second bar of the /f/ result (label "smile", the test follows). The Chinese 「衣」 is gone too ("接著微笑，不要停，直接發聲").
The titles of "pea" and "bee" are no longer the content owner's words ("Say ee — pea" on the picture card): the owner's own picture cards (assets/*.jpg, "Say ee", "Open into ee"...) are pictures and are NOT changed, so the mouth picture on the right still says "Say ee" for pea/bee/me/knee/fee: to be changed by the content owner. What is measured is unchanged (voice after the hiss, lips spread): only the words.
Checked: a sweep of the eight lessons with the lip mirror on found no "ee" in the page text outside the pictures; the other words in comments and in the Dev pages ("Camera log", "How it works") are left as they are.

#### 8c.aq  The two round pictures for every word, one look for every page, Chinese beside every English text (2026-11-01, the user: "add the 2 round pictures for all the words"; "make the background and everything uniform, translate everything into Traditional Chinese a child can understand, set out the things so they are easy to understand")
1. Round pictures. Only "see" had the content owner's two circles (the snake and the eye); the other words showed dashed "to be added" circles. Now every word card has both: the MEANING circle uses the same small drawing as the word's island on the map (learner/pictures.py ART, moved out of map.py; the Chinese meaning is the one printed on the map mockup: 她 費用 蜜蜂 我 豌豆 膝蓋 作弊, now also under the word); the SOUND circle is a new drawing (SOUND_ART: she a finger on the lips, fee a feather in a soft breath, pea a candle flame bent by a puff, bee a balloon, me a humming face, knee a nose with a hum, cheat a train) with a caption (SOUND_CAPTION, English + Chinese). All of them are drawn by the assistant with code, not the content owner's: to be replaced if the owner supplies pictures. "cheat" keeps the map's note that its example word may be replaced.
2. One look. The sky (sun, clouds, sea, light cards: learner/sky.py) is now added on EVERY page of the learners' app: the map (its own blue gradient is gone), Sound Check (the child list is now a white pill, not beige) and the lesson pages. Every lesson now has the same layout (the word card and the mouth card on top, then the recorder; the lip-mirror bar only for the sounds that have a mirror): "fee" used to have the older two-column layout with stretched circles.
3. Chinese. The learners' screens already carried a Chinese text beside most English ones (the content owner's mockup is bilingual); what was English only is now translated: the result panel (label, message, tip, notices: learner/zh.py, which maps the English of the shared scoring package without touching it; a text with no entry stays English alone), the titles of the steps of the ghost mouth and of its three boxes (titleZh in learner/lipcam.py), "Record again 再錄一次". The Chinese is the assistant's own wording, short and everyday, to be reviewed by the content owner; English is kept beside it (not removed) because the lesson teaches English sounds and the owner's cards are bilingual.
Not done / limits: the owner's picture cards (assets/*.jpg) are pictures and keep their English; the Dev pages are not touched; the "Teacher details" and the numbers under the lamps stay in English (they are for the teacher); the layout was checked at 1366 px wide only, not on a phone.

#### 8c.ar  The home page "SeeSound" (2026-11-01, the user's home mockup, made by an image bot from the assistant's brief)
New page learner/home.py, now the page the learners' app opens on (the map is ?page=map; the map has a "Home 首頁" pill; Sound Check's back button still goes to the map). Drawn to the mockup: the child picker (the same list of saved children as the map's) and the star count at the top, "Teachers 老師" at the right; the logo (an eye with a smile for the pupil) and the wordmark "SeeSound" ("See" blue, "Sound" navy); the tagline; three doors (Start Practising -> the map, Sound Check -> ?page=sound, My Stars -> the map) each on a small island; three pills (Watch the mouth, Lip mirror, See your sound); the footer line. All the icons are drawn with code (the mockup's pictures are not used). Under 860 px the cards stack in one column and under 480 px the top bar wraps (checked at 1366 and 390 px wide).
Decisions to confirm: "My Stars" has no page of its own, so it opens the map (each island shows its stars); "Teachers" opens http://localhost:8501 (the Dev app) in a new tab, which only works on this computer; the logo, the tagline, the help lines under the three doors and "first time 第一次" are the assistant's wording, not the content owner's.

#### 8c.as  The home page rebuilt from the second mockup: the path of the eight sounds (2026-11-01)
The second home mockup (made by the image bot from the assistant's brief, "learn from Duolingo / ELSA": one big next action, a path, a mascot) is saved in app/learner/assets/mockups/home_v2_path.png (the first one, three cards, as home_v1_cards.png). learner/home.py was rewritten to it: the logo and a blue mascot with a big "Continue 繼續" (-> the first sound that is not yet at 3 stars; "All done! 全部完成" -> the map when all are); on the right the PATH of the eight sounds, one node each in the order of the app (see, she, fee, pea, bee, me, knee, cheat) drawn as a loop with a dotted line: done (3 stars) = green ring with a check, the next one = large blue with "START 開始", the others grey; the stars the child has under each node (the real ones: learner/stars.py); a navy banner (child picker, star total, "Teachers 老師" -> the Dev app, gear); "Sound Check" (a green "first time 第一次" tag until the room was measured, a check after) and "My Stars" (-> the map) at the bottom right; the footer line. Every node opens its lesson (free order, as on the map). Below 860 px the page stacks (banner, logo, mascot, Continue, then the nodes in two columns).
The first time (no child saved yet): the banner shows "Add a child 新增學生" and 0 stars, the mascot speaks ("Hi! Let's see your sounds! 嗨！一起來看見你的聲音！"), the big button is "Let's start 開始吧" (-> Sound Check) with "Skip for now 先跳過" (-> the map), and the first node says "NEXT 下一個". It is made from the assistant's prompt text: the image bot has not drawn this state yet.
Differences from the mockup: the "3 days" chip is not drawn (nothing counts days: it would be invented); the mascot, the logo, the node pictures (the same as the map's islands) and the hills are the assistant's drawings, not the bot's; the order of the nodes follows the app, not the mockup (the mockup puts "me" before "bee" and "pea").
Checked with screenshots at 1366 and 390 px wide, with the real child (all done), with a temporary child with two sounds done (removed afterwards) and with no child; the links of the big button and of a node were followed. Not checked on a real phone.

#### 8c.at  The first-time home drawn to the third mockup (2026-11-01)
The image bot's first-time home (app/learner/assets/mockups/home_v3_first_time.png) is now what a visitor with no saved child sees (learner/home.py): the same layout as the home with progress, plus the mascot's speech bubble, "Let's start 開始吧" with its second line "First, a quick sound check 先做聲音檢查" (-> Sound Check), "Skip for now 先跳過" (-> the map), "NEXT 下一個" on the first node, a flag at the end of the path, a few small stars, and the three-step strip at the bottom right (1 Sound check highlighted, 2 Pick an island, 3 Collect stars; each a link) in place of the two small buttons. The strip, the flag and the stars are drawn with code. Not taken from the mockup: the grey child's face on the "she" node (the app keeps its own pictures).

#### 8c.au  The home page fits the window (2026-11-01, the user: "it does not fit, make it fit")
The home page was drawn at most 1240 px wide inside the lessons' 1200 px column and a 200 px bottom margin, so on a large screen it floated in the middle and the page scrolled. learner/home.py now removes the column limit and the margins for this page and sizes the stage to the window height (width = (window height - 30 px) x 1024/572, never wider than the window): measured at 1906x905, 1366x650 and 1100x800 the page is exactly as tall as the window (no scrolling) and the stage is 1566, 1110 and 1064 px wide. Two nodes were moved up a little so that their stars no longer sit under the Sound Check button. Below 860 px the stacked layout is unchanged.

#### 8c.av  The image bot's own mascot on the home page (2026-11-01, the user: "keep the character as the other bot drew it, mine is ugly; make the format and everything like its image")
The mascot drawn by the assistant with code is gone. learner/assets/mascot_wave.png is the bot's mascot cut out of its home mockup (home_v2_path.png, 1024 px wide: the cut is about 775x753 px, so a little soft on a large screen): the body is found by its blue (not the sky, not the dark blue button), the holes of eyes and mouth are filled, the navy outline is kept by growing the shape a few pixels, the edge is smoothed (made with scipy/PIL in the scratchpad, not part of the app). Placed as in the mockup, standing on the "Continue" button (z-index above it), with the speech bubble of the first-time page to its right, rounded with a tail. The rest of the page keeps the bot's layout (logo block, cream card, path, banner, steps strip, flag, stars, hills, footer bar).
To replace by a sharper file when the bot gives its separate transparent PNGs (deliverable 2 of the brief): overwrite assets/mascot_wave.png, nothing else changes. The logo's eye, the node pictures and the other small icons are still the assistant's drawings.

#### 8c.aw  The bot's picture is the background of the home page (2026-11-01, the user: "ugly, make the other bot's picture the background itself, no square frame")
The home page no longer draws a frame on the sky: the image bot's mockup (assets/mockups/home_v2_path.png) is the page background, full window, and the app draws on it only what changes. app/static/home_bg.jpg is that picture with what the app draws itself taken out (made by assets/mockups/make_home_bg.py from the mockup): the banner is kept without its contents, the path, nodes, labels and the two quick buttons are replaced by the sky of their rows, the right hill is drawn again, the button and the words under it are replaced by the colour of the card; the logo, the tagline, the sun, the clouds, the mascot (it stands on the card, now baked in the picture, not a separate cut-out), the hills, the sea and the footer line stay as the bot drew them. The picture is repeated at its left and right edges (3 pictures wide) so that a wide window has no bars. The stage (the part that is exactly the picture) is as wide as the window, or as wide as the window is high x 1024/572 when the window is less wide; everything the app draws (child and stars, Teachers, the Continue / Let's start button, the speech bubble, the nodes and the dotted path, Sound Check and My Stars or the three steps) is placed on it in the picture's pixels. At 1906x905, 1366x700: no scrolling. Under 860 px the picture is not used (the old stacked page with the cut-out mascot and a plain sky).
Limits: the picture is 1024 px wide, so on a big screen it is soft; the plate is made by filling the removed parts, so it can show a few small marks (a few dots under the mascot's feet, a notch in the hill) that the buttons hide; the order of the nodes is still the app's (see, she, fee, pea, bee, me, knee, cheat) on the places the mockup gives them. To replace by a sharp, clean picture: ask the bot for the same picture at 2732x1536 without the nodes, the path, the banner's contents, the buttons and the texts of the card, and save it over app/static/home_bg.jpg (with the same edge repeat).

#### 8c.ax  The bot's clean background and files; the logo mark becomes a spectrogram (2026-11-01, the user: "change the eye next to SeeSound into spectrogram lines")
The bot answered the brief for a clean plate: the files are saved in app/learner/assets/mockups (bg_bot_v4.png the plate, mascot_bot_v4.png the waving mascot on white, logo_bot_v4.png, assets_sheet_bot_v4.png the 13 parts on one sheet, about_bot_v1.png the About page as a landscape screen). All of them are 1024 px wide (the brief asked 3072 px / SVG: not delivered), so the picture is still soft when zoomed.
make_home_bg.py (same folder) builds what the app uses from them: app/static/home_bg.jpg (the plate; its eye logo is replaced by a small SPECTROGRAM mark drawn here: a dark panel with a faint frequency grid and three wavy formant tracks in yellow, blue and coral; its small thinking mascot is taken out and the card's top line is drawn again, because the app puts the waving mascot in the card; the edge columns are repeated so that a wide window has no bars) and learner/assets/mascot_wave.png (the bot's mascot, white made transparent). learner/home.py is fitted to the new picture: the banner is thinner (its contents are smaller: the banner's lower edge goes up to y = 39 of 572), the card is at x 50-342, the button and the texts are centred in it, the waving mascot stands in it, the speech bubble is to its right.
Not used yet: the bot's logo (it has the eye), the 13-part sheet and the About page: the About page of the app is still to be built. The eye stays in logo_bot_v4.png only; if the spectrogram mark is kept, the logo file of the brief should be redrawn with it.

#### 8c.ay  Back to the bot's path picture as the background, with the mascot kept whole (2026-11-01, the user: "use this picture again, but do not let the background at the mascot lose its lines")
The user preferred the bot's home picture with the path (saved again as assets/mockups/home_v5_path.png; it is the same picture as home_v2_path.png up to compression) to the clean plate of 8c.ax. make_home_bg.py now builds app/static/home_bg.jpg from it (the v4 script is kept as make_home_bg_v4.py). The earlier cut of this picture (8c.aw) had erased a strip under the mascot's feet and part of their outline with the button; now the mascot is found by its light blue (not the darker blue of the button), its eyes and mouth are filled, and it is grown by 3 px so that its navy outline is protected: only what is not the mascot is turned into card colour, and the card's own bottom line is left alone. The eye of the logo is kept as the bot drew it (SPECTROGRAM = False in the script; True puts the spectrogram mark back). learner/home.py is fitted again to this picture (thicker banner, card at x 36-330, the button just under the mascot's feet). Checked by screenshots at 1906, 1366 and 390 px, with a child and with none.

#### 8c.az  The home page is the bot's picture itself (2026-11-01, the user: "the lines you made are stiff; keep everything as in this picture, put it in, change nothing, only redraw where it is blurred")
On a computer (wider than 860 px) the home page is now exactly the image bot's picture, with nothing drawn on it: assets/mockups/home_returning.png when a child is saved, home_first_time.png the first time (no child). make_home_pictures.py only enlarges each picture 2x and sharpens its soft edges (unsharp mask, radius 1.8, 110 %), and repeats the edge columns outside the picture so that a wide window has no bars (app/static/home_ret.jpg, home_first.jpg). The app puts invisible tap areas on the picture's buttons and nodes (learner/home.py HOT_RETURNING, HOT_FIRST, TEACHER_AREAS, in the picture's 1024 x 572 pixels; ?hot=1 outlines them): each node opens its lesson, "Continue" opens the child's real next word (the map when all are done), Sound Check / the gear / "Let's start" / step 1 / "Add a child" open Sound Check, My Stars / the star count / "Skip for now" / steps 2 and 3 open the map, the name opens the list of children, "Teachers" opens the Dev app. A light glow shows under the pointer and a blue ring with the keyboard; each area has a label for screen readers. Under 860 px the stacked page drawn by the app (with the real name, stars and progress) is kept, because the picture does not fit a phone.
IMPORTANT, what this costs: the picture is fixed. Whoever plays sees "Mia", 24 stars, "3 days", /ʃ/ she as the next sound with START, /s/ see done, one star on "me", and "Next: /sh/ she 她", whatever their real progress (the real progress is only on the map, on a phone and behind "Continue"). The first-time picture is right for its state. Making the page true for each child needs either the drawn overlays the user did not like, or pictures of each state from the bot.

#### 8c.ba  Each child's own home page: name, boy or girl, stars, lit sounds; sounds open in order (2026-11-02, the user: "make the name match the profile, let the profile choose boy or girl, match the stars too; do not let the children press anywhere if they have not got a star on the sound before; the home page lights up the sounds and the stars as far as the child has read")
- Boy or girl: chosen when a child is added in Sound Check (required, "👦 Boy 男生 / 👧 Girl 女生"), changeable on the saved child's page; kept in profiles/_children.json (learner/children.py; personal data, not in git). A child saved before has none: shown as a boy until it is chosen.
- Sounds open one after the other, in the order of the lessons (see, she, fee, pea, bee, me, knee, cheat): a sound opens when the one before it has at least one star (learner/stars.py unlocked, frontier). On the home page a sound not open has no link (a hint says which sound to get a star on); on the map it is grey with "🔒 locked 未開放"; in a lesson its button is disabled, and opened by its address it shows "Not open yet 還沒打開" with a button to the sound to do now. ?open=all opens every sound (for a teacher). The order is the lessons' order, not the dotted path of the bot's picture, which does not run through the sounds in one line.
- The home page (computer): learner/assets/mockups/make_home_parts.py makes a NEUTRAL version of the bot's returning picture (every node grey: the START node of /sh/ is replaced by the grey /sh/ of the first-time picture, its left edge, hidden there by the speech bubble, mirrored from its right edge; the check of /s/ by the grey /s/ without its ribbon, the top of its ring mirrored from the bottom; the little star of /m/ by the mirror of the other side; colours of the first-time picture mapped to the returning one by a straight-line fit per channel on nodes drawn the same in both) and cuts pieces of the bot's drawing: each node lit (its grey disk turned yellow, its navy lines kept), each node "ready" (light blue), the START ribbon, the whole /sh/ START node, a star, the boy of the banner and a girl (the girl of the /sh/ node on the same round face). The page puts them back: face, name and star total in the banner (over a patch of the banner's own colour, which also covers the "3 days" chip), every sound with a star lit with its stars under it, the sound to do now (the first without a star) ready with the START ribbon (gently bobbing; still with reduced motion), "Next: /f/ fee 費用" under the button ("All done! 全部完成" when every sound has 3 stars). "Continue" goes to the sound to do now, else the first sound without 3 stars, else the map. Sound Check keeps its "first time" tag and check as the bot drew them (taking the tag out left a visible patch). The first-time picture is used as it is (it is right when there is no child).
Checked with a test child (girl, then removed): 0 stars (only /s/ open, START on /s/), 1 star on /s/ (the bot's START node on /sh/), /s/ 3 + /sh/ 2 (both lit with their stars, START on /f/, /p/ shows "Not open yet", map with 5 islands locked), and the real child (all lit, 24, "All done!"); tests for the opening rule and for boy/girl added (76 passed).
- "3 days": in the bot's mockup it is a streak (days in a row with practice), which the app does not record: covered, not shown.

#### 8c.bb  Begin with /sh/ (2026-11-02)
User request: start with /sh/, not /s/. Learner ORDER now she, see, fee, pea, bee, me, knee, cheat. Navigation and star-based unlocking consume this order; existing profile progress is preserved. Added an assertion that the first two lessons are she and see. Verification: start_apps.ps1 -Test: 76 passed (initial restricted run had two temporary-directory permission errors; unrestricted rerun passed). Learner server restarted and health reported up. Browser visuals and the first-time static Home artwork have not been verified for this change.


#### 8c.bc  Unpractised Home sounds stay grey (2026-11-02)
User request: unpractised she and see should be dark/grey without stars. Removed blue ready-node and START overlays for zero-star nodes on returning Home, and current-node styling on narrow Home. First-time Home covers the baked-in she/see progress regions with matching regions of the existing neutral background; no original artwork modified. Earned stars still come only from saved progress; unlocking remains she first. Verified: 76 tests passed; learner server health up after restart. Not verified: runtime screenshots, mobile appearance, or edge seams of first-time background patches.


#### 8c.bd  Position the first-time grey artwork patches (2026-11-02)
User reported she still blue. Root cause: the hm-live patch divs from 8c.bc lacked position:absolute; left/top and z-index therefore did not place them over the original first-time artwork. Added absolute positioning and z-index 2; pointer-events remain none so lesson links remain usable. Inspected preview_neutral.png: she and see in the source are grey with no stars. Learner restarted, health up. Runtime browser screenshot not yet verified; existing earned-star overlays remain intentional.


#### 8c.be  Version Home backgrounds to avoid stale artwork (2026-11-02)
Follow-up to 8c.bd: the user screenshot showed the old baked-in START/stars/check while a fresh browser showed neutral grey nodes. Home background URLs now include a SHA-256 content version, including the first-time patches. No progress/profile data changed. HTTP returned 200 image/jpeg for the versioned file. Final visual confirmation came during 8c.bf: returning Home for test 1 shows grey she and see, no earned node stars.

#### 8c.bf  User-supplied SeeSound symbol (2026-11-02)
Copied the supplied PNG unchanged to learner/assets/seesound_logo.png; verified source and destination hashes match. Home covers the old baked-in brand eye with the supplied symbol at the same position, preserving the wordmark and other artwork. Narrow Home also displays the supplied logo. Learner browser-tab icon uses the same PNG. No child-facing wording added, no scoring or profile changes. Restarted via start_apps.ps1 -Only learner: health up. Verified desktop Home in browser screenshot: new eye/wave logo above SeeSound, grey she/see and zero node stars for test 1. Not verified: narrow-screen layout, first-time Home, or actual favicon appearance; no full test suite rerun for this image/CSS-only change.
