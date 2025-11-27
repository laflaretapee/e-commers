import axios from "axios";

export const authApi = axios.create({
  baseURL: "http://127.0.0.1:8001",
});

export const catalogApi = axios.create({
  baseURL: "http://127.0.0.1:8002",
});

export const cartApi = axios.create({
  baseURL: "http://127.0.0.1:8003",
});

export const orderApi = axios.create({
  baseURL: "http://127.0.0.1:8004",
});
