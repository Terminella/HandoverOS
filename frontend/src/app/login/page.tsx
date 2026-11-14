
"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter, usePathname } from "next/navigation";
import { Leaf, Eye, EyeOff } from "lucide-react";
import { apiPost } from "../../lib/api";
import { saveToken, clearToken, getToken } from "../../lib/auth";

type LoginResponse = {
  message: string;
  access_token: string;
  token_type: string;
};

export default function LoginPage() {
  const router = useRouter();
  const pathname = usePathname();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Restore Remember Me preference and saved email from localStorage on mount.
  useEffect(() => {
    const stored = localStorage.getItem("handoveros-remember-me");
    if (stored === "true") {
      setRememberMe(true);
    }
    const savedEmail = localStorage.getItem("handoveros-saved-email");
    if (savedEmail) {
      setEmail(savedEmail);
    }
  }, []);

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setError("");
    },
    []
  );

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const result = await apiPost<LoginResponse>("/auth/login", {
        email: email.trim().toLowerCase(),
        password,
        remember_me: rememberMe,
      });

      saveToken(result.access_token);

      if (rememberMe) {
        localStorage.setItem("handoveros-saved-email", email.trim().toLowerCase());
        localStorage.setItem("handoveros-remember-me", "true");
      } else {
        localStorage.removeItem("handoveros-remember-me");
      }

      router.replace("/");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to connect to the server."
      );
    } finally {
      setLoading(false);
    }
  }

  // If already authenticated, redirect to dashboard.
  useEffect(() => {
    const token = getToken();
    if (token && pathname === "/login") {
      router.replace("/");
    }
  }, [pathname, router]);

  return (
    <main className="auth-page" role="main">
      <div className="auth-card">
        <div className="auth-brand">
          <div className="leaf-container" aria-hidden="true">
            <Leaf size={25} />
          </div>
          <span>HandoverOS</span>
        </div>

        <p className="auth-eyebrow">Project continuity platform</p>
        <h1>Welcome back</h1>
        <p className="auth-subtitle">
          Sign in to continue to your HandoverOS workspace.
        </p>

        {error && <p className="auth-error" role="alert">{error}</p>}

        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            Email address
            <input
              type="email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                handleInputChange(e);
              }}
              onBlur={handleInputChange}
              placeholder="Enter your email address"
              required
              autoComplete="email"
            />
          </label>

          <label className="password-field-wrapper">
            Password
            <div className="password-input-group">
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  handleInputChange(e);
                }}
                onBlur={handleInputChange}
                placeholder="Enter your password"
                minLength={8}
                required
                autoComplete="current-password"
                style={{ width: "100%", paddingRight: 44 }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="password-toggle"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </label>

          <label className="auth-remember">
            <input
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
            />
            Remember me
          </label>

          <button
            type="submit"
            className="auth-button"
            disabled={loading}
          >
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <p className="auth-footer">
          Don&apos;t have an account?{" "}
          <button
            type="button"
            className="auth-switch"
            onClick={() => router.push("/register")}
          >
            Create one free
          </button>
        </p>

        <p className="auth-footer-text">
          Preserving project knowledge. Enabling seamless continuity.
        </p>
      </div>
    </main>
  );
}
