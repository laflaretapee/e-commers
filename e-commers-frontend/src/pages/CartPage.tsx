import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { cartApi, catalogApi } from "../api/client";
import ProductMedia from "../components/ProductMedia";
import { EmptyState, ErrorState, LoadingState } from "../components/UiState";
import UserShell from "../components/UserShell";
import { useAuth } from "../context/AuthContext";
import { type CartResponse, type Product, formatPrice, reasonLabel } from "../lib/shop";

type CartViewLine = {
  product: Product | null;
  price: number;
  quantity: number;
  productId: number;
};

export default function CartPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [cart, setCart] = useState<CartResponse | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
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
          setError("Не удалось получить данные корзины и каталога.");
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
  const cartItems: CartViewLine[] =
    cart?.items.map((item) => ({
      product: productMap.get(item.product_id) ?? null,
      price: item.price,
      quantity: item.quantity,
      productId: item.product_id,
    })) ?? [];

  const recommendedProducts =
    cart?.recommendations
      .map((item) => ({
        product: productMap.get(item.item_id) ?? null,
        reason: item.reason,
        score: item.score,
      }))
      .filter((item) => item.product !== null) ?? [];

  const emptyRecommendations = products.slice(0, 5);
  const total = cartItems.reduce((sum, item) => sum + item.price * item.quantity, 0);

  const removeOne = async (item: CartViewLine) => {
    if (!user) {
      return;
    }

    try {
      await cartApi.post(
        "/cart/remove",
        {
          product_id: item.productId,
          quantity: 1,
          price: item.price,
        },
        { params: { user_id: user.id } }
      );

      const response = await cartApi.get<CartResponse>("/cart", { params: { user_id: user.id } });
      setCart(response.data);
    } catch {
      setError("Не удалось обновить корзину.");
    }
  };

  if (isLoading) {
    return (
      <UserShell>
        <LoadingState title="Загружаем корзину" />
      </UserShell>
    );
  }

  if (error) {
    return (
      <UserShell>
        <ErrorState description={error} title="Ошибка корзины" />
      </UserShell>
    );
  }

  if (!cart || cartItems.length === 0) {
    return (
      <UserShell>
        <section className="empty-cart-layout">
          <EmptyState
            action={
              <Link className="primary-button" to="/">
                Перейти в каталог
              </Link>
            }
            description="Добавь товары в корзину, и AI сразу предложит подходящие дополнения."
            title="Корзина пуста"
          />

          <section className="suggestions-panel">
            <div className="section-heading">
              <h2>Возможно, вам понравится</h2>
            </div>

            <div className="compact-product-row">
              {emptyRecommendations.map((product) => (
                <Link key={product.id} className="compact-product-card" to={`/products/${product.id}`}>
                  <ProductMedia product={product} size="thumb" />
                  <strong>{formatPrice(product.price)}</strong>
                  <span>{product.title}</span>
                </Link>
              ))}
            </div>
          </section>
        </section>
      </UserShell>
    );
  }

  return (
    <UserShell>
      <div className="cart-page-layout">
        <section className="cart-contents-card">
          <div className="section-heading">
            <h1>
              Корзина <span>{cartItems.length} товара</span>
            </h1>
          </div>

          <div className="cart-line-list">
            {cartItems.map((item) => (
              <article key={`${item.productId}-${item.price}`} className="cart-line-card">
                <div className="cart-line-main">
                  {item.product ? <ProductMedia product={item.product} size="thumb" /> : <div className="cart-thumb-fallback" />}
                  <div>
                    <h3>{item.product?.title ?? `Товар #${item.productId}`}</h3>
                    <p>{item.product?.description ?? "Товар из корзины пользователя"}</p>
                    <div className="cart-line-meta">
                      <span>{formatPrice(item.price)}</span>
                      <span>Количество: {item.quantity}</span>
                    </div>
                  </div>
                </div>

                <div className="cart-line-actions">
                  <strong>{formatPrice(item.price * item.quantity)}</strong>
                  <button className="secondary-button" onClick={() => void removeOne(item)} type="button">
                    Удалить 1 шт.
                  </button>
                </div>
              </article>
            ))}
          </div>
        </section>

        <aside className="cart-summary-card">
          <div className="cart-total-block">
            <span>Ваша корзина</span>
            <strong>{formatPrice(total)}</strong>
            <p>Сумма обновляется в реальном времени после каждой операции.</p>
          </div>

          <button className="primary-button wide" onClick={() => navigate("/checkout")} type="button">
            Перейти к оформлению
          </button>

          {recommendedProducts.length > 0 && (
            <section className="cart-ai-box">
              <div className="mini-heading">
                <h3>AI рекомендации</h3>
                <span>{recommendedProducts.length}</span>
              </div>

              <div className="cart-ai-list">
                {recommendedProducts.map((item) => (
                  <Link key={item.product?.id} className="cart-ai-item" to={`/products/${item.product?.id}`}>
                    <strong>{item.product?.title}</strong>
                    <span>{reasonLabel(item.reason)}</span>
                    <span>score {item.score.toFixed(3)}</span>
                  </Link>
                ))}
              </div>
            </section>
          )}
        </aside>
      </div>
    </UserShell>
  );
}
