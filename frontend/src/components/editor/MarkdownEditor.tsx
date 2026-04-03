import MonacoEditor from "./MonacoEditor";

interface MarkdownEditorProps {
  value: string;
  onChange: (value: string) => void;
}

export default function MarkdownEditor({ value, onChange }: MarkdownEditorProps) {
  return <MonacoEditor value={value} onChange={onChange} language="markdown" />;
}
