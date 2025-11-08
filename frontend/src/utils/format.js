//format ngày
export function formatDateVN(isoString) {
  if (!isoString) return "";
  return new Date(isoString).toLocaleString("vi-VN", {
    timeZone: "Asia/Ho_Chi_Minh",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit", // ⬅️ thêm dòng này để hiện giây
  });
}

// format tiền
export function formatCurrencyVN(amount) {
  if (amount == null) return "";
  return new Intl.NumberFormat("vi-VN").format(amount);
}
