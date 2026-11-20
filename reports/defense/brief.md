# Ghost Customer Prediction

## Bản tóm tắt để bảo vệ ngày 20 tháng 11 năm 2026

**Tình trạng:** Bản nghiên cứu và demo chạy được trên dữ liệu Retailrocket thật với thiết lập 4+2+2 tuần đang đề xuất. Các quyết định về cohort, nhãn, split và SEM chưa được phê duyệt. Mọi số liệu bên dưới có nguồn trong repo hoặc artifact tái tạo tại máy, không lấy từ dữ liệu mock.

### Câu trả lời mở đầu trong 30 giây

Nhóm phân tích dấu hiệu giảm tương tác của khách truy cập thương mại điện tử. Từ 2.756.101 sự kiện Retailrocket, nhóm tạo các snapshot hằng tuần; đặc trưng chỉ dùng hành vi trước thời điểm T, còn nhãn Ghost dựa trên 2 tuần xác nhận sau T so với mức hoạt động nền của chính visitor. Chúng tôi kiểm tra khác biệt hành vi, hồi quy, dự báo tỷ lệ Ghost và so sánh các mô hình phân loại. Demo web hiển thị dữ liệu đã xử lý và dự đoán của model đã huấn luyện. Nhãn Ghost là quy ước vận hành trong nghiên cứu, không chứng minh một người đã rời bỏ cửa hàng.

### 12 ý chính cho slide

1. **Vấn đề:** Cần nhận biết visitor có khả năng giảm tương tác sau T. Không có nhãn churn thật hay danh tính khách hàng đã xác minh.
2. **Nguồn:** Retailrocket Kaggle v2, 2.756.101 sự kiện, SHA-256 của `events.csv` là `3745aa83…cfecbf9e7`; file gốc không được đưa lên Git. Cần ghi công nguồn và tuân thủ giấy phép CC BY-NC-SA 4.0.
3. **Thiết kế thời gian:** Baseline 4 tuần, observation 2 tuần trước T, confirmation 2 tuần sau T. Tất cả là đề xuất D-02/D-03. Đặc trưng kết thúc trước T. Horizon chưa đủ quan sát là `unknown`, không gán bằng 0.
4. **Cohort:** 97.489 snapshot đủ lịch sử, 27.327 visitor khác nhau; 85.899 snapshot có horizon chín, 11.590 chưa chín. Trong hàng có nhãn chín có 2.619 Ghost, 9.263 Active, 71.301 Inactive và 2.716 Recovered. Đây là số snapshot lặp visitor, không phải số người độc lập.
5. **Thống kê mô tả và suy luận:** Bảng mô tả theo trạng thái có N và missingness. Kiểm định Welch dùng một snapshot chín mới nhất mỗi visitor, rồi lọc Ghost/Active: 371 Ghost và 896 Active. Recency trước T của Ghost cao hơn trung bình 11,39 ngày; KTC 95% [10,27; 12,51], p = 7,52 × 10⁻⁶³, Cohen d = 1,71. Đây là liên hệ quan sát, không phải tác động nhân quả.
6. **Hồi quy tuyến tính:** Biến phụ thuộc là số phiên trong 2 tuần sau T chia 2, đơn vị phiên/tuần. 43.536 hàng train, 17.368 hàng test không trùng visitor train. Mô hình nhiều biến có R² train 0,355 và RMSE test 0,870. Hệ số `sessions_4w` 0,127 [0,106; 0,148]; OLS dự đoán âm cho 5.927 hàng test, nên mô hình đếm phù hợp hơn cho triển khai.
7. **Logistic suy luận:** Bài toán là Ghost so với các trạng thái chín khác, khác tập dân số của AI. Test có 15.470 hàng, 316 Ghost (2,04%). PR-AUC 0,096 so với mức không kỹ năng 0,020; ROC-AUC 0,761. Với ngưỡng chọn từ validation là 0,10, recall chỉ 5,7% (18/316), nên không dùng logistic này để ra quyết định cảnh báo.
8. **Dự báo:** Có 12 điểm tỷ lệ Ghost theo tuần chín nhãn. Chuỗi quá ngắn để chọn và đánh giá ARIMA ổn định; dùng baseline giữ tỷ lệ chín gần nhất. Ba mốc backtest cho MAE 0,00255 trên thang tỷ lệ, tương đương khoảng 0,255 điểm phần trăm. Demo hiển thị hai tuần tương lai; không có khoảng tin cậy.
9. **Model phân loại Ghost so với Active:** Split theo thời gian và visitor, có purge nhãn: train 2.214, validation 454, test 430 hàng; test có 109 Ghost. XGBoost + Platt được chọn trên validation PR-AUC, đạt test PR-AUC 0,928 [0,887; 0,958]. EDS rule 0,802, Decision Tree của Thành 0,927, Gaussian NB của Lâm 0,667; mức không kỹ năng xấp xỉ 0,254.
10. **Kiểm tra vòng lặp định nghĩa nhãn:** Nhãn chia số phiên tương lai cho số phiên baseline, trong khi model thấy baseline. Bỏ tên các biến baseline/decay nhưng giữ các cửa sổ chồng lấn vẫn đạt 0,909; chỉ giữ 10 biến của observation 1–2 tuần thì còn 0,607. Vì vậy điểm 0,928 phụ thuộc mạnh vào lịch sử baseline, chưa chứng minh tín hiệu cảnh báo độc lập mạnh.
11. **Demo:** Overview → Customers → một timeline theo T → Statistics → Forecast → Predict → Model Metrics. Chọn một hàng Ghost thật trong danh sách và giữ `snapshot_date`. Gửi ID lạ để cho thấy 404; ngày không hợp lệ cho thấy 422. Cả 7 API đã qua smoke với artifact thật và `ENABLE_DEMO_FIXTURES` tắt.
12. **Kết luận và giới hạn:** Nhóm có một nghiên cứu tái tạo được và demo chạy xuyên suốt. Phát hiện chính là baseline rất quan trọng cho nhãn tương đối. Chỉ nên dùng điểm số như tín hiệu nghiên cứu trên cohort này; chưa đủ bằng chứng cho hệ thống tự động tác động khách hàng. D-01–D-05 và SEM D-07 cần xác nhận trước khi gọi kết quả là cuối cùng.

### Ba câu hỏi dễ gặp

**Tại sao tỷ lệ Ghost ở dashboard thấp hơn 25% trong bảng model?** Dashboard chia 2.619 Ghost cho toàn bộ 97.489 snapshot, gồm inactive, unknown và nhiều hàng lặp. AI chỉ học và đánh giá Ghost so với Active sau khi lọc nhãn chín và chia visitor/time, nên test prevalence là 109/430 = 25,35%. Hai mẫu số khác nhau.

**PR-AUC 0,928 có nghĩa model biết ai sẽ bỏ đi không?** Không. Nó đo khả năng xếp hạng nhãn Ghost do nhóm định nghĩa trên 430 hàng test. Khi không dùng thông tin baseline, PR-AUC xuống 0,607. Không có nhãn churn thật hoặc thử nghiệm can thiệp.

**Tại sao không có SEM hoặc ARIMA?** Event log không có mô hình đo lường latent đã được định nghĩa, nên không thể xuất hệ số/fit SEM có cơ sở; nhóm cần hỏi giảng viên liệu có chấp nhận phân tích hồi quy với giới hạn này. Với 12 tuần nhãn chín, ARIMA chưa có đủ chuỗi để chọn và kiểm định; nhóm báo cáo baseline và sai số backtest nhỏ mẫu.

### Việc cần chuẩn bị trước lúc vào phòng

- Trên máy trình bày, chạy `python -m scripts.verify_real_demo` và `npm run build`. Model binary và dữ liệu đã xử lý không nằm trong Git; xem `docs/runbook.md` nếu phải dựng lại.
- Mở trước dashboard và `/docs`, kiểm tra mạng nội bộ localhost, font và kích thước chữ. Chụp/ghi video một lượt để có phương án dự phòng.
- Kiểm tra mọi con số trong báo cáo/slide theo `docs/evidence_register.md`. Ghi rõ đây là bản AI hỗ trợ soạn thảo trong audit theo yêu cầu môn học.
- Xin giảng viên quyết định D-07 về SEM; lấy ảnh Turnitin và kiểm tra AI; đặt tên repo theo mã lớp/nhóm; nộp các file qua hệ thống môn học. Không đánh dấu các mục đó đã xong trước khi có bằng chứng.

### Nguồn chính

- Retailrocket dataset: <https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset>
- Neslin và cộng sự (2006): <https://doi.org/10.1509/jmkr.43.2.204>
- Burez và Van den Poel (2009): <https://doi.org/10.1016/j.eswa.2008.05.027>
- Saito và Rehmsmeier (2015): <https://doi.org/10.1371/journal.pone.0118432>
- Guo và cộng sự (2017): <https://proceedings.mlr.press/v70/guo17a.html>
- Lundberg và Lee (2017): <https://proceedings.neurips.cc/paper_files/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html>
