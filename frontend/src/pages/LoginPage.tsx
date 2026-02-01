import styled from 'styled-components';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { FiMail, FiLock, FiEye, FiEyeOff } from 'react-icons/fi';
import { FcGoogle } from 'react-icons/fc';
import { SiApple, SiMicrosoft } from 'react-icons/si';

const PageContainer = styled.div`
  min-height: 100vh;
  width: 100%;
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
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;

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
  color: #4a5568;
  cursor: pointer;

  input {
    margin-right: 8px;
    width: 16px;
    height: 16px;
    cursor: pointer;
  }
`;

const ForgotLink = styled.a`
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s;

  &:hover {
    color: #764ba2;
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
    content: '';
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

const SignupLink = styled.p`
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

export function LoginPage() {
  const navigate = useNavigate();
  const { login, isLoading, error } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);

    if (!email || !password) {
      setLocalError('Please enter email and password');
      return;
    }

    try {
      await login(email, password);
      navigate('/');
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : 'Login failed');
    }
  };

  return (
    <PageContainer>
      <Card>
        <Title>Welcome Back</Title>
        <Subtitle>Sign in to your account to continue</Subtitle>

        {(error || localError) && <ErrorMessage>{error || localError}</ErrorMessage>}

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
                type={showPassword ? 'text' : 'password'}
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
          </FormGroup>

          <RememberRow>
            <CheckboxLabel>
              <input type="checkbox" />
              Remember me
            </CheckboxLabel>
            <ForgotLink href="#">Forgot password?</ForgotLink>
          </RememberRow>

          <SubmitButton type="submit" disabled={isLoading}>
            {isLoading ? 'Signing in...' : 'Sign In'}
          </SubmitButton>
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
            <SiMicrosoft size={24} color="#00a4ef" />
          </OAuthButton>
        </OAuthContainer>

        <SignupLink>
          Don't have an account? <a onClick={() => navigate('/register')}>Sign up</a>
        </SignupLink>
      </Card>
    </PageContainer>
  );
}
