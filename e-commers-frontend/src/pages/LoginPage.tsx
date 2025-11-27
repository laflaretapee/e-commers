import React, { useState } from "react";
import { authApi } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";

const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    try {
      const res = await authApi.post("/login", { email, password });
      login(res.data);
      navigate("/");
    } catch {
      setError("Неверный email или пароль");
    }
  };

  return (
    <div className="card" style={{ maxWidth: 420 }}>
      <h2 className="page-title">Вход</h2>
      <form className="form" onSubmit={handleSubmit}>
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
          Войти
        </button>
      </form>
      {error && <p style={{ color: "#f97373", marginTop: 8 }}>{error}</p>}
    </div>
  );
};

export default LoginPage;
