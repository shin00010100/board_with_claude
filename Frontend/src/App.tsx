import { BrowserRouter, Route, Routes } from "react-router-dom";
import BoardList from "./pages/BoardList";
import BoardDetail from "./pages/BoardDetail";
import BoardWrite from "./pages/BoardWrite";
import BoardEdit from "./pages/BoardEdit";

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-50">
        <Routes>
          <Route path="/" element={<BoardList />} />
          <Route path="/posts/new" element={<BoardWrite />} />
          <Route path="/posts/:id" element={<BoardDetail />} />
          <Route path="/posts/:id/edit" element={<BoardEdit />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
