import { Shield, Save } from "lucide-react";
import Button from "@/components/ui/Button";

interface WechatConfigSectionProps {
  appid: string;
  appsecret: string;
  proxyUrl: string;
  configured: boolean;
  saving: boolean;
  onAppidChange: (v: string) => void;
  onAppsecretChange: (v: string) => void;
  onProxyUrlChange: (v: string) => void;
  onSave: () => void;
  message?: string;
}

export default function WechatConfigSection({
  appid,
  appsecret,
  proxyUrl,
  configured,
  saving,
  onAppidChange,
  onAppsecretChange,
  onProxyUrlChange,
  onSave,
  message,
}: WechatConfigSectionProps) {
  return (
    <div className="flex flex-col gap-6">
      {/* Title block */}
      <div className="flex flex-col gap-1">
        <h2 className="text-[22px] font-bold text-fg-primary">微信公众号配置</h2>
        <p className="text-[13px] text-fg-muted">连接你的微信公众号，一键推送文章到草稿箱</p>
      </div>

      {/* Card */}
      <div className="bg-surface-secondary rounded-xl border border-border-primary p-6 flex flex-col gap-5">
        {/* Status row */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span
              className={`w-2 h-2 rounded-full ${
                configured ? "bg-[#3A9E7E]" : "bg-fg-muted"
              }`}
            />
            <span
              className={`text-[13px] ${
                configured ? "text-[#3A9E7E]" : "text-fg-muted"
              }`}
            >
              {configured ? "已连接微信公众号" : "未连接"}
            </span>
          </div>
          <button className="border border-border-secondary rounded-md px-2.5 py-1 text-[12px] text-fg-secondary hover:bg-surface-tertiary transition-colors cursor-pointer">
            去设置
          </button>
        </div>

        {/* Divider */}
        <div className="h-px w-full bg-border-primary" />

        {/* AppID field */}
        <div className="flex flex-col gap-1.5">
          <label className="text-[12px] font-semibold text-fg-secondary">AppID</label>
          <input
            value={appid}
            onChange={(e) => onAppidChange(e.target.value)}
            placeholder="wx..."
            className="bg-surface-tertiary border border-border-secondary rounded-lg px-3.5 py-2.5 text-[13px] text-fg-primary placeholder:text-fg-muted outline-none focus:border-accent transition-colors"
          />
        </div>

        {/* AppSecret field */}
        <div className="flex flex-col gap-1.5">
          <label className="text-[12px] font-semibold text-fg-secondary">AppSecret</label>
          <input
            value={appsecret}
            onChange={(e) => onAppsecretChange(e.target.value)}
            type="password"
            placeholder={configured ? "已配置（输入新值覆盖）" : "输入 AppSecret"}
            className="bg-surface-tertiary border border-border-secondary rounded-lg px-3.5 py-2.5 text-[13px] text-fg-primary placeholder:text-fg-muted outline-none focus:border-accent transition-colors"
          />
        </div>

        {/* Proxy URL field */}
        <div className="flex flex-col gap-1.5">
          <label className="text-[12px] font-semibold text-fg-secondary">
            API 代理地址
            <span className="ml-1 text-[11px] font-normal text-fg-muted">(可选)</span>
          </label>
          <input
            value={proxyUrl}
            onChange={(e) => onProxyUrlChange(e.target.value)}
            placeholder="https://your-proxy-server:port"
            className="bg-surface-tertiary border border-border-secondary rounded-lg px-3.5 py-2.5 text-[13px] text-fg-primary placeholder:text-fg-muted outline-none focus:border-accent transition-colors"
          />
          <span className="text-[11px] text-fg-muted">
            所有微信 API 请求将通过此代理发出，用于本地开发时满足 IP 白名单要求
          </span>
        </div>

        {/* Divider */}
        <div className="h-px w-full bg-border-primary" />

        {/* Warning box */}
        <div className="flex items-center gap-2 w-full bg-[#C9923E0D] border border-[#C9923E33] rounded-lg p-3 px-3.5">
          <Shield size={16} className="text-[#C9923E] flex-shrink-0" />
          <span className="text-[12px] text-[#C9923ECC]">
            凭据仅存储在本地服务器，不会上传至任何第三方
          </span>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3">
          {message && <span className="text-[13px] text-fg-muted">{message}</span>}
          <Button
            onClick={onSave}
            loading={saving}
            icon={<Save size={14} />}
            className="px-6 py-2.5 text-[13px] font-medium rounded-lg gap-1.5"
          >
            {saving ? "保存中..." : "保存"}
          </Button>
        </div>
      </div>
    </div>
  );
}
