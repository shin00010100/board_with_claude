// 게시글 API 클라이언트.
// 브라우저는 항상 Nginx와 같은 origin에서 페이지를 로드하므로 절대 경로가
// 아닌 상대 경로(/api/...)만 사용한다.

const API_BASE = "/api";

export interface Post {
  id: string;
  title: string;
  content: string;
  author: string;
  view_count: number;
  created_at: string;
  updated_at: string;
}

export interface PostListResponse {
  items: Post[];
  total: number;
  page: number;
  size: number;
}

export interface PostCreateInput {
  title: string;
  content: string;
  author: string;
  password: string;
}

export interface PostUpdateInput {
  title: string;
  content: string;
  author: string;
  password: string;
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });

  if (!response.ok) {
    const body: unknown = await response.json().catch(() => null);
    const detail =
      body !== null && typeof body === "object" && "detail" in body
        ? String((body as { detail: unknown }).detail)
        : `요청이 실패했습니다 (${response.status})`;
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export function fetchPosts(page: number): Promise<PostListResponse> {
  return request<PostListResponse>(`/posts?page=${page}`);
}

export function fetchPost(id: string): Promise<Post> {
  return request<Post>(`/posts/${id}`);
}

export function createPost(data: PostCreateInput): Promise<Post> {
  return request<Post>("/posts", { method: "POST", body: JSON.stringify(data) });
}

export function updatePost(id: string, data: PostUpdateInput): Promise<Post> {
  return request<Post>(`/posts/${id}`, { method: "PUT", body: JSON.stringify(data) });
}

export function deletePost(id: string, password: string): Promise<void> {
  return request<void>(`/posts/${id}`, {
    method: "DELETE",
    body: JSON.stringify({ password }),
  });
}
