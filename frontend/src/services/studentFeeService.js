import api from "./api";

// Lấy danh sách học kỳ
export async function getSemesters() {
  const { data } = await api.get("/studentfee/semesters");
  return data;
}

// Lấy hóa đơn của chính mình
export async function getMyInvoice(semesterId) {
  const { data } = await api.get("/studentfee/my-invoice", {
    params: { semester_id: semesterId }
  });
  return data;
}

// Lấy hóa đơn của người khác (nếu cần)
export async function getOtherInvoice(studentId) {
  const { data } = await api.get(`/studentfee/invoice/${studentId}`);
  return data;
}

// Thanh toán
export async function payInvoice(invoiceId) {
  const { data } = await api.post(`/studentfee/pay/${invoiceId}`);
  return data;
}
