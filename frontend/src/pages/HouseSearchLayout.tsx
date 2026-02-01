import styled from "styled-components";
import { useState } from "react";
import { GiMushroomHouse } from "react-icons/gi";
import { FiLogOut, FiUser, FiSettings } from "react-icons/fi";
import { useNavigate } from "react-router-dom";
import { HeaderContainer } from "../components/layout/HeaderContainer";
import { FooterContainer } from "../components/layout/FooterContainer";
import { HouseSearch } from "../components/screens/HouseSearch";
import { NavigationPane } from "../components/layout/NavigationPane";
import { colors, animations, spacing } from "../constants";
import { Button } from "../components/layout/Button";
import { useAuth } from "../hooks/useAuth";
import BackgroundPattern from "../components/BackgroundPattern";

const AppContent = styled.div`
  flex: 1;
  overflow: auto;
  background: ${colors.lightBg};
  position: relative;
`;

const BackgroundPatternWrapper = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 0;
`;

const ContentWrapper = styled.div`
  position: relative;
  z-index: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
`;

const SidebarButton = styled(Button)`
  background-color: ${colors.teal};
  margin-left: 12px;
  border: 2px solid ${colors.teal};
  color: white;
  transition: all ${animations.base};

  &:hover {
    background-color: ${colors.white};
    color: ${colors.teal};
    transform: translateY(-2px);
  }
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
  font-size: 1.3rem;
  font-weight: 600;
  color: ${colors.medText};
`;

const LogoIcon = styled.div`
  font-size: 2rem;
  animation: float 3s ease-in-out infinite;

  @keyframes float {
    0%, 100% {
      transform: translateY(0px);
    }
    50% {
      transform: translateY(-8px);
    }
  }
`;

const UserInfo = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  color: ${colors.medText};
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
  color: ${colors.teal};
  border: 2px solid ${colors.teal};
  padding: 8px 12px;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all ${animations.base};

  &:hover {
    background-color: ${colors.teal};
    color: white;
    transform: translateY(-2px);
  }
`;

const LogoutButton = styled(UserButton)`
  border-color: ${colors.error};
  color: ${colors.error};

  &:hover {
    background-color: ${colors.error};
  }
`;

const SettingsButton = styled(UserButton)`
  border-color: ${colors.purple};
  color: ${colors.purple};

  &:hover {
    background-color: ${colors.purple};
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
            <LogoIcon>
              <GiMushroomHouse />
            </LogoIcon>
            Not Rightmove
          </CenteredContainer>

          <TopRightCorner>
            {user && (
              <UserInfo>
                <UserButton onClick={() => navigate('/profile')}>
                  <FiUser />
                  <span>Profile</span>
                </UserButton>
                <SettingsButton onClick={() => navigate('/settings')}>
                  <FiSettings />
                  <span>Settings</span>
                </SettingsButton>
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
        <BackgroundPatternWrapper>
          <BackgroundPattern />
        </BackgroundPatternWrapper>
        <ContentWrapper>
          <HouseSearch />
        </ContentWrapper>
      </AppContent>
      <FooterContainer>Made for IC Hack 2026</FooterContainer>
    </>
  );
}
