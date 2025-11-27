import React, { useState } from "react";
import { authApi } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";

const RegisterPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    try {
      const res = await authApi.post("/register", {
        email,
        password,
        full_name: fullName,
        role: "customer",
      });
      login(res.data);
      navigate("/");
    } catch {
      setError("Ошибка регистрации");
    }
  };

  return (
    <div className="card" style={{ maxWidth: 420 }}>
      <h2 className="page-title">Регистрация</h2>
      <form className="form" onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="ФИО"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
        />
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <input
          type="password"
          placeholder="Пароль"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <button className="btn" type="submit">
          Создать аккаунт
        </button>
      </form>
      {error && <p style={{ color: "#f97373", marginTop: 8 }}>{error}</p>}
    </div>
  );
};

export default RegisterPage;
