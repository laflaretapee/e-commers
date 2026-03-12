import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { orderApi } from "../api/client";
import { EmptyState, ErrorState, LoadingState } from "../components/UiState";
import UserShell from "../components/UserShell";
import { useAuth } from "../context/AuthContext";
import { type Order, formatDateShort, formatPrice } from "../lib/shop";

export default function ProfilePage() {
  const { user, logout } = useAuth();
  const [orders, setOrders] = useState<Order[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    const load = async () => {
      if (!user) {
        return;
      }

      setIsLoading(true);
      setError("");

      try {
        const response = await orderApi.get<Order[]>("/orders", { params: { user_id: user.id } });
        if (active) {
          setOrders(response.data);
        }
      } catch {
        if (active) {
          setError("Не удалось загрузить профиль пользователя.");
        }
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    };

    void load();
    return () => {
      active = false;
    };
  }, [user]);

  const totalSpent = orders.reduce((sum, order) => sum + order.total_amount, 0);

  return (
    <UserShell>
      <div className="profile-grid">
        <section className="profile-card">
          <div className="profile-avatar">{user?.full_name.charAt(0).toUpperCase()}</div>
          <div>
            <h1>{user?.full_name}</h1>
            <p>{user?.email}</p>
            <span className="profile-role-chip">{user?.role}</span>
          </div>
        </section>

        <section className="profile-stats-grid">
          <div className="profile-stat-card">
            <span>Заказы</span>
            <strong>{orders.length}</strong>
          </div>
          <div className="profile-stat-card">
            <span>Сумма покупок</span>
            <strong>{formatPrice(totalSpent || 0)}</strong>
          </div>
          <div className="profile-stat-card">
            <span>AI режим</span>
            <strong>активен</strong>
          </div>
        </section>

        <section className="profile-panel wide">
          <div className="section-heading">
            <h2>Личные данные</h2>
            <button className="secondary-button slim" onClick={logout} type="button">
              Выйти
            </button>
          </div>

          <div className="profile-detail-grid">
            <div>
              <span>Имя</span>
              <strong>{user?.full_name}</strong>
            </div>
            <div>
              <span>Email</span>
              <strong>{user?.email}</strong>
            </div>
            <div>
              <span>Роль</span>
              <strong>{user?.role}</strong>
            </div>
            <div>
              <span>ID пользователя</span>
              <strong>{user?.id}</strong>
            </div>
          </div>
        </section>

        <section className="profile-panel wide">
          <div className="section-heading">
            <h2>Последние заказы</h2>
            <Link className="secondary-button slim" to="/orders">
              Все заказы
            </Link>
          </div>

          {isLoading && <LoadingState title="Подгружаем историю заказов" />}
          {!isLoading && error && <ErrorState description={error} title="Профиль временно недоступен" />}
          {!isLoading && !error && orders.length === 0 && (
            <EmptyState
              action={
                <Link className="primary-button" to="/">
                  Перейти в каталог
                </Link>
              }
              description="Как только оформите первый заказ, он появится здесь."
              title="История заказов пока пуста"
            />
          )}

          {!isLoading && !error && orders.length > 0 && (
            <div className="profile-orders-list">
              {orders.slice(0, 4).map((order) => (
                <article key={order.id} className="profile-order-card">
                  <div>
                    <strong>Заказ #{order.id}</strong>
                    <p>{formatDateShort(order.created_at)}</p>
                  </div>
                  <strong>{formatPrice(order.total_amount)}</strong>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </UserShell>
  );
}
