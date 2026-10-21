import { useEffect, useState } from "react";
import { Mail, Lock, ArrowRight, AlertCircle } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { loginUser, registerUser, verifyOTP, resendOTP } from "@/api/auth";
import { setAuthToken } from "@/api/client";
import { useAuth } from "@/context/AuthContext";
import { toast } from "sonner";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!email.trim() || !password) {
      toast.error("Please enter email and password.");
      return;
    }
    setLoading(true);
    try {
      const response = await loginUser({ email, password });
      const token = (response as any).access_token;
      const user = (response as any).user;
      if (token && user) {
        setAuthToken(token);
        login(token, user);
        toast.success(`Welcome back, ${user.name}!`);
        navigate("/");
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Login failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-header">
          <div className="auth-logo">T<span className="logo-accent">askflow</span></div>
          <h1>Welcome back</h1>
          <p>Sign in to your TaskFlow account</p>
        </div>

        <form onSubmit={handleLogin} className="auth-form">
          <div className="form-group">
            <label className="form-label">Email address</label>
            <div className="input-wrapper">
              <Mail size={16} className="input-icon" />
              <input
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <div className="input-wrapper">
              <Lock size={16} className="input-icon" />
              <input
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
            </div>
          </div>

          <button
            type="submit"
            className="auth-button"
            disabled={loading}
          >
            {loading ? <span>Signing in…</span> : <span>Sign in</span>}
            <ArrowRight size={16} className="button-icon" />
          </button>
        </form>

        <div className="auth-divider">
          <span>Or continue with</span>
        </div>

        <button
          type="button"
          className="auth-button google-button"
          onClick={() => {
            // Google Sign-In is handled by GoogleOneTap or a popup; see GoogleSignInButton component.
            toast.info("Click 'Sign in with Google' below.");
          }}
        >
          <svg className="google-icon" viewBox="0 0 24 24">
            <path
              fill="#4285F4"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="#34A853"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="#FBBC05"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"
            />
            <path
              fill="#EA4335"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 4.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
            />
          </svg>
          Sign in with Google
        </button>

        <p className="auth-footer">
          Don't have an account?{" "}
          <button type="button" className="auth-link" onClick={() => navigate("/register")}>
            Create an account
          </button>
        </p>
      </div>
    </div>
  );
}

export function RegisterPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleRegister = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!name.trim() || !email.trim() || !password) {
      toast.error("Please fill in all fields.");
      return;
    }
    if (password.length < 8) {
      toast.error("Password must be at least 8 characters.");
      return;
    }
    setLoading(true);
    try {
      const response = await registerUser({ name, email, password });
      const user = (response as any).user;
      toast.success("Account created! Please check your email for the verification code.");
      navigate("/verify-otp", { state: { email } });
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Registration failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-header">
          <div className="auth-logo">T<span className="logo-accent">askflow</span></div>
          <h1>Create an account</h1>
          <p>Join TaskFlow and start organizing your tasks</p>
        </div>

        <form onSubmit={handleRegister} className="auth-form">
          <div className="form-group">
            <label className="form-label">Full name</label>
            <div className="input-wrapper">
              <span className="input-icon">👤</span>
              <input
                type="text"
                placeholder="Ada Lovelace"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                autoComplete="name"
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Email address</label>
            <div className="input-wrapper">
              <Mail size={16} className="input-icon" />
              <input
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <div className="input-wrapper">
              <Lock size={16} className="input-icon" />
              <input
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
                autoComplete="new-password"
              />
            </div>
          </div>

          <button
            type="submit"
            className="auth-button"
            disabled={loading}
          >
            {loading ? <span>Creating account…</span> : <span>Create account</span>}
            <ArrowRight size={16} className="button-icon" />
          </button>
        </form>

        <p className="auth-footer">
          Already have an account?{" "}
          <button type="button" className="auth-link" onClick={() => navigate("/login")}>
            Sign in
          </button>
        </p>
      </div>
    </div>
  );
}

export function OTPPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const location = navigate as any;
    // Attempt to read email from route state (React Router v7)
    const state = (location as any).state || {};
    if (state.email) setEmail(state.email);
  }, [navigate]);

  const handleVerify = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!email.trim() || !code) {
      toast.error("Please enter your email and the 6-digit code.");
      return;
    }
    setLoading(true);
    try {
      const response = await verifyOTP({ email, code });
      const token = (response as any).access_token;
      const user = (response as any).user;
      if (token && user) {
        setAuthToken(token);
        login(token, user);
        toast.success(`Welcome to TaskFlow, ${user.name}!`);
        navigate("/");
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Verification failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (!email.trim()) return;
    try {
      await resendOTP(email);
      toast.success("A new verification code has been sent.");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to resend code.");
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-header">
          <div className="auth-logo">T<span className="logo-accent">askflow</span></div>
          <h1>Verify your email</h1>
          <p>A 6-digit code was sent to {email}</p>
        </div>

        <form onSubmit={handleVerify} className="auth-form">
          <div className="form-group">
            <label className="form-label">Verification code</label>
            <div className="input-wrapper">
              <AlertCircle size={16} className="input-icon" />
              <input
                type="text"
                placeholder="000000"
                maxLength={6}
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
                required
                autoComplete="one-time-code"
                inputMode="numeric"
              />
            </div>
          </div>

          <button
            type="submit"
            className="auth-button"
            disabled={loading}
          >
            {loading ? <span>Verifying…</span> : <span>Verify code</span>}
            <ArrowRight size={16} className="button-icon" />
          </button>
        </form>

        <p className="auth-footer">
          Didn't receive a code?{" "}
          <button
            type="button"
            className="auth-link"
            onClick={handleResend}
            disabled={loading}
          >
            Resend code
          </button>
        </p>

        <p className="auth-footer">
          Already verified?{" "}
          <button type="button" className="auth-link" onClick={() => navigate("/login")}>
            Sign in
          </button>
        </p>
      </div>
    </div>
  );
}
