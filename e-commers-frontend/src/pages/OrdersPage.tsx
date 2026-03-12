import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { catalogApi, orderApi } from "../api/client";
import ProductMedia from "../components/ProductMedia";
import { EmptyState, ErrorState, LoadingState } from "../components/UiState";
import UserShell from "../components/UserShell";
import { useAuth } from "../context/AuthContext";
import {
  type Order,
  type Product,
  formatDateTime,
  formatPrice,
  orderStatusLabel,
} from "../lib/shop";

type OrdersFilter = "all" | "active";

export default function OrdersPage() {
  const { user, logout } = useAuth();
  const [orders, setOrders] = useState<Order[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState<OrdersFilter>("all");

  useEffect(() => {
    let active = true;

    const load = async () => {
      if (!user) {
        return;
      }

      setIsLoading(true);
      setError("");

      try {
        const [ordersResponse, productsResponse] = await Promise.all([
          orderApi.get<Order[]>("/orders", { params: { user_id: user.id } }),
          catalogApi.get<Product[]>("/products", { params: { user_id: user.id } }),
        ]);

        if (active) {
          setOrders(ordersResponse.data);
          setProducts(productsResponse.data);
        }
      } catch {
        if (active) {
          setError("Не удалось загрузить заказы пользователя.");
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

  const productMap = new Map(products.map((product) => [product.id, product]));
  const visibleOrders = filter === "active" ? orders.filter((order) => order.status !== "archived") : orders;

  return (
    <UserShell>
      <div className="account-layout">
        <aside className="account-sidebar">
          <div className="account-profile-card">
            <h2>{user?.full_name}</h2>
            <p>ID: {user?.id}</p>
          </div>

          <nav className="account-nav">
            <Link className="account-nav-link is-active" to="/orders">
              <span className="material-symbols-outlined">package_2</span>
              Заказы
            </Link>
            <Link className="account-nav-link" to="/profile">
              <span className="material-symbols-outlined">person</span>
              Личные данные
            </Link>
            <button className="account-nav-link" onClick={logout} type="button">
              <span className="material-symbols-outlined">logout</span>
              Выйти
            </button>
          </nav>
        </aside>

        <section className="account-main">
          <div className="account-heading">
            <h1>Мои заказы</h1>
            <div className="segment-control">
              <button className={filter === "all" ? "is-active" : ""} onClick={() => setFilter("all")} type="button">
                Все
              </button>
              <button
                className={filter === "active" ? "is-active" : ""}
                onClick={() => setFilter("active")}
                type="button"
              >
                Активные
              </button>
            </div>
          </div>

          {isLoading && <LoadingState title="Собираем историю заказов" />}
          {!isLoading && error && <ErrorState description={error} title="Заказы недоступны" />}
          {!isLoading && !error && visibleOrders.length === 0 && (
            <EmptyState
              action={
                <Link className="primary-button" to="/">
                  Перейти в каталог
                </Link>
              }
              description="После оформления заказа он появится в этом разделе."
              title="Заказов пока нет"
            />
          )}

          {!isLoading && !error && visibleOrders.length > 0 && (
            <div className="orders-stack">
              {visibleOrders.map((order) => {
                const firstItem = order.items[0];
                const firstProduct = firstItem ? productMap.get(firstItem.product_id) ?? null : null;

                return (
                  <article key={order.id} className="order-history-card">
                    <div className="order-history-main">
                      <div className="order-history-media">
                        {firstProduct ? <ProductMedia product={firstProduct} size="thumb" /> : <div className="cart-thumb-fallback" />}
                      </div>

                      <div className="order-history-text">
                        <div className="order-status-pill">{orderStatusLabel(order.status)}</div>
                        <h3>{firstProduct?.title ?? `Заказ #${order.id}`}</h3>
                        <p>
                          Заказ №{order.id} • {formatDateTime(order.created_at)}
                        </p>
                        <div className="order-history-actions">
                          <Link className="primary-button slim" to="/">
                            Повторить заказ
                          </Link>
                          <Link className="secondary-button slim" to={firstProduct ? `/products/${firstProduct.id}` : "/"}>
                            Открыть товар
                          </Link>
                        </div>
                      </div>
                    </div>

                    <strong className="order-history-total">{formatPrice(order.total_amount)}</strong>
                  </article>
                );
              })}
            </div>
          )}
        </section>
      </div>
    </UserShell>
  );
}
