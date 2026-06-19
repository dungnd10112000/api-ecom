# Activity (Hoạt động chăm sóc)

Bảng `Activity` ghi lại nhật ký tương tác của Sales Rep với khách hàng tiềm năng.

## 🔗 Liên Kết Dữ Liệu trong Graph View
* Thực hiện chăm sóc đối với: [[Lead]] (LeadId).

## 📊 Phân loại hoạt động (`LoaiHoatDong`)
* `2`: Gọi điện (Call)
* `3`: Email
* `4`: Gặp mặt/Họp (Meeting)
* `5`: Nhiệm vụ (Task)
* `6`: Khác (Other)

> [!NOTE]
> Bảng thống kê local loại trừ `ActivityType = 1` vì đây là log hệ thống tự động, chỉ ghi nhận các hoạt động tương tác thủ công thực tế của nhân viên.
