import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { cartApi, catalogApi, orderApi } from "../api/client";
import ProductMedia from "../components/ProductMedia";
import { EmptyState, ErrorState, LoadingState } from "../components/UiState";
import UserShell from "../components/UserShell";
import { useAuth } from "../context/AuthContext";
import { type CartResponse, type Product, formatPrice } from "../lib/shop";

export default function CheckoutPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [cart, setCart] = useState<CartResponse | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
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
        const [cartResponse, productsResponse] = await Promise.all([
          cartApi.get<CartResponse>("/cart", { params: { user_id: user.id } }),
          catalogApi.get<Product[]>("/products", { params: { user_id: user.id } }),
        ]);

        if (active) {
          setCart(cartResponse.data);
          setProducts(productsResponse.data);
        }
      } catch {
        if (active) {
          setError("Не удалось подготовить оформление заказа.");
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
  const total = cart?.items.reduce((sum, item) => sum + item.price * item.quantity, 0) ?? 0;

  const handleCheckout = async () => {
    if (!user) {
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await orderApi.post("/orders/from-cart", null, {
        params: { user_id: user.id },
      });
      navigate(`/orders?highlight=${response.data.id}`);
    } catch {
      setError("Не удалось оформить заказ.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <UserShell>
      {isLoading && <LoadingState title="Готовим оформление заказа" />}
      {!isLoading && error && <ErrorState description={error} title="Checkout недоступен" />}
      {!isLoading && !error && (!cart || cart.items.length === 0) && (
        <EmptyState
          action={
            <Link className="primary-button" to="/">
              Вернуться в каталог
            </Link>
          }
          description="Корзина пуста, поэтому оформлять пока нечего."
          title="Нет товаров для заказа"
        />
      )}

      {!isLoading && !error && cart && cart.items.length > 0 && (
        <div className="checkout-layout">
          <section className="checkout-main-card">
            <div className="section-heading">
              <h1>Оформление заказа</h1>
              <span>{cart.items.length} позиции</span>
            </div>

            <div className="checkout-items">
              {cart.items.map((item) => {
                const product = productMap.get(item.product_id) ?? null;
                return (
                  <article key={`${item.product_id}-${item.price}`} className="checkout-item-row">
                    {product ? <ProductMedia product={product} size="thumb" /> : <div className="cart-thumb-fallback" />}
                    <div>
                      <h3>{product?.title ?? `Товар #${item.product_id}`}</h3>
                      <p>{item.quantity} × {formatPrice(item.price)}</p>
                    </div>
                  </article>
                );
              })}
            </div>
          </section>

          <aside className="checkout-summary-card">
            <div className="checkout-info-block">
              <h3>Получатель</h3>
              <p>{user?.full_name}</p>
              <span>{user?.email}</span>
            </div>

            <div className="checkout-info-block">
              <h3>Доставка</h3>
              <p>Пункт выдачи Ozon</p>
              <span>Самовывоз сегодня после 18:00</span>
            </div>

            <div className="checkout-total-row">
              <span>Итого</span>
              <strong>{formatPrice(total)}</strong>
            </div>

            <button className="primary-button wide" disabled={isSubmitting} onClick={() => void handleCheckout()} type="button">
              {isSubmitting ? "Оформляем..." : "Подтвердить заказ"}
            </button>
          </aside>
        </div>
      )}
    </UserShell>
  );
}
