Cấu trúc quan hệ (Khóa ngoại \- Foreign Keys) trong database `TCT_CRM`, dưới đây là danh sách các bảng có liên kết với nhau và mục đích sử dụng (nội dung) của chúng:

### **Nhóm Khách Hàng (Customer & Lead)**

* **`Address`** 🔗 **`Customer`**: Bảng `Address` dùng để lưu trữ các địa chỉ liên hệ/giao hàng chi tiết của một Khách hàng (`Customer`). Một khách hàng có thể có nhiều địa chỉ.  
* **`LinkContact`** 🔗 **`Customer`**: Bảng `LinkContact` (có thể là bảng nối) dùng để quản lý các Người liên hệ (Contact) thuộc về một Khách hàng hoặc tổ chức (`Customer`) nào đó.  
* **`Lead`** 🔗 **`RawCustomer`**: Bảng `Lead` (Khách hàng tiềm năng) được liên kết từ `RawCustomer` (Khách hàng thô/chưa phân loại). Dùng trong quy trình lọc từ khách hàng thô sang lead chính thức.  
* **`Activity`** 🔗 **`Lead`**: Bảng `Activity` lưu trữ các hoạt động (gọi điện, gửi email, gặp mặt,...) đã thực hiện để chăm sóc một Khách hàng tiềm năng (`Lead`).

### **Nhóm Báo Giá & Đơn Hàng (Quotation & Order)**

* **`HistoryQuotation`** 🔗 **`Quotation`**: Bảng `HistoryQuotation` dùng để lưu lại lịch sử các phiên bản thay đổi (versions) của một Báo giá (`Quotation`).  
* **`QuotationEditor`** 🔗 **`Quotation`**: Bảng này quản lý danh sách những nhân sự (editor) có quyền chỉnh sửa hoặc đã tham gia chỉnh sửa một Báo giá cụ thể.  
* **`LinkQuotationProduct`** 🔗 **`Quotation`**: Bảng nối dùng để lưu danh sách các Sản phẩm (Product) cụ thể nằm trong một Báo giá (`Quotation`).  
* **`Order`** 🔗 **`Quotation`**: Bảng `Order` (Đơn hàng) được sinh ra từ một Báo giá (`Quotation`) đã được chốt/phê duyệt. **Nhóm Cơ Hội Bán Hàng (Opportunity)**  
* **`LinkOpportunityProduct`** 🔗 **`Opportunity`**: Bảng nối lưu danh sách các Sản phẩm (Product) mà khách hàng đang quan tâm trong một Cơ hội bán hàng (`Opportunity`).

### **Nhóm Phân Loại & Gắn Thẻ (Taxonomy & Tag)**

* **`TreeTaxonomy`** 🔗 **`Taxonomy`**: Bảng `TreeTaxonomy` dùng để quản lý cấu trúc cây phân cấp (cha \- con) của các danh mục/loại (`Taxonomy`).  
* **`LinkRelatedTaxonomy`** 🔗 **`Taxonomy`**: Bảng lưu trữ các mối quan hệ liên kết ngang hàng hoặc liên quan giữa các `Taxonomy` với nhau.  
* **`LinkTag`** 🔗 **`Tag`**: Bảng nối dùng để gắn các Thẻ (Tag) vào các đối tượng khác nhau trong hệ thống (như Customer, Lead, Product...).

### **Nhóm Phân Quyền (User & Role)**

* **`UserFunction`** 🔗 **`RoleFunction`**: Bảng `UserFunction` liên kết với `RoleFunction` để quản lý và map các chức năng (Function/Permission) cụ thể mà một người dùng (User) hoặc một vai trò (Role) được phép thực hiện trong hệ thống.

—-----------------------------------------------Note Join----------------------------------------------------

# LEAD

**\-Số lead theo nguồn (web, event, referral, cold...)**   
 (Cột `SourceId` của bảng `dbo.Lead` được liên kết trực tiếp với cột `Id` của bảng `dbo.Taxonomy`. Cụ thể, các giá trị trong cột `SourceId` (ví dụ như `14`, `20`, `1026`,...) tương ứng với các bản ghi trong bảng `Taxonomy` có `TaxonomyType = 3` (đại diện cho các Nguồn khách hàng / Nguồn gốc cơ hội).)

**\-Số lead theo tỉnh/thành phố**

dbo.Lead  
  └─ RawCustomerId (FK) → dbo.RawCustomer  
                              └─ AreaId (FK) → dbo.Taxonomy (TaxonomyType \= 1\)  
                                                   └─ TieuDe \= "Thành phố Hồ Chí Minh", "Tỉnh Bắc Ninh"...  
**Tỉnh/Thành phố KHÔNG lưu trực tiếp trong dbo.Lead**, mà lưu qua 2 bước:

1. dbo.Lead.RawCustomerId → dbo.RawCustomer.AreaId  
2. dbo.RawCustomer.AreaId → dbo.Taxonomy.Id (với TaxonomyType \= 1)

**\- Số lead theo ngành hàng / nhóm khách hàng (nhóm ngành hàng chưa rõ/ nhóm khác hàng (doanh nghiệp/cá nhân/khác)**  
**\- Số lead theo sales rep (người phụ trách)**  
JOIN dbo.Lead  cột NguoiXuLyId với bảng dbo.UserFunction lấy trường FullName và UserName.

**\- Số lead theo trạng thái (New, Quality, Opty, Quotation, Process, Finshed)**  
 6\. GET /api/leads/stats/by-status  
//    Số lead theo trạng thái (New, Quality, Opty, Quotation, Process, Finshed)

\- **Tỉ lệ lead qualified vs unqualified theo thời gian** 

# Opportunity

**\- Số cơ hội theo thời gian  \==**

* date\_from / date\_to — lọc theo ngày tạo  
* group\_by — chỉ dùng cho by-time: day | week | month (mặc định month)

**\- Số cơ hội theo sales rep \==**

* Query: JOIN UserFunction qua NguoiXuLyId,  
* |date\_from / date\_to — lọc theo ngày tạo  
* group\_by — chỉ dùng cho by-time: day | week | month (mặc định month)

**\- Số cơ hội theo sản phẩm / nhóm sản phẩm**  
LinkOpportunityProduct hoàn toàn **trống** (0 rows). Data thực tế đi qua chain:   
Opportunity → Quotation (OpportunityId) → LinkQuotationProduct → Product → Taxonomy  
//    Join chain (LinkOpportunityProduct trống, dùng Quotation):  
//    Opportunity → Quotation.OpportunityId  
//                → LinkQuotationProduct.QuotationId  
//                → Product.Id  
//                → Taxonomy(NhomThietBiId) ← parent: Taxonomy(KhoaChaId)  
//                → Taxonomy(ThuongHieuId)  
//  
//    view=group      → nhóm theo nhóm sản phẩm CHA  (KhoaChaId)  
//    view=subgroup   → nhóm theo nhóm sản phẩm CON  (NhomThietBiId)  
//    view=product    → nhóm theo từng sản phẩm  
//    view=brand      → nhóm theo thương hiệu

**\- Tổng giá trị pipeline theo thời gian**  
**API 3 – pipeline-by-time**

* Query: SUM(Amount), AVG(Amount) nhóm theo day/week/month  
* Response: { period, so\_co\_hoi, tong\_gia\_tri, trung\_binh }

**\- Tổng giá trị pipeline theo sales rep**

* Query: JOIN UserFunction qua NguoiXuLyId, tính SUM/AVG/MAX(Amount)  
* Response: { FullName, UserName, so\_co\_hoi, tong\_gia\_tri, trung\_binh, max\_gia\_tri } — sắp xếp theo tong\_gia\_tri DESC

**\- Phân bố cơ hội theo stage (funnel view)**

* Query: GROUP BY TinhTrang → map sang tên stage: 2=Đang xử lý, 3=Đã báo giá, 4=Đã chốt, 5=Thất bại  
* Response có thêm: tong\_toan\_bo, tong\_gia\_tri, ti\_le\_so\_luong (%), ti\_le\_gia\_tri (%) — sẵn sàng vẽ funnel chart

**\- Thời gian trung bình từ lead → cơ hội**

* Query: INNER JOIN dbo.Lead ON LeadId, dùng DATEDIFF(minute) để tính chính xác  
* Response: summary (tổng hợp: phút/giờ/ngày, min, max) \+ data (xu hướng theo kỳ nếu có group\_by)  
* Thực tế DB: trung bình \~**55.5 giờ (≈ 2.3 ngày)** từ lead → cơ hội

# BÁO GIÁ (QUOTATION)

\- Số báo giá gửi theo thời gian \==  
\- Số báo giá theo sales rep==  
\- Số báo giá theo sản phẩm / nhóm sản phẩm  
 summary: "Số báo giá theo nhóm sản phẩm (Taxonomy)"  
 \*     description: |  
 \*       Thống kê số lượng báo giá và tổng giá trị theo \*\*nhóm sản phẩm cha\*\* (Taxonomy).  
 \*       JOIN: \`dbo.Quotation\` → \`dbo.LinkQuotationProduct\` → \`dbo.Product\` → \`dbo.Taxonomy\` (nhóm cha).  
 \*       Sản phẩm không thuộc nhóm nào sẽ được gom vào \`Không xác định\`.  
 \*       Hỗ trợ tham số \`level\` để xem theo nhóm cha (\`parent\`) hoặc nhóm con (\`child\`).

\- Tỉ lệ báo giá → thắng / thua==  
\- Thời gian trung bình từ cơ hội → báo giá=  
\- Số lần chỉnh sửa trung bình mỗi báo giá=

# ĐƠN HÀNG (ORDER)

**\- Số đơn hàng theo thời gian=**  
 Hỗ trợ lọc theo \`date\_from\` / \`date\_to\` và nhóm theo \`group\_by\` (day / week / month).  
 \*     tags: \[Orders\]

**\- Doanh thu theo thời gian=**  
 Bảng dbo.\[Order\] có các trường: PhiDonHang (phí đơn hàng),   
Thống kê tổng doanh thu (\`PhiDonHang\`) và số đơn hàng theo từng kỳ thời gian.  
 \*       Hỗ trợ lọc theo \`date\_from\` / \`date\_to\` và nhóm theo \`group\_by\` (day / week / month).

**\- Doanh thu theo sales rep=**  
Bảng dbo.\[Order\] có các trường: PhiDonHang (phí đơn hàng), NguoiCapNhatId (sales rep) 

**\- Doanh thu theo sản phẩm / nhóm sản phẩm=**  
   description: |  
 \*       Thống kê doanh thu từ đơn hàng nhóm theo \*\*sản phẩm\*\* hoặc \*\*nhóm sản phẩm\*\* (Taxonomy).  
 \*       \- \`level=product\`: nhóm theo từng sản phẩm cụ thể  
 \*       \- \`level=group\` (mặc định): nhóm theo danh mục sản phẩm cấp cha (Taxonomy)  
 \*       \- \`level=subgroup\`: nhóm theo danh mục sản phẩm cấp con  
 \*  
 \*       Join chain: \`dbo.\[Order\]\` → \`dbo.Quotation\` (qua \`SoHopDong\`) → \`dbo.LinkQuotationProduct\` → \`dbo.Product\` → \`dbo.Taxonomy\`.  
 \*     tags: \[Orders\]

**\- Doanh thu theo tỉnh/thành phố**

* Tỉnh/thành phố: dbo.Order → dbo.Quotation → dbo.Lead → dbo.RawCustomer → dbo.Taxonomy (AreaId, TaxonomyType=1), hoặc qua dbo.Customer  
* Join chain: Order → Quotation (SoHopDong) → Lead → RawCustomer → Taxonomy (AreaId, TaxonomyType=1)  
* Trả về: area\_id, tinh\_thanh, so\_don\_hang, tong\_doanh\_thu, ti\_le %

**\- Doanh thu theo nhóm khách hàng**

* Nhóm khách hàng: Customer.ClassifyType (1=Doanh nghiệp, 2=Cá nhân) hoặc Customer.NhomKhachHangId → Taxonomy  
* Join chain: Order → Quotation → Opportunity → Customer (PartnerId)  
* Nhóm theo ClassifyType: 1=Doanh nghiệp, 2=Cá nhân, null=Không xác định  
* Trả về: nhom\_khach\_hang, so\_don\_hang, so\_khach\_hang, tong\_doanh\_thu, ti\_le %

**\- Giá trị đơn hàng trung bình (Average Deal Size)**

* Average Deal Size \+ Thời gian báo giá→chốt đơn: từ dbo.\[Order\] và dbo.Quotation  
* Tính AVG(PhiDonHang) trực tiếp trên dbo.\[Order\]  
* Hỗ trợ group\_by (day/week/month) để xem xu hướng,  
* Trả về summary (avg/min/max/tổng) \+ data trend theo kỳ

\- **Thời gian trung bình từ báo giá → chốt đơn**

* DATEDIFF(minute, Quotation.NgayTao, Order.NgayCapNhat) join qua SoHopDong  
* Chỉ tính cặp hợp lệ: Order.NgayCapNhat \>= Quotation.NgayTao  
* Hỗ trợ group\_by, trả về phút/giờ/ngày TB, min, max

# CHUYỂN ĐỔI (CONVERSION)

**\- Tỉ lệ Lead → Cơ hội**

**Lead →** Opportunity: dbo.Lead → dbo.Opportunity (qua Opportunity.LeadId) đếm Lead đã có Opportunity  
Tính tỉ lệ % số Lead được chuyển thành Cơ hội (Opportunity).  
 \*       \- \*\*Tổng Lead\*\*: đếm tất cả Lead có TrangThai \= 1 trong khoảng thời gian lọc.  
 \*       \- \*\*Lead chuyển đổi\*\*: đếm Lead đã có ít nhất 1 Opportunity liên kết (Opportunity.LeadId \= Lead.Id).  
 \*       \- \*\*Tỉ lệ\*\*: \`(lead\_da\_chuyen / tong\_lead) \* 100\` (%).

**\- Tỉ lệ Cơ hội → Báo giá**

**Cơ hội → Báo giá**: dbo.Opportunity → dbo.Quotation (qua Quotation.OpportunityId)  
 Opportunity LEFT JOIN Quotation ON q.OpportunityId \= op.Id — đếm Opportunity đã có Quotation   
Tính tỉ lệ % số Cơ hội được chuyển thành Báo giá (Quotation).  
 \*       \- \*\*Tổng Cơ hội\*\*: đếm Opportunity có TrangThai \= 1 trong khoảng thời gian lọc.  
 \*       \- \*\*Cơ hội có Báo giá\*\*: đếm Opportunity đã có ít nhất 1 Quotation liên kết (Quotation.OpportunityId \= Opportunity.Id).  
 \*       \- \*\*Tỉ lệ\*\*: \`(co\_hoi\_da\_bao\_gia / tong\_co\_hoi) \* 100\` (%).  
 \*

**\- Tỉ lệ Báo giá → Đơn hàng (Win Rate)**

Tính Win Rate – tỉ lệ % số Báo giá được chuyển thành Đơn hàng (Chốt thành công).  
 \*       Dựa trên trường \`Quotation.TinhTrang\`:  
 \*       \- \*\*1\*\* \= Nháp (Draft)  
 \*       \- \*\*2\*\* \= Đã gửi (Delivered)  
 \*       \- \*\*3\*\* \= Đã xác nhận (Confirmed)  
 \*       \- \*\*4\*\* \= \*\*Thắng / Chốt (Close Won)\*\* ← được tính là "thành đơn"  
 \*       \- \*\*5\*\* \= Thua / Từ chối (Close Lost)

**\- Tỉ lệ chuyển đổi end-to-end: Lead → Đơn hàng**  
 \*       \*\*Định nghĩa "Lead thành đơn"\*\*: Lead có ít nhất 1 chuỗi:  
 \*       \`Lead → Opportunity (LeadId) → Quotation (OpportunityId, TinhTrang=4 Close Won)\`.  
 \*  
 \*       \- \*\*Tổng Lead\*\*: Lead có TrangThai \= 1 trong khoảng thời gian lọc.  
 \*       \- \*\*Lead có cơ hội\*\*: Lead đã tạo Opportunity.  
 \*       \- \*\*Lead có báo giá\*\*: Lead có Opportunity đã tạo Quotation.  
 \*       \- \*\*Lead thành đơn\*\*: Lead có Quotation với \`TinhTrang \= 4\` (Close Won).  
 \*       \- \*\*Tỉ lệ\*\*: \`(lead\_thanh\_don / tong\_lead) \* 100\` (%).

**\- Win Rate theo sales rep**  
Join: Quotation → Opportunity.NguoiXuLyId → UserFunction

Lead thành đơn \= Lead có ít nhất 1 Quotation với TinhTrang \= 4 (Close Won)  
Chain: Lead → Opportunity.LeadId → Quotation.OpportunityId (TinhTrang \= 4\)

Tỉ lệ % Báo giá chốt thành công (Close Won) phân tách theo từng nhân viên phụ trách cơ hội (\`Opportunity.NguoiXuLyId\`).  
 \*  
 \*       Dựa trên \`Quotation.TinhTrang\`:  
 \*       \- \*\*4\*\* \= Close Won ← được tính là "thành đơn"  
 \*       \- \*\*5\*\* \= Close Lost  
 \*       \- \*\*3\*\* \= Đã xác nhận  
 \*       \- \*\*2\*\* \= Đã gửi  
 \*       \- \*\*1\*\* \= Nháp  
 \*  
 \*       \- \*\*win\_rate\_phan\_tram\*\*: tính trên số đã có kết quả (Close Won \+ Close Lost).  
 \*       \- \*\*win\_rate\_toan\_bo\*\*: tính trên toàn bộ báo giá của rep đó.  
 \*  
 \*       Lọc ngày theo \`Quotation.NgayTao\`.

**\- Win Rate theo sản phẩm / nhóm sản phẩm**

Tỉ lệ % Báo giá chốt thành công (Close Won) phân tách theo sản phẩm hoặc nhóm sản phẩm.  
 \*  
 \*       Dựa trên \`Quotation.TinhTrang\`:  
 \*       \- \*\*4\*\* \= Close Won ← được tính là "thành đơn"  
 \*       \- \*\*5\*\* \= Close Lost  
 \*  
 \*       \- \*\*Tổng Báo giá\*\* (có chứa sản phẩm đó): số Quotation có LineItem sản phẩm đó.  
 \*       \- \*\*Báo giá thành đơn\*\*: Quotation có \`TinhTrang \= 4\` (Close Won).  
 \*       \- \*\*win\_rate\_phan\_tram\*\*: tính trên đã có kết quả (Close Won \+ Close Lost).  
 \*       \- \*\*win\_rate\_toan\_bo\*\*: tính trên toàn bộ báo giá có sản phẩm đó.  
 \*  
 \*       Tham số \`level\`:  
 \*       \- \`group\` (mặc định): nhóm theo \*\*danh mục sản phẩm cấp cha\*\* (Taxonomy)  
 \*       \- \`subgroup\`: nhóm theo \*\*danh mục sản phẩm cấp con\*\*  
 \*       \- \`product\`: nhóm theo \*\*từng sản phẩm\*\* cụ thể  
 \*  
 \*       Join chain: \`Quotation → LinkQuotationProduct → Product → Taxonomy\`.  
 \*       Lọc ngày theo \`Quotation.NgayTao\`.

# HOẠT ĐỘNG CHĂM SÓC (ACTIVITY)

**\- Số activity theo loại (gọi điện, email, gặp mặt...) theo thời gian**  
 JOIN với dbo.UserFunction để lấy tên nhân viên, lọc TrangThai \= 1   
Thống kê số lượng hoạt động (Activity) phân loại theo loại hình (gọi điện, email, gặp mặt...).  
 \*       \- \*\*Tổng activity theo loại\*\*: đếm Activity nhóm theo \`LoaiHoatDong\` (loại hoạt động).  
 \*       \- Hỗ trợ \`group\_by\` để xem xu hướng theo ngày / tuần / tháng.

**\- Số activity theo sales rep**  
 JOIN với dbo.UserFunction để lấy tên nhân viên, lọc TrangThai \= 1   
Thống kê số lượng hoạt động (Activity) theo từng nhân viên phụ trách (\`Activity.NguoiTaoId\` hoặc \`NguoiXuLyId\`).  
 \*       \- Đếm tổng số activity và phân loại theo \`LoaiHoatDong\` cho từng sales rep.  
 \*       \- Lọc ngày theo \`Activity.NgayTao\`.  
 \*       \- Hỗ trợ \`group\_by\` để xem xu hướng theo ngày / tuần / tháng cho từng nhân viên.

**\- Số activity trung bình per lead**  
JOIN qua Activity.LeadId   
 Tính số lượng hoạt động (Activity) trung bình được ghi nhận cho mỗi Lead.  
 \*       \- \*\*Cách tính\*\*: đếm số Activity liên kết với mỗi Lead (qua \`Activity.LeadId\`), rồi lấy trung bình.  
 \*       \- Chỉ tính các Lead đang hoạt động (\`Lead.TrangThai \= 1\`).  
 \*       \- Chỉ tính các Activity đang hoạt động (\`Activity.TrangThai \= 1\`).  
 \*       \- Lọc ngày theo \`Lead.NgayTao\`.  
 \*       \- Hỗ trợ \`group\_by\` để xem xu hướng trung bình theo kỳ thời gian.

**\- Thời gian phản hồi trung bình từ lúc có lead đến activity đầu tiên**  
JOIN qua Activity.LeadId   
 Tính thời gian trung bình (giờ) từ khi Lead được tạo (\`Lead.NgayTao\`) đến khi Activity đầu tiên  
 \*       được ghi nhận cho Lead đó (\`MIN(Activity.NgayTao)\`).  
 \*       \- Chỉ tính các Lead đã có ít nhất 1 Activity liên kết.  
 \*       \- Loại bỏ các trường hợp Activity xảy ra \*\*trước\*\* ngày tạo Lead (dữ liệu lỗi).  
 \*       \- Lọc ngày theo \`Lead.NgayTao\`.  
 \*       \- Hỗ trợ \`group\_by\` để xem xu hướng thời gian phản hồi theo kỳ.  
 \*  
 \*       Đơn vị trả về: \*\*giờ\*\* (\`gio\`) và \*\*phút\*\* (\`phut\`) để tiện sử dụng.

# KHÁCH HÀNG (CUSTOMER)

**\- Số khách hàng mới theo thời gian**  
Thống kê số lượng khách hàng mới được tạo theo kỳ thời gian.  
 \*       \- Lọc ngày theo \`Customer.NgayTao\`.  
 \*       \- Hỗ trợ \`group\_by\` (day | week | month) để phân kỳ.  
 \*       \- Trả về tổng (\`tong\_khach\_hang\`) và mảng \`data\` phân kỳ (khi có \`group\_by\`).

**\- Số khách hàng theo tỉnh/thành phố**  
JOIN: Customer.AreaId → dbo.Taxonomy (TaxonomyType \= 1 \= tỉnh/thành phố)  
 Thống kê số lượng khách hàng phân theo tỉnh/thành phố.  
 \*       \- Tỉnh/thành phố lấy từ \`Customer.AreaId\` JOIN \`dbo.Taxonomy\` (\`TaxonomyType \= 1\`).  
 \*       \- Hỗ trợ lọc khoảng thời gian tạo (\`NgayTao\`).  
 \*       \- Kết quả sắp xếp giảm dần theo số khách hàng.  
 \*       \- Các khách hàng chưa chọn tỉnh/thành sẽ được nhóm vào \`"Không xác định"\`.

**\- Số khách hàng theo nhóm / ngành**  
  Thống kê số lượng khách hàng phân theo nhóm/loại từ các trường nội bộ:  
 \*       \- \*\*\`ClassifyType\`\*\*: phân loại hình thức KH — \`1 \= Cá nhân\`, \`2 \= Công ty / Doanh nghiệp\`.  
 \*       \- \*\*\`CustomerType\`\*\*: loại mối quan hệ — \`1 \= Khách hàng thường\`, \`2 \= Đại lý / Partner\`.  
 \*       \- Kết quả gồm 2 mảng \`by\_classify\_type\` và \`by\_customer\_type\`, mỗi mảng có \`so\_luong\` và \`ti\_le\`.  
 \*       \- Hỗ trợ lọc theo \`date\_from\` / \`date\_to\` (theo \`Customer.NgayTao\`).

**\- Tỉ lệ khách hàng quay lại (repeat order)**  
 JOIN sử dụng:  
//      • dbo.Customer            — thông tin khách hàng  
//      • dbo.Quotation           — JOIN qua Quotation.PartnerId \= Customer.Id  
//      • dbo.\[Order\]             — JOIN qua Order.Id \= Quotation.Id  
//                                  (Order.Id là FK trỏ vào Quotation.Id)  
//  
//    Logic: Khách "quay lại" \= có ≥ 2 Order trong khoảng thời gian lọc

**\- Doanh thu từ khách mới vs khách cũ**  
    JOIN sử dụng:  
//      • dbo.Customer            — ngày tạo KH (Customer.NgayTao)  
//      • dbo.Quotation           — JOIN qua Quotation.PartnerId \= Customer.Id  
//                                  → lấy TongGiaTri (doanh thu)  
//      • dbo.\[Order\]             — JOIN qua Order.Id \= Quotation.Id  
//  
//    Logic phân loại:  
//      \- "Khách MỚI"  \= KH lần đầu có đơn hàng TRONG khoảng lọc  
//                       (không có đơn hàng nào TRƯỚC date\_from)  
//      \- "Khách CŨ"   \= KH đã từng có đơn hàng TRƯỚC khoảng lọc  
// ═══════════════════════════════════════════════════════════════════

