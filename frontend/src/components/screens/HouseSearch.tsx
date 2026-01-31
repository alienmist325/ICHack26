import styled from "styled-components";
import { Scrollable } from "../layout/Scrollable";
import { useState } from "react";
import { Button } from "../layout/Button";
import reactLogo from "../../assets/react.svg";
import viteLogo from "/vite.svg";
import { useGlobalData } from "../hooks/useGlobalData";
import { HouseCard } from "../layout/HouseCard";

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

const LeftSidebar = styled.div<{ isOpen: boolean }>`
  position: fixed;
  top: 0;
  left: 0;
  width: 250px;
  height: 100%;
  background-color: #49dfb5;
  border-right: 1px solid #000000ff;
  transform: translateX(${props => props.isOpen ? '0' : '-100%'});
  transition: transform 0.3s ease;
  z-index: 1000;
  padding: 1rem;
  overflow-y: auto;
`;

const Overlay = styled.div<{ isOpen: boolean }>`
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  opacity: ${props => props.isOpen ? 1 : 0};
  visibility: ${props => props.isOpen ? 'visible' : 'hidden'};
  transition: opacity 0.3s ease, visibility 0.3s ease;
  z-index: 999;
`;

const NavItem = styled.button`
  display: block;
  width: 100%;
  padding: 0.75rem;
  margin-bottom: 0.5rem;
  border: none;
  background-color: transparent;
  text-align: left;
  cursor: pointer;
  border-radius: 4px;
  &:hover {
    background-color: #7cf1d0ff;
  }
`;

export function HouseSearch() {
  const [count, setCount] = useState(0);
  const [leftSidebarOpen, setLeftSidebarOpen] = useState(false);

  const toggleLeftSidebar = () => setLeftSidebarOpen(!leftSidebarOpen);
  const{ houses } = useGlobalData();

  return (
    <ContentArea>
      <Scrollable>
        <VerticalList>
            {houses.map(house => (
              <HouseCard key={house.id} house={house} />
            ))}
        </VerticalList>
      </Scrollable>

      <TopLeftCorner>
        <Button onClick={toggleLeftSidebar}>☰</Button>
      </TopLeftCorner>

      <Overlay isOpen={leftSidebarOpen} onClick={toggleLeftSidebar} />
      <LeftSidebar isOpen={leftSidebarOpen}>
        <h2>Navigation</h2>
        <NavItem>Home</NavItem>
        <NavItem>Search Houses</NavItem>
        <NavItem>Favorites</NavItem>
        <NavItem>Profile</NavItem>
        <NavItem>Settings</NavItem>
      </LeftSidebar>
    </ContentArea>
  );
}
