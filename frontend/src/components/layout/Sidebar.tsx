import styled from "styled-components";

export const Sidebar = styled.div<{ isOpen: boolean }>`
  position: fixed;
  top: 0;
  right: 0;
  width: 3rem;
  height: 100%;
  background-color: #49dfb5;
  border-left: 1px solid #000000ff;
  transform: translateX(${(props) => (props.isOpen ? "0" : "100%")});
  transition: transform 0.3s ease;
  z-index: 1000;
  padding: 1rem;
  overflow-y: auto;
`;
