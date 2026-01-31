import { ButtonHTMLAttributes } from "react";
import styled from "styled-components";

interface SizeProps {
  size?: number;
}

export function Button(
  props: ButtonHTMLAttributes<HTMLButtonElement> & SizeProps
) {
  const { size, ...rest } = props;
  return <ButtonBox size={size ?? 1} {...rest}> {props.children} </ButtonBox>;
}

const ButtonBox = styled.button<SizeProps>`
  font-size: ${(props) => props.size}rem;
  margin: 0.5rem;
`;
