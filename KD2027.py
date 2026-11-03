import numpy as np
import pandas as pd
import streamlit as st
from sklearn.linear_model import LinearRegression

# 1. CẤU HÌNH GIAO DIỆN TRANG WEB
st.set_page_config(
    page_title="Hệ Thống Phân Tích Tài Chính Doanh Nghiệp", 
    layout="centered"
)

st.title("📊 Báo Cáo Tài Chính Dự Báo (AI Học Máy Thực Tế)")
st.write(
    "Mô hình phân tích biên lợi nhuận và trực quan hóa vùng lời/lỗ từ dữ liệu thực tế kinh doanh."
)

# ---------------------------------------------------------
# PHẦN 1: NẠP DỮ LIỆU TỪ EXCEL
# ---------------------------------------------------------
st.sidebar.header("📁 Quản lý dữ liệu đầu vào")
uploaded_file = st.sidebar.file_uploader(
    "Tải lên file Excel (data_kinh_doanh.xlsx)", type=["xlsx"]
)

try:
    if uploaded_file is not None:
        df_config = pd.read_excel(uploaded_file, sheet_name="ThongSo")
        df_lich_su = pd.read_excel(uploaded_file, sheet_name="LichSuAI")
        st.sidebar.success("Đã nạp dữ liệu thành công!")
    else:
        df_config = pd.read_excel("data_kinh_doanh.xlsx", sheet_name="ThongSo")
        df_lich_su = pd.read_excel("data_kinh_doanh.xlsx", sheet_name="LichSuAI")
        st.sidebar.info("Đang dùng file mẫu mặc định.")

    # Đọc các thông số tài chính cơ bản
    fc = float(df_config["Chi_Phi_Co_Dinh"].iloc[0])
    v = float(df_config["Chi_Phi_Bien_Doi"].iloc[0])

    X_qua_khu = df_lich_su[["San_Luong"]]
    y_qua_khu = df_lich_su["Doanh_Thu"]

except Exception as e:
    st.error(f"Lỗi đọc file Excel: {e}")
    st.stop()

# Hiển thị cấu hình định phí và biến phí ban đầu
st.subheader("1. Thông số chi phí nền tảng")
col1, col2 = st.columns(2)
col1.metric("Chi phí cố định (FC)", f"{fc:,.0f} VNĐ")
col2.metric("Chi phí biến đổi đơn vị (v)", f"{v:,.0f} VNĐ")

# ---------------------------------------------------------
# PHẦN 2: AI HỌC MỨC GIÁ THỰC TẾ & TÍNH ĐIỂM HÒA VỐN
# ---------------------------------------------------------
# Cấu hình thuộc tính fit_intercept=False (Không bán hàng = Không có doanh thu nền)
model = LinearRegression(fit_intercept=False)
model.fit(X_qua_khu, y_qua_khu)
gia_ban_ai_hoc = float(model.coef_[0])

# Tính toán điểm hòa vốn thực tế kinh doanh
loi_nhuan_bien_doi_ai = gia_ban_ai_hoc - v
diem_hoa_von_thuc_te = int(np.ceil(fc / loi_nhuan_bien_doi_ai))
doanh_thu_hoa_von = diem_hoa_von_thuc_te * gia_ban_ai_hoc

st.subheader("2. Kết quả AI học máy và Điểm hòa vốn thực tế")
st.info(
    f"💡 **Mức giá bán tối ưu AI tự đúc kết từ lịch sử:** `{gia_ban_ai_hoc:,.0f} VNĐ / sản phẩm`"
)

col_hv1, col_hv2 = st.columns(2)
col_hv1.metric("Sản lượng hòa vốn tối thiểu", f"{diem_hoa_von_thuc_te:,} SP")
col_hv2.metric("Doanh thu hòa vốn tương ứng", f"{doanh_thu_hoa_von:,.0f} VNĐ")

# ---------------------------------------------------------
# PHẦN 3: BẢNG CHI TIẾT BIÊN LỢI NHUẬN & VÙNG LỜI LỖ
# ---------------------------------------------------------
st.subheader("3. Bảng phân tích phân phối Lời/Lỗ & Biên lợi nhuận")

# Thiết lập các mốc sản lượng mô phỏng từ Lỗ đến Lời
cac_moc_san_luong = [0, 300, 600, diem_hoa_von_thuc_te, 1000, 1500, 2000]
df_mo_phong = pd.DataFrame({"San_Luong": cac_moc_san_luong})

# Tính toán các chỉ số kinh doanh dựa trên giá AI học được
doanh_thu_du_bao = model.predict(df_mo_phong)
tong_chi_phi = fc + (df_mo_phong["San_Luong"] * v)
loi_nhuan = doanh_thu_du_bao - tong_chi_phi

# Tính Tỷ suất/Biên lợi nhuận trên doanh thu (%)
# Nếu doanh thu = 0 thì biên lợi nhuận mặc định là 0%
bien_loi_nhuan = np.where(doanh_thu_du_bao > 0, (loi_nhuan / doanh_thu_du_bao) * 100, 0.0)

# Phân loại vùng tài chính rõ ràng
vung_tai_chinh = []
for ln in loi_nhuan:
    if ln < -5000:
        vung_tai_chinh.append("🔴 Vùng Lỗ Chịu Đựng")
    elif ln > 5000:
        vung_tai_chinh.append("🟢 Vùng Lời Thần Tốc")
    else:
        vung_tai_chinh.append("⚖️ Điểm Hòa Vốn")

# Tổng hợp bảng dữ liệu
df_ket_qua = pd.DataFrame({
    "Sản lượng (SP)": df_mo_phong["San_Luong"],
    "Doanh thu (VNĐ)": doanh_thu_du_bao,
    "Tổng chi phí (VNĐ)": tong_chi_phi,
    "Lợi nhuận (VNĐ)": loi_nhuan,
    "Biên lợi nhuận (%)": bien_loi_nhuan,
    "Phân vùng dòng tiền": vung_tai_chinh
})

# Hiển thị bảng định dạng số chuyên nghiệp lên Streamlit
st.dataframe(
    df_ket_qua.style.format({
        "Sản lượng (SP)": "{:,.0f}",
        "Doanh thu (VNĐ)": "{:,.0f}",
        "Tổng chi phí (VNĐ)": "{:,.0f}",
        "Lợi nhuận (VNĐ)": "{:,.0f}",
        "Biên lợi nhuận (%)": "{:,.1f}%"
    }),
    use_container_width=True,
)

# ---------------------------------------------------------
# PHẦN 4: TRỰC QUAN HÓA BIỂU ĐỒ ĐƯỜNG KINH DOANH
# ---------------------------------------------------------
st.subheader("📈 Đồ thị trực quan hóa Vùng Lời/Lỗ")

# Chuẩn bị dữ liệu vẽ đồ thị liền mạch
moc_do_thi = np.linspace(0, 2000, 100)
df_chart_calc = pd.DataFrame({"San_Luong": moc_do_thi})
chart_doanh_thu = model.predict(df_chart_calc)
chart_chi_phi = fc + (moc_do_thi * v)

df_chart_final = pd.DataFrame({
    "Doanh thu thực tế (AI)": chart_doanh_thu,
    "Tổng chi phí vận hành": chart_chi_phi
}, index=moc_do_thi)

# Vẽ biểu đồ đường tương quan
st.line_chart(df_chart_final, use_container_width=True)
st.caption(
    "💡 *Gợi ý đọc biểu đồ: Điểm giao nhau giữa 2 đường chính là Điểm hòa vốn. "
    "Khu vực đường Doanh thu nằm dưới đường Chi phí là Vùng Lỗ, ngược lại là Vùng Lời.*"
)
