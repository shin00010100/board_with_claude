import { useEffect, useRef, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { fetchPost, updatePost } from "../api/client";

export default function BoardEdit() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [title, setTitle] = useState("");
  const [author, setAuthor] = useState("");
  const [content, setContent] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // GET 조회가 서버에서 조회수를 증가시키므로, StrictMode 개발 모드의 effect
  // 이중 실행으로 같은 id에 대해 요청이 두 번 나가지 않도록 막는다.
  const requestedIdRef = useRef<string | null>(null);

  useEffect(() => {
    if (id === undefined) return;
    if (requestedIdRef.current === id) return;
    requestedIdRef.current = id;

    fetchPost(id)
      .then((post) => {
        if (requestedIdRef.current !== id) return;
        setTitle(post.title);
        setAuthor(post.author);
        setContent(post.content);
      })
      .catch((err: unknown) => {
        if (requestedIdRef.current === id) {
          setLoadError(err instanceof Error ? err.message : "게시글을 불러오지 못했습니다");
        }
      })
      .finally(() => {
        if (requestedIdRef.current === id) setLoading(false);
      });
  }, [id]);

  async function handleSubmit(event: FormEvent): Promise<void> {
    event.preventDefault();
    if (id === undefined) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      await updatePost(id, { title, author, content, password });
      navigate(`/posts/${id}`);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "수정에 실패했습니다");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-10 text-center text-slate-400">불러오는 중...</div>
    );
  }

  if (loadError !== null) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-10 text-center">
        <p className="text-red-500">{loadError}</p>
        <Link to="/" className="mt-4 inline-block text-sm text-slate-500 hover:underline">
          목록으로
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-10">
      <h1 className="mb-6 text-2xl font-bold text-slate-900">글 수정</h1>
      <form
        onSubmit={(e) => void handleSubmit(e)}
        className="space-y-4 rounded-lg border border-slate-200 bg-white p-6 shadow-sm"
      >
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">제목</label>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            maxLength={100}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">작성자</label>
          <input
            value={author}
            onChange={(e) => setAuthor(e.target.value)}
            required
            maxLength={50}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">내용</label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            required
            rows={10}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">비밀번호 확인</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
          />
        </div>

        {submitError !== null && <p className="text-sm text-red-500">{submitError}</p>}

        <div className="flex justify-end gap-2 pt-2">
          <Link
            to={`/posts/${id ?? ""}`}
            className="rounded-md px-4 py-2 text-sm text-slate-600 hover:bg-slate-100"
          >
            취소
          </Link>
          <button
            type="submit"
            disabled={submitting}
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-700 disabled:opacity-50"
          >
            {submitting ? "저장 중..." : "저장"}
          </button>
        </div>
      </form>
    </div>
  );
}
