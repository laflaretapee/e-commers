import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { cartApi, catalogApi } from "../api/client";
import ProductMedia from "../components/ProductMedia";
import { EmptyState, ErrorState, LoadingState } from "../components/UiState";
import UserShell from "../components/UserShell";
import { useAuth } from "../context/AuthContext";
import {
  type Product,
  discountLabel,
  extractBrand,
  formatPrice,
  inferCategory,
  oldPriceForProduct,
  ratingForProduct,
  reviewCountForProduct,
} from "../lib/shop";

type SortMode = "popular" | "price_asc" | "price_desc" | "newest";

export default function CatalogPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [products, setProducts] = useState<Product[]>([]);
  const [search, setSearch] = useState("");
  const [selectedBrand, setSelectedBrand] = useState<string>("Все");
  const [priceFrom, setPriceFrom] = useState("");
  const [priceTo, setPriceTo] = useState("");
  const [sortMode, setSortMode] = useState<SortMode>("popular");
  const [onlyDiscount, setOnlyDiscount] = useState(false);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [notice, setNotice] = useState("");

  useEffect(() => {
    let active = true;

    const loadProducts = async () => {
      setIsLoading(true);
      setError("");

      try {
        const response = await catalogApi.get<Product[]>("/products", {
          params: user ? { user_id: user.id } : undefined,
        });

        if (active) {
          setProducts(response.data);
        }
      } catch {
        if (active) {
          setError("Не удалось загрузить каталог из catalog_service.");
        }
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    };

    void loadProducts();
    return () => {
      active = false;
    };
  }, [user]);

  const brands = ["Все", ...Array.from(new Set(products.map((product) => extractBrand(product.title))))].slice(0, 6);

  const filteredProducts = products
    .filter((product) => {
      const normalizedSearch = search.trim().toLowerCase();
      const matchesSearch =
        normalizedSearch.length === 0 ||
        product.title.toLowerCase().includes(normalizedSearch) ||
        (product.description ?? "").toLowerCase().includes(normalizedSearch);

      const matchesBrand = selectedBrand === "Все" || extractBrand(product.title) === selectedBrand;
      const matchesPriceFrom = !priceFrom || product.price >= Number(priceFrom);
      const matchesPriceTo = !priceTo || product.price <= Number(priceTo);
      const matchesDiscount = !onlyDiscount || Boolean(discountLabel(product));

      return matchesSearch && matchesBrand && matchesPriceFrom && matchesPriceTo && matchesDiscount;
    })
    .sort((left, right) => {
      if (sortMode === "price_asc") {
        return left.price - right.price;
      }
      if (sortMode === "price_desc") {
        return right.price - left.price;
      }
      if (sortMode === "newest") {
        return right.id - left.id;
      }
      return right.stock - left.stock;
    });

  const addToCart = async (product: Product) => {
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
        {
          params: { user_id: user.id },
        }
      );
      setNotice(`Товар "${product.title}" добавлен в корзину.`);
    } catch {
      setNotice("Не удалось добавить товар в корзину.");
    }
  };

  return (
    <UserShell searchValue={search} onSearchChange={setSearch}>
      <div className="catalog-layout">
        <aside className="catalog-filters">
          <div className="panel-card">
            <h3>Фильтры</h3>
            <label className="filter-label">
              <span>Цена, ₽</span>
              <div className="price-row">
                <input onChange={(event) => setPriceFrom(event.target.value)} placeholder="от" value={priceFrom} />
                <input onChange={(event) => setPriceTo(event.target.value)} placeholder="до" value={priceTo} />
              </div>
            </label>

            <div className="filter-group">
              <span className="filter-title">Бренд</span>
              {brands.map((brand) => (
                <label key={brand} className="checkbox-row">
                  <input
                    checked={selectedBrand === brand}
                    name="brand"
                    onChange={() => setSelectedBrand(brand)}
                    type="radio"
                  />
                  <span>{brand}</span>
                </label>
              ))}
            </div>

            <div className="filter-group">
              <span className="filter-title">Рейтинг</span>
              <div className="rating-row">
                <span className="material-symbols-outlined">star</span>
                <span>4.5 и выше</span>
              </div>
            </div>

            <label className="toggle-row">
              <span>Только со скидкой</span>
              <input checked={onlyDiscount} onChange={() => setOnlyDiscount((value) => !value)} type="checkbox" />
            </label>
          </div>
        </aside>

        <section className="catalog-content">
          <div className="catalog-heading">
            <div>
              <h1>Электроника</h1>
              <p>{filteredProducts.length} товаров</p>
            </div>

            <label className="sort-select">
              <span>Сортировать:</span>
              <select onChange={(event) => setSortMode(event.target.value as SortMode)} value={sortMode}>
                <option value="popular">Популярные</option>
                <option value="newest">Новые</option>
                <option value="price_asc">Сначала дешевле</option>
                <option value="price_desc">Сначала дороже</option>
              </select>
            </label>
          </div>

          {notice && <div className="inline-notice">{notice}</div>}

          {isLoading && <LoadingState title="Загружаем каталог" />}

          {!isLoading && error && (
            <ErrorState description={error} title="Каталог недоступен" />
          )}

          {!isLoading && !error && filteredProducts.length === 0 && (
            <EmptyState
              action={
                <Link className="primary-button" to="/admin/ai/recommendations">
                  Открыть AI Console
                </Link>
              }
              description="Попробуй изменить фильтры или наполни каталог через seeder."
              title="Товаров пока нет"
            />
          )}

          {!isLoading && !error && filteredProducts.length > 0 && (
            <div className="catalog-grid">
              {filteredProducts.map((product) => {
                const oldPrice = oldPriceForProduct(product);
                return (
                  <article key={product.id} className="catalog-card">
                    {discountLabel(product) && <span className="discount-chip">{discountLabel(product)}</span>}

                    <Link className="catalog-card-link" to={`/products/${product.id}`}>
                      <ProductMedia product={product} />
                    </Link>

                    <div className="catalog-card-body">
                      <div className="catalog-card-price-row">
                        <strong>{formatPrice(product.price)}</strong>
                        {oldPrice && <span>{formatPrice(oldPrice)}</span>}
                      </div>

                      <Link className="catalog-card-title" to={`/products/${product.id}`}>
                        {product.title}
                      </Link>

                      <p className="catalog-card-caption">{inferCategory(product.title)}</p>

                      <div className="catalog-rating-row">
                        <span className="material-symbols-outlined">star</span>
                        <span>{ratingForProduct(product.id).toFixed(1)}</span>
                        <span className="catalog-muted">{reviewCountForProduct(product.id)} отзывов</span>
                      </div>

                      <button className="primary-button wide" onClick={() => void addToCart(product)} type="button">
                        <span className="material-symbols-outlined">shopping_cart</span>
                        В корзину
                      </button>
                    </div>
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
