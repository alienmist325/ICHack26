import styled from 'styled-components';
import { colors } from '../constants';

const SpinnerWrapper = styled.div`
  display: inline-flex;
  align-items: center;
  justify-content: center;
`;

const SpinnerIcon = styled.div`
  width: 40px;
  height: 40px;
  border: 3px solid ${colors.borderColor};
  border-top: 3px solid ${colors.teal};
  border-radius: 50%;
  animation: spin 1s linear infinite;

  @keyframes spin {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }
`;

interface SpinnerProps {
  size?: 'small' | 'medium' | 'large';
  color?: string;
}

const SpinnerSizes = {
  small: '24px',
  medium: '40px',
  large: '60px',
};

const CustomSpinner = styled.div<{ $size: string; $color: string }>`
  width: ${(props) => props.$size};
  height: ${(props) => props.$size};
  border: 3px solid ${(props) => `${props.$color}20`};
  border-top: 3px solid ${(props) => props.$color};
  border-radius: 50%;
  animation: spin 1s linear infinite;

  @keyframes spin {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }
`;

export function Spinner({ size = 'medium', color = colors.teal }: SpinnerProps) {
  const sizeValue = SpinnerSizes[size];
  
  return (
    <SpinnerWrapper>
      <CustomSpinner $size={sizeValue} $color={color} />
    </SpinnerWrapper>
  );
}

export default Spinner;
