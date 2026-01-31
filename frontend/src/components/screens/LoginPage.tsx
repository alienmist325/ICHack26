import styled from "styled-components";
import { useState } from "react";
import { Button } from "../layout/Button";

const LoginContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f8f9fa;
`;

const LoginForm = styled.div`
  background-color: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  width: 300px;
  text-align: center;
`;

const Input = styled.input`
  width: 100%;
  padding: 0.5rem;
  margin: 0.5rem 0;
  border: 1px solid #ddd;
  border-radius: 4px;
`;

export function LoginPage() {
  const [currentView, setCurrentView] = useState("search");

  return (
    <LoginContainer>
      <LoginForm>
        <h2>Login</h2>
        <Input type="email" placeholder="Email" />
        <Input type="password" placeholder="Password" />
        <Button>Login</Button>
      </LoginForm>
    </LoginContainer>
  );
}
