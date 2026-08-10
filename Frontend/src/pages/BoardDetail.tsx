import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { deletePost, fetchPost, type Post } from "../api/client";
import { formatDateTime } from "../lib/format";

export default function BoardDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [post, setPost] = useState<Post | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deletePassword, setDeletePassword] = useState("");
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (id === undefined) return;
    let cancelled = false;
    setLoading(true);
    setLoadError(null);
    fetchPost(id)
      .then((data) => {
        if (!cancelled) setPost(data);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setLoadError(err instanceof Error ? err.message : "게시글을 불러오지 못했습니다");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  async function handleDelete(): Promise<void> {
    if (id === undefined) return;
    setDeleting(true);
    setDeleteError(null);
    try {
      await deletePost(id, deletePassword);
      navigate("/");
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : "삭제에 실패했습니다");
    } finally {
      setDeleting(false);
    }
  }

  if (loading) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10 text-center text-slate-400">불러오는 중...</div>
    );
  }

  if (loadError || post === null) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10 text-center">
        <p className="text-red-500">{loadError ?? "게시글을 찾을 수 없습니다"}</p>
        <Link to="/" className="mt-4 inline-block text-sm text-slate-500 hover:underline">
          목록으로
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="text-xl font-bold text-slate-900">{post.title}</h1>
        <div className="mt-2 flex gap-4 border-b border-slate-100 pb-4 text-sm text-slate-500">
          <span>{post.author}</span>
          <span>{formatDateTime(post.created_at)}</span>
          <span>조회 {post.view_count}</span>
        </div>
        <p className="whitespace-pre-wrap py-6 text-slate-800">{post.content}</p>

        <div className="flex justify-end gap-2 border-t border-slate-100 pt-4">
          <Link to="/" className="rounded-md px-4 py-2 text-sm text-slate-600 hover:bg-slate-100">
            목록
          </Link>
          <Link
            to={`/posts/${post.id}/edit`}
            className="rounded-md border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
          >
            수정
          </Link>
          <button
            type="button"
            onClick={() => setShowDeleteConfirm((v) => !v)}
            className="rounded-md border border-red-200 px-4 py-2 text-sm text-red-600 hover:bg-red-50"
          >
            삭제
          </button>
        </div>

        {showDeleteConfirm && (
          <div className="mt-4 flex items-center gap-2 rounded-md bg-slate-50 p-3">
            <input
              type="password"
              value={deletePassword}
              onChange={(e) => setDeletePassword(e.target.value)}
              placeholder="비밀번호 입력"
              className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
            />
            <button
              type="button"
              onClick={() => void handleDelete()}
              disabled={deleting || deletePassword === ""}
              className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-red-500 disabled:opacity-50"
            >
              {deleting ? "삭제 중..." : "확인"}
            </button>
          </div>
        )}
        {deleteError !== null && <p className="mt-2 text-sm text-red-500">{deleteError}</p>}
      </div>
    </div>
  );
}
