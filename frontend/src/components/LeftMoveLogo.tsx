import styled from 'styled-components';
import { colors } from '../constants';

const LogoContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    transform: scale(1.05);
  }
`;

const LogoIcon = styled.svg`
  width: 40px;
  height: 40px;
  flex-shrink: 0;
`;

const LogoText = styled.span`
  font-size: 1.3rem;
  font-weight: 700;
  color: ${colors.darkText};
  letter-spacing: -0.5px;
`;

interface LeftMoveLogoProps {
  onClick?: () => void;
}

export function LeftMoveLogo({ onClick }: LeftMoveLogoProps) {
  return (
    <LogoContainer onClick={onClick}>
      <LogoIcon viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        {/* House outline */}
        <path
          d="M 20 50 L 50 20 L 80 50 L 75 50 L 75 80 L 25 80 L 25 50 L 20 50"
          fill="none"
          stroke={colors.teal}
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        {/* L shape inside house (left side) */}
        <path
          d="M 30 35 L 30 70 L 40 70"
          fill="none"
          stroke={colors.purple}
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        {/* M shape inside house (right side) */}
        <path
          d="M 60 35 L 60 70 M 60 35 L 65 45 L 70 35 L 70 70"
          fill="none"
          stroke={colors.purple}
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </LogoIcon>
      <LogoText>LeftMove</LogoText>
    </LogoContainer>
  );
}

export default LeftMoveLogo;
