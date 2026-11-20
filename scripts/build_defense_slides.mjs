/** Editable, evidence-linked Vietnamese defense deck. Run with bundled Node. */
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { Presentation, PresentationFile } from '@oai/artifact-tool';

const root = process.env.GHOSTCUSTOMER_ROOT || path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const build = path.join(root, 'data/processed/slide_build');
const output = path.join(root, 'reports/slides');
const skill = 'C:/Users/ASUS/.codex/plugins/cache/openai-primary-runtime/presentations/26.1119.11507/skills/presentations';
const python = 'C:/Program Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1119-907-0_26.1119.907.0_x64__3k8sg7r9htsxt/dependencies/python/python.exe';
await fs.mkdir(build, { recursive: true });
await fs.mkdir(output, { recursive: true });

const ppt = Presentation.create({ slideSize: { width: 1280, height: 720 } });
const C = { navy:'#0B2033', blue:'#116A9A', cyan:'#45B5D2', pale:'#EAF5F8', white:'#FFFFFF', ink:'#17334A', muted:'#516979', line:'#C4DCE6', orange:'#E78949' };
const font = 'Arial';
function box(slide,x,y,w,h,fill=C.white) {
  return slide.shapes.add({ geometry:'rect', position:{left:x,top:y,width:w,height:h}, fill, line:{style:'solid',fill:'none',width:0} });
}
function txt(slide,value,x,y,w,h,size=22,color=C.ink,bold=false) {
  const s=slide.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{style:'solid',fill:'none',width:0}});
  s.text=value; s.text.style={fontFamily:font,fontSize:`${size}pt`,color,bold,verticalAlignment:'middle'}; return s;
}
function base(title,num,subtitle='') {
  const s=ppt.slides.add(); s.background.fill=C.white;
  box(s,0,0,1280,14,C.cyan); txt(s,title,58,45,1150,72,31,C.navy,true);
  if(subtitle) txt(s,subtitle,60,116,1140,54,15,C.muted);
  box(s,58,656,1164,1,C.line); txt(s,'STAT3013 · Ghost Customer · Bản thảo bảo vệ',58,665,900,32,10,C.muted); txt(s,String(num).padStart(2,'0'),1165,665,55,32,10,C.muted,true);
  return s;
}
function label(s,text,x,y,w=300) { txt(s,text,x,y,w,34,15,C.blue,true); }
function body(s,text,x,y,w,h=120,size=19) { txt(s,text,x,y,w,h,size,C.ink,false); }
function stat(s,value,title,x,y,w=330) { box(s,x,y,w,155,C.pale); txt(s,value,x+20,y+18,w-40,72,37,C.blue,true); txt(s,title,x+20,y+91,w-40,52,16,C.ink); }
function bar(s,name,value,max,x,y,width=670,color=C.blue) { txt(s,name,x,y,300,40,16,C.ink); box(s,x+300,y+8,width,20,C.pale); box(s,x+300,y+8,width*value/max,20,color); txt(s,String(value),x+300+width+12,y,100,40,16,C.ink,true); }

{
 const s=ppt.slides.add(); s.background.fill=C.navy; box(s,0,0,1280,16,C.cyan);
 txt(s,'GHOST CUSTOMER',72,160,1060,82,48,C.white,true);
 txt(s,'Dự đoán giảm tương tác từ event log thương mại điện tử',74,270,1060,105,30,C.white);
 txt(s,'STAT3013 · Dữ liệu Retailrocket · Bản thảo ngày 20/11/2026',74,500,1050,60,18,C.cyan);
 txt(s,'Định nghĩa nhãn, cohort và SEM đang chờ xác nhận với giảng viên.',74,582,1050,45,16,C.white);
}
{
 const s=base('Câu hỏi nghiên cứu',2,'Ta biết gì tại thời điểm T để nhận diện visitor có xu hướng giảm tương tác?');
 label(s,'DỮ LIỆU QUAN SÁT',76,218); body(s,'Lượt xem, thêm giỏ, giao dịch và phiên truy cập trước T.',76,265,495,145,23);
 label(s,'KẾT QUẢ ĐO',685,218); body(s,'Ghost là nhãn vận hành từ 2 tuần sau T so với mức hoạt động nền của chính visitor.',685,265,495,170,23);
 box(s,76,493,1100,96,C.pale); body(s,'Không có nhãn churn thật, danh tính khách hàng đã xác minh hoặc bằng chứng can thiệp.',101,506,1050,72,20);
}
{
 const s=base('Nguồn và phạm vi dữ liệu',3,'Retailrocket e-commerce dataset, Kaggle v2 · CC BY-NC-SA 4.0');
 stat(s,'2.756.101','sự kiện trong events.csv',72,205,345);
 stat(s,'27.327','visitor khác nhau trong cohort',465,205,345);
 stat(s,'97.489','snapshot đủ lịch sử',858,205,345);
 body(s,'Dữ liệu gốc không nằm trên Git. SHA-256 events.csv: 3745aa83…cfecbf9e7.',80,447,1100,86,20);
 body(s,'Nguồn: kaggle.com/datasets/retailrocket/ecommerce-dataset; evidence E-01–E-03.',80,541,1100,47,15);
}
{
 const s=base('Thiết kế thời gian và nhãn',4,'Thiết kế 4 + 2 + 2 tuần đang đề xuất; không đưa sự kiện tương lai vào đặc trưng.');
 const parts=[['4 tuần','Mức hoạt động nền',C.blue],['2 tuần','Quan sát trước T',C.cyan],['T','Thời điểm dự đoán',C.orange],['2 tuần','Xác nhận sau T',C.blue]];
 let x=62; for(const [top,below,color] of parts){const w=top==='T'?145:330;box(s,x,250,w,100,color);txt(s,top,x+10,263,w-20,72,29,C.white,true);body(s,below,x,363,w,90,18);x+=w+18;}
 body(s,'Horizon chưa đủ quan sát → unknown. Một visitor có nhiều snapshot; khi suy luận phải tránh coi chúng độc lập.',72,500,1130,92,20);
}
{
 const s=base('Cohort và trạng thái',5,'85.899 snapshot chín nhãn; 11.590 snapshot còn censored/unknown.');
 bar(s,'Inactive',71301,71301,75,220,600,C.muted);bar(s,'Active',9263,71301,75,285,600,C.blue);bar(s,'Recovered',2716,71301,75,350,600,C.cyan);bar(s,'Ghost',2619,71301,75,415,600,C.orange);
 body(s,'Các con số là snapshot, không phải số người độc lập. Tỷ lệ ở dashboard và test model có mẫu số khác nhau.',75,527,1110,86,20);
}
{
 const s=base('Thống kê suy luận và hồi quy',6,'Tách một snapshot chín nhãn mới nhất mỗi visitor cho kiểm định Ghost–Active.');
 stat(s,'11,39 ngày','chênh lệch recency trung bình',75,220,345);
 stat(s,'[10,27; 12,51]','khoảng tin cậy 95%',465,220,345);
 stat(s,'0,355','R² train của OLS đa biến',855,220,345);
 body(s,'Welch: 371 Ghost, 896 Active; p = 7,52 × 10⁻⁶³, d = 1,71. Đây là liên hệ quan sát.',75,421,1110,83,20);
 body(s,'OLS dự đoán âm trên 5.927 hàng test; phù hợp để phân tích, chưa phù hợp làm model đếm triển khai.',75,515,1110,86,20);
}
{
 const s=base('Hồi quy logistic và dự báo',7,'Hai bài toán khác nhau: Ghost so với mọi trạng thái chín; tỷ lệ Ghost theo tuần.');
 label(s,'LOGISTIC SUY LUẬN',77,210,480);body(s,'Test 15.470 hàng, 316 Ghost. PR-AUC 0,096; ROC-AUC 0,761. Ngưỡng 0,10 chỉ bắt đúng 18/316 Ghost.',77,260,500,245,21);
 label(s,'DỰ BÁO TUẦN',675,210,480);body(s,'Chỉ có 12 tuần chín nhãn. Baseline giữ tỷ lệ gần nhất; 3 mốc backtest, MAE 0,255 điểm phần trăm. Chưa đủ để chọn ARIMA ổn định.',675,260,500,245,21);
 body(s,'Không diễn giải forecast như khoảng tin cậy hay khuyến nghị vận hành.',77,557,1080,55,18);
}
{
 const s=base('So sánh model trên cùng split',8,'Ghost so với Active · Test 430 snapshot, 109 Ghost · PR-AUC càng cao càng tốt.');
 bar(s,'XGBoost + Platt',0.928,1,75,212,635,C.blue);bar(s,'Decision Tree',0.927,1,75,285,635,C.cyan);bar(s,'EDS rule',0.802,1,75,358,635,C.orange);bar(s,'Gaussian NB',0.667,1,75,431,635,C.muted);
 body(s,'Mức không kỹ năng ≈ 0,254. XGBoost được chọn bằng validation, không chọn sau khi xem test.',75,545,1090,67,19);
}
{
 const s=base('Giới hạn quan trọng của PR-AUC 0,928',9,'Nhãn chia hoạt động tương lai cho baseline; model cũng nhìn thấy baseline.');
 stat(s,'0,928','đầy đủ đặc trưng',78,223,340);stat(s,'0,909','bỏ tên biến baseline/decay',470,223,340);stat(s,'0,607','chỉ 10 biến observation',862,223,340);
 body(s,'Đặc trưng cửa sổ chồng lấn vẫn mang thông tin baseline. Kết quả cao chưa chứng minh tín hiệu cảnh báo độc lập mạnh.',78,460,1095,125,23);
}
{
 const s=base('Demo end-to-end trên dữ liệu thật',10,'Chạy backend và frontend ở chế độ real; dữ liệu và model binary tái tạo cục bộ.');
 const steps=['Overview','Customers','Timeline','Statistics','Forecast','Predict','Model Metrics'];
 let x=64;let y=247;for(let i=0;i<steps.length;i++){const w=i===6?220:153;box(s,x,y,w,68,i===5?C.blue:C.pale);txt(s,steps[i],x+9,y+11,w-18,48,16,i===5?C.white:C.ink,true);x+=w+9;}
 body(s,'API: 7/7 route qua smoke test với artifact thật; ID lạ trả 404, ngày không hợp lệ trả 422.',73,393,1110,94,21);
 body(s,'Lệnh kiểm tra: python -m scripts.verify_real_demo',73,514,1110,58,19);
}
{
 const s=base('Kết luận và các quyết định còn mở',11,'Nghiên cứu có thể tái tạo và demo chạy được; kết luận vẫn cần đúng phạm vi.');
 body(s,'Có bằng chứng về mối liên hệ giữa hành vi trước T và nhãn Ghost vận hành trên cohort này.',75,218,1100,103,24);
 body(s,'Chưa có nhãn churn thật, tác động nhân quả, SEM hợp lệ hoặc chuỗi dài cho ARIMA.',75,342,1100,93,22);
 body(s,'Cần giảng viên xác nhận cohort, nhãn, split và yêu cầu SEM (D-01–D-07).',75,468,1100,95,22);
}
{
 const s=base('Hỏi đáp nhanh',12,'Nguồn số liệu: docs/evidence_register.md; quy trình: docs/runbook.md.');
 label(s,'VÌ SAO DASHBOARD ≠ TEST PREVALENCE?',76,210,900);body(s,'Dashboard: 2.619/97.489 snapshot. Test AI: 109/430 sau khi lọc Ghost–Active và split.',76,248,1080,80,20);
 label(s,'MODEL CÓ DỰ ĐOÁN CHURN THẬT KHÔNG?',76,350,900);body(s,'Chưa. Model dự đoán nhãn do nhóm định nghĩa; observation-only PR-AUC 0,607.',76,388,1080,74,20);
 label(s,'TẠI SAO CHƯA CÓ SEM/ARIMA?',76,487,900);body(s,'Thiếu measurement model cho SEM và chỉ có 12 tuần chín nhãn cho forecast.',76,525,1080,73,20);
}

for(let i=0;i<ppt.slides.items.length;i++){
 const blob=await ppt.export({slide:ppt.slides.items[i],format:'png',scale:1});
 await fs.writeFile(path.join(build,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await blob.arrayBuffer()));
}
const candidate=path.join(build,'candidate.pptx');
await (await PresentationFile.exportPptx(ppt)).save(candidate);
const { finalizePresentation }=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const result=await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:path.join(output,'defense_deck.pptx'),pythonExecutable:python,integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit'],requiredNativeTableOwnerSlides:[],fontPolicy:{basis:'design',families:[font]},verifyArtifactToolImport:true,receiptPath:path.join(build,'validation.json')});
console.log(result);
