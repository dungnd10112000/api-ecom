from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Boolean, Table
from sqlalchemy.orm import relationship
from app.database import Base

# Junction Table for many-to-many relationship between Quotation and Product
class LinkQuotationProduct(Base):
    __tablename__ = "LinkQuotationProduct"
    
    QuotationId = Column(Integer, ForeignKey("Quotation.Id"), primary_key=True)
    ProductId = Column(Integer, ForeignKey("Product.Id"), primary_key=True)

class Taxonomy(Base):
    __tablename__ = "Taxonomy"

    Id = Column(Integer, primary_key=True, index=True)
    TieuDe = Column(String(255), nullable=True)
    TaxonomyType = Column(Integer, nullable=True)  # 1 = Area, 3 = Source
    KhoaChaId = Column(Integer, ForeignKey("Taxonomy.Id"), nullable=True)

    parent = relationship("Taxonomy", remote_side=[Id], backref="children")

class UserFunction(Base):
    __tablename__ = "UserFunction"

    Id = Column(String(100), primary_key=True)  # Using String UUID since NguoiTaoId/NguoiCapNhatId is UUID
    FullName = Column(String(255), nullable=True)
    UserName = Column(String(100), nullable=True)

class RawCustomer(Base):
    __tablename__ = "RawCustomer"

    Id = Column(Integer, primary_key=True, index=True)
    AreaId = Column(Integer, ForeignKey("Taxonomy.Id"), nullable=True)

    area = relationship("Taxonomy", foreign_keys=[AreaId])

class Customer(Base):
    __tablename__ = "Customer"

    Id = Column(Integer, primary_key=True)
    TenKhachHang = Column(String(255), nullable=True)
    SoDiDong = Column(String(50), nullable=True)
    Email = Column(String(100), nullable=True)
    DiaChi = Column(String(500), nullable=True)
    TinhTrang = Column(Integer, nullable=True)
    TrangThai = Column(Integer, nullable=True)
    NguoiTaoId = Column(String(100), nullable=True)
    NgayTao = Column(DateTime, nullable=True)
    NguoiCapNhatId = Column(String(100), nullable=True)
    NgayCapNhat = Column(DateTime, nullable=True)
    SanPhamSanXuat = Column(String(255), nullable=True)
    ImportId = Column(Integer, nullable=True)
    GioiTinh = Column(Integer, nullable=True)
    NgonNguId = Column(Integer, nullable=True)
    TinhCachId = Column(Integer, nullable=True)
    NguoiPhuTrachId = Column(String(100), nullable=True)
    TongGiaTri = Column(Numeric(18, 2), nullable=True)
    Active = Column(Boolean, nullable=True)
    
    AreaId = Column(Integer, ForeignKey("Taxonomy.Id"), nullable=True)
    NhomKhachHangId = Column(Integer, ForeignKey("Taxonomy.Id"), nullable=True)
    ClassifyType = Column(Integer, nullable=True)  # 1 = Enterprise, 2 = Individual
    CustomerType = Column(Integer, nullable=True)  # 1 = Normal, 2 = Partner

    area = relationship("Taxonomy", foreign_keys=[AreaId])
    customer_group = relationship("Taxonomy", foreign_keys=[NhomKhachHangId])

class Lead(Base):
    __tablename__ = "Lead"

    Id = Column(Integer, primary_key=True)
    TenKhachHang = Column(String(255), nullable=True)
    Email = Column(String(100), nullable=True)
    SoDienThoai = Column(String(50), nullable=True)
    DiaChi = Column(String(500), nullable=True)
    RawCustomerId = Column(Integer, ForeignKey("RawCustomer.Id"), nullable=True)
    SourceId = Column(Integer, ForeignKey("Taxonomy.Id"), nullable=True)
    NguoiXuLyId = Column(String(100), nullable=True)  # Changed to String to hold UUIDs
    TrangThai = Column(Integer, nullable=True)  # e.g., 1 = Active
    NgayTao = Column(DateTime, nullable=True)
    NgayCapNhat = Column(DateTime, nullable=True)

    raw_customer = relationship("RawCustomer")
    source = relationship("Taxonomy", foreign_keys=[SourceId])
    activities = relationship("Activity", back_populates="lead")

class Opportunity(Base):
    __tablename__ = "Opportunity"

    Id = Column(Integer, primary_key=True)
    LeadId = Column(Integer, ForeignKey("Lead.Id"), nullable=True)
    NguoiXuLyId = Column(String(100), nullable=True)
    Amount = Column(Numeric(18, 2), nullable=True)  # Pipeline value
    TinhTrang = Column(Integer, nullable=True)  # Stage: 2=Processing, 3=Quoted, 4=Won, 5=Lost
    TrangThai = Column(Integer, nullable=True)  # 1 = Active
    NgayTao = Column(DateTime, nullable=True)

    lead = relationship("Lead")
    quotations = relationship("Quotation", back_populates="opportunity")

class Quotation(Base):
    __tablename__ = "Quotation"

    Id = Column(Integer, primary_key=True)
    OpportunityId = Column(Integer, ForeignKey("Opportunity.Id"), nullable=True)
    PartnerId = Column(Integer, ForeignKey("Customer.Id"), nullable=True)
    SoHopDong = Column(String(100), nullable=True)
    TinhTrang = Column(Integer, nullable=True)  # 1=Draft, 2=Delivered, 3=Confirmed, 4=Won, 5=Lost
    NgayTao = Column(DateTime, nullable=True)
    TongGiaTri = Column(Numeric(18, 2), nullable=True)

    opportunity = relationship("Opportunity", back_populates="quotations")
    customer = relationship("Customer")
    products = relationship("Product", secondary="LinkQuotationProduct", back_populates="quotations")
    order = relationship("Order", primaryjoin="Quotation.SoHopDong == Order.SoHopDong", foreign_keys="[Order.SoHopDong]", back_populates="quotation", uselist=False)

class Order(Base):
    __tablename__ = "Order"

    Id = Column(Integer, primary_key=True)
    SoPO = Column(String(100), nullable=True)
    SoHopDong = Column(String(100), nullable=True)
    MaVanDon = Column(String(100), nullable=True)
    XuatHoaDon = Column(String(100), nullable=True)
    TinhTrangDatHangId = Column(Integer, nullable=True)
    TinhTrangThanhToanId = Column(Integer, nullable=True)
    ShipCODId = Column(Integer, nullable=True)
    PhiDonHang = Column(Numeric(18, 2), nullable=True)
    PhiDaNop = Column(Numeric(18, 2), nullable=True)
    PhiConLai = Column(Numeric(18, 2), nullable=True)
    GhiChu = Column(String(500), nullable=True)
    NgayGuiSkype = Column(DateTime, nullable=True)
    Deadline = Column(DateTime, nullable=True)
    NgayBanGiao = Column(DateTime, nullable=True)
    TrangThai = Column(Integer, nullable=True)
    NguoiCapNhatId = Column(String(100), nullable=True)
    NgayCapNhat = Column(DateTime, nullable=True)
    ChungTuId = Column(Integer, nullable=True)
    TinhTrangThanhToanKTId = Column(Integer, nullable=True)

    quotation = relationship("Quotation", primaryjoin="Order.SoHopDong == Quotation.SoHopDong", foreign_keys=[SoHopDong], back_populates="order")

class Product(Base):
    __tablename__ = "Product"

    Id = Column(Integer, primary_key=True)
    SKU = Column(String(100), nullable=True)
    TenSanPham = Column(String(500), nullable=True)
    GiaNhap = Column(Numeric(18, 2), nullable=True)
    GiaBan = Column(Numeric(18, 2), nullable=True)
    DonVi = Column(Integer, nullable=True)
    ThuongHieuId = Column(Integer, ForeignKey("Taxonomy.Id"), nullable=True)
    NhomThietBiId = Column(Integer, ForeignKey("Taxonomy.Id"), nullable=True)
    PimId = Column(Integer, nullable=True)
    TrangThai = Column(Integer, nullable=True)
    NgayCapNhat = Column(DateTime, nullable=True)

    category = relationship("Taxonomy", foreign_keys=[NhomThietBiId])
    brand = relationship("Taxonomy", foreign_keys=[ThuongHieuId])
    quotations = relationship("Quotation", secondary="LinkQuotationProduct", back_populates="products")

class Activity(Base):
    __tablename__ = "Activity"

    Id = Column(Integer, primary_key=True)
    LeadId = Column(Integer, ForeignKey("Lead.Id"), nullable=True)
    NguoiTaoId = Column(String(100), nullable=True)
    NguoiXuLyId = Column(String(100), nullable=True)
    LoaiHoatDong = Column(String(50), nullable=True)  # e.g., call, email, meeting
    TrangThai = Column(Integer, nullable=True)  # 1 = Active
    NgayTao = Column(DateTime, nullable=True)

    lead = relationship("Lead", back_populates="activities")
