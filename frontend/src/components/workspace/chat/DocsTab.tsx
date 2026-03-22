/**
 * DocsTab
 * Displays documentation links collected by the Librarian.
 */
"use client";

import { useState } from "react";
import { ExternalLink, ChevronDown, ChevronUp, BookOpen } from "lucide-react";
import { useProjectStore } from "@/stores/useProjectStore";

export function DocsTab() {
  const docLinks = useProjectStore((s) => s.docLinks);
  const [expanded, setExpanded] = useState<string | null>(null);

  if (docLinks.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-cyan-500/10 ring-1 ring-cyan-500/20">
          <BookOpen className="h-7 w-7 text-cyan-500/60" />
        </div>
        <h3
          className="mb-2 text-lg text-slate-300"
          style={{ fontFamily: "var(--font-display)" }}
        >
          No docs yet
        </h3>
        <p className="max-w-xs text-sm text-slate-600">
          Documentation will appear here once the Librarian phase completes.
        </p>
      </div>
    );
  }

  const grouped = docLinks.reduce(
    (acc, doc) => {
      const key = doc.tech_name || "Other";
      if (!acc[key]) acc[key] = [];
      acc[key].push(doc);
      return acc;
    },
    {} as Record<string, typeof docLinks>
  );

  return (
    <div className="flex-1 overflow-y-auto px-5 py-6 space-y-4">
      <p className="text-xs text-slate-500">
        {docLinks.length} source{docLinks.length !== 1 ? "s" : ""} collected by the Librarian
      </p>

      {Object.entries(grouped).map(([techName, docs]) => (
        <div
          key={techName}
          className="rounded-2xl border border-white/8 bg-[#0d1220] overflow-hidden"
        >
          <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5">
            <div className="h-2 w-2 rounded-full bg-cyan-400" />
            <span
              className="text-sm font-medium text-slate-200"
              style={{ fontFamily: "var(--font-display)" }}
            >
              {techName}
            </span>
            <span className="ml-auto text-xs text-slate-600">
              {docs.length} source{docs.length !== 1 ? "s" : ""}
            </span>
          </div>

          {docs.map((doc, i) => {
            const key = `${techName}-${i}`;
            return (
              <div key={i} className="border-b border-white/5 last:border-0">
                <div
                  className="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-white/3 transition"
                  onClick={() => setExpanded(expanded === key ? null : key)}
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-slate-400 truncate">
                      {doc.doc_url}
                    </p>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <a
                      href={doc.doc_url}
                      target="_blank"
                      rel="noreferrer"
                      onClick={(e: React.MouseEvent) => e.stopPropagation()}
                      className="flex items-center gap-1 rounded-lg border border-white/8 px-2 py-1 text-[10px] text-slate-500 transition hover:border-cyan-500/30 hover:text-cyan-400"
                    >
                      <ExternalLink className="h-3 w-3" />
                      Open
                    </a>

                    {doc.scraped_content && (
                      <button className="text-slate-600 hover:text-slate-400 transition">
                        {expanded === key ? (
                          <ChevronUp className="h-3.5 w-3.5" />
                        ) : (
                          <ChevronDown className="h-3.5 w-3.5" />
                        )}
                      </button>
                    )}
                  </div>
                </div>

                {expanded === key && doc.scraped_content && (
                  <div className="px-4 pb-4">
                    <div className="rounded-xl border border-white/5 bg-black/30 p-3">
                      <p className="text-xs leading-relaxed text-slate-500 whitespace-pre-wrap line-clamp-10">
                        {doc.scraped_content}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ))}
    </div>
  );
}