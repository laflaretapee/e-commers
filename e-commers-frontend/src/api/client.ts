import axios from "axios";

export const authApi = axios.create({
  baseURL: "http://127.0.0.1:8001",
  timeout: 12000,
});

export const catalogApi = axios.create({
  baseURL: "http://127.0.0.1:8002",
  timeout: 12000,
});

export const cartApi = axios.create({
  baseURL: "http://127.0.0.1:8003",
  timeout: 12000,
});

export const orderApi = axios.create({
  baseURL: "http://127.0.0.1:8004",
  timeout: 12000,
});

export const aiApi = axios.create({
  baseURL: "http://127.0.0.1:8006",
  timeout: 18000,
});
