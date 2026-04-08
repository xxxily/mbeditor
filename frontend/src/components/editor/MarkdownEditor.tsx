import { forwardRef } from "react";
import MonacoEditor, { type MonacoEditorHandle } from "./MonacoEditor";

interface MarkdownEditorProps {
  value: string;
  onChange: (value: string) => void;
}

const MarkdownEditor = forwardRef<MonacoEditorHandle, MarkdownEditorProps>(
  function MarkdownEditor({ value, onChange }, ref) {
    return <MonacoEditor ref={ref} value={value} onChange={onChange} language="markdown" />;
  },
);

export default MarkdownEditor;
