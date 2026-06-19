# UserFunction (Nhân viên / Phân quyền)

Bảng `UserFunction` lưu danh sách các tài khoản nhân viên (Sales Rep, Admin, Kế toán) tham gia vận hành CRM.

## 🔗 Liên Kết Dữ Liệu trong Graph View
* Chăm sóc và xử lý: [[Lead]] (NguoiXuLyId).
* Phụ trách thúc đẩy: [[Opportunity]] (NguoiXuLyId).
* Lập và gửi báo giá: [[Quotation]] (NguoiXuLyId).
* Chốt và bàn giao: [[Order]] (NguoiCapNhatId).

## 🛠️ Logic Code:
Các thống kê theo nhân sự (Sales Rep performance) sử dụng bảng này để lấy trường hiển thị `FullName` và `UserName` thay vì hiển thị ID dạng chuỗi UUID.
