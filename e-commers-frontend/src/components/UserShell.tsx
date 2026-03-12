import type { ReactNode } from "react";
import { Link, NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

type UserShellProps = {
  children: ReactNode;
  searchValue?: string;
  onSearchChange?: (value: string) => void;
  searchPlaceholder?: string;
};

const iconLinkClass = ({ isActive }: { isActive: boolean }) =>
  `user-shell-icon-link${isActive ? " is-active" : ""}`;

export default function UserShell({
  children,
  searchValue,
  onSearchChange,
  searchPlaceholder = "Искать на Ozon",
}: UserShellProps) {
  const { user, logout } = useAuth();

  return (
    <div className="user-shell">
      <header className="user-header">
        <div className="user-header-row">
          <Link className="user-brand" to="/">
            <div className="user-brand-logo">
              <span className="material-symbols-outlined">shopping_bag</span>
            </div>
            <div className="user-brand-name">Ozon</div>
          </Link>

          <NavLink className={({ isActive }) => `catalog-pill${isActive ? " is-active" : ""}`} to="/">
            Каталог
          </NavLink>

          <div className="header-search">
            <span className="material-symbols-outlined">search</span>
            <input
              onChange={(event) => onSearchChange?.(event.target.value)}
              placeholder={searchPlaceholder}
              value={searchValue ?? ""}
            />
          </div>

          <div className="user-header-actions">
            <NavLink className={iconLinkClass} to="/orders">
              <span className="material-symbols-outlined">package_2</span>
              <span>Заказы</span>
            </NavLink>
            <NavLink className={iconLinkClass} to="/cart">
              <span className="material-symbols-outlined">shopping_cart</span>
              <span>Корзина</span>
            </NavLink>
            <NavLink className={iconLinkClass} to="/profile">
              <span className="material-symbols-outlined">person</span>
              <span>Профиль</span>
            </NavLink>
            <NavLink className={iconLinkClass} to="/admin/ai">
              <span className="material-symbols-outlined">smart_toy</span>
              <span>AI</span>
            </NavLink>

            {user ? (
              <button className="avatar-button" onClick={logout} type="button">
                {user.full_name.charAt(0).toUpperCase()}
              </button>
            ) : (
              <Link className="auth-link-pill" to="/login">
                Войти
              </Link>
            )}
          </div>
        </div>

        <nav className="category-nav">
          {["Акции", "Электроника", "Одежда и обувь", "Дом и сад", "Красота и здоровье", "Спорт"].map((item) => (
            <span key={item} className="category-link">
              {item}
            </span>
          ))}
        </nav>
      </header>

      <main className="user-main">{children}</main>

      <footer className="user-footer">
        <div>
          <h4>Покупателям</h4>
          <a href="#help">Как сделать заказ</a>
          <a href="#delivery">Доставка</a>
          <a href="#return">Возврат товара</a>
        </div>
        <div>
          <h4>Партнёрам</h4>
          <a href="#sell">Продавайте на Ozon</a>
          <a href="#brands">Для брендов</a>
          <a href="#pickup">Пункты выдачи</a>
        </div>
        <div>
          <h4>Компания</h4>
          <a href="#about">О компании</a>
          <a href="#vacancies">Вакансии</a>
          <a href="#press">Пресс-центр</a>
        </div>
        <div>
          <h4>Мы в соцсетях</h4>
          <div className="footer-socials">
            <span className="material-symbols-outlined">share</span>
            <span className="material-symbols-outlined">alternate_email</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
