# Kịch bản video demo Ghost Customer — khoảng 8 phút

Quay bằng tiếng Việt, dùng **real mode**. Kịch bản này bao quát các phương pháp thống kê, hồi quy, dự báo và mọi thuật toán phân loại đã chạy trong repo. Các mốc là thời lượng mục tiêu; đọc tự nhiên, không cần nói đúng từng chữ.

## Chuẩn bị trước khi bấm quay

1. Làm theo [README](../README.md#run-the-complete-project-locally-windows-powershell). Chỉ bắt đầu khi `python -m scripts.verify_real_demo` báo `data_mode: real` và 7 API; dùng Python trong `.venv` như README. Mở sẵn website ở `/dashboard`, `/customers`, `/statistics`, `/forecast`, `/predict`, `/models`.
2. Mở [báo cáo tiếng Anh](../reports/full-report/GhostCustomer_STAT3013_Full_Report_EN.docx) tại mục 5 (OLS/logistic) và mục 8, Bảng 16 (Decision Tree/Gaussian NB). Mở `ai/evaluation/results_tables.md` bằng Markdown Preview trong VS Code cho bảng đầy đủ SVM và Isolation Forest. Tăng zoom để nhìn rõ số liệu.
3. Ở `/customers`, lọc `Ghost`, chọn một dòng **có nhãn chín** và ghi riêng ID cùng `snapshot_date` để nhập lại ở `/predict`. Không dùng số cụ thể trong lời thoại vì snapshot trên máy khác có thể thay đổi. Che ID visitor và đường dẫn cá nhân khi xuất video; không mở CSV gốc, token hoặc file `.env.local` trên màn hình.
4. Tắt thông báo nổi, kiểm tra micro, quay thử 15 giây và nghe lại. Hai server phải chạy suốt lượt quay. Các trang web là giao diện tiếng Việt; báo cáo và bảng kết quả là bằng chứng nghiên cứu.

## Lời thoại và thao tác

### 00:00–00:40 — Mở đầu (40 giây)

**Màn hình:** `/dashboard`, cho thấy dòng thông báo nguồn dữ liệu và năm KPI.

**Nói:** “Chào thầy cô, nhóm em thực hiện đề tài *Ghost Customer Prediction*: phân tích sự giảm tương tác của visitor trên website thương mại điện tử. Đây là bản demo chạy với dữ liệu Retailrocket thật, không phải dữ liệu mock. Nhóm không quan sát được việc một người thật sự rời bỏ cửa hàng; Ghost là nhãn vận hành dựa trên mức hoạt động tương đối qua thời gian. Video sẽ đi từ nguồn dữ liệu, kiểm định thống kê, hồi quy, dự báo, so sánh thuật toán đến một lần dự đoán trên web.”

### 00:40–01:20 — Dữ liệu và cách tạo nhãn (40 giây)

**Màn hình:** KPI Overview; chuyển nhanh sang hình thiết kế thời gian ở mục 3 của báo cáo.

**Nói:** “Nguồn có 2.756.101 sự kiện. Từ đó pipeline tạo 97.489 snapshot tuần của 27.327 visitor khác nhau; một visitor có thể xuất hiện nhiều lần. Mỗi snapshot có bốn tuần nền, hai tuần quan sát trước mốc T và hai tuần xác nhận sau T. Mô hình chỉ nhận đặc trưng có sẵn trước T; phần sau T dùng để gán nhãn. Trong số snapshot đủ lịch sử, 11.590 hàng chưa quan sát đủ tương lai được giữ là *unknown*, không tự gán thành không Ghost. Các cửa sổ và ngưỡng hiện là quyết định nghiên cứu đang đề xuất.”

### 01:20–02:05 — Dòng dữ liệu trên web (45 giây)

**Màn hình:** `/customers`, lọc Ghost; mở một trang `/customers/{id}` và chỉ mốc snapshot, đặc trưng trước T, timeline xác nhận.

**Nói:** “Trang danh sách cho lọc trạng thái, tìm kiếm và sắp xếp các snapshot. Em mở một hàng Ghost và chỉ mốc T. Bên trái là lịch sử và đặc trưng đã biết khi chấm điểm; đoạn xác nhận nằm sau T để người xem kiểm tra nhãn, nhưng không được đưa ngược vào mô hình. Đây là visitor ẩn danh của bộ dữ liệu, không phải khách hàng đã xác minh danh tính. Trang chi tiết giúp kiểm tra vì sao cùng một visitor có thể có trạng thái khác nhau ở các tuần khác nhau.”

### 02:05–02:55 — Thống kê mô tả và kiểm định Welch (50 giây)

**Màn hình:** `/statistics`; cuộn từ biểu đồ và bảng mô tả xuống kiểm định. Dừng ở N, khoảng tin cậy, p-value và effect size.

**Nói:** “Phân tích mô tả trình bày số quan sát, giá trị thiếu, mean, median, độ lệch chuẩn và phân vị theo từng nhóm. Để kiểm định chênh lệch *recency* trước T, nhóm chọn đúng một snapshot đủ nhãn mới nhất trên mỗi visitor rồi so Ghost với Active: 371 và 896 visitor. Ghost có recency trung bình cao hơn 11,39 ngày, khoảng tin cậy 95% từ 10,27 đến 12,51 ngày; kiểm định Welch cho p khoảng 7,52 nhân 10 mũ âm 63 và Cohen d là 1,71. Đây là liên hệ trong mẫu được chọn, không chứng minh nguyên nhân khiến khách hàng rời đi.”

### 02:55–03:45 — Hai bài toán hồi quy (50 giây)

**Màn hình:** Báo cáo mục 5, lần lượt Bảng 10–13 và hình chẩn đoán OLS/logistic.

**Nói:** “Nhóm chạy hai bài toán hồi quy riêng. OLS dự đoán số phiên mỗi tuần trong hai tuần sau T; mô hình nhiều biến có R bình phương trên tập train là 0,355 và RMSE test 0,870 phiên mỗi tuần. Tuy vậy, 5.927 dự đoán test bị âm, nên OLS chủ yếu phục vụ giải thích và chẩn đoán, chưa phù hợp để triển khai dự báo số đếm. Logistic là suy luận Ghost so với *mọi trạng thái đủ nhãn khác*, không cùng mẫu với bài toán phân loại Ghost–Active lát nữa. Trên 15.470 hàng test, chỉ 316 Ghost; PR-AUC là 0,096 và recall tại ngưỡng validation 0,10 chỉ 5,7%. Vì vậy không dùng kết quả logistic này làm cảnh báo.”

### 03:45–04:20 — Dự báo chuỗi tuần (35 giây)

**Màn hình:** `/forecast`, chỉ 12 điểm lịch sử, hai điểm tương lai và các ô MAE/RMSE.

**Nói:** “Trang dự báo dùng tỷ lệ Ghost theo tuần chỉ khi nhãn tương lai đã đủ chín. Chuỗi có 12 tuần, nên nhóm dùng baseline ngây thơ: giữ tỷ lệ tuần chín gần nhất, thay vì tuyên bố đã chọn được ARIMA ổn định. Ba mốc kiểm tra ngược cho MAE khoảng 0,255 điểm phần trăm; hai điểm màu dự báo là tiếp diễn ngắn hạn, không kèm khoảng tin cậy. Kết quả này dùng để minh họa quy trình, chưa đủ cho dự báo dài hạn.”

### 04:20–05:25 — Đầy đủ các thuật toán phân loại (65 giây)

**Màn hình:** `/models`; chuyển sang Bảng 16 báo cáo cho Decision Tree/Gaussian NB, rồi `ai/evaluation/results_tables.md` để quét toàn bộ danh sách.

**Nói:** “Đối với phân loại, nhóm so Ghost với Active trên split tách visitor và thời gian: 2.214 hàng train, 454 validation và 430 test, trong đó test có 109 Ghost. Mức PR-AUC không kỹ năng là khoảng 0,254. Luật EDS đạt 0,802. Thành chạy Decision Tree đạt 0,927; Lâm chạy Gaussian Naive Bayes đạt 0,667. Bộ so sánh của Kiệt còn có Logistic Regression 0,899, Random Forest 0,929, XGBoost 0,928, SVM kernel RBF 0,803 và Isolation Forest 0,322. Như vậy các baseline mạnh yếu đều được trình bày; Random Forest nhỉnh hơn XGBoost một chút trên test, nhưng model phục vụ được chọn bằng validation và hiệu chuẩn Platt, không chọn lại theo test. Các số này chỉ so trực tiếp được vì cùng nhãn Ghost–Active và cùng split.”

### 05:25–06:15 — Dự đoán thật và xử lý lỗi (50 giây)

**Màn hình:** `/predict`, nhập ID và ngày đã chuẩn bị, nhấn “Dự đoán”; chỉ score, model version, tín hiệu giải thích. Sau đó nhập một ID không tồn tại và gửi lại.

**Nói:** “Bây giờ em nhập visitor và đúng ngày snapshot T, rồi gửi đến API. Backend lấy đặc trưng trước T và chạy model XGBoost đã huấn luyện, có hiệu chuẩn Platt. Score hiển thị là xác suất ước lượng theo nhãn Ghost vận hành, kèm version model và các tín hiệu đóng góp; đó không phải xác suất người này chắc chắn bỏ đi, và tín hiệu không phải giải thích nhân quả. Em thử ID không tồn tại để thấy hệ thống báo lỗi rõ ràng, thay vì tự tạo điểm số. API cũng kiểm tra ngày không hợp lệ.”

### 06:15–07:05 — Đánh giá, ngưỡng và kiểm tra rò rỉ định nghĩa (50 giây)

**Màn hình:** `/models`, dừng ở confusion matrix/calibration; mở hình ablation ở mục 8 báo cáo.

**Nói:** “Model được phục vụ đạt PR-AUC test 0,928, khoảng tin cậy 95% từ 0,887 đến 0,958; ROC-AUC 0,970. Ở ngưỡng 0,05 chọn trên validation theo giả định bỏ sót tốn gấp năm lần báo động giả, test có 109 true positive, 74 false positive, không có false negative. Ngưỡng thấp giúp recall cao nhưng tăng số cảnh báo sai. Điểm cần nhấn mạnh là phép ablation: giữ toàn bộ lịch sử đạt 0,928; chỉ giữ mười biến quan sát gần T thì còn 0,607. Vì nhãn dùng hoạt động nền làm mẫu số, điểm cao phụ thuộc mạnh vào baseline và chưa chứng minh tín hiệu độc lập về nguy cơ rời bỏ.”

### 07:05–08:00 — Giới hạn và kết thúc (55 giây)

**Màn hình:** báo cáo mục 7 và 11, rồi quay về `/dashboard`.

**Nói:** “Dữ liệu chỉ là log tương tác ẩn danh; nhãn Ghost do nhóm đề xuất, nhiều snapshot có cùng visitor, và các phép phân tích dùng những mẫu số khác nhau. Báo cáo cũng ghi rõ chưa có mô hình đo lường biến tiềm ẩn đủ cơ sở để công bố SEM; nhóm cần quyết định của giảng viên, nên không bịa hệ số hoặc chỉ số fit. Hệ thống hiện chạy xuyên suốt từ dữ liệu, thống kê, các thuật toán và API đến website với bảy route đã kiểm tra. Đóng góp chính là quy trình có thể tái tạo và cách công khai giới hạn của dự đoán. Nhóm chỉ đề xuất dùng score làm tín hiệu nghiên cứu, chưa dùng tự động để tác động tới khách hàng. Em xin cảm ơn thầy cô.”

## Bảng nhắc nhanh khi quay

| Phần | Thuật toán / phương pháp | Chứng cứ nên mở |
| --- | --- | --- |
| Thống kê | Mô tả theo nhóm; Welch t-test | `/statistics`; `research/statistics/results.json` |
| Hồi quy | OLS nhiều biến; logistic Ghost-vs-rest | Báo cáo mục 5; `research/regression/results/` |
| Dự báo | Last mature value / naive | `/forecast`; `research/forecasting/analysis_manifest.json` |
| Phân loại | EDS rule, Decision Tree, Gaussian NB, Logistic Regression, Random Forest, XGBoost + Platt, SVM RBF, Isolation Forest | `/models`; Bảng 16 báo cáo; `ai/evaluation/results_tables.md` |
| Độ tin cậy | Calibration, confusion matrix, ablation full vs observation-only | `/models`; báo cáo mục 8 |

**Không nói:** “đã chứng minh churn”, “XGBoost tốt nhất trên test”, “đã làm SEM/ARIMA”, hoặc “PR-AUC 0,928 trên toàn bộ 97.489 snapshot”. Test phân loại chỉ có 430 hàng Ghost/Active; dashboard có mẫu số khác.
