# Order (Đơn hàng)

Bảng `Order` lưu các đơn hàng e-commerce chính thức được chuyển đổi từ Báo giá thành công.

## 🔗 Liên Kết Dữ Liệu trong Graph View
* Được tạo từ báo giá gốc: [[Quotation]] (kết nối 1-1 hoặc 1-N qua trường `SoHopDong`).
* Nhân viên cập nhật đơn hàng: [[UserFunction]] (NguoiCapNhatId).

## 💰 Các cột doanh thu chính
* `PhiDonHang`: Tổng phí giá trị của đơn hàng (Được dùng làm KPI Doanh thu).
* `PhiDaNop`: Số tiền khách hàng đã thanh toán.
* `PhiConLai`: Khoản nợ còn lại cần thu hồi.

## 🛠️ Logic Join thống kê doanh thu theo Nhân viên Kinh doanh:
```sql
SELECT uf.FullName, SUM(o.PhiDonHang) AS tong_doanh_thu
FROM dbo.[Order] o
JOIN dbo.UserFunction uf ON o.NguoiCapNhatId = uf.Id
GROUP BY uf.FullName
ORDER BY tong_doanh_thu DESC;
```
