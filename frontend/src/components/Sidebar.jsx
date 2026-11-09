
import React, { useEffect, useState, useRef } from "react";
import { LogOut, Plus, Settings, Trash2, Sparkles, Pencil, Check, X } from "lucide-react";

export default function Sidebar({
    onLogout,
    onNewChat,
    onSelectChat,
    onDeleteSession,
    onUpdateInstruction,
    onRenameSession,
    activeChatId,
    sessions = [],
    profile,
}) {
    const [instruction, setInstruction] = useState(
        profile?.custom_instruction || ""
    );
    const [showSettings, setShowSettings] = useState(false);
    const [editingSessionId, setEditingSessionId] = useState(null);
    const [editingTitle, setEditingTitle] = useState("");
    const renameInputRef = useRef(null);

    useEffect(() => {
        setInstruction(profile?.custom_instruction || "");
    }, [profile?.custom_instruction]);

    useEffect(() => {
        if (editingSessionId && renameInputRef.current) {
            renameInputRef.current.focus();
            renameInputRef.current.select();
        }
    }, [editingSessionId]);

    const handleSave = () => {
        onUpdateInstruction(instruction);
        setShowSettings(false);
    };

    const startRename = (session, e) => {
        e.stopPropagation();
        setEditingSessionId(session.id);
        setEditingTitle(session.title);
    };

    const confirmRename = (e) => {
        e?.stopPropagation();
        if (editingTitle.trim() && onRenameSession) {
            onRenameSession(editingSessionId, editingTitle.trim());
        }
        setEditingSessionId(null);
    };

    const cancelRename = (e) => {
        e?.stopPropagation();
        setEditingSessionId(null);
    };

    return (
        <aside className="w-64 shrink-0 flex flex-col bg-[#151518] text-gray-300 border-r border-white/[0.07]">
            <div className="px-4 pt-5 pb-4">
                <div className="flex items-center gap-3 px-2 mb-7">
                    <div className="w-9 h-9 rounded-xl bg-white text-black flex items-center justify-center">
                        <Sparkles size={19} />
                    </div>
                    <div>
                        <h1 className="text-sm font-semibold tracking-wide text-white">
                            Upgraded AI
                        </h1>
                        <p className="text-[11px] text-gray-500">
                            Your AI workspace
                        </p>
                    </div>
                </div>

                <button
                    onClick={onNewChat}
                    className="w-full flex items-center gap-3 px-3 py-3 rounded-xl border border-white/10 hover:bg-white/[0.06] text-sm text-white transition-colors"
                >
                    <Plus size={18} />
                    <span>New chat</span>
                </button>
            </div>

            <nav className="flex-1 px-3 py-3 overflow-y-auto">
                <p className="px-3 mb-3 text-[11px] uppercase tracking-[0.16em] text-gray-500">
                    Recent chats
                </p>

                {sessions.length === 0 ? (
                    <p className="px-3 py-2 text-xs text-gray-600">
                        Your conversations will appear here.
                    </p>
                ) : (
                    <div className="space-y-1">
                        {sessions.map((session) => (
                            <div
                                key={session.id}
                                className={`group flex items-center rounded-lg transition-colors ${
                                    activeChatId === session.id
                                        ? "bg-white/[0.09] text-white"
                                        : "text-gray-400 hover:bg-white/[0.045] hover:text-gray-200"
                                }`}
                            >
                                {editingSessionId === session.id ? (
                                    /* ── Inline rename input ── */
                                    <div className="flex flex-1 items-center gap-1 px-2 py-1.5">
                                        <input
                                            ref={renameInputRef}
                                            value={editingTitle}
                                            onChange={(e) => setEditingTitle(e.target.value)}
                                            onKeyDown={(e) => {
                                                if (e.key === "Enter") confirmRename(e);
                                                if (e.key === "Escape") cancelRename(e);
                                            }}
                                            onClick={(e) => e.stopPropagation()}
                                            className="flex-1 min-w-0 rounded-md bg-white/[0.08] border border-white/20 px-2 py-1 text-[13px] text-white outline-none"
                                        />
                                        <button
                                            onClick={confirmRename}
                                            title="Save"
                                            className="shrink-0 p-1 rounded hover:bg-white/10 text-green-400"
                                        >
                                            <Check size={13} />
                                        </button>
                                        <button
                                            onClick={cancelRename}
                                            title="Cancel"
                                            className="shrink-0 p-1 rounded hover:bg-white/10 text-gray-500 hover:text-gray-300"
                                        >
                                            <X size={13} />
                                        </button>
                                    </div>
                                ) : (
                                    /* ── Normal session row ── */
                                    <>
                                        <button
                                            onClick={() => onSelectChat(session.id)}
                                            title={session.title}
                                            className="flex-1 min-w-0 text-left px-3 py-2.5 text-[13px] truncate"
                                        >
                                            {session.title}
                                        </button>

                                        {/* Rename button */}
                                        <button
                                            onClick={(e) => startRename(session, e)}
                                            title="Rename chat"
                                            aria-label={`Rename ${session.title}`}
                                            className="shrink-0 p-1.5 rounded-md opacity-0 group-hover:opacity-100 focus:opacity-100 hover:bg-white/10 hover:text-blue-300 transition-all"
                                        >
                                            <Pencil size={13} />
                                        </button>

                                        {/* Delete button */}
                                        <button
                                            onClick={() => onDeleteSession(session.id)}
                                            title="Delete chat"
                                            aria-label={`Delete ${session.title}`}
                                            className="shrink-0 mr-1 p-1.5 rounded-md opacity-0 group-hover:opacity-100 focus:opacity-100 hover:bg-white/10 hover:text-red-300 transition-all"
                                        >
                                            <Trash2 size={13} />
                                        </button>
                                    </>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </nav>

            <div className="p-3 border-t border-white/[0.07] space-y-1">
                {showSettings && (
                    <div className="p-3 mb-3 rounded-xl bg-white/[0.04] border border-white/[0.08] space-y-3">
                        <label className="block text-xs font-medium text-gray-300">
                            Custom instructions
                        </label>

                        <textarea
                            value={instruction}
                            onChange={(e) => setInstruction(e.target.value)}
                            rows={4}
                            placeholder="How should the AI respond?"
                            className="w-full resize-y rounded-lg bg-[#101013] border border-white/10 p-3 text-sm text-gray-200 placeholder:text-gray-600 outline-none focus:border-white/25"
                        />

                        <button
                            onClick={handleSave}
                            className="w-full rounded-lg bg-white px-3 py-2 text-sm font-medium text-black hover:bg-gray-200 transition-colors"
                        >
                            Save instructions
                        </button>
                    </div>
                )}

                <button
                    onClick={() => setShowSettings((value) => !value)}
                    className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-400 hover:text-white hover:bg-white/[0.05] transition-colors"
                >
                    <Settings size={17} />
                    <span>Settings</span>
                </button>

                <button
                    onClick={onLogout}
                    className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-400 hover:text-red-300 hover:bg-red-400/[0.06] transition-colors"
                >
                    <LogOut size={17} />
                    <span>Log out</span>
                </button>
            </div>
        </aside>
    );
}
