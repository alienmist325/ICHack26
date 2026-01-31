import styled from "styled-components";

interface NavigationPanelProps {
  toggleLeftSidebar: () => void;
  leftSidebarOpen: boolean;
}

const RightSidebar = styled.div<{ isOpen: boolean }>`
  position: fixed;
  top: 0;
  right: 0;
  width: 250px;
  height: 100%;
  background-color: #49dfb5;
  border-left: 1px solid #000000ff;
  transform: translateX(${(props) => (props.isOpen ? "0" : "100%")});
  transition: transform 0.3s ease;
  z-index: 1000;
  padding: 1rem;
  overflow-y: auto;
`;

const RightOverlay = styled.div<{ isOpen: boolean }>`
  position: fixed;
  top: 0;
  right: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  opacity: ${(props) => (props.isOpen ? 1 : 0)};
  visibility: ${(props) => (props.isOpen ? "visible" : "hidden")};
  transition:
    opacity 0.3s ease,
    visibility 0.3s ease;
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

export function NavigationPane({
  toggleLeftSidebar,
  leftSidebarOpen,
}: NavigationPanelProps) {
  return (
    <>
      <RightOverlay isOpen={leftSidebarOpen} onClick={toggleLeftSidebar} />
      <RightSidebar isOpen={leftSidebarOpen}>
        <h2>Navigation</h2>
        <NavItem>Home</NavItem>
        <NavItem>Search Houses</NavItem>
        <NavItem>Favorites</NavItem>
        <NavItem>Profile</NavItem>
        <NavItem>Settings</NavItem>
      </RightSidebar>
    </>
  );
}
