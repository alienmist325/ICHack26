import { ButtonHTMLAttributes, useState } from "react";
import reactLogo from "./assets/react.svg";
import viteLogo from "/vite.svg";
import "./App.css";
import styled from "styled-components";

function Button(props: ButtonHTMLAttributes<HTMLButtonElement> & SizeProps) {
  return <ButtonBox size={props.size ?? 1}> {props.children} </ButtonBox>;
}

interface SizeProps {
  size?: number;
}

const BottomRightCorner = styled.div`
  position: fixed;
  right: 0;
  bottom: 0;
  margin: 0.75rem;
`;

const TopLeftCorner = styled.div`
  position: fixed;
  left: 0;
  top: 0;
  margin: 0.75rem;
`;

const ButtonBox = styled.button<SizeProps>`
  font-size: ${(props) => props.size}rem;
  margin: 0.5rem;
`;

const VerticalList = styled.div`
  display: flex;
  flex-direction: column;
`;

function App() {
  const [count, setCount] = useState(0);

  return (
    <>
      <div>
        <a href="https://vite.dev" target="_blank">
          <img src={viteLogo} className="logo" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>
      <h1>Vite + React</h1>
      <div className="card">
        <button onClick={() => setCount((count) => count + 1)}>
          count is {count}
        </button>
        <p>
          Edit <code>src/App.tsx</code> and save to test HMR
        </p>
      </div>
      <p className="read-the-docs">
        Click on the Vite and React logos to learn more
      </p>
      <VerticalList>
        <Button size={5}>A thing</Button>
        <Button>A thing</Button>
        <Button>A thing</Button>
        <Button>A thing</Button>
        <Button>A thing</Button>
        <Button>A thing</Button>
        <Button>A thing</Button>
        <Button>A thing</Button>
      </VerticalList>

      <BottomRightCorner>
        <Button>@</Button>
      </BottomRightCorner>

      <TopLeftCorner>
        <Button>£</Button>
      </TopLeftCorner>
    </>
  );
}

export default App;
