import React, { useEffect, useState } from "react";
import { catalogApi, cartApi } from "../api/client";
import { useAuth } from "../context/AuthContext";

type Product = {
  id: number;
  title: string;
  description: string | null;
  price: number;
  stock: number;
  seller_id: number;
  image_url: string | null;
};

const defaultImage =
  "https://images.pexels.com/photos/3738733/pexels-photo-3738733.jpeg?auto=compress&cs=tinysrgb&w=1200";

const CatalogPage: React.FC = () => {
  const { user } = useAuth();
  const [products, setProducts] = useState<Product[]>([]);

  useEffect(() => {
    catalogApi.get<Product[]>("/products").then((res) => setProducts(res.data));
  }, []);

  const addToCart = async (p: Product) => {
    if (!user) {
      alert("Сначала войдите");
      return;
    }
    await cartApi.post(
      "/cart/add",
      {
        product_id: p.id,
        quantity: 1,
        price: p.price,
      },
      { params: { user_id: user.id } }
    );
    alert("Добавлено в корзину");
  };

  return (
    <div>
      <h2 className="page-title">Каталог</h2>

      {products.length === 0 && (
        <p className="text-muted">Товаров пока нет. Добавь через Swagger.</p>
      )}

      <div className="product-grid">
        {products.map((p) => (
          <div key={p.id} className="product-card">
            <div className="product-card-image">
              <img src={p.image_url || defaultImage} alt={p.title} />
            </div>

            <div className="product-card-body">
              <div className="card-header">
                <div>
                  <div className="card-title">{p.title}</div>
                  {p.description && (
                    <div className="card-subtitle">
                      {p.description.length > 80
                        ? p.description.slice(0, 80) + "…"
                        : p.description}
                    </div>
                  )}
                </div>
              </div>

              <div className="product-card-footer">
                <div className="price-pill">{p.price} ₽</div>
                <div className="stock-pill">В наличии: {p.stock}</div>
              </div>

              <button className="btn" style={{ marginTop: 10 }} onClick={() => addToCart(p)}>
                В корзину
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CatalogPage;
