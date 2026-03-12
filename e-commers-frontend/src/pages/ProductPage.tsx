import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { aiApi, cartApi, catalogApi } from "../api/client";
import ProductMedia from "../components/ProductMedia";
import { ErrorState, LoadingState } from "../components/UiState";
import UserShell from "../components/UserShell";
import { useAuth } from "../context/AuthContext";
import {
  type Product,
  type RecommendationResponse,
  buildProductSpecs,
  extractBrand,
  formatPrice,
  ratingForProduct,
  reviewCountForProduct,
} from "../lib/shop";

export default function ProductPage() {
  const { productId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [product, setProduct] = useState<Product | null>(null);
  const [allProducts, setAllProducts] = useState<Product[]>([]);
  const [similarProducts, setSimilarProducts] = useState<Product[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let active = true;

    const load = async () => {
      if (!productId) {
        setError("Не найден ID товара.");
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setError("");

      try {
        const [productResponse, productsResponse] = await Promise.all([
          catalogApi.get<Product>(`/products/${productId}`, {
            params: user ? { user_id: user.id } : undefined,
          }),
          catalogApi.get<Product[]>("/products", {
            params: user ? { user_id: user.id } : undefined,
          }),
        ]);

        const currentProduct = productResponse.data;
        const products = productsResponse.data;

        let similar = products.filter((item) => item.id !== currentProduct.id).slice(0, 5);

        if (user) {
          try {
            const recommendationResponse = await aiApi.get<RecommendationResponse>("/recommendations", {
              params: {
                user_id: user.id,
                context: "product",
                item_id: currentProduct.id,
                limit: 5,
              },
            });

            const recommendedIds = recommendationResponse.data.items.map((item) => item.item_id);
            const productMap = new Map(products.map((item) => [item.id, item]));
            similar = recommendedIds.flatMap((id) => {
              const item = productMap.get(id);
              return item && item.id !== currentProduct.id ? [item] : [];
            });
          } catch {
            // fallback to catalog-based picks
          }
        }

        if (active) {
          setProduct(currentProduct);
          setAllProducts(products);
          setSimilarProducts(similar);
        }
      } catch {
        if (active) {
          setError("Не удалось загрузить карточку товара.");
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
  }, [productId, user]);

  const addToCart = async () => {
    if (!product) {
      return;
    }

    if (!user) {
      navigate("/login");
      return;
    }

    try {
      await cartApi.post(
        "/cart/add",
        {
          product_id: product.id,
          quantity: 1,
          price: product.price,
        },
        { params: { user_id: user.id } }
      );
      setNotice("Товар добавлен в корзину.");
    } catch {
      setNotice("Не удалось добавить товар в корзину.");
    }
  };

  if (isLoading) {
    return (
      <UserShell>
        <LoadingState title="Загружаем карточку товара" />
      </UserShell>
    );
  }

  if (error || !product) {
    return (
      <UserShell>
        <ErrorState description={error || "Товар не найден."} title="Ошибка карточки товара" />
      </UserShell>
    );
  }

  const specs = buildProductSpecs(product);

  return (
    <UserShell>
      <div className="product-page">
        <nav className="breadcrumbs">
          <Link to="/">Электроника</Link>
          <span>/</span>
          <span>{extractBrand(product.title)}</span>
          <span>/</span>
          <span>{product.title}</span>
        </nav>

        <section className="product-hero">
          <div className="product-gallery-card">
            <ProductMedia product={product} size="hero" />
            <div className="thumbnail-row">
              {[0, 1, 2].map((index) => (
                <div key={index} className="thumbnail-card">
                  <ProductMedia product={product} size="thumb" />
                </div>
              ))}
            </div>
          </div>

          <div className="product-summary">
            <div className="product-rating-inline">
              <span className="material-symbols-outlined">star</span>
              <strong>{ratingForProduct(product.id).toFixed(1)}</strong>
              <span>{reviewCountForProduct(product.id)} отзывов</span>
            </div>

            <h1>{product.title}</h1>

            <div className="product-spec-grid">
              {specs.slice(0, 4).map(([label, value]) => (
                <div key={label}>
                  <span>{label}</span>
                  <strong>{value}</strong>
                </div>
              ))}
            </div>
          </div>

          <aside className="product-buy-box">
            <strong>{formatPrice(product.price)}</strong>
            <span>{product.stock > 0 ? "В наличии" : "Нет на складе"}</span>
            <button className="primary-button wide" onClick={() => void addToCart()} type="button">
              Добавить в корзину
            </button>
            <button className="secondary-button wide" onClick={() => navigate("/checkout")} type="button">
              Купить в один клик
            </button>
            <div className="delivery-card-list">
              <div>
                <span className="material-symbols-outlined">local_shipping</span>
                <p>Доставка Ozon сегодня</p>
              </div>
              <div>
                <span className="material-symbols-outlined">inventory_2</span>
                <p>Оригинальный товар</p>
              </div>
            </div>
          </aside>
        </section>

        {notice && <div className="inline-notice">{notice}</div>}

        <section className="product-copy-section">
          <div>
            <h2>Описание</h2>
            <p>
              {product.description ??
                "Товар добавлен через catalog_service и участвует в AI-сценариях рекомендаций, корзины и обучения модели."}
            </p>
          </div>

          <div>
            <h2>Характеристики</h2>
            <div className="spec-table">
              {buildProductSpecs(product).map(([label, value]) => (
                <div key={label} className="spec-row">
                  <span>{label}</span>
                  <strong>{value}</strong>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="product-related-section">
          <div className="section-heading">
            <h2>Похожие товары</h2>
            <span>{Math.min(similarProducts.length, allProducts.length)} позиций</span>
          </div>

          <div className="compact-product-row">
            {similarProducts.map((item) => (
              <Link key={item.id} className="compact-product-card" to={`/products/${item.id}`}>
                <ProductMedia product={item} size="thumb" />
                <strong>{formatPrice(item.price)}</strong>
                <span>{item.title}</span>
              </Link>
            ))}
          </div>
        </section>
      </div>
    </UserShell>
  );
}
