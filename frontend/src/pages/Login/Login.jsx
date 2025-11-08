// src/pages/LoginPage.jsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../../services/authService";     // ⬅️ dùng service
import "./Login.css";
import tdtLogo from "../../assets/tdt_logo.png";
import EyeOpen from "../../assets/eye_open.svg";
import EyeClose from "../../assets/eye_close.svg";

export default function Login() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!username || !password) {
      alert("Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu");
      return;
    }
    setLoading(true);
    try {
      const data = await login({ username, password });  // ⬅️ gọi service
      // alert(`Xin chào ${data.username}`);
      navigate("/home");
    } catch (error) {
      const msg = error?.response?.data?.detail || "Có lỗi xảy ra khi đăng nhập";
      alert(msg);
      console.error("Lỗi:", error);
    } finally {
      setLoading(false);
    }
  };

  return (

    <div className="login-container">
      {/* Left section */}
      
      <div className="login-sidebar">
        <div className="logo-container">
          <img src={tdtLogo} alt="TDT Logo" className="tdt-logo" />
        </div>
        <div className="ibanking-text">iBanking</div>
      </div>

      {/* Right section */}
      <div className="login-content">
        <div className="login-header">
          <h2>Đăng nhập</h2>
          <span className="bank-icon" role="img" aria-label="bank icon">🏦</span>
        </div>

        <form onSubmit={handleLogin} className="login-form">
          <label htmlFor="username">Tên đăng nhập</label>
          <input
            type="text"
            id="username"
            placeholder=""
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="input-field"
            // disabled={loading}
            // autoComplete="username"
          />

          <label htmlFor="password">Mật khẩu</label>
          <div className="password-wrapper">
            <input
              type={showPassword ? 'text' : 'password'}
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-field-pass"
              // disabled={loading}
              // autoComplete="current-password"
            />
            <button
              type="button"
              className="toggle-btn"
              onClick={() => setShowPassword((prev) => !prev)}
              // aria-label={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
              // disabled={loading}
            >
              <img
                src={showPassword ? EyeClose : EyeOpen}
                alt={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
                className="eye-icon"
              />
            </button>
          </div>

          <button type="submit" className="login-button">
            {'Đăng nhập'}
          </button>
        </form>
      </div>
    </div>

  );
}

