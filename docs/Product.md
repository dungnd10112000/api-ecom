# Product (Sản phẩm / Thiết bị)

Bảng `Product` lưu trữ danh mục thiết bị kỹ thuật, sản phẩm đo lường e-commerce phục vụ báo giá.

## 🔗 Liên Kết Dữ Liệu trong Graph View
* Thương hiệu sản phẩm: [[Taxonomy]] (ThuongHieuId, TaxonomyType = 26).
* Nhóm ngành hàng / Danh mục: [[Taxonomy]] (NhomThietBiId, TaxonomyType = 3).
* Nằm trong danh sách chào hàng của: [[Quotation]] (thông qua bảng nối `LinkQuotationProduct`).

## 🛠️ Các thông tin giá cả
* `GiaNhap`: Giá vốn nhập kho của sản phẩm.
* `GiaBan`: Giá niêm yết chào bán e-commerce.
