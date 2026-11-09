
import React, { useState } from "react";
import { Sparkles } from "lucide-react";
import { handleLogin, handleRegister } from "../api";

const Field = ({ name, type, placeholder, value, onChange }) => (
    <div>
        <label htmlFor={name} className="sr-only">{placeholder}</label>
        <input
            id={name}
            name={name}
            type={type}
            value={value}
            onChange={onChange}
            placeholder={placeholder}
            required
            autoComplete={name === "password" ? "current-password" : "on"}
            className="w-full rounded-xl border border-white/10 bg-white/[0.035] px-4 py-3 text-sm text-white placeholder:text-gray-600 outline-none transition-colors focus:border-white/30"
        />
    </div>
);

export default function AuthScreen({ onLoginSuccess }) {
    const [isLoginView, setIsLoginView] = useState(true);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState("");
    const [formData, setFormData] = useState({
        identifier: "",
        password: "",
        name: "",
        email: "",
        phone_number: "",
        confirm_password: "",
    });

    const handleInputChange = (event) => {
        const { name, value } = event.target;
        setFormData((prev) => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        setIsLoading(true);
        setError("");

        try {
            if (isLoginView) {
                const result = await handleLogin(
                    formData.identifier,
                    formData.password
                );

                if (result?.access_token) {
                    localStorage.setItem("accessToken", result.access_token);
                    onLoginSuccess();
                } else {
                    setError("Unable to sign in. Check your details and try again.");
                }
            } else {
                if (formData.password !== formData.confirm_password) {
                    setError("Passwords do not match.");
                    return;
                }

                const result = await handleRegister({
                    name: formData.name,
                    email: formData.email,
                    phone_number: formData.phone_number,
                    password: formData.password,
                    confirm_password: formData.confirm_password,
                });

                if (result?.message) {
                    setIsLoginView(true);
                    setFormData((prev) => ({
                        ...prev,
                        identifier: prev.email,
                    }));
                } else {
                    setError("Registration failed. Please check your details.");
                }
            }
        } catch {
            setError("Something went wrong. Please try again.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <main className="flex min-h-screen items-center justify-center bg-[#171717] px-5 py-10 text-white">
            <div className="w-full max-w-[390px]">
                <div className="mb-9 flex flex-col items-center text-center">
                    <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-black">
                        <Sparkles size={22} />
                    </div>

                    <h1 className="text-2xl font-semibold tracking-tight">
                        {isLoginView ? "Welcome back" : "Create your account"}
                    </h1>

                    <p className="mt-2 text-sm text-gray-500">
                        {isLoginView
                            ? "Sign in to continue to your AI workspace."
                            : "Get started with your personal AI workspace."}
                    </p>
                </div>

                <form
                    onSubmit={handleSubmit}
                    className="space-y-3 rounded-2xl border border-white/[0.09] bg-white/[0.025] p-5 sm:p-6"
                >
                    {!isLoginView && (
                        <>
                            <Field
                                name="name"
                                type="text"
                                placeholder="Full name"
                                value={formData.name}
                                onChange={handleInputChange}
                            />
                            <Field
                                name="email"
                                type="email"
                                placeholder="Email address"
                                value={formData.email}
                                onChange={handleInputChange}
                            />
                            <Field
                                name="phone_number"
                                type="tel"
                                placeholder="Phone number"
                                value={formData.phone_number}
                                onChange={handleInputChange}
                            />
                        </>
                    )}

                    {isLoginView && (
                        <Field
                            name="identifier"
                            type="text"
                            placeholder="Email or phone number"
                            value={formData.identifier}
                            onChange={handleInputChange}
                        />
                    )}

                    <Field
                        name="password"
                        type="password"
                        placeholder="Password"
                        value={formData.password}
                        onChange={handleInputChange}
                    />

                    {!isLoginView && (
                        <Field
                            name="confirm_password"
                            type="password"
                            placeholder="Confirm password"
                            value={formData.confirm_password}
                            onChange={handleInputChange}
                        />
                    )}

                    {error && (
                        <p role="alert" className="text-sm leading-5 text-red-400">
                            {error}
                        </p>
                    )}

                    <button
                        type="submit"
                        disabled={isLoading}
                        className="w-full rounded-xl bg-white py-3 text-sm font-semibold text-black transition-colors hover:bg-gray-200 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                        {isLoading
                            ? "Please wait..."
                            : isLoginView
                              ? "Sign in"
                              : "Create account"}
                    </button>

                    <p className="pt-2 text-center text-sm text-gray-500">
                        {isLoginView
                            ? "New here?"
                            : "Already have an account?"}

                        <button
                            type="button"
                            onClick={() => {
                                setIsLoginView((value) => !value);
                                setError("");
                            }}
                            className="ml-2 font-medium text-gray-200 hover:text-white"
                        >
                            {isLoginView ? "Create account" : "Sign in"}
                        </button>
                    </p>
                </form>
            </div>
        </main>
    );
}
