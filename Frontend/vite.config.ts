import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// 브라우저는 항상 Nginx(8080)에만 접속하고, Nginx가 /와 /api/를 각각
// vite(5173)와 uvicorn(8000)으로 프록시한다. 따라서 이 설정에는
// server.proxy가 필요 없다 (vite가 /api의 존재를 알 필요가 없음).
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // 명시하지 않으면 환경에 따라 IPv6(::1)에만 바인딩되어 nginx의
    // proxy_pass http://127.0.0.1:5173 연결이 실패(502)할 수 있으므로 고정한다.
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    // vite HMR 웹소켓이 브라우저가 실제로 접속한 Nginx 포트로 나가도록 설정
    hmr: {
      clientPort: 8080,
    },
  },
});
