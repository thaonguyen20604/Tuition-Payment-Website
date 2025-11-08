import api from "./api";

// studentId = người được thanh toán (chính mình hoặc người khác)
export async function createIntent(payerUserId, studentId, semesterId) {
  return api.post("/payment/intents", {
    payer_user_id: payerUserId,
    token_for_my_invoice: null, // BE tự điền thêm token
    student_id: studentId,
    semester_id: semesterId
  });
}

export async function sendOtp(intentId) {
  return api.post(`/payment/intents/${intentId}/send-otp`);
}

export async function confirmPayment(intentId, otp) {
  return api.post(`/payment/intents/${intentId}/confirm`, { otp });
}


export async function getCurrentIntent(studentId, semesterId) {
  const res = await api.get("/payment/intents/current", {
    params: { student_id: studentId, semester_id: semesterId },
  });
  return res.data;
}


export async function cancelIntent(intentId) {
  return api.post(`/payment/intents/${intentId}/cancel`);
}


// export async function getPaymentHistory(studentId) {
//   const res = await api.get(`/payment/payments/history/${studentId}`);
//   return res.data;
// }

// ... các import/đoạn có sẵn
export async function getPaymentHistoryByPayer(payerId, semesterId) {
  // BE nên hỗ trợ query theo payer_id
  // ví dụ: GET /payments/history?payer_id=...&semester_id=...
  return await api.get(`/payments/history`, {
    params: { payer_id: payerId, semester_id: semesterId }
  });
}


export async function getPaymentHistory(studentId, semesterId) {
  return await api.get(`/payment/payments/history/${studentId}/${semesterId}`);
}

