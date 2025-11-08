// src/services/userService.js
import api from "./api";

export async function getMe() {
  const { data } = await api.get("/user/me");
  return data; // { username, email, name, balance, ... }
}

// Thêm để tìm thanh toán hộ
export async function findUserByUsername(username) {
  const { data } = await api.get(`/user/by-username/${username}`);
  return data;
}

export async function deposit(userId, amount) {
  const res = await api.post(`/user/${userId}/deposit`, { amount });
  return res.data;
}
