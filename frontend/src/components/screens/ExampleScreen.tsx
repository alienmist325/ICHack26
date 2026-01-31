import styled from "styled-components";
import { Scrollable } from "../layout/Scrollable";
import { useState } from "react";
import { Button } from "../layout/Button";
import reactLogo from "../../assets/react.svg";
import viteLogo from "/vite.svg";

const ContentArea = styled.div`
  flex: 1;
  position: relative;
  display: flex;
  flex-direction: column;
  min-height: 0;
`;

const BottomRightCorner = styled.div`
  position: absolute;
  right: 0;
  bottom: 0;
  margin: 0.75rem;
`;

const TopLeftCorner = styled.div`
  position: absolute;
  left: 0;
  top: 0;
  margin: 0.75rem;
`;

const VerticalList = styled.div`
  display: flex;
  flex-direction: column;
`;

export function ExampleScreen() {
  const [count, setCount] = useState(0);

  return (
    <ContentArea>
      <Scrollable>
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
      </Scrollable>
      <BottomRightCorner>
        <Button>@</Button>
      </BottomRightCorner>

      <TopLeftCorner>
        <Button>£</Button>
      </TopLeftCorner>
    </ContentArea>
  );
}
