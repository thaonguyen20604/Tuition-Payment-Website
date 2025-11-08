// src/pages/Home.jsx
import { useEffect, useState } from "react";
import React from 'react'
import { useNavigate } from "react-router-dom";
import { getMe, findUserByUsername, deposit  } from "../../services/userService";
import { isAuthenticated, logout } from "../../services/authService";
import { getSemesters, getMyInvoice, getOtherInvoice } from "../../services/studentFeeService";
import { formatDateVN, formatCurrencyVN } from "../../utils/format";
import { createIntent, sendOtp, confirmPayment, cancelIntent, getPaymentHistory } from "../../services/paymentService";
import "./Home.css";

import LogoTDT from "../../assets/tdt_logo.png";
import Logout from "../../assets/Logout.png";






export default function Home(){
  const [userData, setUserData] = useState(null);
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("self")
  
  // fe tĩnh chưa lấy data từ be
  const [showOtherInfo, setShowOtherInfo] = useState(false);
  const [showGuide, setShowGuide] = useState(false);
  const [showPay, setShowPay] = useState(false);
  const [amount, setAmount] = useState(""); // số tiền nhập
  // const [debt, setDebt] = useState(0);      // nợ kỳ trước
  // const [mustPay, setMustPay] = useState(20); // tổng phải nộp ví dụ
  const [message, setMessage] = useState(""); // thông báo sau khi thanh toán
  const [showOtp, setShowOtp] = useState(false);
  const [otp, setOtp] = useState("");
  const [generatedOtp, setGeneratedOtp] = useState(null);
  // const [otpExpire, setOtpExpire] = useState(null);
  const [showConfirmAutoPay, setShowConfirmAutoPay] = useState(false);


  // state cho studentfee
  const [semesters, setSemesters] = useState([]);
  const [selectedSemester, setSelectedSemester] = useState("");
  const [invoice, setInvoice] = useState(null);


  // cho tab "other"
  const [otherMssv, setOtherMssv] = useState("");
  const [otherInvoice, setOtherInvoice] = useState(null);
  const [otherError, setOtherError] = useState("");
  const [otherUser, setOtherUser] = useState(null);

  // state payment
  const [intent, setIntent] = useState(null);
  const [otpTimer, setOtpTimer] = useState(180); // 5 phút = 300 giây
  const [canResend, setCanResend] = useState(false);
  const [otpError, setOtpError] = useState("");
  const [paymentHistory, setPaymentHistory] = useState([]);
  const [otherPaymentHistory, setOtherPaymentHistory] = useState([]);
  const [isPayingOther, setIsPayingOther] = useState(false);

  const [showInsufficient, setShowInsufficient] = useState(false);
  const [payerHistory, setPayerHistory] = useState([]);
  const [isCreatingIntent, setIsCreatingIntent] = useState(false);
  const [agreed, setAgreed] = useState(false);
  const [showTerms, setShowTerms] = useState(false);
  const [agreedOther, setAgreedOther] = useState(false);





  

//  -------------------------------------------
//  auth & user
//  -------------------------------------------
 useEffect(() => {
  console.log("Render Home");
    // Chặn nếu chưa đăng nhập
    if (!isAuthenticated()) {
      navigate("/login");
      return;
    }
(async () => {
      try {
        const me = await getMe();           //gọi qua service
        // console.log("hello check user")
        // console.log(me)
        setUserData(me);
        setError("");
      } catch (err) {
        console.error("Error fetching user data:", err);
        const status = err?.response?.status;
        // Hết hạn/invalid token → logout và quay về login
        if (status === 401 || status === 404) {
          logout();
          navigate("/login");
          return;
        }
        setError("Không thể tải thông tin người dùng.");
      } finally {
        setLoading(false);
      }
    })();
  }, [navigate]);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };


  //  -------------------------------------------
  //  studentfee
  //  -------------------------------------------
  useEffect(() => {
    console.log("StudentFee useEffect run");
    if (!isAuthenticated()) {
      navigate("/login");
      return;
    }

    async function fetchSemesters() {
      try {
        const data = await getSemesters();
        setSemesters(data);
        if (data.length > 0) {
          setSelectedSemester(data[0].semester_id); // mặc định chọn học kỳ đầu tiên
        }
      } catch (err) {
        console.error("Error fetching semesters:", err);
      }
    }

    fetchSemesters();
  }, [navigate]);

  useEffect(() => {
    async function fetchInvoice() {
      if (!selectedSemester) return;
      try {
        const data = await getMyInvoice(selectedSemester);
        // console.log("Hello check data")
        console.log(data);
        setInvoice(data);
      } catch (err) {
        console.error("Error fetching invoice:", err);
        setInvoice(null);
      }
    }
    fetchInvoice();
  }, [selectedSemester]);

  // -------------------------------
  // studentfee: lấy hóa đơn của người khác
  // -------------------------------
  async function handleFindOther(username) {
    try {
      const user = await findUserByUsername(username); 
      setOtherUser(user);

      const invoice = await getOtherInvoice(user.id);
      console.log("hello check invoice other")
      console.log(invoice) 
      setOtherInvoice(invoice);

      setOtherError("");
      setShowOtherInfo(true);
    } catch (err) {
      console.error("Error fetching other invoice:", err);
      setOtherError("Không tìm thấy sinh viên.");
      setOtherUser(null);
      setOtherInvoice(null);
      setShowOtherInfo(false);
    }
  }



  //  -------------------------------------------
  //  payment
  //  -------------------------------------------
  useEffect(() => {
    async function fetchIntent() {
      if (!invoice || !userData) return;
      try {
        const data = await getCurrentIntent(userData.id, selectedSemester);
        console.log("🔎 Current Intent:", data);
        setIntent(data); // lưu intent hiện tại
      } catch (err) {
        console.warn("Không có intent đang xử lý");
        setIntent(null);
      }
    }

    fetchIntent();
  }, [invoice, userData, selectedSemester]);

  async function handlePayClick() {
    setIsPayingOther(false);
    if (!invoice) {
      setMessage("Không tìm thấy hóa đơn.");
      return;
    }

    // Nếu hóa đơn đã thanh toán
    if (invoice.status === "paid") {
      setMessage("Hóa đơn này đã được thanh toán. Không thể thanh toán lại.");
      return;
    }
    
    const balance = userData?.balance ?? 0;
    const total = invoice?.total_amount ?? 0;

    if (balance < total) {
      // ❌ Không đủ tiền → hiện modal nạp thêm
    
      setShowInsufficient(true);
      return;
    }

    try {
      // Gọi BE tạo intent
      const resIntent = await createIntent(
        userData.id,      // payer_user_id
        userData.id,      // student_id
        selectedSemester
      );

      const intentId = resIntent.data.id;

      // Gửi OTP
      await sendOtp(intentId);
      setGeneratedOtp(intentId);
      setShowConfirmAutoPay(false);
      setShowOtp(true);
      setMessage("Mã OTP đã được gửi đến email của bạn.");

      // reset đồng hồ
      setOtpTimer(180);
      setCanResend(false);
      setOtpError("");
    } catch (err) {
      console.error("Error create/send OTP:", err);
      // let raw = err.response?.data?.detail || "";
      // Lấy thông báo lỗi thực từ BE
      let raw = err.response?.data?.detail || err.response?.data?.message || err.message || "Lỗi không xác định";
      let msg = raw;

      // parse nếu BE trả string dạng JSON
      try {
        msg = JSON.parse(raw.replace(/'/g, '"')).message || raw;
      } catch (_) {}

      if (msg.includes("uq_pi_one_open_per_invoice") || msg.includes("duplicate key")) {
        setMessage("Hóa đơn đang được xử lý hoặc đã có yêu cầu thanh toán đang chờ OTP.");
      } else if (msg.includes("đã được thanh toán")) {
        setMessage("Hóa đơn này đã được thanh toán trước đó.");
      } else {
        setMessage("Lỗi khi tạo giao dịch: " + msg);
      }
    }
  }

  async function handlePayOther() {
    setIsPayingOther(true);

    if (!otherInvoice || !otherUser) {
      setMessage("Không tìm thấy hóa đơn hoặc sinh viên.");
      return;
    }

    if (otherInvoice.status === "paid") {
      setMessage("Hóa đơn này đã được thanh toán.");
      return;
    }

    const balance = Number(userData?.balance ?? 0);
    const total = Number(otherInvoice?.total_amount ?? 0);

    // ❌ Nếu không đủ tiền -> hiển thị popup nạp thêm (giống tự thanh toán)
    if (balance < total) {
      setIsPayingOther(true);   // 🟢 thêm dòng này
      setShowInsufficient(true);
      return;
    }


    try {
      const semesterId = semesters[0]?.semester_id || selectedSemester;

      // ✅ Đủ tiền → tạo intent & gửi OTP
      const resIntent = await createIntent(
        userData.id,        // payer_user_id = mình
        otherUser.id,       // student_id = người được nộp hộ
        semesterId
      );
const intentId = resIntent.data.id;

      await sendOtp(intentId);
      setGeneratedOtp(intentId);
      setShowPay(false);
      setShowOtp(true);
      setMessage("Mã OTP đã được gửi đến email của bạn.");

    } catch (err) {
      console.error("Error create/send OTP:", err);
      const msg = err.response?.data?.detail || "Lỗi khi tạo giao dịch.";
      setMessage(msg);
    }
  }

  useEffect(() => {
    let interval;
    if (showOtp && otpTimer > 0) {
      interval = setInterval(() => {
        setOtpTimer((prev) => {
          if (prev <= 1) {
            clearInterval(interval);
            setCanResend(true);
            setOtpError("Mã OTP đã hết hạn. Vui lòng gửi lại mã mới.");
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [showOtp, otpTimer]);


  async function handleResendOtp() {
    if (!generatedOtp) {
      setOtpError("Không có giao dịch nào đang chờ OTP.");
      return;
    }

    try {
      await sendOtp(generatedOtp);
      setOtpError("");
      setMessage("Mã OTP mới đã được gửi lại đến email của bạn.");

      // reset lại giao diện nhập OTP
      setOtp("");
      setOtpTimer(180);
      setCanResend(false);
      setShowOtp(true);
    } catch (err) {
      console.error("Error resend OTP:", err);
      setOtpError("Không thể gửi lại OTP. Vui lòng thử lại sau.");
    }
  }
  // useEffect(() => {
  //   async function fetchPaymentHistory() {
  //     if (!userData || !selectedSemester) return;
  //     try {
  //       const res = await getPaymentHistory(userData.id, selectedSemester);
  //       setPaymentHistory(res.data);
  //     } catch (err) {
  //       console.error("Error fetching payment history:", err);
  //     }
  //   }

  //   fetchPaymentHistory();
  // }, [userData, selectedSemester]);
  useEffect(() => {
  async function fetchPaymentHistory() {
    if (!userData || !selectedSemester) return;
    try {
      const res = await getPaymentHistory(userData.id, selectedSemester);
      const all = res.data || [];

      // 🔥 Lọc các giao dịch mà user là người nộp hoặc được nộp
      const related = all.filter(p =>
        p.payer_user_id === userData.id || p.student_id === userData.id
      );

      // Sắp xếp theo ngày mới nhất
      related.sort((a, b) => new Date(b.paid_at) - new Date(a.paid_at));

      setPaymentHistory(related);
    } catch (err) {
      console.error("Error fetching payment history:", err);
    }
  }

  fetchPaymentHistory();
}, [userData, selectedSemester]);



  useEffect(() => {
    async function fetchOtherPaymentHistory() {
      if (!otherUser || !semesters.length) return;
      try {
        const semesterId = semesters[0].semester_id || selectedSemester;
        const res = await getPaymentHistory(otherUser.id, semesterId);
        setOtherPaymentHistory(res.data);
      } catch (err) {
        console.error("Error fetching other payment history:", err);
        setOtherPaymentHistory([]);
      }
    }

    fetchOtherPaymentHistory();
  }, [otherUser, semesters, selectedSemester]);


// ----------------------------------------

  if (error) {
    return (
      <div className="error-container">
        <div className="error-message">{error}</div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading">Loading...</div>
      </div>
    );
  }

  const displayName = userData?.name ?? "";
  const displayId   = userData?.studentId ?? userData?.username ?? "";



  return (
    <>
    <header className="topbar">
<div className="topbar__left">
        {/* <img className="topbar__logo" src={LogoTDT} alt="TDTU Logo" /> */}

        <img
          className="topbar__logo"
          src={LogoTDT}
          alt="TDTU Logo"
          style={{ cursor: "pointer" }}
          onClick={() => {

            navigate("/home");
            window.location.reload();
          
          }
          }          
        />


        <h1 className="topbar__title">HỌC PHÍ - LỆ PHÍ</h1>
      </div>

      <div className="topbar__right">
        <span className="topbar__user">{displayName} ({displayId})</span>

        <button
          type="button"
          className="topbar__logout-btn"
          onClick={handleLogout}
          aria-label="Đăng xuất"
          title="Đăng xuất"
        >
          <img className="topbar__logout" src={Logout} alt="" />
        </button>
      </div>
    </header>





      <div className="divider"></div>

    <main className="container">
      {/* <!-- THÔNG TIN SINH VIÊN --> */}
    <section className="card">
      <div className="card__header">THÔNG TIN SINH VIÊN</div>
      <div className="grid grid--student">
        <div className="field">
          <label>MSSV</label>
          <input type="text" value={userData?.username ?? ""} disabled />
        </div>

        <div className="field">
          <label>Họ và tên</label>
          <input type="text" value={userData?.name ?? ""} disabled />
        </div>

        <div className="field">
          <label>Giới tính</label>
          <input
            type="text"
            value={
              userData?.gender === "male" ? "Nam"
              : userData?.gender === "female" ? "Nữ"
              : (userData?.gender ?? "")
            }
            disabled
          />
        </div>

        <div className="field field--wide">
          <label>Email</label>
          <input type="email" value={userData?.email ?? ""} disabled />
        </div>

        <div className="field">
          <label>Số điện thoại</label>
          <input type="text" value={userData?.phone ?? ""} disabled />
        </div>
      </div>
    </section>


      {/* <!-- Tabs --> */} 
      <nav className="tabs">
          <button
            className={`tab ${activeTab === "self" ? "tab--active" : ""}`}
            type="button"
            onClick={() => setActiveTab("self")}
          >
            Thanh toán
          </button>
          <button
            className={`tab ${activeTab === "other" ? "tab--active" : ""}`}
            type="button"
            onClick={() => setActiveTab("other")}
          >
            Thanh toán cho người khác
          </button>
        </nav>

    {/* Thanh toán cho */}
      {/* <!-- Học kỳ --> */}
      {activeTab === "self" && (
          <>
            {/* Khung thanh toán cho chính mình */}
            <section className="row">
              <div className="field field--select">
                <label>Học kỳ</label>
                <select
                  value={selectedSemester}
                  onChange={(e) => setSelectedSemester(e.target.value)}
                >
                  {semesters.map((s) => (
<option key={s.semester_id} value={s.semester_id}>
                      {s.semester_name} ({s.school_year})
                    </option>
                  ))}
                </select>
              </div>
            </section>

          {/* <!-- Học phí --> */}
          <section className="card">
            <div className="card__subtabs">
              <button className="subtab subtab--active" type="button">Học phí</button>
              <button
                className="subtab subtab--link"
                type="button"
                onClick={() => setShowGuide(true)}
              >
                Hướng dẫn thanh toán học phí
              </button>

            </div>

            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>
                      SỐ DƯ KHẢ DỤNG
                      <br />
                      <span className="muted">(1)</span>
                    </th>
                    <th>
                      HỌC PHÍ HỌC KỲ
                      <br />
                      <span className="muted">(2)</span>
                    </th>
                    {/* <th>
                      MIỄN GIẢM
                      <br />
                      <span className="muted">(3)</span>
                    </th> */}
                    {/* <th>
                      TỔNG HỌC PHÍ PHẢI NỘP
                      <br />
                      <span className="muted">(3) = (2) - (1)</span>
                    </th> */}
                    <th>
                      TỔNG HỌC PHÍ ĐÃ NỘP
                      <br />
                      <span className="muted">(3)</span>
                    </th>
                    <th>
                      SỐ TIỀN CÒN PHẢI NỘP
                      <br />
                      <span className="muted">(4) = (2) - (3)</span>
                    </th>
                    <th>
                      GHI CHÚ
                      <br />
                      <span className="muted">(5)</span>
                    </th>
                  </tr>

                </thead>
                <tbody>
                  <tr>
                    <td>{formatCurrencyVN(userData?.balance ?? 0)}</td>

                    {/* Học phí học kỳ */}
                    <td style={{ fontWeight: "bold", color: "red" }}>
                      {formatCurrencyVN(invoice?.total_amount ?? 0)}
                    </td>

                    {/* Tổng học phí đã nộp */}
                    <td style={{ fontWeight: "bold", color: "red" }}>
                      {invoice?.status === "paid"
                        ? formatCurrencyVN(invoice?.total_amount ?? 0)
                        : formatCurrencyVN(0)}
                    </td>

                    {/* Số tiền còn phải nộp = (2) - (3) */}
<td style={{ fontWeight: "bold", color: "red" }}>
                      {invoice?.status === "paid"
                        ? formatCurrencyVN(0)
                        : formatCurrencyVN(Number(invoice?.total_amount ?? 0) - 0)}
                    </td>

                    {/* Ghi chú */}
                    <td>
                      {!invoice
                        ? "CHƯA CÓ HÓA ĐƠN"
                        : invoice.status === "unpaid"
                          ? "CHƯA THANH TOÁN"
                          : "ĐÃ THANH TOÁN"}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          {/* <!-- Danh sách môn học tính phí --> */}
          <section className="card">
            <h2 className="section-title">Danh sách môn học trong học kỳ</h2>
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>MÃ MÔN HỌC</th>
                    <th>TÊN MÔN HỌC</th>
                    <th>NGÀY ĐĂNG KÍ MÔN HỌC</th>
                    <th>SỐ TIỀN</th>
                  </tr>
                </thead>
                <tbody>
                  {invoice && invoice.invoice_items.length > 0 ? (
                    invoice.invoice_items.map((item) => (
                      <tr key={item.invoice_items_id}>
                        <td>{item.subject_id}</td>
                        <td>{item.subject_name}</td>
                        <td>{formatDateVN(item.registration_date)}</td>
                        <td>{formatCurrencyVN(item.amount)}</td>
                      </tr>
                    ))
                  ) : (
                    <tr><td colSpan="4" className="empty">— Chưa có dữ liệu —</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>


          {/* Lịch sử thanh toán của mình */}
          <section className="card">
            <h2 className="section-title">Lịch sử thanh toán</h2>
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>NGÀY THANH TOÁN</th>
                    <th>SỐ TIỀN</th>
                    <th>NGƯỜI NỘP</th>
                    <th>NGƯỜI ĐƯỢC THANH TOÁN</th>
                  </tr>
                </thead>
                <tbody>
                  {paymentHistory.length > 0 ? (
                    paymentHistory.map((p, i) => (
                      <tr key={i}>
                        <td>{formatDateVN(p.created_at)}</td>
                        <td>{formatCurrencyVN(p.amount)}</td>
                        <td>{p.payer_username || "—"}</td>
                        <td>{p.student_username || "—"}</td>
                        {/* <td>{p.payer_username || "—"}</td> */}
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="4" className="empty">— Chưa có lịch sử thanh toán —</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>


          {/* <div className="center">
            <button
              className="btn btn--primary"
              type="button"
              onClick={handlePayClick}
            >
              Thanh toán
            </button>
          </div> */}

          <label style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <input
                type="checkbox"
                checked={agreed}
                onChange={(e) => setAgreed(e.target.checked)}
              />
              <span>
                Tôi đã đọc và đồng ý với{" "}
                <button
                  type="button"
                  className="link-button"
                  onClick={() => setShowTerms(true)}
                  style={{
                    background: "none",
                    border: "none",
                    color: "#1B4683",
                    textDecoration: "underline",
                    cursor: "pointer",
                    padding: 0,        
                    margin: 0,         
                    display: "inline", 
                    lineHeight: "inherit",
                    verticalAlign: "baseline"
                  }}
                >
                  điều khoản thanh toán
                </button>
              </span>

            </label>

          <div className="center">
            <button
              className={`btn btn--primary ${!agreed ? "btn--disabled" : ""}`}
              type="button"
              disabled={!agreed}
              onClick={handlePayClick}
            >
              Thanh toán
            </button>
          </div>
          

        </>
      )}
      {activeTab === "other" && (
          <>
            {!showOtherInfo && (
              <section className="card">
                <div className="field">
                  <label>Nhập MSSV cần thanh toán hộ</label>
                  <input 
                    type="text" 
                    placeholder="Nhập MSSV..." 
                    value={otherMssv}
                    onChange={(e) => setOtherMssv(e.target.value)}
                  />
                </div>
                <div className="center">
                  <button
                    className="btn btn--primary"
                    onClick={() => handleFindOther(otherMssv)}
                  >
                    Tìm sinh viên
                  </button>
                </div>
                {otherError && (
                  <p style={{ color: "red", textAlign: "center", marginTop: "8px" }}>
                    {otherError}
                  </p>
                )}

              </section>
            )}

            {showOtherInfo && (
              <>
                {/* Thông tin người được nộp hộ */}
                <section className="card">
                  <div className="grid grid--two">
                    <div className="field">
                      <label>MSSV</label>
                      <input type="text" value={otherUser?.username ?? ""} disabled />
                    </div>
                    <div className="field">
                      <label>Họ và tên</label>
                      <input type="text" value={otherUser?.name ?? ""} disabled />
                    </div>
                  </div>
                </section>

                {/* Học kỳ hiện tại */}
                {/* <section className="pill-row">
                  <div className="pill">
                    <span className="pill__label">Học kỳ hiện tại</span>
                    <span className="pill__value"> HK1/2025-2026</span>
                  </div>
                </section> */}
                <section className="pill-row">
                  <div className="pill">
                    <span className="pill__label">Học kỳ hiện tại</span>
                    <span className="pill__value">
                      {semesters.length > 0
? `${semesters[0].semester_name}/${semesters[0].school_year}`
                        : "—"}
                    </span>
                  </div>
                </section>


                {/* Học phí */}
                <section className="card">
                  <div className="card__subtabs">
                    <button className="subtab subtab--active">Học phí</button>
                    <button
                      className="subtab subtab--link"
                      type="button"
                      onClick={() => setShowGuide(true)}
                    >
                      Hướng dẫn thanh toán học phí
                    </button>
                  </div>

                  <div className="table-wrap">
                    <table className="table">
                      <thead>
                        <tr>
                          <th>
                            SỐ DƯ KHẢ DỤNG
                            <br />
                            <span className="muted">(1)</span>
                          </th>
                          <th>
                            HỌC PHÍ HỌC KỲ
                            <br />
                            <span className="muted">(2)</span>
                          </th>
                          {/* <th>MIỄN GIẢM</th> */}
                          {/* <th>TỔNG HỌC PHÍ PHẢI NỘP</th> */}
                          <th>
                            TỔNG HỌC PHÍ ĐÃ NỘP
                            <br />
                            <span className="muted">(3)</span>
                          </th>
                          <th>
                            SỐ TIỀN CÒN PHẢI NỘP
                            <br />
                            <span className="muted">(4) = (2) - (3)</span>
                          </th>
                          <th>
                            GHI CHÚ
                            <br />
                            <span className="muted">(5)</span>
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>{formatCurrencyVN(userData?.balance ?? 0)}</td>

                          {/* Học phí học kỳ */}
                          <td style={{ fontWeight: "bold", color: "red" }}>
                            {formatCurrencyVN(otherInvoice?.total_amount ?? 0)}
                          </td>

                          {/* Tổng học phí đã nộp */}
                          <td style={{ fontWeight: "bold", color: "red" }}>
                            {otherInvoice?.status === "paid"
                              ? formatCurrencyVN(otherInvoice?.total_amount ?? 0)
                              : formatCurrencyVN(0)}
                          </td>

                          {/* Số tiền còn phải nộp = (2) - (3) */}
      <td style={{ fontWeight: "bold", color: "red" }}>
                            {otherInvoice?.status === "paid"
                              ? formatCurrencyVN(0)
                              : formatCurrencyVN(Number(otherInvoice?.total_amount ?? 0) - 0)}
                          </td>

                          {/* Ghi chú */}
                          <td>
                            {!otherInvoice
                              ? "CHƯA CÓ HÓA ĐƠN"
                              : otherInvoice.status === "unpaid"
                                ? "CHƯA THANH TOÁN"
                                : "ĐÃ THANH TOÁN"}
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </section>

                {/* Danh sách môn học tính phí */}
                <section className="card">
                  <h2 className="section-title">Danh sách môn học</h2>
                  <div className="table-wrap">
                    <table className="table">
                      <thead>
                        <tr>
                          <th>MÃ MÔN HỌC</th>
                          <th>TÊN MÔN HỌC</th>
                          <th>NGÀY ĐĂNG KÝ</th>
                          <th>SỐ TIỀN</th>
                        </tr>
                      </thead>
                      <tbody>
                        {otherInvoice && otherInvoice.invoice_items?.length > 0 ? (
                          otherInvoice.invoice_items.map((item) => (
                            <tr key={item.invoice_items_id}>
                              <td>{item.subject_id}</td>
                              <td>{item.subject_name}</td>
                              <td>{formatDateVN(item.registration_date)}</td>
                              <td>{formatCurrencyVN(item.amount)}</td>
                            </tr>
                          ))
                        ) : (
                          <tr>
                            <td colSpan="4" className="empty">— Chưa có dữ liệu —</td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </section>

                {/* Lịch sử thanh toán */}
                <section className="card">
                  <h2 className="section-title">Lịch sử thanh toán hộ</h2>
                  <div className="table-wrap">
                    <table className="table">
                      <thead>
                        <tr>
                          <th>NGÀY THANH TOÁN</th>
                          <th>SỐ TIỀN</th>
                          <th>NGƯỜI NỘP</th>
                          <th>NGƯỜI ĐƯỢC THANH TOÁN</th>
                        </tr>
                      </thead>
                      <tbody>
                        {otherPaymentHistory.length > 0 ? (
                          otherPaymentHistory.map((p, i) => (
                            <tr key={i}>
                              <td>{formatDateVN(p.created_at)}</td>
                              <td>{formatCurrencyVN(p.amount)}</td>
                              <td>{p.payer_username || "—"}</td>
                              <td>{p.student_username || "—"}</td>
                            </tr>
                          ))
                        ) : (
                          <tr>
                            <td colSpan="4" className="empty">— Chưa có lịch sử —</td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </section>

                {/* <div className="center">
                  <button
                    className="btn btn--primary"
                    type="button"
                    onClick={handlePayOther}
                  >
                    Thanh toán
                  </button>
                </div> */}

                <label style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                  <input
                    type="checkbox"
                    checked={agreed}
                    onChange={(e) => setAgreed(e.target.checked)}
                  />
                  <span>
                    Tôi đã đọc và đồng ý với{" "}
                    <button
                      type="button"
                      className="link-button"
                      onClick={() => setShowTerms(true)}
                      style={{
                        background: "none",
                        border: "none",
                        color: "#1B4683",
                        textDecoration: "underline",
                        cursor: "pointer",
                        padding: 0,        
                        margin: 0,         
                        display: "inline", 
                        lineHeight: "inherit",
                        verticalAlign: "baseline"
                      }}
                    >
                      điều khoản thanh toán
                    </button>
                  </span>

                </label>

              <div className="center">
                <button
                  className={`btn btn--primary ${!agreed ? "btn--disabled" : ""}`}
                  type="button"
                  disabled={!agreed}
                  onClick={handlePayOther}
                >
                  Thanh toán
                </button>
              </div>

               
              </>
            )}
          </>
        )}


        {/* -----------------
        POP UP SHOW MESSESAGE
        ----------------- */}
        {message && (
          <div className="modal">
            <div className="modal-content">
              <p>{message}</p>
              {/* <p>Số dư hiện tại: {formatCurrencyVN(userData?.balance)}</p> */}
              <div className="center">
                <button className="btn btn--primary" onClick={() => setMessage("")}>
                  Đóng
                </button>
              </div>
            </div>
          </div>
        )}

        {/* -----------------
        POP UP SHOW GUIDE
        ----------------- */}
        {showGuide && (
          <div className="modal">
            <div className="modal-content">
              <h3>Hướng dẫn thanh toán học phí</h3>
              <p>1. Chọn học kỳ muốn thanh toán.</p>
              <p>2. Kiểm tra số tiền còn nợ và danh sách môn học.</p>
              <p>3. Nhấn nút <b>Thanh toán</b> để chuyển sang cổng thanh toán.</p>
              <p>4. Hoàn tất giao dịch và chờ xác nhận từ hệ thống.</p>
              <div className="center">
                <button className="btn btn--primary" onClick={() => setShowGuide(false)}>
                  Đóng
                </button>
              </div>
            </div>
          </div>
        )}

      {/* -----------------
          POP UP SHOW TERMS
      ----------------- */}
      {showTerms && (
        <div className="modal">
          <div className="modal-content">
            <h3>Điều khoản thanh toán</h3>
            <div style={{ textAlign: "left", lineHeight: "1.6" }}>
              <p>1. Sau khi xác nhận thanh toán, giao dịch sẽ không thể hoàn tác.</p>
              <p>2. Người nộp cần đảm bảo thông tin học phí và tài khoản chính xác.</p>
              <p>3. Mọi sai sót trong quá trình thanh toán là trách nhiệm của người nộp.</p>
              <p>4. Hệ thống sẽ lưu trữ lịch sử giao dịch để đối chiếu khi cần thiết.</p>
              <p>5. Việc tiếp tục sử dụng chức năng thanh toán đồng nghĩa với việc bạn đồng ý với các điều khoản trên.</p>
            </div>
            <div className="center" style={{ marginTop: "16px" }}>
              <button className="btn btn--primary" onClick={() => setShowTerms(false)}>
                Tôi đã hiểu
              </button>
            </div>
          </div>
        </div>
      )}



      {/* -----------------
          POP UP SHOW PAY
      ----------------- */}
      {showPay && (
        <div className="modal">
          <div className="modal-content">
            <h3>Nhập số tiền bạn muốn nạp thêm</h3>
            <input
              type="number"
              placeholder="Nhập số tiền..."
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />

            {message && (
              <p style={{ color: "red", textAlign: "center", marginTop: "8px" }}>
                {message}
              </p>
            )}

            <div className="center" style={{ marginTop: "16px" }}>
              <button
                className="btn btn--primary"
                id="confirm"
                onClick={async () => {
                  // const balance = Number(userData?.balance ?? 0);
                  // const total = Number(invoice?.total_amount ?? 0);
                  // const add = Number(amount.trim());
                  const balance = Number(userData?.balance ?? 0);
                  const total = isPayingOther
                    ? Number(otherInvoice?.total_amount ?? 0)   // 💥 nếu đang ở tab người khác
                    : Number(invoice?.total_amount ?? 0);       // 💥 nếu ở tab tự thanh toán
                  const add = Number(amount.trim());


                  if (isNaN(add) || add <= 0) {
                    setMessage("Vui lòng nhập số tiền hợp lệ.");
                    return;
                  }

                  console.log("DEBUG 💰:", { balance, add, total, sum: balance + add });

                  if (balance + add < total) {
                    setMessage("Số tiền không đủ để thanh toán hóa đơn.");
                    return;
}

                  try {
                    // 🟢 1️⃣ Nạp tiền thật vào DB
                    await deposit(userData.id, add);

                    // 🟢 2️⃣ Cập nhật lại FE (hiển thị realtime)
                    setUserData((prev) => ({
                      ...prev,
                      balance: Number(prev?.balance ?? 0) + add,
                    }));

                    // ✅ Thông báo thành công
                    setMessage("Nạp tiền thành công!");
                    setShowPay(false);
                  } catch (err) {
                    console.error("Error:", err);
                    const msg = err.response?.data?.detail || "Lỗi khi nạp tiền.";
                    setMessage(msg);
                  }
                }}
              >
                Xác nhận
              </button>

              <button
                className="btn"
                onClick={() => {
                  setShowPay(false);
                  setAmount("");
                  setMessage("");
                }}
              >
                Hủy
              </button>
            </div>
          </div>
        </div>
      )}

      {/* -----------------
          POP UP KHÔNG ĐỦ TIỀN
      ----------------- */}
      {showInsufficient && (
        <div className="modal">
          <div className="modal-content">
            <h3>Số dư của bạn không đủ để thanh toán hóa đơn.</h3>
            <p>Vui lòng nạp thêm tiền để tiếp tục.</p>
            <div className="center">
              <button
                className="btn btn--primary"
                onClick={() => {
                  setShowInsufficient(false);
                  setShowPay(true); // 🔥 Mở modal nạp tiền
                }}
              >
                Nạp tiền
              </button>
              <button
                className="btn"
                onClick={() => setShowInsufficient(false)}
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}


      {/* -----------------
        POP UP SHOW OTP
        ----------------- */}
      {showOtp && (
        <div className="modal">
          <div className="modal-content">
            <h3>Nhập mã OTP</h3>
            <p>
              Mã OTP có hiệu lực trong:{" "}
              <b style={{ color: "red" }}>
                {Math.floor(otpTimer / 60)}:{String(otpTimer % 60).padStart(2, "0")}
              </b>
            </p>

            <input
              type="text"
              placeholder="Nhập 6 chữ số OTP..."
              value={otp}
              maxLength={6} // chỉ cho phép nhập tối đa 6 ký tự
              onChange={(e) => {
                const value = e.target.value.replace(/\D/g, ""); // chỉ giữ số
                setOtp(value);
              }}
            />
          {otpError && <p style={{ color: "red" }}>{otpError}</p>}

            <div className="center" style={{ marginTop: "16px" }}>
              <button
                className={`btn btn--primary ${otp.length !== 6 ? "btn--disabled" : ""}`}
                id="confirm"
                disabled={otp.length !== 6}
                onClick={async () => {
                  if (otpTimer <= 0) {
                    setOtpError("Mã OTP đã hết hạn. Vui lòng gửi lại mã mới.");
                    setCanResend(true);
                    return;
                  }

                  try {
                    await confirmPayment(generatedOtp, otp);
                    setMessage("Thanh toán thành công!");
                    setShowOtp(false);
                    setOtp("");
                    setOtpError("");
                    setTimeout(() => window.location.reload(), 1000); // ✅ reload sau 1 giây

                    // ✅ Cập nhật lại dữ liệu của mình
                    const me = await getMe();
                    setUserData(me);
                    const inv = await getMyInvoice(selectedSemester);
                    setInvoice(inv);


                    // 🔁 BỔ SUNG: refresh lịch sử của mình
                    try {
                      const resSelf = await getPaymentHistory(me.id, selectedSemester);
                      setPaymentHistory(resSelf.data);
                    } catch (e) {
                      console.warn("Không load lại được lịch sử của mình:", e);
                    }

                    // 🔁 BỔ SUNG: nếu là thanh toán hộ thì refresh lịch sử & hóa đơn của người đó
                    if (isPayingOther && otherUser) {
                      try {
                        const semesterId = semesters[0]?.semester_id || selectedSemester;
                        const resOther = await getPaymentHistory(otherUser.id, semesterId);
                        setOtherPaymentHistory(resOther.data);

                        const invOther = await getOtherInvoice(otherUser.id);
                        setOtherInvoice(invOther);
                      } catch (e) {
                        console.warn("Không load lại được lịch sử/hoá đơn của người khác:", e);
                      }
                    }
                  } catch (err) {
                    console.error("Error confirm payment:", err);
                    const msg = err.response?.data?.detail || "OTP không hợp lệ hoặc đã hết hạn.";
                    if (msg.includes("OTP hết hạn")) {
                      setOtpError("Mã OTP đã hết hạn. Vui lòng gửi lại mã mới.");
                      setCanResend(true);
                    } else if (msg.includes("OTP sai")) {
                      setOtpError("Mã OTP không chính xác. Vui lòng thử lại.");
                    } else {
                      setOtpError(msg);


                    }
                  }
                }}
              >
                Xác nhận OTP
</button>

              {/* Ẩn nút gửi lại cho đến khi hết 5 phút */}
              {canResend ? (
                <button className="btn btn--secondary" onClick={handleResendOtp}>
                  Gửi lại OTP
                </button>
              ) : (
                <button className="btn btn--disabled" disabled>
                  Gửi lại OTP ({Math.floor(otpTimer / 60)}:{String(otpTimer % 60).padStart(2, "0")})
                </button>
              )}

              <button
                className="btn"
                onClick={async () => {
                  try {
                    await cancelIntent(generatedOtp);
                    console.log("Intent đã bị hủy trên BE");
                  } catch (err) {
                    console.error("Lỗi khi hủy intent:", err);
                  } finally {
                    setShowOtp(false);
                    setOtp("");
                    setOtpError("");
                    setMessage("Giao dịch đã bị hủy.");
                    setTimeout(() => window.location.reload(), 1000); // ✅ reload sau 1 giây
                  }
                }}
              >
                Hủy
              </button>
            </div>
          </div>
        </div>
      )}


      {/* -----------------
        POP UP SHOW ENOUGH BALANCE
        ----------------- */}
      {showConfirmAutoPay && (
        <div className="modal">
          <div className="modal-content">
            <h3>Số dư khả dụng đủ để thanh toán</h3>
            <p>Bạn có muốn sử dụng số dư để thanh toán học phí kỳ này không?</p>
            <div className="center" style={{ marginTop: "16px" }}>
              <button
                className={`btn btn--primary`}
                id="confirm"
                disabled={isCreatingIntent}
                onClick={async () => {
                  if (isCreatingIntent) return;
                  try {
                    setIsCreatingIntent(true);

                    const { data } = await createIntent(
                      userData.id,      // payer_user_id
                      userData.id,      // student_id
                      selectedSemester
                    );
                    const intentId = data.id;

                    await sendOtp(intentId);
                    setGeneratedOtp(intentId);
                    setShowConfirmAutoPay(false);
                    setShowOtp(true);
                    setMessage("Mã OTP đã được gửi đến email của bạn.");
                  } catch (err) {
                    console.error("Error create/send OTP:", err);

                    const rawDetail = err?.response?.data?.detail ?? err?.message ?? "";
                    const rawCode   = (err?.response?.data?.code ?? "").toString();
                    const text = typeof rawDetail === "string" ? rawDetail : JSON.stringify(rawDetail);
                    const low  = text.replace(/'/g, '"').toLowerCase();

                    if (
                      low.includes("uq_pi_one_open_per_invoice") ||
                      low.includes("duplicate key") ||
                      low.includes("already exists") ||
                      low.includes("invoice_id") ||
                      rawCode === "23505"
                    ) {
                      setMessage("Hóa đơn đang được xử lý hoặc đã có yêu cầu thanh toán trước đó. Vui lòng đợi.");
                    } else if (low.includes("đã được thanh toán") || low.includes("already paid")) {
                      setMessage("Hóa đơn này đã được thanh toán trước đó.");
                    } else {
                      setMessage("Lỗi khi tạo giao dịch: " + text);
                    }
                  } finally {
                    setIsCreatingIntent(false);
                  }
                }}
              >
                Xác nhận
              </button>

              <button className="btn" onClick={() => setShowConfirmAutoPay(false)}>Hủy</button>
            </div>
          </div>
        </div>
      )}
    </main>
        <footer className="footer">
      <p>
      Copyright © 2025 TDTU iBanking System. Developed by{" "}
       <span className="highlight">Group 09, TDTU</span>.<br />
      Reproduction or distribution without permission is prohibited.</p>
    </footer>

    </>
  )
}
