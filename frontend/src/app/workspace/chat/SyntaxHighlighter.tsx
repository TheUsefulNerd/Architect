/**
 * SyntaxHighlighter
 * Code block renderer for markdown inside the chat.
 */
"use client";

import { Prism as Highlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";

interface SyntaxHighlighterProps {
  language: string;
  children: string;
}

export function SyntaxHighlighter({ language, children }: SyntaxHighlighterProps) {
  return (
    <Highlighter
      language={language}
      style={vscDarkPlus}
      showLineNumbers
      customStyle={{
        background: "rgba(8, 12, 20, 0.8)",
        border: "1px solid rgba(59,130,246,0.12)",
        borderRadius: "12px",
        fontSize: "12px",
        lineHeight: "1.6",
        margin: "8px 0",
      }}
      lineNumberStyle={{
        color: "rgba(148,163,184,0.3)",
        fontSize: "11px",
      }}
    >
      {children}
    </Highlighter>
  );
}