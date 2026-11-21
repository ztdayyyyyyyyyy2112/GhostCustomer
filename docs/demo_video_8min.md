# Kịch bản video 8 phút — chỉ thao tác trên website

Chỉ ghi trình duyệt ở `http://localhost:3000`. Không chuyển sang code, terminal, báo cáo, CSV hoặc trang API. Mốc thời gian là mục tiêu để tập trước khi quay. **Trang Thuật toán mở các kết quả nghiên cứu đã tính sẵn; chỉ trang Dự đoán chạy model XGBoost + Platt theo từng visitor.**

## Chuẩn bị trước khi quay

1. Khởi chạy backend và frontend theo [README](../README.md#run-the-complete-project-locally-windows-powershell) **trước** khi ghi hình. Mở `http://localhost:3000/dashboard`, kiểm tra giao diện báo dữ liệu thật, không phải mock. Giữ hai server chạy trong nền.
2. Dùng trình duyệt toàn màn hình, zoom 80–90% nếu màn hình nhỏ. Tắt thông báo nổi. Tập bấm menu trên đầu trang: **Tổng quan, Khách hàng, Thống kê, Dự báo, Dự đoán, Mô hình, Thuật toán**.
3. Tập thử dự đoán mã `2432`, ngày `2015-08-31`. Nếu dữ liệu local khác, chọn một dòng Ghost ở trang Khách hàng và ghi cả mã lẫn ngày snapshot để nhập vào form.
4. Trang Thuật toán có bốn nút nhảy: **1. Kiểm định và hồi quy**, **2. Dự báo**, **3. Phân loại**, **4. Giới hạn**. Bấm vào tên thẻ để mở, bấm lần nữa để thu gọn. Cuộn bằng bánh xe để xem tiếp.

## 00:00–00:45 — Tổng quan (45 giây)

**Bấm:** Đứng ở **Tổng quan**. Chỉ dòng nguồn dữ liệu thật và các ô KPI; cuộn nhẹ rồi trở lại đầu.

**Nói:** “Chào thầy cô. Nhóm em phân tích Ghost Customer từ dữ liệu sự kiện Retailrocket. Website hiện nối dữ liệu thật của dự án. Có 97.489 snapshot theo tuần, và một visitor có thể xuất hiện nhiều tuần. Ghost là nhãn vận hành mô tả sự giảm tương tác, chưa chứng minh một người thực sự rời bỏ cửa hàng. Em sẽ trình bày dữ liệu, thống kê, các thuật toán, đánh giá và một lần dự đoán trên web.”

## 00:45–01:30 — Xem khách hàng (45 giây)

**Bấm:** Menu **Khách hàng** → ô **Trạng thái** chọn **Ghost** → **Áp dụng**. Chỉ các cột **Khách hàng**, **Snapshot**, **Trạng thái**, **Risk score**. Ở dòng đầu bấm **Xem chi tiết**. Cuộn từ **Đặc trưng dự đoán** xuống **Baseline và observation**, rồi **Confirmation sau T**.

**Nói:** “Mỗi dòng là một visitor tại ngày snapshot T. Trang chi tiết tách đặc trưng trước T khỏi cửa sổ xác nhận sau T. Model chỉ dùng phần trước T; phần tương lai dùng để kiểm tra nhãn. Risk score là ước lượng theo định nghĩa của nhóm, không phải kết luận chắc chắn về khách hàng.”

## 01:30–02:20 — Mô tả và Welch t-test (50 giây)

**Bấm:** Menu **Thống kê** → chỉ biểu đồ phân phối và bảng mô tả → cuộn xuống bảng kiểm định. Bấm menu **Thuật toán** → nút **1. Kiểm định và hồi quy** → mở thẻ **Welch t-test**.

**Nói:** “Trang thống kê mô tả phân phối các nhóm. Để so recency Ghost và Active, nhóm lấy một snapshot đủ nhãn mới nhất cho mỗi visitor: 1.267 người. Welch t-test cho chênh lệch trung bình 11,39 ngày, khoảng tin cậy 95% từ 10,27 đến 12,51 ngày, p rất nhỏ và Cohen d 1,71. Đây là liên hệ quan sát, không phải bằng chứng nhân quả.”

## 02:20–03:15 — OLS và logistic suy luận (55 giây)

**Bấm:** Ở nhóm **1. Kiểm định và hồi quy**, bấm **OLS nhiều biến**; chỉ R², RMSE và số dự đoán âm. Bấm tiếp **Logistic suy luận**; chỉ PR-AUC và recall. Thu gọn Welch nếu thiếu chỗ.

**Nói:** “OLS dự đoán số phiên mỗi tuần sau T. R bình phương train là 0,355, RMSE test khoảng 0,870 phiên mỗi tuần, nhưng 5.927 dự đoán test bị âm. Nhóm dùng OLS để phân tích, chưa triển khai như dự báo số đếm. Logistic suy luận so Ghost với mọi trạng thái đủ nhãn khác: test có 15.470 snapshot, 316 Ghost, PR-AUC 0,096 và recall 5,7% tại ngưỡng 0,10. Đây là bài toán khác tập Ghost–Active dùng cho các classifier bên dưới.”

## 03:15–04:00 — Dự báo (45 giây)

**Bấm:** Trên trang **Thuật toán**, nút **2. Dự báo** → mở thẻ **Last mature value · naive** → bấm **Xem biểu đồ dự báo**. Ở trang **Dự báo**, chỉ các điểm lịch sử, fitted, hai điểm tương lai và ô sai số dưới biểu đồ.

**Nói:** “Nhóm chỉ dùng những tuần đã đủ thời gian xác nhận nhãn. Chuỗi có 12 tuần, nên baseline ngây thơ giữ tỷ lệ tuần chín gần nhất để dự báo hai tuần tiếp. Ba mốc backtest có MAE khoảng 0,255 điểm phần trăm. Đây là dự báo ngắn hạn chưa có khoảng tin cậy; chuỗi quá ngắn để tuyên bố đã chọn ARIMA ổn định.”

## 04:00–05:35 — Tất cả thuật toán phân loại (95 giây)

**Bấm:** Menu **Thuật toán** → nút **3. Phân loại**. Giữ bảng trên màn hình. Nếu bảng rộng, cuộn ngang **trong khung bảng** để thấy **PR-AUC**, **ROC-AUC**, **Precision**, **Recall**. Di con trỏ theo từng hàng: **Mức nền không kỹ năng**, **Luật EDS**, **Decision Tree · Thành**, **Gaussian Naive Bayes · Lâm**, **Logistic Regression · ML**, **Random Forest**, **XGBoost**, **XGBoost + Platt · Kiệt**, **SVM RBF**, **Isolation Forest**. Sau đó cuộn xuống các thẻ; mở lần lượt **Decision Tree**, **Gaussian Naive Bayes**, **Random Forest**, **XGBoost + Platt**, **SVM RBF**, **Isolation Forest**. Mỗi thẻ dừng 2–3 giây rồi bấm lại để thu gọn.

**Nói:** “Các thuật toán này dùng cùng bài toán Ghost–Active: 2.214 train, 454 validation và 430 test, trong đó có 109 Ghost. PR-AUC mức nền là 0,254, luật EDS 0,802. Decision Tree của Thành đạt 0,927; Gaussian Naive Bayes của Lâm 0,667. Logistic Regression cho ML đạt 0,899, Random Forest 0,929, XGBoost 0,928, SVM RBF 0,803 và Isolation Forest 0,322. XGBoost hiệu chuẩn Platt vẫn khoảng 0,928 và là phiên bản đang phục vụ. Random Forest nhỉnh hơn trên test, nhưng model phục vụ đã được chọn trên validation; nhóm không chọn lại bằng test. Các thẻ dưới bảng giải thích vai trò và giới hạn từng thuật toán.”

**Nhớ:** Chỉ **XGBoost + Platt** chạy theo visitor trên trang Dự đoán. Những hàng còn lại là kết quả đánh giá đã tính.

## 05:35–06:25 — Đánh giá model (50 giây)

**Bấm:** Menu **Mô hình** → chỉ bảng so sánh validation/test → cuộn xuống **Ma trận nhầm lẫn** rồi phần **Calibration**. Dừng ở các ô TN, FP, FN, TP; cuộn ngang trong khung bảng nếu cần.

**Nói:** “Ở ngưỡng 0,05 được chọn trên validation theo giả định bỏ sót tốn kém hơn, tập test có 109 true positive, 74 false positive và không có false negative. Recall cao nhưng có cảnh báo sai. Calibration cho thấy xác suất dự đoán so với tỷ lệ quan sát. Các chỉ số này thuộc 430 hàng test Ghost–Active, không phải toàn bộ 97.489 snapshot trên dashboard.”

## 06:25–07:20 — Chạy dự đoán và kiểm tra lỗi (55 giây)

**Bấm:** Menu **Dự đoán** → ô **Mã khách hàng**: xóa giá trị cũ, nhập `2432` → ô **Snapshot date**: chọn/gõ `2015-08-31` → **Dự đoán**. Chờ kết quả, chỉ **risk score**, **model version** và các tín hiệu. Sau đó thay mã bằng `not-a-real-visitor`, giữ ngày, bấm **Dự đoán**; chỉ thông báo lỗi. Hãy tập thử cặp mã/ngày trên dữ liệu máy mình trước khi quay.

**Nói:** “Đây là lần chạy trực tiếp XGBoost + Platt. Website lấy đặc trưng trước T rồi trả score, version của model và các tín hiệu liên quan. Score không phải xác suất chắc chắn người này bỏ đi, và các tín hiệu không chứng minh nguyên nhân. Với mã không tồn tại, website báo lỗi thay vì tự tạo điểm.”

## 07:20–08:00 — Giới hạn và kết thúc (40 giây)

**Bấm:** Menu **Thuật toán** → nút **4. Giới hạn**. Chỉ PR-AUC full và observation-only. Cuối cùng bấm **Tổng quan**, giữ màn hình yên 2 giây.

**Nói:** “Điểm cao còn phụ thuộc lịch sử nền: chỉ giữ 10 biến quan sát gần T thì PR-AUC giảm từ khoảng 0,928 xuống 0,607. Nhãn dùng hoạt động nền để định nghĩa suy giảm, nên score chưa chứng minh một cảnh báo churn độc lập mạnh. Event log cũng chưa đủ cơ sở để công bố SEM; nhóm không trình bày SEM hay ARIMA như kết quả đã hoàn thành. Website minh họa trọn luồng phân tích và dự đoán, đồng thời công khai giới hạn. Em xin cảm ơn thầy cô.”

## Nhắc nhanh

- Chỉ thao tác trong website. Nếu cuộn quá xa, bấm lại **Thuật toán** và nút nhóm tương ứng.
- Bấm vào **tên thẻ** để mở; bấm lại để đóng. Dừng con trỏ ở kết quả cho người xem đọc.
- Không gọi 97.489 snapshot là tập test; test classifier có 430 hàng. Không nói “đã chứng minh churn”, “XGBoost tốt nhất trên test”, “đã hoàn thành SEM/ARIMA”, hay “mọi thuật toán chạy lại khi bấm”.
