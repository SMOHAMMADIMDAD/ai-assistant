
import React, { useState, useRef, useEffect } from "react";
import { Plus, ArrowUp, X, BrainCircuit, Image as ImageIcon } from "lucide-react";

export default function InputBox({ onSendMessage, isLoading }) {
    const [prompt, setPrompt] = useState("");
    const [imageFile, setImageFile] = useState(null);
    const [imagePreviewUrl, setImagePreviewUrl] = useState(null);
    const [isDeepResearch, setIsDeepResearch] = useState(false);
    const fileInputRef = useRef(null);
    const textareaRef = useRef(null);

    useEffect(() => {
        const textarea = textareaRef.current;
        if (!textarea) return;

        textarea.style.height = "auto";
        textarea.style.height = `${Math.min(textarea.scrollHeight, 180)}px`;
    }, [prompt]);

    useEffect(() => {
        return () => {
            if (imagePreviewUrl) URL.revokeObjectURL(imagePreviewUrl);
        };
    }, [imagePreviewUrl]);

    const removeImage = () => {
        setImageFile(null);
        setImagePreviewUrl(null);
        if (fileInputRef.current) fileInputRef.current.value = "";
    };

    const handleFileChange = (event) => {
        const file = event.target.files?.[0];
        if (!file) return;

        if (imagePreviewUrl) URL.revokeObjectURL(imagePreviewUrl);

        setImageFile(file);
        setImagePreviewUrl(URL.createObjectURL(file));
    };

    const handleSend = () => {
        if ((!prompt.trim() && !imageFile) || isLoading) return;

        onSendMessage({
            prompt: prompt.trim(),
            imageFile,
            isDeepResearch,
        });

        setPrompt("");
        removeImage();

        if (textareaRef.current) {
            textareaRef.current.style.height = "auto";
        }
    };

    return (
        <div className="rounded-2xl border border-white/[0.12] bg-[#202020] p-3 transition-colors focus-within:border-white/25 sm:p-4">
            {imagePreviewUrl && (
                <div className="relative mb-3 inline-block">
                    <img
                        src={imagePreviewUrl}
                        alt="Image preview"
                        className="h-20 w-24 rounded-lg border border-white/10 object-cover"
                    />
                    <button
                        type="button"
                        onClick={removeImage}
                        aria-label="Remove attached image"
                        className="absolute -right-2 -top-2 rounded-full bg-[#404040] p-1 text-white hover:bg-[#555]"
                    >
                        <X size={13} />
                    </button>
                </div>
            )}

            <textarea
                ref={textareaRef}
                value={prompt}
                onChange={(event) => setPrompt(event.target.value)}
                onKeyDown={(event) => {
                    if (event.key === "Enter" && !event.shiftKey) {
                        event.preventDefault();
                        handleSend();
                    }
                }}
                placeholder="Message your AI..."
                rows={1}
                className="max-h-[180px] min-h-[44px] w-full resize-none bg-transparent px-1 py-2 text-[15px] leading-6 text-gray-100 outline-none placeholder:text-gray-500"
            />

            <div className="mt-2 flex items-center justify-between gap-2">
                <div className="flex min-w-0 items-center gap-1">
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/*"
                        onChange={handleFileChange}
                        className="hidden"
                    />

                    <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        title="Attach an image"
                        aria-label="Attach an image"
                        className="rounded-lg p-2 text-gray-400 transition-colors hover:bg-white/[0.07] hover:text-white"
                    >
                        <Plus size={19} />
                    </button>

                    <button
                        type="button"
                        onClick={() => setIsDeepResearch((value) => !value)}
                        aria-pressed={isDeepResearch}
                        className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-xs transition-colors ${
                            isDeepResearch
                                ? "border-white/20 bg-white/10 text-white"
                                : "border-transparent text-gray-400 hover:bg-white/[0.06] hover:text-gray-200"
                        }`}
                    >
                        <BrainCircuit size={15} />
                        <span>Deep research</span>
                    </button>

                    {imageFile && (
                        <span className="hidden max-w-24 truncate text-xs text-gray-500 sm:inline">
                            {imageFile.name}
                        </span>
                    )}
                </div>

                <button
                    type="button"
                    onClick={handleSend}
                    disabled={isLoading || (!prompt.trim() && !imageFile)}
                    aria-label="Send message"
                    title="Send message"
                    className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white text-black transition-colors hover:bg-gray-200 disabled:cursor-not-allowed disabled:bg-[#393939] disabled:text-gray-600"
                >
                    <ArrowUp size={19} />
                </button>
            </div>
        </div>
    );
}
