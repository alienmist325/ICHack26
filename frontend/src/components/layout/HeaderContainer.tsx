import styled from "styled-components";
import { colors, spacing, animations, shadows } from "../../constants";

export const HeaderContainer = styled.header`
  flex: 0 0 auto;
  background-color: ${colors.white};
  color: ${colors.darkText};
  z-index: 10;
  display: flex;
  padding: ${spacing.lg} ${spacing.xl};
  font-size: 1.3rem;
  justify-content: center;
  font-weight: 600;
  border-bottom: 2px solid ${colors.borderColor};
  box-shadow: ${shadows.light};
  position: relative;

  &::after {
    content: '';
    position: absolute;
    bottom: -2px;
    left: 0;
    width: 100%;
    height: 3px;
    background: linear-gradient(90deg, ${colors.teal} 0%, ${colors.purple} 100%);
    animation: slideInWidth 0.6s ease-out;
  }

  @keyframes slideInWidth {
    from {
      width: 0;
    }
    to {
      width: 100%;
    }
  }
`;
