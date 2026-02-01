import styled from "styled-components";
import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { FiMail, FiLock, FiEye, FiEyeOff, FiCheck, FiX } from "react-icons/fi";
import { FcGoogle } from "react-icons/fc";
import { SiApple } from "react-icons/si";
import { FaMicrosoft } from "react-icons/fa";
import BackgroundPattern from "../components/BackgroundPattern";
import Button from "../components/FormElements/Button";
import FormInput from "../components/FormElements/Input";
import CardComponent from "../components/FormElements/Card";
import { colors, spacing, animations } from "../constants";

const PageContainer = styled.div`
  min-height: 100vh;
  width: 100vw;
  box-sizing: border-box;
  background: ${colors.lightBg};
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
  position: relative;
`;

const CardWrapper = styled(CardComponent)`
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
  color: ${colors.darkText};
  margin: 0 0 10px 0;
  letter-spacing: -0.5px;
`;

const Subtitle = styled.p`
  font-size: 14px;
  color: ${colors.lightText};
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
  color: ${colors.medText};
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const InputWrapper = styled.div`
  position: relative;
  display: flex;
  align-items: center;
`;

const InputIcon = styled.div`
  position: absolute;
  left: 14px;
  color: ${colors.lightText};
  font-size: 18px;
  pointer-events: none;
`;

const TogglePassword = styled.button`
  position: absolute;
  right: 14px;
  background: none;
  border: none;
  color: ${colors.lightText};
  font-size: 18px;
  cursor: pointer;
  transition: color 0.2s;

  &:hover {
    color: ${colors.teal};
  }
`;

const PasswordStrengthContainer = styled.div`
  margin-top: 12px;
`;

const StrengthBar = styled.div`
  height: 6px;
  background: ${colors.borderColor};
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
    if (props.strength < 2) return colors.error;
    if (props.strength < 3) return colors.warning;
    if (props.strength < 4) return colors.info;
    return colors.success;
  }};
  transition:
    width 0.3s ease,
    background 0.3s ease;
`;

const PasswordCriteria = styled.div`
  font-size: 12px;
  color: ${colors.lightText};
`;

const CriteriaItem = styled.div<{ met?: boolean }>`
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 4px 0;
  color: ${(props) => (props.met ? colors.success : colors.lightText)};
`;

const CriteriaIcon = styled.span<{ met?: boolean }>`
  font-size: 14px;
  color: ${(props) => (props.met ? colors.success : colors.borderColor)};
`;

const CheckboxLabel = styled.label`
  display: flex;
  align-items: flex-start;
  gap: 8px;
  color: ${colors.medText};
  cursor: pointer;
  font-size: 13px;
  line-height: 1.5;

  input {
    margin-top: 3px;
    width: 16px;
    height: 16px;
    cursor: pointer;
    flex-shrink: 0;
    accent-color: ${colors.teal};
  }
`;

const SubmitButtonWrapper = styled.div`
  margin-top: 20px;
  margin-bottom: 20px;
`;

const Divider = styled.div`
  display: flex;
  align-items: center;
  margin: 30px 0;
  color: ${colors.lightText};
  font-size: 13px;

  &::before,
  &::after {
    content: "";
    flex: 1;
    height: 1px;
    background: ${colors.borderColor};
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
  border: 2px solid ${colors.borderColor};
  background: ${colors.white};
  border-radius: 10px;
  cursor: pointer;
  font-size: 18px;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;

  &:hover {
    border-color: ${colors.teal};
    background: ${colors.lightBg};
    transform: translateY(-2px);
  }
`;

const LoginLink = styled.p`
  text-align: center;
  font-size: 14px;
  color: ${colors.medText};
  margin: 0;

  a {
    color: ${colors.teal};
    text-decoration: none;
    font-weight: 600;
    cursor: pointer;
    transition: color 0.2s;

    &:hover {
      color: ${colors.purple};
    }
  }
`;

const ErrorMessage = styled.div`
  background: ${colors.error}15;
  color: ${colors.error};
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 20px;
  font-size: 13px;
  animation: slideDown 0.3s ease-out;
  border: 1px solid ${colors.error}30;

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
  background: ${colors.success}15;
  color: ${colors.success};
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 20px;
  font-size: 13px;
  animation: slideDown 0.3s ease-out;
  border: 1px solid ${colors.success}30;

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
      <BackgroundPattern />
      <CardWrapper>
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
              <FormInput
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={isLoading}
                style={{ paddingLeft: "44px" }}
              />
            </InputWrapper>
          </FormGroup>

          <FormGroup>
            <Label>Password</Label>
            <InputWrapper>
              <InputIcon>
                <FiLock />
              </InputIcon>
              <FormInput
                type={showPassword ? "text" : "password"}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={isLoading}
                style={{ paddingLeft: "44px", paddingRight: "44px" }}
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
              <FormInput
                type={showConfirm ? "text" : "password"}
                placeholder="••••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                disabled={isLoading}
                style={{ paddingLeft: "44px", paddingRight: "44px" }}
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
                style={{ color: colors.error, fontSize: "12px", marginTop: "6px" }}
              >
                Passwords do not match
              </div>
            )}
            {confirmPassword && passwordsMatch && (
              <div
                style={{ color: colors.success, fontSize: "12px", marginTop: "6px" }}
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

          <SubmitButtonWrapper>
            <Button
              variant="primary"
              style={{ width: "100%", textTransform: "uppercase", letterSpacing: "0.5px" }}
              type="submit"
              disabled={isLoading || !isFormValid}
            >
              {isLoading ? "Creating Account..." : "Create Account"}
            </Button>
          </SubmitButtonWrapper>
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
      </CardWrapper>
    </PageContainer>
  );
}
