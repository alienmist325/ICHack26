import styled from "styled-components";
import { FiLogOut, FiUser, FiSettings, FiHeart } from "react-icons/fi";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import { colors, animations } from "../../constants";
import LeftMoveLogo from "../LeftMoveLogo";

const HeaderContainer = styled.header`
  flex: 0 0 auto;
  background-color: ${colors.white};
  color: ${colors.darkText};
  z-index: 10;
  display: flex;
  padding: 1rem 1.5rem;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  border-bottom: 2px solid ${colors.borderColor};
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  position: relative;

  &::after {
    content: '';
    position: absolute;
    bottom: -2px;
    left: 0;
    width: 100%;
    height: 3px;
    background: linear-gradient(90deg, ${colors.teal} 0%, ${colors.purple} 100%);
  }
`;

const LogoContainer = styled.div`
  display: flex;
  align-items: center;
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

export function UnifiedHeader() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <HeaderContainer>
      <LogoContainer>
        <LeftMoveLogo onClick={() => navigate('/')} />
      </LogoContainer>

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
  );
}

export default UnifiedHeader;
