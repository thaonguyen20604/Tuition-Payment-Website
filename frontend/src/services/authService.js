// src/services/authService.js
import api from "./api";

export async function login({ username, password }) {
  const { data } = await api.post("/auth/login", { username, password });
  localStorage.setItem("token", data.access_token);
  return data; // { access_token, username, ... }
}

export function logout() {
  localStorage.removeItem("token");
}

export function isAuthenticated() {
  return !!localStorage.getItem("token");
}
