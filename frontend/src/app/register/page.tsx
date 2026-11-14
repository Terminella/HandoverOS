
"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Leaf, Eye, EyeOff } from "lucide-react";
import { apiPost } from "../../lib/api";
import { saveToken } from "../../lib/auth";

type RegisterResponse = {
  message: string;
  user_id: string;
};

export default function RegisterPage() {
  const router = useRouter();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

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
      if (!name.trim()) {
        setError("Full name is required.");
        return;
      }
      if (!confirmPassword) {
        setError("Please confirm your password.");
        return;
      }
      if (password !== confirmPassword) {
        setError("Passwords do not match.");
        return;
      }

      await apiPost<RegisterResponse>("/auth/register", {
        name: name.trim(),
        email: email.trim().toLowerCase(),
        password,
      });

      router.push("/login");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to connect to the server."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-page" role="main">
      <div className="auth-card">
        <div className="auth-brand">
          <div className="leaf-container" aria-hidden="true">
            <Leaf size={25} />
          </div>
          <span>HandoverOS</span>
        </div>

        <p className="auth-eyebrow">Create your account</p>
        <h1>Create your account</h1>
        <p className="auth-subtitle">
          Start preserving your team&apos;s project knowledge.
        </p>

        {error && <p className="auth-error" role="alert">{error}</p>}

        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            Full name
            <input
              type="text"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                handleInputChange(e);
              }}
              onBlur={handleInputChange}
              placeholder="Enter your full name"
              required
              minLength={2}
              maxLength={150}
              autoComplete="name"
            />
          </label>

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
                autoComplete="new-password"
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

          <label className="password-field-wrapper">
            Confirm password
            <div className="password-input-group">
              <input
                type={showConfirmPassword ? "text" : "password"}
                value={confirmPassword}
                onChange={(e) => {
                  setConfirmPassword(e.target.value);
                  handleInputChange(e);
                }}
                onBlur={handleInputChange}
                placeholder="Confirm your password"
                minLength={8}
                required
                autoComplete="new-password"
                style={{ width: "100%", paddingRight: 44 }}
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="password-toggle"
                aria-label={showConfirmPassword ? "Hide password" : "Show password"}
              >
                {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </label>

          <button
            type="submit"
            className="auth-button"
            disabled={loading}
          >
            {loading ? "Creating account…" : "Create account"}
          </button>
        </form>

        <p className="auth-footer">
          Already have an account?{" "}
          <button
            type="button"
            className="auth-switch"
            onClick={() => router.push("/login")}
          >
            Sign in
          </button>
        </p>

        <p className="auth-footer-text">
          Preserving project knowledge. Enabling seamless continuity.
        </p>
      </div>
    </main>
  );
}
