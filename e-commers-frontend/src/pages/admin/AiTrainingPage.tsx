import { useEffect, useState } from "react";
import { aiApi } from "../../api/client";
import AdminShell from "../../components/AdminShell";
import { ErrorState, LoadingState } from "../../components/UiState";
import {
  type ModelRecord,
  type TrainingJob,
  formatDateTime,
  trainingMetricValue,
} from "../../lib/shop";

type TrainingForm = {
  lookback_days: number;
  max_samples: number;
  min_samples: number;
  epochs: number;
  learning_rate: number;
  l2: number;
  min_positive_samples: number;
  activate_model: boolean;
  random_seed: number;
};

const initialForm: TrainingForm = {
  lookback_days: 90,
  max_samples: 1000,
  min_samples: 10,
  epochs: 5,
  learning_rate: 0.03,
  l2: 0.001,
  min_positive_samples: 1,
  activate_model: true,
  random_seed: 4322026,
};

export default function AiTrainingPage() {
  const [jobs, setJobs] = useState<TrainingJob[]>([]);
  const [models, setModels] = useState<ModelRecord[]>([]);
  const [form, setForm] = useState<TrainingForm>(initialForm);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = async () => {
    setIsLoading(true);
    setError("");

    try {
      const [jobsResponse, modelsResponse] = await Promise.all([
        aiApi.get<TrainingJob[]>("/training/jobs", { params: { limit: 30 } }),
        aiApi.get<ModelRecord[]>("/models", { params: { limit: 30 } }),
      ]);

      setJobs(jobsResponse.data);
      setModels(modelsResponse.data);
    } catch {
      setError("Не удалось загрузить training center.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const completedJobs = jobs.filter((job) => job.status === "completed").length;
  const successRate = jobs.length > 0 ? ((completedJobs / jobs.length) * 100).toFixed(1) : "0.0";
  const activeModels = models.filter((model) => model.is_active).length;

  const launchTraining = async () => {
    setIsSubmitting(true);
    setNotice("");
    setError("");

    try {
      await aiApi.post("/training/recommendation/run", form);
      setNotice("Recommendation training job успешно запущен.");
      await load();
    } catch {
      setError("Не удалось запустить recommendation training.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AdminShell subtitle="Запуск обучения, просмотр job-ов и оперативных метрик MLOps-контура." title="Training Jobs">
      {isLoading && <LoadingState title="Готовим training center" />}
      {!isLoading && error && <ErrorState description={error} title="Training center недоступен" />}

      {!isLoading && !error && (
        <>
          {notice && <div className="inline-notice">{notice}</div>}

          <div className="training-layout">
            <section className="training-form-card">
              <h3>Start New Training</h3>
              <p>Configure and launch a new training session.</p>

              <label>
                <span>Lookback Days</span>
                <input
                  onChange={(event) => setForm({ ...form, lookback_days: Number(event.target.value) })}
                  type="number"
                  value={form.lookback_days}
                />
              </label>

              <label>
                <span>Max Samples</span>
                <input
                  onChange={(event) => setForm({ ...form, max_samples: Number(event.target.value) })}
                  type="number"
                  value={form.max_samples}
                />
              </label>

              <div className="split-fields">
                <label>
                  <span>Learning Rate</span>
                  <input
                    onChange={(event) => setForm({ ...form, learning_rate: Number(event.target.value) })}
                    step="0.001"
                    type="number"
                    value={form.learning_rate}
                  />
                </label>
                <label>
                  <span>Epochs</span>
                  <input onChange={(event) => setForm({ ...form, epochs: Number(event.target.value) })} type="number" value={form.epochs} />
                </label>
              </div>

              <div className="compute-card selected">
                <strong>NVIDIA H100 (80GB)</strong>
                <span>Оптимально для recommendation training</span>
              </div>

              <button className="primary-button wide" disabled={isSubmitting} onClick={() => void launchTraining()} type="button">
                {isSubmitting ? "Launching..." : "Launch Training Job"}
              </button>

              <div className="usage-highlight-card">
                <span>Monthly Compute Usage</span>
                <strong>742.5 hrs</strong>
                <p>74% of 1000h quota used</p>
              </div>
            </section>

            <section className="training-jobs-card">
              <div className="section-heading">
                <h3>Training Jobs</h3>
                <span>{jobs.length} записей</span>
              </div>

              <div className="admin-table">
                <div className="admin-table-head">
                  <span>Job Info</span>
                  <span>Status</span>
                  <span>Metrics</span>
                  <span>Updated</span>
                </div>

                {jobs.map((job) => (
                  <div key={job.id} className="admin-table-row">
                    <span>
                      {job.job_type} #{job.id}
                    </span>
                    <span className={`status-pill ${job.status === "completed" ? "success" : job.status === "failed" ? "danger" : "info"}`}>
                      {job.status}
                    </span>
                    <span>
                      loss {trainingMetricValue(job, "loss_after")} • samples {trainingMetricValue(job, "sample_count")}
                    </span>
                    <span>{formatDateTime(job.updated_at)}</span>
                  </div>
                ))}
              </div>

              <div className="training-mini-stats">
                <div className="admin-kpi-card">
                  <span>Success Rate</span>
                  <strong>{successRate}%</strong>
                </div>
                <div className="admin-kpi-card">
                  <span>Active Models</span>
                  <strong>{activeModels}</strong>
                </div>
                <div className="admin-kpi-card">
                  <span>Queue Time</span>
                  <strong>4.2m</strong>
                </div>
              </div>
            </section>
          </div>
        </>
      )}
    </AdminShell>
  );
}
