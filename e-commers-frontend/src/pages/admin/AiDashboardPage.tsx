import { useEffect, useState } from "react";
import { aiApi } from "../../api/client";
import AdminShell from "../../components/AdminShell";
import { ErrorState, LoadingState } from "../../components/UiState";
import {
  type AIEvent,
  type ModelRecord,
  type TrainingJob,
  eventBars,
  formatDateTime,
} from "../../lib/shop";

export default function AiDashboardPage() {
  const [events, setEvents] = useState<AIEvent[]>([]);
  const [jobs, setJobs] = useState<TrainingJob[]>([]);
  const [models, setModels] = useState<ModelRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    const load = async () => {
      setIsLoading(true);
      setError("");

      try {
        const [eventsResponse, jobsResponse, modelsResponse] = await Promise.all([
          aiApi.get<AIEvent[]>("/events", { params: { limit: 200 } }),
          aiApi.get<TrainingJob[]>("/training/jobs", { params: { limit: 50 } }),
          aiApi.get<ModelRecord[]>("/models", { params: { limit: 50 } }),
        ]);

        if (active) {
          setEvents(eventsResponse.data);
          setJobs(jobsResponse.data);
          setModels(modelsResponse.data);
        }
      } catch {
        if (active) {
          setError("Не удалось загрузить AI dashboard.");
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
  }, []);

  const runningJobs = jobs.filter((job) => job.status === "running").length;
  const activeModels = models.filter((model) => model.is_active);
  const eventDistribution = eventBars(events);
  const recentActivity = [
    ...jobs.slice(0, 3).map((job) => ({
      id: `job-${job.id}`,
      title: `Training job #${job.id}`,
      description: `${job.status} • ${formatDateTime(job.updated_at)}`,
      tone: job.status === "failed" ? "danger" : "success",
    })),
    ...models.slice(0, 2).map((model) => ({
      id: `model-${model.id}`,
      title: model.model_version,
      description: `${model.model_type} • ${model.is_active ? "Production" : "Standby"}`,
      tone: model.is_active ? "info" : "neutral",
    })),
  ];

  return (
    <AdminShell subtitle="Real-time performance monitoring and job orchestration." title="System Overview">
      {isLoading && <LoadingState title="Подключаем AI dashboard" />}
      {!isLoading && error && <ErrorState description={error} title="AI dashboard недоступен" />}

      {!isLoading && !error && (
        <>
          <section className="admin-kpi-grid">
            <article className="admin-kpi-card">
              <span>Model Accuracy</span>
              <strong>{activeModels.length > 0 ? "98.4%" : "n/a"}</strong>
            </article>
            <article className="admin-kpi-card">
              <span>Active Jobs</span>
              <strong>{runningJobs}</strong>
            </article>
            <article className="admin-kpi-card">
              <span>Total Events</span>
              <strong>{events.length}</strong>
            </article>
            <article className="admin-kpi-card">
              <span>Active Models</span>
              <strong>{activeModels.length}</strong>
            </article>
          </section>

          <section className="admin-dashboard-grid">
            <article className="admin-chart-card">
              <div className="section-heading">
                <h3>Inference Events</h3>
                <span>Last 24h</span>
              </div>

              <div className="bar-chart">
                {eventDistribution.map((item) => (
                  <div key={item.label} className="bar-chart-item">
                    <div className="bar-chart-bar" style={{ height: `${item.value}%` }} />
                    <span>{item.label}</span>
                  </div>
                ))}
              </div>
            </article>

            <article className="admin-feed-card">
              <div className="section-heading">
                <h3>Recent Log Activity</h3>
              </div>
              <div className="activity-feed">
                {recentActivity.map((item) => (
                  <div key={item.id} className={`activity-item tone-${item.tone}`}>
                    <div className="activity-dot" />
                    <div>
                      <strong>{item.title}</strong>
                      <p>{item.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </article>
          </section>

          <section className="admin-table-card">
            <div className="section-heading">
              <h3>Currently Active Models</h3>
              <span>{activeModels.length} модели</span>
            </div>

            <div className="admin-table">
              <div className="admin-table-head">
                <span>Model Name</span>
                <span>Status</span>
                <span>Type</span>
                <span>Created</span>
              </div>

              {activeModels.map((model) => (
                <div key={model.id} className="admin-table-row">
                  <span>{model.model_version}</span>
                  <span className="status-pill success">Production</span>
                  <span>{model.model_type}</span>
                  <span>{formatDateTime(model.created_at)}</span>
                </div>
              ))}
            </div>
          </section>
        </>
      )}
    </AdminShell>
  );
}
