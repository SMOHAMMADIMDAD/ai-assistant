
import React from "react";
import { ArrowUpRight, Sparkles } from "lucide-react";

export default function WelcomeScreen({ onPromptClick }) {
    const promptStarters = [
        {
            title: "Understand a concept",
            prompt: "Explain quantum computing in simple terms.",
        },
        {
            title: "Write some code",
            prompt: "Write a clean Python script to scrape a website.",
        },
        {
            title: "Explore an idea",
            prompt: "Suggest practical AI project ideas I can build.",
        },
        {
            title: "Solve a problem",
            prompt: "Help me break a difficult problem into simple steps.",
        },
    ];

    return (
        <div className="flex min-h-full flex-col items-center justify-center px-5 py-12">
            <div className="mb-7 flex h-12 w-12 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.04]">
                <Sparkles size={22} className="text-gray-200" />
            </div>

            <p className="mb-3 text-xs font-medium uppercase tracking-[0.22em] text-gray-500">
                Your AI workspace
            </p>

            <h1 className="text-center text-3xl font-medium tracking-tight text-gray-100 sm:text-4xl">
                What can I help with?
            </h1>

            <p className="mt-3 max-w-md text-center text-sm leading-6 text-gray-500">
                Ask a question, explore an idea, or work through a problem.
            </p>

            <div className="mt-10 grid w-full max-w-2xl grid-cols-1 gap-3 sm:grid-cols-2">
                {promptStarters.map((item) => (
                    <button
                        key={item.title}
                        onClick={() => onPromptClick(item.prompt)}
                        className="group flex min-h-[92px] items-center justify-between gap-4 rounded-xl border border-white/[0.09] bg-white/[0.02] p-4 text-left transition-colors hover:border-white/20 hover:bg-white/[0.045]"
                    >
                        <div>
                            <p className="text-sm font-medium text-gray-200">
                                {item.title}
                            </p>
                            <p className="mt-1.5 text-xs leading-5 text-gray-500">
                                {item.prompt}
                            </p>
                        </div>

                        <ArrowUpRight
                            size={16}
                            className="shrink-0 text-gray-600 transition-colors group-hover:text-gray-300"
                        />
                    </button>
                ))}
            </div>
        </div>
    );
}
