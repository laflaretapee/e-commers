import { useEffect, useState } from "react";
import { aiApi, catalogApi } from "../../api/client";
import AdminShell from "../../components/AdminShell";
import { ErrorState, LoadingState } from "../../components/UiState";
import {
  type ModelRecord,
  type Product,
  type RecommendationResponse,
  formatPrice,
  reasonLabel,
} from "../../lib/shop";

type RecommendationContext = "catalog" | "product" | "cart";

export default function AiRecommendationsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [models, setModels] = useState<ModelRecord[]>([]);
  const [preview, setPreview] = useState<RecommendationResponse | null>(null);
  const [userId, setUserId] = useState("1");
  const [itemId, setItemId] = useState("");
  const [context, setContext] = useState<RecommendationContext>("catalog");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  const load = async () => {
    setIsLoading(true);
    setError("");

    try {
      const [productsResponse, modelsResponse] = await Promise.all([
        catalogApi.get<Product[]>("/products"),
        aiApi.get<ModelRecord[]>("/models", { params: { model_type: "recommendation", limit: 30 } }),
      ]);

      setProducts(productsResponse.data);
      setModels(modelsResponse.data);
    } catch {
      setError("Не удалось загрузить витрину рекомендаций.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const productMap = new Map(products.map((product) => [product.id, product]));
  const activeModel = models.find((model) => model.is_active) ?? null;

  const previewRecommendations = async () => {
    setNotice("");
    setError("");

    try {
      const response = await aiApi.get<RecommendationResponse>("/recommendations", {
        params: {
          user_id: Number(userId),
          context,
          item_id: itemId ? Number(itemId) : undefined,
          limit: 5,
        },
      });

      setPreview(response.data);
      setNotice("Preview рекомендаций обновлен.");
    } catch {
      setError("Не удалось получить рекомендации для выбранного пользователя.");
    }
  };

  const activateModel = async (modelId: number) => {
    setNotice("");
    setError("");

    try {
      await aiApi.post(`/models/${modelId}/activate`);
      setNotice("Активная recommendation-модель обновлена.");
      await load();
    } catch {
      setError("Не удалось активировать выбранную модель.");
    }
  };

  return (
    <AdminShell subtitle="Управление активной recommendation-моделью и preview выдачи." title="Настройка рекомендаций">
      {isLoading && <LoadingState title="Загружаем recommendation center" />}
      {!isLoading && error && <ErrorState description={error} title="Recommendation console недоступна" />}

      {!isLoading && !error && (
        <>
          {notice && <div className="inline-notice">{notice}</div>}

          <div className="recommendations-admin-layout">
            <section className="admin-chart-card">
              <div className="section-heading">
                <h3>CTR Recommendation Blocks</h3>
                <button className="secondary-button slim" onClick={() => void previewRecommendations()} type="button">
                  Preview Store
                </button>
              </div>

              <div className="recommendation-preview-form">
                <label>
                  <span>User ID</span>
                  <input onChange={(event) => setUserId(event.target.value)} value={userId} />
                </label>
                <label>
                  <span>Context</span>
                  <select onChange={(event) => setContext(event.target.value as RecommendationContext)} value={context}>
                    <option value="catalog">catalog</option>
                    <option value="product">product</option>
                    <option value="cart">cart</option>
                  </select>
                </label>
                <label>
                  <span>Item ID</span>
                  <input onChange={(event) => setItemId(event.target.value)} placeholder="опционально" value={itemId} />
                </label>
              </div>

              <div className="recommendation-preview-results">
                {(preview?.items ?? []).map((item) => (
                  <div key={item.item_id} className="recommendation-preview-item">
                    <strong>{productMap.get(item.item_id)?.title ?? `Товар #${item.item_id}`}</strong>
                    <span>{reasonLabel(item.reason)}</span>
                    <span>score {item.score.toFixed(3)}</span>
                  </div>
                ))}
              </div>
            </section>

            <aside className="toggle-stack-card">
              <div className="toggle-card is-active">
                <div>
                  <strong>AI-based Recommendations</strong>
                  <span>{activeModel?.model_version ?? "heuristic-v1"}</span>
                </div>
                <div className="toggle-ui is-on" />
              </div>
              <div className="toggle-card">
                <div>
                  <strong>Best Sellers</strong>
                  <span>Каталог подключен</span>
                </div>
                <div className="toggle-ui is-on" />
              </div>
              <div className="toggle-card">
                <div>
                  <strong>Recently Viewed</strong>
                  <span>Работает через AI events</span>
                </div>
                <div className="toggle-ui is-on" />
              </div>
            </aside>
          </div>

          <section className="admin-table-card">
            <div className="section-heading">
              <h3>Available Recommendation Models</h3>
              <span>{models.length} моделей</span>
            </div>

            <div className="admin-table">
              <div className="admin-table-head">
                <span>Version</span>
                <span>Status</span>
                <span>Artifact</span>
                <span>Action</span>
              </div>

              {models.map((model) => (
                <div key={model.id} className="admin-table-row">
                  <span>{model.model_version}</span>
                  <span className={`status-pill ${model.is_active ? "success" : "neutral"}`}>
                    {model.is_active ? "Production" : "Standby"}
                  </span>
                  <span>{model.artifact_uri}</span>
                  <button className="secondary-button slim" onClick={() => void activateModel(model.id)} type="button">
                    Активировать
                  </button>
                </div>
              ))}
            </div>
          </section>

          <section className="admin-table-card">
            <div className="section-heading">
              <h3>'Hero' Featured Products</h3>
              <span>Топ каталога</span>
            </div>

            <div className="admin-table">
              <div className="admin-table-head">
                <span>Product</span>
                <span>Category</span>
                <span>Inventory</span>
                <span>Price</span>
              </div>

              {products.slice(0, 5).map((product) => (
                <div key={product.id} className="admin-table-row">
                  <span>{product.title}</span>
                  <span>{product.seller_id}</span>
                  <span>{product.stock} in stock</span>
                  <span>{formatPrice(product.price)}</span>
                </div>
              ))}
            </div>
          </section>
        </>
      )}
    </AdminShell>
  );
}
