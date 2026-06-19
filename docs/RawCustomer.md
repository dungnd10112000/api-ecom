# RawCustomer (Khách hàng thô)

Bảng `RawCustomer` lưu thông tin khách hàng thô chưa qua xử lý, đóng vai trò trung gian chứa dữ liệu địa phương.

## 🔗 Liên Kết Dữ Liệu trong Graph View
* Là thông tin gốc của: [[Lead]] (RawCustomerId).
* Lưu trữ khu vực tỉnh/thành: [[Taxonomy]] (AreaId, TaxonomyType = 1).
