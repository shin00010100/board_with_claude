import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { fetchPosts, type Post } from "../api/client";
import { formatDateTime } from "../lib/format";

export default function BoardList() {
  const [searchParams, setSearchParams] = useSearchParams();
  const page = Math.max(1, Number(searchParams.get("page") ?? "1"));

  const [posts, setPosts] = useState<Post[]>([]);
  const [total, setTotal] = useState(0);
  const [size, setSize] = useState(10);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetchPosts(page)
      .then((res) => {
        if (cancelled) return;
        setPosts(res.items);
        setTotal(res.total);
        setSize(res.size);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "목록을 불러오지 못했습니다");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [page]);

  const totalPages = Math.max(1, Math.ceil(total / size));

  function goToPage(next: number): void {
    setSearchParams(next === 1 ? {} : { page: String(next) });
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">게시판</h1>
        <Link
          to="/posts/new"
          className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-700"
        >
          글쓰기
        </Link>
      </div>

      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-slate-500">
            <tr>
              <th className="w-16 px-4 py-3 font-medium">번호</th>
              <th className="px-4 py-3 font-medium">제목</th>
              <th className="w-32 px-4 py-3 font-medium">작성자</th>
              <th className="w-40 px-4 py-3 font-medium">작성일</th>
              <th className="w-20 px-4 py-3 font-medium">조회</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading && (
              <tr>
                <td colSpan={5} className="px-4 py-10 text-center text-slate-400">
                  불러오는 중...
                </td>
              </tr>
            )}
            {!loading && error && (
              <tr>
                <td colSpan={5} className="px-4 py-10 text-center text-red-500">
                  {error}
                </td>
              </tr>
            )}
            {!loading && !error && posts.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-10 text-center text-slate-400">
                  등록된 게시글이 없습니다
                </td>
              </tr>
            )}
            {!loading &&
              !error &&
              posts.map((post, index) => (
                <tr key={post.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3 text-slate-400">
                    {total - ((page - 1) * size + index)}
                  </td>
                  <td className="px-4 py-3">
                    <Link to={`/posts/${post.id}`} className="text-slate-900 hover:underline">
                      {post.title}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-slate-600">{post.author}</td>
                  <td className="px-4 py-3 text-slate-500">{formatDateTime(post.created_at)}</td>
                  <td className="px-4 py-3 text-slate-500">{post.view_count}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="mt-6 flex justify-center gap-1">
          {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => goToPage(p)}
              className={`h-8 w-8 rounded-md text-sm transition ${
                p === page ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
