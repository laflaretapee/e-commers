import React from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./context/AuthContext";

import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import CatalogPage from "./pages/CatalogPage";
import CartPage from "./pages/CartPage";
import OrdersPage from "./pages/OrdersPage";
import ProductPage from "./pages/ProductPage";
import CheckoutPage from "./pages/CheckoutPage";
import ProfilePage from "./pages/ProfilePage";
import AiDashboardPage from "./pages/admin/AiDashboardPage";
import AiRecommendationsPage from "./pages/admin/AiRecommendationsPage";
import AiModerationPage from "./pages/admin/AiModerationPage";
import AiTrainingPage from "./pages/admin/AiTrainingPage";

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  if (!user) {
    return <Navigate replace to="/login" />;
  }
  return <>{children}</>;
}

const App: React.FC = () => {
  const { user } = useAuth();
  return (
    <Routes>
      <Route path="/" element={<CatalogPage />} />
      <Route path="/products/:productId" element={<ProductPage />} />
      <Route path="/login" element={user ? <Navigate replace to="/" /> : <LoginPage />} />
      <Route path="/register" element={user ? <Navigate replace to="/" /> : <RegisterPage />} />
      <Route
        path="/cart"
        element={
          <RequireAuth>
            <CartPage />
          </RequireAuth>
        }
      />
      <Route
        path="/checkout"
        element={
          <RequireAuth>
            <CheckoutPage />
          </RequireAuth>
        }
      />
      <Route
        path="/orders"
        element={
          <RequireAuth>
            <OrdersPage />
          </RequireAuth>
        }
      />
      <Route
        path="/profile"
        element={
          <RequireAuth>
            <ProfilePage />
          </RequireAuth>
        }
      />
      <Route path="/admin/ai" element={<AiDashboardPage />} />
      <Route path="/admin/ai/recommendations" element={<AiRecommendationsPage />} />
      <Route path="/admin/ai/moderation" element={<AiModerationPage />} />
      <Route path="/admin/ai/training" element={<AiTrainingPage />} />
      <Route path="*" element={<Navigate replace to="/" />} />
    </Routes>
  );
};

export default App;
