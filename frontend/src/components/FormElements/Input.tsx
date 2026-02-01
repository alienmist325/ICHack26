import styled from 'styled-components';
import { colors, spacing, borderRadius, animations, shadows } from '../../constants';

export const Input = styled.input`
  width: 100%;
  padding: ${spacing.sm} ${spacing.md};
  font-size: 1rem;
  font-family: inherit;
  background-color: ${colors.lightBg};
  color: ${colors.darkText};
  border: 2px solid ${colors.borderColor};
  border-radius: ${borderRadius.inputs};
  transition: all ${animations.base};

  &:hover {
    border-color: ${colors.teal};
  }

  &:focus {
    outline: none;
    border-color: ${colors.teal};
    background-color: ${colors.white};
    box-shadow: 0 0 0 3px rgba(73, 223, 181, 0.1);
  }

  &:disabled {
    background-color: #f0f0f0;
    color: ${colors.lightText};
    cursor: not-allowed;
  }

  &::placeholder {
    color: ${colors.lightText};
  }
`;

export default Input;
