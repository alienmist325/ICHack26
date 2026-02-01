import styled from "styled-components";
import { useState } from "react";
import { GiMushroomHouse } from "react-icons/gi";
import { FiLogOut, FiUser } from "react-icons/fi";
import { useNavigate } from "react-router-dom";
import { HeaderContainer } from "../components/layout/HeaderContainer";
import { FooterContainer } from "../components/layout/FooterContainer";
import { HouseSearch } from "../components/screens/HouseSearch";
import { NavigationPane } from "../components/layout/NavigationPane";
import { colors } from "../constants";
import { Button } from "../components/layout/Button";
import { useAuth } from "../hooks/useAuth";

const AppContent = styled.div`
  flex: 1;
  overflow: auto;
`;

const SidebarButton = styled(Button)`
  background-color: ${colors.rightMoveBlue};
  margin-left: 12px;
`;

const TopRightCorner = styled.div`
  position: absolute;
  right: 0;
  top: 0;
  margin: 0.75rem;
  display: flex;
  gap: 12px;
`;

const CenteredContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  gap: 20px;
`;

const UserInfo = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  color: ${colors.rightMoveBlue};
  font-size: 14px;
`;

const UserEmail = styled.span`
  font-weight: 500;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;

  @media (max-width: 768px) {
    display: none;
  }
`;

const UserButton = styled(Button)`
  background-color: transparent;
  color: ${colors.rightMoveBlue};
  border: 2px solid ${colors.rightMoveBlue};
  padding: 8px 12px;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;

  &:hover {
    background-color: ${colors.rightMoveBlue};
    color: white;
  }
`;

const LogoutButton = styled(UserButton)`
  border-color: #e53e3e;
  color: #e53e3e;

  &:hover {
    background-color: #e53e3e;
  }
`;

export function HouseSearchLayout() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [leftSidebarOpen, setLeftSidebarOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const toggleLeftSidebar = () => setLeftSidebarOpen(!leftSidebarOpen);

  return (
    <>
      <HeaderContainer>
        <>
          <CenteredContainer>
            <GiMushroomHouse />
            Not Rightmove
          </CenteredContainer>

          <TopRightCorner>
            {user && (
              <UserInfo>
                <UserButton onClick={() => navigate('/profile')}>
                  <FiUser />
                  <span>Profile</span>
                </UserButton>
                <UserEmail title={user.email}>{user.email}</UserEmail>
              </UserInfo>
            )}
            <LogoutButton onClick={handleLogout}>
              <FiLogOut />
              <span>Logout</span>
            </LogoutButton>
            <SidebarButton onClick={toggleLeftSidebar}>☰</SidebarButton>
          </TopRightCorner>
        </>
      </HeaderContainer>
      <NavigationPane
        leftSidebarOpen={leftSidebarOpen}
        toggleLeftSidebar={toggleLeftSidebar}
      />
      <AppContent>
        <HouseSearch />
      </AppContent>
      <FooterContainer>Made for IC Hack 2026</FooterContainer>
    </>
  );
}
