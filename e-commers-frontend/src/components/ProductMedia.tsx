import type { CSSProperties } from "react";
import type { Product } from "../lib/shop";
import { extractBrand, inferProductTheme } from "../lib/shop";

type ProductMediaProps = {
  product: Product;
  size?: "card" | "hero" | "thumb";
};

const letters = (title: string): string => {
  const words = title.split(/\s+/).filter(Boolean);
  return words.slice(0, 2).map((word) => word[0]?.toUpperCase() ?? "").join("");
};

export default function ProductMedia({ product, size = "card" }: ProductMediaProps) {
  const theme = inferProductTheme(product.title);
  const style = {
    "--media-bg": theme.background,
    "--media-accent": theme.accent,
  } as CSSProperties;

  return (
    <div className={`product-media product-media-${size}`} style={style}>
      <div className="product-media-orb" />
      <div className="product-media-frame">
        <span className="material-symbols-outlined product-media-icon">{theme.icon}</span>
      </div>
      <div className="product-media-badge">{extractBrand(product.title)}</div>
      <div className="product-media-letters">{letters(product.title)}</div>
    </div>
  );
}
