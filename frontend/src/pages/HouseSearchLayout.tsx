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

const SidebarButton = styled.button`
  background: none;
  border: none;
  color: ${colors.medText};
  cursor: pointer;
  font-size: 1.5rem;
  transition: all ${animations.base};
  padding: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  margin-left: 8px;

  &:hover {
    color: ${colors.teal};
    background-color: ${colors.teal}15;
    transform: translateY(-2px);
  }

  &:active {
    transform: scale(0.95);
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



const IconButton = styled.button`
  background: none;
  border: none;
  color: ${colors.medText};
  cursor: pointer;
  font-size: 1.5rem;
  transition: all ${animations.base};
  padding: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;

  &:hover {
    color: ${colors.teal};
    background-color: ${colors.teal}15;
    transform: translateY(-2px);
  }

  &:active {
    transform: scale(0.95);
  }
`;

const AccountIcon = styled.div`
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: ${colors.teal}20;
  border: 2px solid ${colors.teal};
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.3rem;
  color: ${colors.teal};
  cursor: pointer;
  transition: all ${animations.base};

  &:hover {
    background-color: ${colors.teal}30;
    transform: scale(1.05);
  }

  &:active {
    transform: scale(0.95);
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
              <AccountIcon 
                onClick={() => navigate('/profile')} 
                title={user.email}
              >
                <FiUser />
              </AccountIcon>
            )}
            <IconButton 
              onClick={() => navigate('/settings')} 
              title="Settings"
            >
              <FiSettings />
            </IconButton>
            <IconButton 
              onClick={handleLogout}
              title="Logout"
            >
              <FiLogOut />
            </IconButton>
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
