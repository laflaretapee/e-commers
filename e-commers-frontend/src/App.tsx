import React from "react";
import { Routes, Route, Link, Navigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext";

import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import CatalogPage from "./pages/CatalogPage";
import CartPage from "./pages/CartPage";
import OrdersPage from "./pages/OrdersPage";

const App: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <div className="app-root">
      <header className="app-header">
        <div className="app-logo">Mini Ozon</div>

        <nav className="app-nav">
          <Link to="/">Каталог</Link>
          {user && (
            <>
              <Link to="/cart">Корзина</Link>
              <Link to="/orders">Заказы</Link>
            </>
          )}
        </nav>

        <div className="app-user">
          {user ? (
            <>
              <span className="text-muted">{user.email}</span>
              <button className="btn btn-secondary" onClick={logout}>
                Выйти
              </button>
            </>
          ) : (
            <>
              <Link to="/login">Вход</Link>
              <span className="text-muted">/</span>
              <Link to="/register">Регистрация</Link>
            </>
          )}
        </div>
      </header>

      <main>
        <Routes>
          <Route path="/" element={<CatalogPage />} />
          <Route
            path="/login"
            element={user ? <Navigate to="/" /> : <LoginPage />}
          />
          <Route
            path="/register"
            element={user ? <Navigate to="/" /> : <RegisterPage />}
          />
          <Route
            path="/cart"
            element={user ? <CartPage /> : <Navigate to="/login" />}
          />
          <Route
            path="/orders"
            element={user ? <OrdersPage /> : <Navigate to="/login" />}
          />
        </Routes>
      </main>
    </div>
  );
};

export default App;
