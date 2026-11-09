
import React, { useState, useEffect, useRef } from "react";
import toast from "react-hot-toast";
import AuthScreen from "./components/AuthScreen";
import Sidebar from "./components/Sidebar";
import WelcomeScreen from "./components/WelcomeScreen";
import Message from "./components/Message";
import InputBox from "./components/InputBox";
import {
    sendMessage,
    getChatMessages,
    getProfile,
    getAllSessions,
    deleteSession,
    updateCustomInstruction,
    renameSession,
} from "./api";

export default function App() {
    const [messages, setMessages] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [isLoggedIn, setIsLoggedIn] = useState(
        !!localStorage.getItem("accessToken")
    );
    const [activeChatId, setActiveChatId] = useState(null);
    const [profile, setProfile] = useState(null);
    const [sessions, setSessions] = useState([]);
    const [historyKey, setHistoryKey] = useState(0);
    // Track last prompt for regeneration
    const lastPromptRef = useRef(null);
    const chatEndRef = useRef(null);

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    useEffect(() => {
        if (!isLoggedIn) return;

        loadProfile();
        loadSessions();
    }, [isLoggedIn, historyKey]);

    const loadProfile = async () => {
        const data = await getProfile();
        if (data) setProfile(data);
    };

    const loadSessions = async () => {
        const data = await getAllSessions();
        if (data?.sessions) setSessions(data.sessions);
    };

    const handleSendMessage = async (payload) => {
        if ((!payload.prompt?.trim() && !payload.imageFile) || isLoading) {
            return;
        }

        const prompt = payload.prompt || "";
        const imageName = payload.imageFile
            ? ` [Image: ${payload.imageFile.name}]`
            : "";

        // Store last prompt for regenerate
        lastPromptRef.current = payload;

        setIsLoading(true);
        setMessages((prev) => [
            ...prev,
            { role: "user", content: prompt + imageName, createdAt: new Date().toISOString() },
            { role: "model", content: "Thinking...", createdAt: null },
        ]);

        try {
            const data = await sendMessage({
                ...payload,
                sessionId: activeChatId,
            });

            if (data) {
                setMessages((prev) => {
                    const updated = [...prev];
                    updated[updated.length - 1] = {
                        role: "model",
                        content: data.response,
                        sources: data.sources,
                        createdAt: new Date().toISOString(),
                    };
                    return updated;
                });

                if (!activeChatId && data.session_id) {
                    setActiveChatId(data.session_id);
                    setHistoryKey((prev) => prev + 1);
                }
            } else {
                setMessages((prev) => {
                    const updated = [...prev];
                    updated[updated.length - 1] = {
                        role: "model",
                        content: "I couldn't complete that request. Please try again.",
                        createdAt: new Date().toISOString(),
                    };
                    return updated;
                });
            }
        } catch {
            setMessages((prev) => {
                const updated = [...prev];
                updated[updated.length - 1] = {
                    role: "model",
                    content: "Something went wrong. Please try again.",
                    createdAt: new Date().toISOString(),
                };
                return updated;
            });
        } finally {
            setIsLoading(false);
        }
    };

    // Regenerate: remove last AI message and re-send last user prompt
    const handleRegenerate = async () => {
        if (isLoading || !lastPromptRef.current) return;

        // Remove the last AI message from view
        setMessages((prev) => prev.slice(0, -1));

        await handleSendMessage(lastPromptRef.current);
    };

    const handleSelectChat = async (sessionId) => {
        if (isLoading) return;

        setIsLoading(true);
        setActiveChatId(sessionId);

        try {
            const chatData = await getChatMessages(sessionId);

            setMessages(
                chatData?.history?.map((msg) => ({
                    role: msg.role,
                    content: msg.content,
                    createdAt: msg.created_at,
                })) || []
            );
        } finally {
            setIsLoading(false);
        }
    };

    const handleNewChat = () => {
        setActiveChatId(null);
        setMessages([]);
        lastPromptRef.current = null;
    };

    const handleDeleteSession = async (sessionId) => {
        const result = await deleteSession(sessionId);

        if (result) {
            toast.success("Chat deleted.");
            if (activeChatId === sessionId) handleNewChat();
            setHistoryKey((prev) => prev + 1);
        }
    };

    const handleRenameSession = async (sessionId, newTitle) => {
        const result = await renameSession(sessionId, newTitle);

        if (result) {
            toast.success("Chat renamed.");
            setSessions((prev) =>
                prev.map((s) =>
                    s.id === sessionId ? { ...s, title: newTitle } : s
                )
            );
        }
    };

    const handleUpdateInstruction = async (instruction) => {
        const result = await updateCustomInstruction(instruction);

        if (result) {
            toast.success("Custom instructions saved.");
            await loadProfile();
        }
    };

    const handleLogout = () => {
        localStorage.removeItem("accessToken");
        setIsLoggedIn(false);
        setProfile(null);
        setSessions([]);
        handleNewChat();
    };

    if (!isLoggedIn) {
        return <AuthScreen onLoginSuccess={() => setIsLoggedIn(true)} />;
    }

    return (
        <div className="flex h-screen w-full overflow-hidden bg-[#171717] text-[#e5e5e5]">
            <Sidebar
                onLogout={handleLogout}
                onNewChat={handleNewChat}
                onSelectChat={handleSelectChat}
                onDeleteSession={handleDeleteSession}
                onRenameSession={handleRenameSession}
                onUpdateInstruction={handleUpdateInstruction}
                activeChatId={activeChatId}
                sessions={sessions}
                profile={profile}
            />

            <main className="flex min-w-0 flex-1 flex-col">
                <header className="flex h-14 shrink-0 items-center justify-between border-b border-white/[0.07] px-5 sm:px-8">
                    <div className="text-sm font-medium text-gray-200">
                        {activeChatId ? "Conversation" : "New conversation"}
                    </div>
                    <div className="text-xs text-gray-500">
                        AI assistant
                    </div>
                </header>

                <section className="min-h-0 flex-1 overflow-y-auto">
                    {messages.length === 0 ? (
                        <WelcomeScreen
                            onPromptClick={(prompt) =>
                                handleSendMessage({
                                    prompt,
                                    imageFile: null,
                                    isDeepResearch: false,
                                })
                            }
                        />
                    ) : (
                        <div className="mx-auto w-full max-w-3xl px-5 py-6 sm:px-8 sm:py-10">
                            {messages.map((msg, index) => {
                                const isLastAI =
                                    msg.role === "model" &&
                                    index === messages.length - 1 &&
                                    msg.content !== "Thinking...";

                                return (
                                    <Message
                                        key={`${activeChatId ?? "new"}-${index}`}
                                        role={msg.role}
                                        content={msg.content}
                                        sources={msg.sources}
                                        createdAt={msg.createdAt}
                                        onRegenerate={isLastAI ? handleRegenerate : undefined}
                                    />
                                );
                            })}
                            <div ref={chatEndRef} />
                        </div>
                    )}
                </section>

                <footer className="shrink-0 px-4 pb-4 pt-3 sm:px-8 sm:pb-6">
                    <div className="mx-auto w-full max-w-3xl">
                        <InputBox
                            onSendMessage={handleSendMessage}
                            isLoading={isLoading}
                        />
                        <p className="mt-3 text-center text-[11px] text-gray-600">
                            AI can make mistakes. Verify important information.
                        </p>
                    </div>
                </footer>
            </main>
        </div>
    );
}
