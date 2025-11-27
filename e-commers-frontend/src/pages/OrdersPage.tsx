import React, { useEffect, useState } from "react";
import { orderApi } from "../api/client";
import { useAuth } from "../context/AuthContext";

type OrderItem = {
  id: number;
  product_id: number;
  quantity: number;
  price: number;
};

type Order = {
  id: number;
  user_id: number;
  status: string;
  total_amount: number;
  created_at: string;
  items: OrderItem[];
};

const OrdersPage: React.FC = () => {
  const { user } = useAuth();
  const [orders, setOrders] = useState<Order[]>([]);

  useEffect(() => {
    orderApi
      .get<Order[]>("/orders", { params: { user_id: user!.id } })
      .then((res) => setOrders(res.data));
  }, []);

  return (
    <div>
      <h2 className="page-title">Мои заказы</h2>

      {orders.length === 0 && (
        <div className="card">
          <p className="text-muted">Пока заказов нет.</p>
        </div>
      )}

      <ul className="list-clean">
        {orders.map((o) => (
          <li key={o.id} className="card">
            <div className="card-header">
              <div>
                <div className="card-title">Заказ #{o.id}</div>
                <div className="card-subtitle">
                  {new Date(o.created_at).toLocaleString()}
                </div>
              </div>
              <div className="text-right">
                <div style={{ fontWeight: 600 }}>{o.total_amount} ₽</div>
                <div className="card-subtitle">Статус: {o.status}</div>
              </div>
            </div>

            <ul className="list-clean">
              {o.items.map((i) => (
                <li key={i.id} className="card-subtitle">
                  Товар #{i.product_id} — {i.quantity} × {i.price} ₽
                </li>
              ))}
            </ul>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default OrdersPage;
