
import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Sparkles, User, ExternalLink, Copy, Check, RefreshCw } from "lucide-react";
import toast from "react-hot-toast";

function CodeBlock({ language, value }) {
    const [copied, setCopied] = useState(false);

    const handleCopy = async () => {
        try {
            await navigator.clipboard.writeText(value);
            setCopied(true);
            toast.success("Copied to clipboard!", { duration: 2000 });
            setTimeout(() => setCopied(false), 2000);
        } catch {
            toast.error("Failed to copy.");
        }
    };

    return (
        <div className="my-5 overflow-hidden rounded-xl border border-white/10 bg-[#111111]">
            <div className="flex items-center justify-between border-b border-white/[0.08] px-4 py-2">
                <span className="text-xs text-gray-500">
                    {language || "code"}
                </span>
                <button
                    onClick={handleCopy}
                    title="Copy code"
                    className="flex items-center gap-1.5 rounded-md px-2 py-1 text-xs text-gray-500 transition-colors hover:bg-white/[0.07] hover:text-gray-200"
                >
                    {copied ? (
                        <>
                            <Check size={12} className="text-green-400" />
                            <span className="text-green-400">Copied</span>
                        </>
                    ) : (
                        <>
                            <Copy size={12} />
                            <span>Copy</span>
                        </>
                    )}
                </button>
            </div>

            <SyntaxHighlighter
                language={language || "text"}
                style={oneDark}
                customStyle={{
                    margin: 0,
                    padding: "16px",
                    background: "transparent",
                    fontSize: "13px",
                    lineHeight: "1.7",
                }}
                wrapLongLines
            >
                {String(value).replace(/\n$/, "")}
            </SyntaxHighlighter>
        </div>
    );
}

export default function Message({ role, content, sources, createdAt, onRegenerate }) {
    const isUser = role === "user";
    const isThinking = content === "Thinking...";

    const formattedTime = createdAt
        ? new Date(createdAt).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
          })
        : null;

    return (
        <article className="flex items-start gap-3 py-5 sm:gap-4">
            <div
                className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl ${
                    isUser
                        ? "border border-white/10 bg-white/[0.06] text-gray-300"
                        : "bg-white text-black"
                }`}
            >
                {isUser ? <User size={16} /> : <Sparkles size={16} />}
            </div>

            <div className="min-w-0 flex-1">
                <div className="mb-2 flex items-center gap-2 text-xs font-medium text-gray-400">
                    <span>{isUser ? "You" : "Assistant"}</span>
                    {formattedTime && (
                        <span className="text-gray-600">{formattedTime}</span>
                    )}
                </div>

                {isThinking ? (
                    <div className="flex items-center gap-1.5 py-2">
                        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-gray-500" />
                        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-gray-500 [animation-delay:150ms]" />
                        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-gray-500 [animation-delay:300ms]" />
                    </div>
                ) : (
                    <div className="prose prose-invert max-w-none break-words text-[14px] leading-7 prose-p:my-3 prose-p:text-gray-300 prose-headings:font-medium prose-headings:tracking-tight prose-headings:text-gray-100 prose-li:text-gray-300 prose-strong:text-gray-100 prose-a:text-gray-200 prose-a:underline prose-a:decoration-white/30 prose-code:before:content-none prose-code:after:content-none prose-blockquote:border-l-white/20 prose-blockquote:text-gray-400">
                        <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                                code({ inline, className, children, ...props }) {
                                    const match = /language-(\w+)/.exec(
                                        className || ""
                                    );

                                    if (!inline && match) {
                                        return (
                                            <CodeBlock
                                                language={match[1]}
                                                value={String(children)}
                                            />
                                        );
                                    }

                                    if (!inline) {
                                        return (
                                            <CodeBlock
                                                language="text"
                                                value={String(children)}
                                            />
                                        );
                                    }

                                    return (
                                        <code
                                            className="rounded bg-white/10 px-1.5 py-0.5 font-mono text-[0.9em] text-gray-200"
                                            {...props}
                                        >
                                            {children}
                                        </code>
                                    );
                                },
                            }}
                        >
                            {content || ""}
                        </ReactMarkdown>
                    </div>
                )}

                {/* Regenerate button for AI messages */}
                {!isUser && !isThinking && onRegenerate && (
                    <button
                        onClick={onRegenerate}
                        title="Regenerate response"
                        className="mt-2 flex items-center gap-1.5 rounded-lg px-2 py-1 text-xs text-gray-600 transition-colors hover:bg-white/[0.06] hover:text-gray-300"
                    >
                        <RefreshCw size={12} />
                        <span>Regenerate</span>
                    </button>
                )}

                {sources?.length > 0 && (
                    <div className="mt-5 border-t border-white/[0.08] pt-4">
                        <p className="mb-3 text-xs font-medium text-gray-500">
                            Sources
                        </p>

                        <div className="grid gap-2 sm:grid-cols-2">
                            {sources.map((source, index) => (
                                <a
                                    key={index}
                                    href={source.link}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="group min-w-0 rounded-xl border border-white/[0.08] bg-white/[0.02] p-3 transition-colors hover:bg-white/[0.05]"
                                >
                                    <div className="flex items-center justify-between gap-2">
                                        <p className="truncate text-xs font-medium text-gray-300">
                                            {source.title || source.link}
                                        </p>
                                        <ExternalLink
                                            size={13}
                                            className="shrink-0 text-gray-600 group-hover:text-gray-300"
                                        />
                                    </div>

                                    {source.snippet && (
                                        <p className="mt-1.5 line-clamp-2 text-xs leading-5 text-gray-500">
                                            {source.snippet}
                                        </p>
                                    )}
                                </a>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </article>
    );
}
