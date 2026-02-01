import styled from "styled-components";
import { useState } from "react";
import { FiLogOut, FiUser, FiSettings, FiHeart } from "react-icons/fi";
import { useNavigate } from "react-router-dom";
import { HeaderContainer } from "../components/layout/HeaderContainer";
import { FooterContainer } from "../components/layout/FooterContainer";
import { HouseSearch } from "../components/screens/HouseSearch";
import { colors, spacing, animations } from "../constants";
import { useAuth } from "../hooks/useAuth";
import BackgroundPattern from "../components/BackgroundPattern";
import LeftMoveLogo from "../components/LeftMoveLogo";

const AppContent = styled.div`
  flex: 1;
  overflow: auto;
  background: ${colors.lightBg};
  position: relative;
  scroll-behavior: smooth;
  
  /* Smooth scroll for webkit browsers */
  scrollbar-width: thin;
  scrollbar-color: ${colors.teal}40 transparent;

  &::-webkit-scrollbar {
    width: 8px;
  }

  &::-webkit-scrollbar-track {
    background: transparent;
  }

  &::-webkit-scrollbar-thumb {
    background: ${colors.teal}40;
    border-radius: 4px;
    transition: background 0.3s ease;

    &:hover {
      background: ${colors.teal}60;
    }
  }
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
  animation: fadeIn 0.4s ease-out;

  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
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

const IconsContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
`;

const LogoAndText = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
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

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <>
      <HeaderContainer>
        <LogoAndText>
          <LeftMoveLogo onClick={() => navigate('/')} />
        </LogoAndText>

        <IconsContainer>
          <IconButton 
            onClick={handleLogout}
            title="Logout"
          >
            <FiLogOut />
          </IconButton>
          <IconButton 
            onClick={() => navigate('/settings')} 
            title="Settings"
          >
            <FiSettings />
          </IconButton>
          <IconButton 
            onClick={() => navigate('/favorites')} 
            title="Favorites"
          >
            <FiHeart />
          </IconButton>
          {user && (
            <AccountIcon 
              onClick={() => navigate('/profile')} 
              title={user.email}
            >
              <FiUser />
            </AccountIcon>
          )}
        </IconsContainer>
      </HeaderContainer>
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
