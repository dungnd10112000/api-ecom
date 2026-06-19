# Lead (Khách hàng tiềm năng)

Bảng `Lead` quản lý thông tin các khách hàng tiềm năng thu thập từ các nguồn (Web, Sự kiện, Gọi điện...).

## 🔗 Liên Kết Dữ Liệu trong Graph View
* Được tạo từ dữ liệu thô: [[RawCustomer]] (chứa thông tin tỉnh thành).
* Có nguồn gốc từ danh mục: [[Taxonomy]] (SourceId, TaxonomyType = 3).
* Được xử lý bởi nhân viên: [[UserFunction]] (NguoiXuLyId).
* Chuyển đổi thành cơ hội: [[Opportunity]] (Opportunity.LeadId).
* Chứa nhật ký chăm sóc: [[Activity]] (Activity.LeadId).

## 📊 Trạng Thái Lead (`TrangThai`)
* `1`: **New** (Mới tiếp nhận)
* `2`: **Quality** (Đạt tiêu chuẩn / Qualified)
* `3`: **Opty** (Đã tạo Cơ hội)
* `4`: **Quotation** (Đã gửi Báo giá)
* `5`: **Process** (Đang triển khai)
* `6`: **Finished** (Hoàn thành)

## 🛠️ Trích đoạn Code SQL Query Thống kê
```sql
-- Số lead theo tỉnh/thành phố
SELECT t.TieuDe AS tinh_thanh, COUNT(l.Id) AS so_lead
FROM dbo.Lead l
JOIN dbo.RawCustomer rc ON l.RawCustomerId = rc.Id
JOIN dbo.Taxonomy t ON rc.AreaId = t.Id
WHERE t.TaxonomyType = 1
GROUP BY t.TieuDe;
```
