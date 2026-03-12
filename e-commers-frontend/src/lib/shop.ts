export type Product = {
  id: number;
  title: string;
  description: string | null;
  price: number;
  stock: number;
  seller_id: number;
  image_url: string | null;
};

export type User = {
  id: number;
  email: string;
  full_name: string;
  role: string;
};

export type CartLine = {
  product_id: number;
  quantity: number;
  price: number;
};

export type RecommendationItem = {
  item_id: number;
  score: number;
  reason?: string | null;
};

export type RecommendationResponse = {
  request_id: number;
  user_id: number;
  context: string;
  model_version: string;
  latency_ms: number;
  items: RecommendationItem[];
};

export type CartResponse = {
  user_id: number;
  items: CartLine[];
  recommendations: RecommendationItem[];
};

export type OrderItem = {
  id: number;
  product_id: number;
  quantity: number;
  price: number;
};

export type Order = {
  id: number;
  user_id: number;
  status: string;
  total_amount: number;
  created_at: string;
  items: OrderItem[];
};

export type AIEvent = {
  id: number;
  event_type: string;
  user_id: number | null;
  item_id: number | null;
  order_id: number | null;
  session_id: string | null;
  ts: string;
  payload: Record<string, unknown>;
};

export type TrainingJob = {
  id: number;
  job_type: string;
  status: string;
  parameters: Record<string, unknown>;
  metrics: Record<string, unknown>;
  error_text: string | null;
  created_at: string;
  updated_at: string;
};

export type ModelRecord = {
  id: number;
  model_type: string;
  model_version: string;
  metrics: Record<string, unknown>;
  artifact_uri: string;
  is_active: boolean;
  created_at: string;
};

export type ModerationDecision = {
  request_id: number;
  decision: "publish" | "manual_review" | "reject";
  confidence: number;
  reason_code: string;
  model_version: string;
};

type ProductTheme = {
  icon: string;
  category: string;
  background: string;
  accent: string;
};

const THEME_RULES: Array<{ match: string[]; theme: ProductTheme }> = [
  {
    match: ["iphone", "смартф", "phone"],
    theme: {
      icon: "smartphone",
      category: "Смартфоны",
      background: "linear-gradient(145deg, #d7efe7 0%, #f6f4ef 100%)",
      accent: "#065bf9",
    },
  },
  {
    match: ["ноут", "laptop", "matebook", "macbook"],
    theme: {
      icon: "laptop_chromebook",
      category: "Ноутбуки",
      background: "linear-gradient(145deg, #f4e8de 0%, #f8f3ef 100%)",
      accent: "#ef4444",
    },
  },
  {
    match: ["науш", "head", "sony", "airpods"],
    theme: {
      icon: "headphones",
      category: "Аудио",
      background: "linear-gradient(145deg, #dce7f7 0%, #f8fafc 100%)",
      accent: "#0f766e",
    },
  },
  {
    match: ["часы", "watch"],
    theme: {
      icon: "watch",
      category: "Носимые устройства",
      background: "linear-gradient(145deg, #f9ecdf 0%, #fdf8f3 100%)",
      accent: "#ea580c",
    },
  },
  {
    match: ["клав", "keyboard"],
    theme: {
      icon: "keyboard",
      category: "Периферия",
      background: "linear-gradient(145deg, #e8ebf3 0%, #f8fafc 100%)",
      accent: "#475569",
    },
  },
  {
    match: ["мыш", "mouse"],
    theme: {
      icon: "mouse",
      category: "Периферия",
      background: "linear-gradient(145deg, #edf6ea 0%, #f8fafc 100%)",
      accent: "#16a34a",
    },
  },
  {
    match: ["рюкзак", "bagpack", "backpack"],
    theme: {
      icon: "backpack",
      category: "Аксессуары",
      background: "linear-gradient(145deg, #ece9f7 0%, #f8fafc 100%)",
      accent: "#7c3aed",
    },
  },
  {
    match: ["роут", "router"],
    theme: {
      icon: "router",
      category: "Сеть",
      background: "linear-gradient(145deg, #e1f0fb 0%, #f8fafc 100%)",
      accent: "#0284c7",
    },
  },
  {
    match: ["колон", "speaker"],
    theme: {
      icon: "speaker",
      category: "Аудио",
      background: "linear-gradient(145deg, #eaeff2 0%, #f8fafc 100%)",
      accent: "#334155",
    },
  },
  {
    match: ["планш", "tablet"],
    theme: {
      icon: "tablet_mac",
      category: "Планшеты",
      background: "linear-gradient(145deg, #dff0fb 0%, #f8fafc 100%)",
      accent: "#2563eb",
    },
  },
];

const DEFAULT_THEME: ProductTheme = {
  icon: "inventory_2",
  category: "Товары",
  background: "linear-gradient(145deg, #eef2f7 0%, #ffffff 100%)",
  accent: "#065bf9",
};

export function formatPrice(value: number): string {
  return `${value.toLocaleString("ru-RU")} ₽`;
}

export function formatDateTime(value: string): string {
  return new Date(value).toLocaleString("ru-RU", {
    day: "2-digit",
    month: "long",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatDateShort(value: string): string {
  return new Date(value).toLocaleDateString("ru-RU", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });
}

export function extractBrand(title: string): string {
  const parts = title.trim().split(/\s+/);
  return parts[1] ?? parts[0] ?? "Market";
}

export function inferProductTheme(title: string): ProductTheme {
  const lower = title.toLowerCase();
  return THEME_RULES.find((rule) => rule.match.some((token) => lower.includes(token)))?.theme ?? DEFAULT_THEME;
}

export function inferCategory(title: string): string {
  return inferProductTheme(title).category;
}

export function ratingForProduct(productId: number): number {
  return 4 + ((productId * 7) % 9) / 10;
}

export function reviewCountForProduct(productId: number): number {
  return 20 + ((productId * 37) % 1500);
}

export function oldPriceForProduct(product: Product): number | null {
  const multiplier = 1.06 + ((product.id % 5) * 0.03);
  const oldPrice = Math.round(product.price * multiplier);
  return oldPrice > product.price ? oldPrice : null;
}

export function discountLabel(product: Product): string | null {
  const oldPrice = oldPriceForProduct(product);
  if (!oldPrice) {
    return null;
  }

  const discount = Math.round(((oldPrice - product.price) / oldPrice) * 100);
  if (discount < 5) {
    return null;
  }

  return `-${discount}%`;
}

export function buildProductSpecs(product: Product): Array<[string, string]> {
  const category = inferCategory(product.title);
  const memory = ["128 ГБ", "256 ГБ", "512 ГБ"][product.id % 3];
  const color = ["Графитовый", "Синий", "Титановый", "Белый"][product.id % 4];
  const battery = `${3600 + (product.id % 6) * 250} мАч`;

  return [
    ["Категория", category],
    ["Бренд", extractBrand(product.title)],
    ["Складской остаток", `${product.stock} шт.`],
    ["Артикул", `SKU-${product.id.toString().padStart(5, "0")}`],
    ["Память", memory],
    ["Цвет", color],
    ["Питание", battery],
  ];
}

export function reasonLabel(reason?: string | null): string {
  const labels: Record<string, string> = {
    popular: "Популярный товар",
    price_drop: "Снижение цены",
    new_arrival: "Новая позиция",
    similar_items: "Похожий товар",
  };

  if (!reason) {
    return "AI подбор";
  }

  return labels[reason] ?? reason.replaceAll("_", " ");
}

export function orderStatusLabel(status: string): string {
  if (status === "created") {
    return "Оформлен";
  }
  return status;
}

export function eventBars(events: AIEvent[]): Array<{ label: string; value: number }> {
  const byHour = new Map<number, number>();

  for (const event of events) {
    const hour = new Date(event.ts).getHours();
    byHour.set(hour, (byHour.get(hour) ?? 0) + 1);
  }

  const items = Array.from({ length: 12 }, (_, index) => {
    const hour = (index * 2) % 24;
    return {
      label: `${hour.toString().padStart(2, "0")}:00`,
      value: byHour.get(hour) ?? 0,
    };
  });

  const max = Math.max(...items.map((item) => item.value), 1);
  return items.map((item) => ({
    label: item.label,
    value: Math.max(8, Math.round((item.value / max) * 100)),
  }));
}

export function trainingMetricValue(job: TrainingJob, key: string): string {
  const value = job.metrics[key];
  if (typeof value === "number") {
    return value.toFixed(2);
  }
  if (typeof value === "string") {
    return value;
  }
  return "n/a";
}
