# Taxonomy (Phân loại & Danh mục)

Bảng `Taxonomy` đóng vai trò là danh mục dùng chung phân loại mọi thông tin trong CRM theo cấu trúc phân cấp (Cha - Con).

## 🔗 Liên Kết Dữ Liệu trong Graph View
* Phân loại tỉnh thành cho khách hàng: [[Customer]] (AreaId).
* Phân loại tỉnh thành cho lead thô: [[RawCustomer]] (AreaId).
* Phân loại nguồn gốc tiếp cận của lead: [[Lead]] (SourceId).
* Phân nhóm thiết bị / Thương hiệu cho sản phẩm: [[Product]] (NhomThietBiId / ThuongHieuId).

## 📊 Các loại Taxonomy (`TaxonomyType`)
* `1`: **Khu vực / Tỉnh thành** (Tỉnh Bắc Ninh, TP Hà Nội, TP Hồ Chí Minh...)
* `3`: **Nguồn lead / Nguồn cơ hội** (Web, Event, Referral, Cold Call...)
* `26`: **Thương hiệu** (Mitutoyo, Insize, Mahr, Bosch...)
* `3` (Nhóm Thiết Bị): **Danh mục thiết bị** (Thước kẹp, Đồng hồ so, Ampe kìm...)
