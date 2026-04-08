import Editor, { type OnMount } from "@monaco-editor/react";
import { useRef, useImperativeHandle, forwardRef } from "react";
import { useTheme } from "@/hooks/useTheme";
import type * as monaco from "monaco-editor";

export interface MonacoEditorHandle {
  insertAtCursor: (text: string) => void;
}

interface MonacoEditorProps {
  value: string;
  onChange: (value: string) => void;
  language: string;
  height?: string;
}

const MonacoEditor = forwardRef<MonacoEditorHandle, MonacoEditorProps>(
  function MonacoEditor({ value, onChange, language, height = "100%" }, ref) {
    const { resolvedTheme } = useTheme();
    const editorRef = useRef<monaco.editor.IStandaloneCodeEditor | null>(null);

    const handleMount: OnMount = (editor) => {
      editorRef.current = editor;
    };

    useImperativeHandle(ref, () => ({
      insertAtCursor(text: string) {
        const editor = editorRef.current;
        if (!editor) return;
        const position = editor.getPosition();
        if (!position) return;
        const range = new (window as any).monaco.Range(
          position.lineNumber,
          position.column,
          position.lineNumber,
          position.column,
        );
        editor.executeEdits("insert", [{ range, text, forceMoveMarkers: true }]);
        editor.focus();
      },
    }));

    return (
      <Editor
        height={height}
        language={language}
        value={value}
        onChange={(v) => onChange(v ?? "")}
        onMount={handleMount}
        theme={resolvedTheme === "light" ? "light" : "vs-dark"}
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          fontFamily: "'JetBrains Mono', monospace",
          lineNumbers: "on",
          wordWrap: "on",
          scrollBeyondLastLine: false,
          automaticLayout: true,
          tabSize: 2,
          padding: { top: 12 },
        }}
      />
    );
  },
);

export default MonacoEditor;
