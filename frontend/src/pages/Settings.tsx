import { useState, useEffect } from "react";
import api from "@/lib/api";

export default function Settings() {
  const [appid, setAppid] = useState("");
  const [appsecret, setAppsecret] = useState("");
  const [configured, setConfigured] = useState(false);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    api.get("/config").then((res) => {
      if (res.data.code === 0) {
        const d = res.data.data;
        setAppid(d.appid || "");
        setConfigured(d.configured);
      }
    });
  }, []);

  const save = async () => {
    setSaving(true);
    setMsg("");
    try {
      await api.put("/config", { appid, appsecret });
      setMsg("保存成功");
      setConfigured(true);
    } catch {
      setMsg("保存失败");
    }
    setSaving(false);
  };

  return (
    <div className="p-8 max-w-lg mx-auto">
      <h1 className="text-xl font-semibold mb-6">微信公众号配置</h1>
      <div className="space-y-4">
        <div>
          <label className="block text-sm text-fg-secondary mb-1">AppID</label>
          <input
            value={appid}
            onChange={(e) => setAppid(e.target.value)}
            className="w-full px-3 py-2 bg-surface-secondary border border-border rounded-lg text-sm text-fg-primary outline-none focus:border-accent"
            placeholder="wx..."
          />
        </div>
        <div>
          <label className="block text-sm text-fg-secondary mb-1">AppSecret</label>
          <input
            value={appsecret}
            onChange={(e) => setAppsecret(e.target.value)}
            type="password"
            className="w-full px-3 py-2 bg-surface-secondary border border-border rounded-lg text-sm text-fg-primary outline-none focus:border-accent"
            placeholder={configured ? "已配置（输入新值覆盖）" : "输入 AppSecret"}
          />
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={save}
            disabled={saving}
            className="px-4 py-2 bg-accent hover:bg-accent-hover text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
          >
            {saving ? "保存中..." : "保存"}
          </button>
          {msg && <span className="text-sm text-success">{msg}</span>}
          {configured && <span className="text-xs text-fg-muted">&#10003; 已配置</span>}
        </div>
      </div>
    </div>
  );
}
