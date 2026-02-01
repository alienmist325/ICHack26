import styled from 'styled-components';
import { colors, spacing, borderRadius, shadows } from '../../constants';

export const Card = styled.div`
  background: ${colors.white};
  border-radius: ${borderRadius.cards};
  box-shadow: ${shadows.card};
  padding: ${spacing.xl};
  transition: all 0.3s ease;

  &:hover {
    box-shadow: 0 15px 50px rgba(0, 0, 0, 0.15);
    transform: translateY(-2px);
  }
`;

export default Card;
