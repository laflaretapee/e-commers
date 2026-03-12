import { useEffect, useState } from "react";
import { aiApi } from "../../api/client";
import AdminShell from "../../components/AdminShell";
import { ErrorState, LoadingState } from "../../components/UiState";
import {
  type AIEvent,
  type ModerationDecision,
  formatPrice,
} from "../../lib/shop";

type DecisionHistory = {
  requestId: number;
  itemId: number | null;
  decision: string;
  reasonCode: string;
  confidence: number;
};

const baseForm = {
  item_id: 54921,
  seller_id: 1,
  title: "Смартфон Samsung Galaxy S23",
  description: "Новый смартфон в заводской упаковке. Гарантия от производителя 1 год. В комплекте кабель USB-C.",
  category_id: 1,
  price: 74990,
};

export default function AiModerationPage() {
  const [form] = useState(baseForm);
  const [history, setHistory] = useState<DecisionHistory[]>([]);
  const [currentDecision, setCurrentDecision] = useState<ModerationDecision | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    const loadHistory = async () => {
      setIsLoading(true);
      setError("");

      try {
        const response = await aiApi.get<AIEvent[]>("/events", { params: { limit: 200 } });
        if (!active) {
          return;
        }

        const decisions = response.data
          .filter((event) => event.event_type === "ModerationDecision")
          .slice(0, 5)
          .map((event) => {
            const payload = event.payload;
            return {
              requestId: Number(payload.request_id ?? 0),
              itemId: event.item_id,
              decision: String(payload.decision ?? "unknown"),
              reasonCode: String(payload.reason_code ?? "n/a"),
              confidence: Number(payload.confidence ?? 0),
            };
          });

        setHistory(decisions);
      } catch {
        if (active) {
          setError("Не удалось загрузить историю AI-модерации.");
        }
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    };

    void loadHistory();
    return () => {
      active = false;
    };
  }, []);

  const runCheck = async (mode: "approve" | "manual" | "reject") => {
    setError("");

    const payload =
      mode === "approve"
        ? {
            ...form,
          }
        : mode === "manual"
          ? {
              ...form,
              description: "Короткое описание",
              price: 0,
            }
          : {
              ...form,
              title: "Ставки casino premium",
              description: "Переходите на сайт и смотрите подробности",
            };

    try {
      const response = await aiApi.post<ModerationDecision>("/moderation/check", payload);
      setCurrentDecision(response.data);
      setHistory((previous) => [
        {
          requestId: response.data.request_id,
          itemId: payload.item_id,
          decision: response.data.decision,
          reasonCode: response.data.reason_code,
          confidence: response.data.confidence,
        },
        ...previous,
      ]);
    } catch {
      setError("Не удалось выполнить AI-проверку карточки.");
    }
  };

  return (
    <AdminShell subtitle="Очередь проверки карточек и демонстрация publish/manual_review/reject." title="AI Модерация товаров">
      {isLoading && <LoadingState title="Загружаем AI moderation queue" />}
      {!isLoading && error && <ErrorState description={error} title="Модерация недоступна" />}

      {!isLoading && !error && (
        <div className="moderation-layout">
          <section className="moderation-main-card">
            <div className="moderation-product-grid">
              <div className="moderation-product-visual">
                <div className="moderation-device-placeholder">
                  <span className="material-symbols-outlined">smartphone</span>
                </div>
              </div>

              <div className="moderation-product-copy">
                <span className="admin-tag">Электроника</span>
                <h1>{form.title}</h1>
                <p>Продавец: TechnoMir</p>
                <p>{form.description}</p>
                <strong>{formatPrice(form.price)}</strong>

                {currentDecision && (
                  <div className={`moderation-ai-result tone-${currentDecision.decision}`}>
                    <strong>AI решение: {currentDecision.decision}</strong>
                    <span>
                      confidence {(currentDecision.confidence * 100).toFixed(1)}% • {currentDecision.reason_code}
                    </span>
                  </div>
                )}
              </div>
            </div>

            <div className="moderation-action-card">
              <h3>Решение модератора</h3>
              <p>Кнопки ниже запускают разные сценарии AI-проверки для демонстрации всех исходов.</p>
              <div className="moderation-actions-row">
                <button className="approve-button" onClick={() => void runCheck("approve")} type="button">
                  Одобрить
                </button>
                <button className="review-button" onClick={() => void runCheck("manual")} type="button">
                  На доработку
                </button>
                <button className="reject-button" onClick={() => void runCheck("reject")} type="button">
                  Отклонить
                </button>
              </div>
            </div>
          </section>

          <aside className="moderation-history-card">
            <div className="section-heading">
              <h3>История решений</h3>
            </div>

            <div className="moderation-history-list">
              {history.map((item) => (
                <div key={`${item.requestId}-${item.itemId}`} className="moderation-history-item">
                  <div>
                    <strong>Item ID {item.itemId ?? "n/a"}</strong>
                    <p>request #{item.requestId}</p>
                    <span>{item.reasonCode}</span>
                  </div>
                  <span className={`status-pill ${item.decision === "publish" ? "success" : item.decision === "reject" ? "danger" : "warning"}`}>
                    {item.decision}
                  </span>
                </div>
              ))}
            </div>
          </aside>
        </div>
      )}
    </AdminShell>
  );
}
