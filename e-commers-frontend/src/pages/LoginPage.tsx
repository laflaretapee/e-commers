import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { authApi } from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      const response = await authApi.post("/login", { email, password });
      login(response.data);
      navigate("/");
    } catch {
      setError("Неверный email или пароль.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <header className="auth-topbar">
        <Link className="auth-brand" to="/">
          <span className="material-symbols-outlined">shopping_bag</span>
          <strong>Ozon</strong>
        </Link>
      </header>

      <main className="auth-main">
        <section className="auth-card">
          <h1>Вход или регистрация</h1>
          <p>Войди в аккаунт, чтобы увидеть персональные рекомендации, историю заказов и AI-сценарии.</p>

          <form className="auth-form" onSubmit={handleSubmit}>
            <label>
              <span>Электронная почта</span>
              <input
                autoComplete="email"
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@example.com"
                type="email"
                value={email}
              />
            </label>

            <label>
              <span>Пароль</span>
              <input
                autoComplete="current-password"
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Минимум 8 символов"
                type="password"
                value={password}
              />
            </label>

            {error && <div className="form-error">{error}</div>}

            <button className="primary-button wide" disabled={isSubmitting} type="submit">
              {isSubmitting ? "Выполняем вход..." : "Войти"}
            </button>

            <div className="social-divider">или войти через</div>

            <div className="social-grid">
              <button className="social-button" type="button">
                VK ID
              </button>
              <button className="social-button" type="button">
                Google
              </button>
            </div>
          </form>

          <div className="auth-bottom-link">
            Нет аккаунта? <Link to="/register">Зарегистрироваться</Link>
          </div>
        </section>
      </main>
    </div>
  );
}
