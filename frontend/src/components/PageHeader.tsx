import styled from 'styled-components';
import { colors, spacing, typography } from '../constants';
import { FiArrowLeft } from 'react-icons/fi';

const HeaderContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: ${spacing.xl};
  padding-bottom: ${spacing.lg};
  border-bottom: 2px solid ${colors.borderColor};
`;

const TitleSection = styled.div`
  display: flex;
  align-items: center;
  gap: ${spacing.md};
  flex: 1;
`;

const BackButton = styled.button`
  background: none;
  border: none;
  color: ${colors.teal};
  cursor: pointer;
  font-size: 1.5rem;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;

  &:hover {
    transform: translateX(-4px);
    color: ${colors.deepPurple};
  }
`;

const TitleContent = styled.div``;

const Title = styled.h1`
  font-size: ${typography.pageTitle.fontSize};
  font-weight: ${typography.pageTitle.fontWeight};
  color: ${typography.pageTitle.color};
  margin: 0;
  padding: 0;
  position: relative;
  display: inline-block;

  &::after {
    content: '';
    position: absolute;
    bottom: -4px;
    left: 0;
    width: 100%;
    height: 3px;
    background: linear-gradient(90deg, ${colors.teal} 0%, ${colors.purple} 100%);
    border-radius: 2px;
    animation: slideIn 0.6s ease-out;
  }

  @keyframes slideIn {
    from {
      width: 0;
    }
    to {
      width: 100%;
    }
  }
`;

const Subtitle = styled.p`
  font-size: 0.95rem;
  color: ${colors.lightText};
  margin: ${spacing.xs} 0 0 0;
`;

const ActionsContainer = styled.div`
  display: flex;
  gap: ${spacing.md};
  align-items: center;
`;

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  onBack?: () => void;
  actions?: React.ReactNode;
  showBackButton?: boolean;
}

export function PageHeader({
  title,
  subtitle,
  onBack,
  actions,
  showBackButton = false,
}: PageHeaderProps) {
  return (
    <HeaderContainer>
      <TitleSection>
        {showBackButton && onBack && (
          <BackButton onClick={onBack} aria-label="Go back">
            <FiArrowLeft />
          </BackButton>
        )}
        <TitleContent>
          <Title>{title}</Title>
          {subtitle && <Subtitle>{subtitle}</Subtitle>}
        </TitleContent>
      </TitleSection>
      {actions && <ActionsContainer>{actions}</ActionsContainer>}
    </HeaderContainer>
  );
}

export default PageHeader;
