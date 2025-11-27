import React, { useEffect, useState } from "react";
import { cartApi, orderApi } from "../api/client";
import { useAuth } from "../context/AuthContext";

type CartItem = {
  product_id: number;
  quantity: number;
  price: number;
};

type Cart = {
  user_id: number;
  items: CartItem[];
};

const CartPage: React.FC = () => {
  const { user } = useAuth();
  const [cart, setCart] = useState<Cart | null>(null);

  const load = async () => {
    const res = await cartApi.get<Cart>("/cart", {
      params: { user_id: user!.id },
    });
    setCart(res.data);
  };

  useEffect(() => {
    load();
  }, []);

  if (!cart || cart.items.length === 0) {
    return (
      <div className="card">
        <h2 className="page-title">Корзина</h2>
        <p className="text-muted">Корзина пуста</p>
      </div>
    );
  }

  const total = cart.items.reduce(
    (sum, i) => sum + i.price * i.quantity,
    0
  );

  const checkout = async () => {
    const res = await orderApi.post("/orders/from-cart", null, {
      params: { user_id: user!.id },
    });
    alert("Заказ создан: " + res.data.id);
    load();
  };

  return (
    <div className="card">
      <h2 className="page-title">Корзина</h2>
      <ul className="list-clean">
        {cart.items.map((i, idx) => (
          <li key={idx} style={{ marginBottom: 6 }}>
            Товар #{i.product_id} — {i.quantity} × {i.price} ₽
          </li>
        ))}
      </ul>
      <div className="divider" />
      <div className="card-header">
        <div className="card-subtitle">Итого</div>
        <div style={{ fontWeight: 600 }}>{total} ₽</div>
      </div>
      <button className="btn" onClick={checkout}>
        Оформить заказ
      </button>
    </div>
  );
};

export default CartPage;
