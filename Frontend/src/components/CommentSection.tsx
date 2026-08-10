import { useEffect, useRef, useState, type FormEvent } from "react";
import { createComment, deleteComment, fetchComments, type Comment } from "../api/client";
import { formatDateTime } from "../lib/format";

interface CommentSectionProps {
  postId: string;
}

export default function CommentSection({ postId }: CommentSectionProps) {
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [author, setAuthor] = useState("");
  const [content, setContent] = useState("");
  const [password, setPassword] = useState("");
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [openDeleteId, setOpenDeleteId] = useState<string | null>(null);
  const [deletePassword, setDeletePassword] = useState("");
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // StrictMode 개발 모드의 effect 이중 실행으로 같은 postId에 대해
  // 목록 조회 요청이 두 번 나가지 않도록 막는다.
  const requestedPostIdRef = useRef<string | null>(null);

  useEffect(() => {
    if (requestedPostIdRef.current === postId) return;
    requestedPostIdRef.current = postId;

    setLoading(true);
    setLoadError(null);
    fetchComments(postId)
      .then((data) => {
        if (requestedPostIdRef.current === postId) setComments(data);
      })
      .catch((err: unknown) => {
        if (requestedPostIdRef.current === postId) {
          setLoadError(err instanceof Error ? err.message : "댓글을 불러오지 못했습니다");
        }
      })
      .finally(() => {
        if (requestedPostIdRef.current === postId) setLoading(false);
      });
  }, [postId]);

  async function handleSubmit(event: FormEvent): Promise<void> {
    event.preventDefault();
    setSubmitting(true);
    setSubmitError(null);
    try {
      const comment = await createComment(postId, { author, content, password });
      setComments((prev) => [...prev, comment]);
      setAuthor("");
      setContent("");
      setPassword("");
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "댓글 작성에 실패했습니다");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(commentId: string): Promise<void> {
    setDeletingId(commentId);
    setDeleteError(null);
    try {
      await deleteComment(postId, commentId, deletePassword);
      setComments((prev) => prev.filter((c) => c.id !== commentId));
      setOpenDeleteId(null);
      setDeletePassword("");
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : "댓글 삭제에 실패했습니다");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="mt-6 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="mb-4 text-lg font-bold text-slate-900">
        댓글{comments.length > 0 ? ` (${comments.length})` : ""}
      </h2>

      {loading && <p className="text-sm text-slate-400">불러오는 중...</p>}
      {!loading && loadError !== null && <p className="text-sm text-red-500">{loadError}</p>}
      {!loading && loadError === null && comments.length === 0 && (
        <p className="text-sm text-slate-400">첫 댓글을 남겨보세요.</p>
      )}

      <ul className="space-y-3">
        {comments.map((comment) => (
          <li key={comment.id} className="rounded-md bg-slate-50 p-3">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-baseline gap-2">
                <span className="font-medium text-slate-900">{comment.author}</span>
                <span className="text-xs text-slate-400">{formatDateTime(comment.created_at)}</span>
              </div>
              <button
                type="button"
                onClick={() => {
                  setOpenDeleteId((v) => (v === comment.id ? null : comment.id));
                  setDeletePassword("");
                  setDeleteError(null);
                }}
                className="text-xs text-red-500 hover:underline"
              >
                삭제
              </button>
            </div>
            <p className="mt-1 whitespace-pre-wrap text-sm text-slate-800">{comment.content}</p>

            {openDeleteId === comment.id && (
              <div className="mt-2 flex items-center gap-2">
                <input
                  type="password"
                  value={deletePassword}
                  onChange={(e) => setDeletePassword(e.target.value)}
                  placeholder="비밀번호 입력"
                  className="flex-1 rounded-md border border-slate-300 px-2 py-1 text-xs focus:border-slate-500 focus:outline-none"
                />
                <button
                  type="button"
                  onClick={() => void handleDelete(comment.id)}
                  disabled={deletingId === comment.id || deletePassword === ""}
                  className="rounded-md bg-red-600 px-3 py-1 text-xs font-medium text-white transition hover:bg-red-500 disabled:opacity-50"
                >
                  {deletingId === comment.id ? "삭제 중..." : "확인"}
                </button>
              </div>
            )}
            {openDeleteId === comment.id && deleteError !== null && (
              <p className="mt-1 text-xs text-red-500">{deleteError}</p>
            )}
          </li>
        ))}
      </ul>

      <form
        onSubmit={(e) => void handleSubmit(e)}
        className="mt-4 space-y-2 border-t border-slate-100 pt-4"
      >
        <div className="flex gap-2">
          <input
            value={author}
            onChange={(e) => setAuthor(e.target.value)}
            placeholder="작성자"
            required
            maxLength={50}
            className="w-32 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="비밀번호"
            required
            className="w-32 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
          />
        </div>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="댓글을 입력하세요"
          required
          rows={2}
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
        />
        {submitError !== null && <p className="text-sm text-red-500">{submitError}</p>}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={submitting}
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-700 disabled:opacity-50"
          >
            {submitting ? "등록 중..." : "댓글 등록"}
          </button>
        </div>
      </form>
    </div>
  );
}
