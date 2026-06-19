# Opportunity (Cơ hội kinh doanh)

Bảng `Opportunity` lưu trữ thông tin về các cơ hội bán hàng đã được xác định từ Lead, đi kèm giá trị dự tính (Amount / Pipeline).

## 🔗 Liên Kết Dữ Liệu trong Graph View
* Chuyển đổi từ khách hàng tiềm năng: [[Lead]] (LeadId).
* Phân bổ cho nhân sự phụ trách: [[UserFunction]] (NguoiXuLyId).
* Liên kết với các báo giá chi tiết: [[Quotation]] (Quotation.OpportunityId).

## 📊 Phân loại Giai đoạn (`TinhTrang`)
* `2`: **Đang xử lý** (Processing)
* `3`: **Đã báo giá** (Quoted)
* `4`: **Đã chốt** (Close Won)
* `5`: **Thất bại** (Close Lost)

## 🛠️ Trích đoạn Logic Code Python (FastAPI)
```python
# Lấy phễu cơ hội kinh doanh (Funnel)
results = db.query(
    Opportunity.TinhTrang,
    func.count(Opportunity.Id),
    func.sum(Opportunity.Amount)
).filter(Opportunity.TrangThai == 1).group_by(Opportunity.TinhTrang).all()
```
