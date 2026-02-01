import styled from "styled-components";
import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { FiMail, FiLock, FiEye, FiEyeOff } from "react-icons/fi";
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
  margin: 0 0 40px 0;
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

const RememberRow = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 24px 0;
  font-size: 13px;
`;

const CheckboxLabel = styled.label`
  display: flex;
  align-items: center;
  color: ${colors.medText};
  cursor: pointer;

  input {
    margin-right: 8px;
    width: 16px;
    height: 16px;
    cursor: pointer;
    accent-color: ${colors.teal};
  }
`;

const ForgotLink = styled.a`
  color: ${colors.teal};
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s;
  cursor: pointer;

  &:hover {
    color: ${colors.purple};
  }
`;

const SubmitButtonWrapper = styled.div`
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

const SignupLink = styled.p`
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

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isLoading, error } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);

    if (!email || !password) {
      setLocalError("Please enter email and password");
      return;
    }

    try {
      await login(email, password);
      // Redirect to the page the user was trying to visit, or to home
      const from = (location.state as any)?.from?.pathname || "/";
      navigate(from);
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Login failed");
    }
  };

  return (
    <PageContainer>
      <BackgroundPattern />
      <CardWrapper>
        <Title>Welcome Back</Title>
        <Subtitle>Sign in to your account to continue</Subtitle>

        {(error || localError) && (
          <ErrorMessage>{error || localError}</ErrorMessage>
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
          </FormGroup>

          <RememberRow>
            <CheckboxLabel>
              <input type="checkbox" />
              Remember me
            </CheckboxLabel>
            <ForgotLink>Forgot password?</ForgotLink>
          </RememberRow>

          <SubmitButtonWrapper>
            <Button
              variant="primary"
              style={{ width: "100%", textTransform: "uppercase", letterSpacing: "0.5px" }}
              type="submit"
              disabled={isLoading}
            >
              {isLoading ? "Signing in..." : "Sign In"}
            </Button>
          </SubmitButtonWrapper>
        </form>

        <Divider>or</Divider>

        <OAuthContainer>
          <OAuthButton title="Sign in with Google">
            <FcGoogle size={24} />
          </OAuthButton>
          <OAuthButton title="Sign in with Apple">
            <SiApple size={24} />
          </OAuthButton>
          <OAuthButton title="Sign in with Microsoft">
            <FaMicrosoft size={24} color="#00a4ef" />
          </OAuthButton>
        </OAuthContainer>

        <SignupLink>
          Don't have an account?{" "}
          <a onClick={() => navigate("/register")}>Sign up</a>
        </SignupLink>
      </CardWrapper>
    </PageContainer>
  );
}
