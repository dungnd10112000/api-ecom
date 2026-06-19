# Quotation (Báo giá)

Bảng `Quotation` lưu các báo giá chi tiết gửi đến khách hàng, chứa giá trị, số hợp đồng và danh mục thiết bị chào hàng.

## 🔗 Liên Kết Dữ Liệu trong Graph View
* Thuộc về cơ hội bán hàng: [[Opportunity]] (OpportunityId).
* Gửi cho khách hàng doanh nghiệp/cá nhân: [[Customer]] (PartnerId).
* Chứa danh sách các thiết bị/sản phẩm: [[Product]] (thông qua bảng nối `LinkQuotationProduct`).
* Được chuyển đổi thành đơn hàng chính thức: [[Order]] (kết nối qua trường `SoHopDong`).

## 📊 Trạng Thái Báo Giá (`TinhTrang`)
* **Hệ thống Database Local**:
  * `1` = Nháp (Draft)
  * `2` = Đã gửi (Delivered)
  * `3` = Đã xác nhận (Confirmed)
  * `4` = Thắng / Chốt (Won / Close Won)
  * `5` = Thua / Từ chối (Lost / Close Lost)
* **Tài liệu Swagger Live (Sai khác)**:
  * `3` = Thắng (Won)
  * `4` = Thua (Lost)

> [!WARNING]
> Có sự sai biệt giữa API Live và DB Local. Xem chi tiết đối chiếu trạng thái tại: [[00_Start_Here]].
