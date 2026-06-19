# Customer (Khách hàng chính thức)

Bảng `Customer` lưu trữ thông tin về các tài khoản khách hàng doanh nghiệp hoặc cá nhân đã phát sinh giao dịch.

## 🔗 Liên Kết Dữ Liệu trong Graph View
* Tỉnh/Thành phố đăng ký: [[Taxonomy]] (AreaId, TaxonomyType = 1).
* Nhóm phân loại khách hàng: [[Taxonomy]] (NhomKhachHangId).
* Lịch sử các báo giá gửi khách hàng: [[Quotation]] (PartnerId).

## 📊 Phân loại Khách hàng
* `ClassifyType`:
  * `1`: Doanh nghiệp (Enterprise)
  * `2`: Cá nhân (Individual)
* `CustomerType`:
  * `1`: Khách hàng thường (Normal)
  * `2`: Đại lý / Đối tác (Partner)
