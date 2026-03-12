import type { ReactNode } from "react";

type CardStateProps = {
  title: string;
  description: string;
  action?: ReactNode;
};

export function LoadingState({ title = "Загрузка интерфейса" }: { title?: string }) {
  return (
    <div className="state-card">
      <div className="state-spinner" />
      <h3>{title}</h3>
      <p>Подтягиваем данные из сервисов и готовим страницу.</p>
    </div>
  );
}

export function ErrorState({ title, description, action }: CardStateProps) {
  return (
    <div className="state-card is-error">
      <span className="material-symbols-outlined state-icon">error</span>
      <h3>{title}</h3>
      <p>{description}</p>
      {action}
    </div>
  );
}

export function EmptyState({ title, description, action }: CardStateProps) {
  return (
    <div className="state-card">
      <span className="material-symbols-outlined state-icon">inventory_2</span>
      <h3>{title}</h3>
      <p>{description}</p>
      {action}
    </div>
  );
}
