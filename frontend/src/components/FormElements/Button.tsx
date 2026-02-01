import styled from 'styled-components';
import { colors, spacing, borderRadius, animations, shadows } from '../../constants';

interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'danger' | 'accent';
  disabled?: boolean;
  loading?: boolean;
}

const getButtonStyles = (variant: string = 'primary') => {
  switch (variant) {
    case 'secondary':
      return `
        background-color: ${colors.white};
        color: ${colors.teal};
        border: 2px solid ${colors.teal};
        
        &:hover:not(:disabled) {
          background-color: ${colors.teal};
          color: ${colors.white};
        }
      `;
    case 'danger':
      return `
        background-color: ${colors.error};
        color: ${colors.white};
        border: 2px solid ${colors.error};
        
        &:hover:not(:disabled) {
          background-color: #e53e3e;
          box-shadow: ${shadows.hover};
        }
      `;
    case 'accent':
      return `
        background: linear-gradient(135deg, ${colors.purple} 0%, ${colors.deepPurple} 100%);
        color: ${colors.white};
        border: none;
        
        &:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: ${shadows.card};
        }
      `;
    case 'primary':
    default:
      return `
        background-color: ${colors.teal};
        color: ${colors.white};
        border: 2px solid ${colors.teal};
        
        &:hover:not(:disabled) {
          box-shadow: ${shadows.hover};
          transform: translateY(-2px);
        }
      `;
  }
};

export const Button = styled.button<ButtonProps>`
  padding: ${spacing.sm} ${spacing.lg};
  font-size: 1rem;
  font-weight: 500;
  border-radius: ${borderRadius.buttons};
  cursor: pointer;
  transition: all ${animations.base};
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: ${spacing.sm};
  font-family: inherit;
  
  ${(props) => getButtonStyles(props.variant)}

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  &:active:not(:disabled) {
    transform: translateY(0);
  }
`;

export default Button;
