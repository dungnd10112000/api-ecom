# Bản Đồ Quan Hệ Cơ Sở Dữ Liệu TCT_CRM

Chào mừng bạn đến với tài liệu dự án dạng mạng liên kết. Tệp này đóng vai trò là **Hub trung tâm** kết nối toàn bộ cấu trúc dữ liệu. 

> [!TIP]
> Hãy nhấn phím tắt `Ctrl + G` (hoặc mở menu bên trái chọn **Graph View**) trong Obsidian để xem sơ đồ quan hệ tương tác trực quan của toàn bộ cơ sở dữ liệu! Các tệp tin dưới đây sẽ tự động hiển thị thành các nút liên kết với nhau.

---

## 1. Bản Đồ Thực Thể Chính (Core Entities)
Dưới đây là các thực thể cốt lõi trong hệ thống CRM và các liên kết trực tiếp giữa chúng:

* **Khách hàng tiềm năng**: [[Lead]] - Nơi tiếp nhận thông tin thô ban đầu, liên kết với [[RawCustomer]].
* **Cơ hội kinh doanh**: [[Opportunity]] - Được chuyển đổi từ [[Lead]], định giá giá trị dự án (Pipeline).
* **Báo giá**: [[Quotation]] - Báo giá chi tiết gửi khách hàng, chứa danh sách [[Product]].
* **Đơn hàng**: [[Order]] - Đơn hàng chính thức chốt từ báo giá thành công.
* **Khách hàng chính thức**: [[Customer]] - Thông tin tổ chức/công ty đại lý mua hàng.

---

## 2. Các Thực Thể Hỗ Trợ (Supporting Entities)
Các danh mục dùng chung để phân loại, quản lý nhân sự và thông tin chi tiết:

* **Phân loại & Tag**: [[Taxonomy]] - Lưu tỉnh thành, nguồn lead, thương hiệu, nhóm sản phẩm.
* **Khách hàng thô**: [[RawCustomer]] - Cầu nối tỉnh thành cho lead.
* **Nhân sự**: [[UserFunction]] - Tài khoản phụ trách xử lý lead, cơ hội, đơn hàng.
* **Hoạt động chăm sóc**: [[Activity]] - Nhật ký chăm sóc khách hàng (Call, Email, Meeting).

---

## 3. Bản Đồ Luồng Đồng Bộ & API
* Xem chi tiết luồng xử lý và đồng bộ từ live API về Database local tại: [[Data_Flows]]
