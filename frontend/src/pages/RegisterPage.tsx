import styled from "styled-components";
import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { FiMail, FiLock, FiEye, FiEyeOff, FiCheck, FiX } from "react-icons/fi";
import { FcGoogle } from "react-icons/fc";
import { SiApple } from "react-icons/si";
import { FaMicrosoft } from "react-icons/fa";

const PageContainer = styled.div`
  min-height: 100vh;
  width: 100vw;
  box-sizing: border-box;
  background: linear-gradient(
    135deg,
    #667eea 0%,
    #764ba2 25%,
    #f093fb 50%,
    #4facfe 75%,
    #00f2fe 100%
  );
  background-size: 400% 400%;
  animation: gradientShift 15s ease infinite;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;

  @keyframes gradientShift {
    0% {
      background-position: 0% 50%;
    }
    50% {
      background-position: 100% 50%;
    }
    100% {
      background-position: 0% 50%;
    }
  }
`;

const Card = styled.div`
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  padding: 60px 50px;
  width: 100%;
  max-width: 440px;
  animation: slideUp 0.6s ease-out;
  max-height: 90vh;
  overflow-y: auto;

  @keyframes slideUp {
    from {
      opacity: 0;
      transform: translateY(40px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  @media (max-width: 768px) {
    padding: 40px 30px;
    margin: 20px;
  }
`;

const Title = styled.h1`
  font-size: 32px;
  font-weight: 700;
  color: #1a202c;
  margin: 0 0 10px 0;
  letter-spacing: -0.5px;
`;

const Subtitle = styled.p`
  font-size: 14px;
  color: #718096;
  margin: 0 0 30px 0;
  line-height: 1.5;
`;

const FormGroup = styled.div`
  margin-bottom: 20px;
`;

const Label = styled.label`
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const InputWrapper = styled.div`
  position: relative;
  display: flex;
  align-items: center;
`;

const Input = styled.input`
  width: 100%;
  padding: 14px 16px 14px 44px;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-size: 15px;
  transition: all 0.3s ease;
  background: #f7fafc;

  &:focus {
    outline: none;
    border-color: #667eea;
    background: white;
    box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
  }

  &::placeholder {
    color: #cbd5e0;
  }
`;

const InputIcon = styled.div`
  position: absolute;
  left: 14px;
  color: #a0aec0;
  font-size: 18px;
  pointer-events: none;
`;

const TogglePassword = styled.button`
  position: absolute;
  right: 14px;
  background: none;
  border: none;
  color: #a0aec0;
  font-size: 18px;
  cursor: pointer;
  transition: color 0.2s;

  &:hover {
    color: #667eea;
  }
`;

const PasswordStrengthContainer = styled.div`
  margin-top: 12px;
`;

const StrengthBar = styled.div`
  height: 6px;
  background: #e2e8f0;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 8px;
`;

interface StrengthBarFillProps {
  strength: number;
}

const StrengthBarFill = styled.div<StrengthBarFillProps>`
  height: 100%;
  width: ${(props) => (props.strength / 4) * 100}%;
  background: ${(props) => {
    if (props.strength < 2) return "#f56565";
    if (props.strength < 3) return "#ed8936";
    if (props.strength < 4) return "#ecc94b";
    return "#48bb78";
  }};
  transition:
    width 0.3s ease,
    background 0.3s ease;
`;

const PasswordCriteria = styled.div`
  font-size: 12px;
  color: #718096;
`;

const CriteriaItem = styled.div<{ met?: boolean }>`
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 4px 0;
  color: ${(props) => (props.met ? "#48bb78" : "#718096")};
`;

const CriteriaIcon = styled.span<{ met?: boolean }>`
  font-size: 14px;
  color: ${(props) => (props.met ? "#48bb78" : "#cbd5e0")};
`;

const CheckboxLabel = styled.label`
  display: flex;
  align-items: flex-start;
  gap: 8px;
  color: #4a5568;
  cursor: pointer;
  font-size: 13px;
  line-height: 1.5;

  input {
    margin-top: 3px;
    width: 16px;
    height: 16px;
    cursor: pointer;
    flex-shrink: 0;
  }
`;

const SubmitButton = styled.button`
  width: 100%;
  padding: 14px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 20px;
  margin-bottom: 20px;
  text-transform: uppercase;
  letter-spacing: 0.5px;

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
  }

  &:active:not(:disabled) {
    transform: translateY(0);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`;

const Divider = styled.div`
  display: flex;
  align-items: center;
  margin: 30px 0;
  color: #cbd5e0;
  font-size: 13px;

  &::before,
  &::after {
    content: "";
    flex: 1;
    height: 1px;
    background: #e2e8f0;
  }

  &::before {
    margin-right: 15px;
  }

  &::after {
    margin-left: 15px;
  }
`;

const OAuthContainer = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 12px;
  margin-bottom: 20px;
`;

const OAuthButton = styled.button`
  padding: 12px;
  border: 2px solid #e2e8f0;
  background: white;
  border-radius: 10px;
  cursor: pointer;
  font-size: 18px;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;

  &:hover {
    border-color: #667eea;
    background: #f7fafc;
    transform: translateY(-2px);
  }
`;

const LoginLink = styled.p`
  text-align: center;
  font-size: 14px;
  color: #4a5568;
  margin: 0;

  a {
    color: #667eea;
    text-decoration: none;
    font-weight: 600;
    cursor: pointer;
    transition: color 0.2s;

    &:hover {
      color: #764ba2;
    }
  }
`;

const ErrorMessage = styled.div`
  background: #fed7d7;
  color: #c53030;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 20px;
  font-size: 13px;
  animation: slideDown 0.3s ease-out;

  @keyframes slideDown {
    from {
      opacity: 0;
      transform: translateY(-10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
`;

const SuccessMessage = styled.div`
  background: #c6f6d5;
  color: #22543d;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 20px;
  font-size: 13px;
  animation: slideDown 0.3s ease-out;

  @keyframes slideDown {
    from {
      opacity: 0;
      transform: translateY(-10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
`;

interface PasswordStrength {
  score: number;
  feedback: string;
}

function calculatePasswordStrength(password: string): PasswordStrength {
  let score = 0;

  if (password.length >= 8) score++;
  if (password.length >= 12) score++;
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score++;
  if (/\d/.test(password)) score++;

  return { score, feedback: "" };
}

export function RegisterPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { register, isLoading, error } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [agreeTerms, setAgreeTerms] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const passwordStrength = calculatePasswordStrength(password);
  const passwordsMatch = password === confirmPassword;
  const isFormValid =
    email &&
    password &&
    confirmPassword &&
    agreeTerms &&
    passwordsMatch &&
    passwordStrength.score >= 2;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    setSuccess(false);

    // Validation
    if (!email) {
      setLocalError("Please enter an email address");
      return;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setLocalError("Please enter a valid email address");
      return;
    }

    if (password.length < 8) {
      setLocalError("Password must be at least 8 characters long");
      return;
    }

    if (passwordStrength.score < 2) {
      setLocalError("Password is too weak. Please use a stronger password");
      return;
    }

    if (password !== confirmPassword) {
      setLocalError("Passwords do not match");
      return;
    }

    if (!agreeTerms) {
      setLocalError("Please agree to the terms and conditions");
      return;
    }

    try {
      await register(email, password);
      setSuccess(true);
      // Redirect to the page the user was trying to visit, or to home
      const from = (location.state as any)?.from?.pathname || "/";
      setTimeout(() => navigate(from), 1500);
    } catch (err) {
      setLocalError(
        err instanceof Error
          ? err.message
          : "Registration failed. Please try again."
      );
    }
  };

  return (
    <PageContainer>
      <Card>
        <Title>Create Account</Title>
        <Subtitle>Join us to find your perfect property</Subtitle>

        {(error || localError) && (
          <ErrorMessage>{error || localError}</ErrorMessage>
        )}
        {success && (
          <SuccessMessage>
            Account created successfully! Redirecting...
          </SuccessMessage>
        )}

        <form onSubmit={handleSubmit}>
          <FormGroup>
            <Label>Email Address</Label>
            <InputWrapper>
              <InputIcon>
                <FiMail />
              </InputIcon>
              <Input
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={isLoading}
              />
            </InputWrapper>
          </FormGroup>

          <FormGroup>
            <Label>Password</Label>
            <InputWrapper>
              <InputIcon>
                <FiLock />
              </InputIcon>
              <Input
                type={showPassword ? "text" : "password"}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={isLoading}
              />
              <TogglePassword
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                tabIndex={-1}
              >
                {showPassword ? <FiEyeOff /> : <FiEye />}
              </TogglePassword>
            </InputWrapper>

            {password && (
              <PasswordStrengthContainer>
                <StrengthBar>
                  <StrengthBarFill strength={passwordStrength.score} />
                </StrengthBar>
                <PasswordCriteria>
                  <CriteriaItem met={password.length >= 8}>
                    <CriteriaIcon met={password.length >= 8}>
                      {password.length >= 8 ? <FiCheck /> : <FiX />}
                    </CriteriaIcon>
                    At least 8 characters
                  </CriteriaItem>
                  <CriteriaItem
                    met={/[a-z]/.test(password) && /[A-Z]/.test(password)}
                  >
                    <CriteriaIcon
                      met={/[a-z]/.test(password) && /[A-Z]/.test(password)}
                    >
                      {/[a-z]/.test(password) && /[A-Z]/.test(password) ? (
                        <FiCheck />
                      ) : (
                        <FiX />
                      )}
                    </CriteriaIcon>
                    Mix of uppercase & lowercase letters
                  </CriteriaItem>
                  <CriteriaItem met={/\d/.test(password)}>
                    <CriteriaIcon met={/\d/.test(password)}>
                      {/\d/.test(password) ? <FiCheck /> : <FiX />}
                    </CriteriaIcon>
                    Contains numbers
                  </CriteriaItem>
                </PasswordCriteria>
              </PasswordStrengthContainer>
            )}
          </FormGroup>

          <FormGroup>
            <Label>Confirm Password</Label>
            <InputWrapper>
              <InputIcon>
                <FiLock />
              </InputIcon>
              <Input
                type={showConfirm ? "text" : "password"}
                placeholder="••••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                disabled={isLoading}
              />
              <TogglePassword
                type="button"
                onClick={() => setShowConfirm(!showConfirm)}
                tabIndex={-1}
              >
                {showConfirm ? <FiEyeOff /> : <FiEye />}
              </TogglePassword>
            </InputWrapper>
            {confirmPassword && !passwordsMatch && (
              <div
                style={{ color: "#c53030", fontSize: "12px", marginTop: "6px" }}
              >
                Passwords do not match
              </div>
            )}
            {confirmPassword && passwordsMatch && (
              <div
                style={{ color: "#22543d", fontSize: "12px", marginTop: "6px" }}
              >
                Passwords match ✓
              </div>
            )}
          </FormGroup>

          <FormGroup>
            <CheckboxLabel>
              <input
                type="checkbox"
                checked={agreeTerms}
                onChange={(e) => setAgreeTerms(e.target.checked)}
                disabled={isLoading}
              />
              I agree to the terms and conditions and privacy policy
            </CheckboxLabel>
          </FormGroup>

          <SubmitButton type="submit" disabled={isLoading || !isFormValid}>
            {isLoading ? "Creating Account..." : "Create Account"}
          </SubmitButton>
        </form>

        <Divider>or</Divider>

        <OAuthContainer>
          <OAuthButton title="Sign up with Google">
            <FcGoogle size={24} />
          </OAuthButton>
          <OAuthButton title="Sign up with Apple">
            <SiApple size={24} />
          </OAuthButton>
          <OAuthButton title="Sign up with Microsoft">
            <FaMicrosoft size={24} color="#00a4ef" />
          </OAuthButton>
        </OAuthContainer>

        <LoginLink>
          Already have an account?{" "}
          <a onClick={() => navigate("/login")}>Sign in</a>
        </LoginLink>
      </Card>
    </PageContainer>
  );
}
