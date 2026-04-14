import { useState, useEffect } from "react";
import api from "@/lib/api";
import SettingsHeader from "@/components/layout/SettingsHeader";
import SettingsSidebar from "@/components/settings/SettingsSidebar";
import WechatConfigSection from "@/components/settings/WechatConfigSection";
import AppearanceSection from "@/components/settings/AppearanceSection";
import EditorPreferencesSection from "@/components/settings/EditorPreferencesSection";
import KeyboardShortcutsSection from "@/components/settings/KeyboardShortcutsSection";
import AboutSection from "@/components/settings/AboutSection";
import { useTheme } from "@/hooks/useTheme";

export default function Settings() {
  const [appid, setAppid] = useState("");
  const [appsecret, setAppsecret] = useState("");
  const [proxyUrl, setProxyUrl] = useState("");
  const [configured, setConfigured] = useState(false);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");
  const [activeSection, setActiveSection] = useState("wechat");
  const { theme, setTheme } = useTheme();

  useEffect(() => {
    api.get("/config").then((res) => {
      if (res.data.code === 0) {
        const d = res.data.data;
        setAppid(d.appid || "");
        setProxyUrl(d.proxy_url || "");
        setConfigured(d.configured);
      }
    });
  }, []);

  const save = async () => {
    setSaving(true);
    setMsg("");
    try {
      await api.put("/config", { appid, appsecret, proxy_url: proxyUrl });
      setMsg("保存成功");
      setConfigured(true);
    } catch {
      setMsg("保存失败");
    }
    setSaving(false);
  };

  return (
    <div className="h-full flex flex-col bg-bg-primary">
      <SettingsHeader />

      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar - 240px */}
        <SettingsSidebar
          activeSection={activeSection}
          onSectionChange={setActiveSection}
        />

        {/* Main content */}
        <div className="flex-1 overflow-y-auto px-12 py-8">
          <div className="max-w-[600px] flex flex-col gap-6">
            {activeSection === "wechat" && (
              <WechatConfigSection
                appid={appid}
                appsecret={appsecret}
                proxyUrl={proxyUrl}
                configured={configured}
                saving={saving}
                onAppidChange={setAppid}
                onAppsecretChange={handleAppsecretChange}
                onProxyUrlChange={setProxyUrl}
                onSave={save}
                message={msg}
              />
            )}
            {activeSection === "appearance" && (
              <AppearanceSection
                theme={theme}
                onThemeChange={setTheme}
              />
            )}
            {activeSection === "editor" && <EditorPreferencesSection />}
            {activeSection === "shortcuts" && <KeyboardShortcutsSection />}
            {activeSection === "about" && <AboutSection />}
          </div>
        </div>
      </div>
    </div>
  );
}
