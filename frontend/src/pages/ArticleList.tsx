import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, FileText, Trash2 } from "lucide-react";
import api from "@/lib/api";
import type { ArticleSummary } from "@/types";

export default function ArticleList() {
  const navigate = useNavigate();
  const [articles, setArticles] = useState<ArticleSummary[]>([]);

  const load = () => {
    api.get("/articles").then((res) => {
      if (res.data.code === 0) setArticles(res.data.data);
    });
  };

  useEffect(() => { load(); }, []);

  const createArticle = async () => {
    const res = await api.post("/articles", { title: "未命名文章", mode: "html" });
    if (res.data.code === 0) {
      navigate(`/editor/${res.data.data.id}`);
    }
  };

  const deleteArticle = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    await api.delete(`/articles/${id}`);
    load();
  };

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold">文章列表</h1>
        <button
          onClick={createArticle}
          className="flex items-center gap-2 px-4 py-2 bg-accent hover:bg-accent-hover text-white rounded-lg text-sm font-medium transition-colors"
        >
          <Plus size={16} /> 新建文章
        </button>
      </div>

      {articles.length === 0 ? (
        <div className="text-center text-fg-muted py-20">暂无文章，点击上方按钮创建</div>
      ) : (
        <div className="space-y-2">
          {articles.map((a) => (
            <div
              key={a.id}
              onClick={() => navigate(`/editor/${a.id}`)}
              className="flex items-center justify-between p-4 rounded-xl bg-surface-secondary hover:bg-surface-tertiary cursor-pointer transition-colors"
            >
              <div className="flex items-center gap-3">
                <FileText size={18} className="text-fg-muted" />
                <div>
                  <div className="text-sm font-medium">{a.title}</div>
                  <div className="text-xs text-fg-muted mt-0.5">
                    {a.mode.toUpperCase()} · {new Date(a.updated_at).toLocaleString("zh-CN")}
                  </div>
                </div>
              </div>
              <button
                onClick={(e) => deleteArticle(a.id, e)}
                className="p-2 rounded-lg hover:bg-surface-primary text-fg-muted hover:text-error transition-colors"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
