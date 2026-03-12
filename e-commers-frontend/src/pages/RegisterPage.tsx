import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { authApi } from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function RegisterPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordRepeat, setPasswordRepeat] = useState("");
  const [consent, setConsent] = useState(true);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");

    if (!consent) {
      setError("Нужно принять условия использования.");
      return;
    }

    if (password !== passwordRepeat) {
      setError("Пароли не совпадают.");
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await authApi.post("/register", {
        email,
        password,
        full_name: `${firstName} ${lastName}`.trim() || email,
        role: "customer",
      });
      login(response.data);
      navigate("/");
    } catch {
      setError("Ошибка регистрации. Возможно, пользователь уже существует.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <header className="auth-topbar">
        <Link className="auth-brand" to="/">
          <span className="material-symbols-outlined">auto_awesome</span>
          <strong>Ozon</strong>
        </Link>

        <Link className="ghost-link-button" to="/login">
          Уже есть аккаунт?
        </Link>
      </header>

      <main className="auth-main">
        <section className="auth-card">
          <h1>Регистрация</h1>
          <p>Создайте профиль, чтобы делать покупки, отслеживать заказы и получать AI-подборки.</p>

          <form className="auth-form" onSubmit={handleSubmit}>
            <div className="split-fields">
              <label>
                <span>Имя</span>
                <input onChange={(event) => setFirstName(event.target.value)} placeholder="Иван" value={firstName} />
              </label>
              <label>
                <span>Фамилия</span>
                <input onChange={(event) => setLastName(event.target.value)} placeholder="Иванов" value={lastName} />
              </label>
            </div>

            <label>
              <span>Электронная почта</span>
              <input onChange={(event) => setEmail(event.target.value)} placeholder="example@mail.ru" type="email" value={email} />
            </label>

            <label>
              <span>Номер телефона</span>
              <input onChange={(event) => setPhone(event.target.value)} placeholder="+7 (900) 000-00-00" value={phone} />
            </label>

            <label>
              <span>Пароль</span>
              <input
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Минимум 8 символов"
                type="password"
                value={password}
              />
            </label>

            <label>
              <span>Подтвердите пароль</span>
              <input
                onChange={(event) => setPasswordRepeat(event.target.value)}
                placeholder="Повторите ваш пароль"
                type="password"
                value={passwordRepeat}
              />
            </label>

            <label className="checkbox-row">
              <input checked={consent} onChange={() => setConsent((value) => !value)} type="checkbox" />
              <span>
                Я согласен с условиями использования и политикой конфиденциальности. {phone && <strong>{phone}</strong>}
              </span>
            </label>

            {error && <div className="form-error">{error}</div>}

            <button className="primary-button wide" disabled={isSubmitting} type="submit">
              {isSubmitting ? "Создаем аккаунт..." : "Зарегистрироваться"}
            </button>
          </form>

          <div className="auth-bottom-link">
            Уже зарегистрированы? <Link to="/login">Войти в аккаунт</Link>
          </div>
        </section>
      </main>
    </div>
  );
}
