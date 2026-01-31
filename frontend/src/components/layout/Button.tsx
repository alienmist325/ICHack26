import { ButtonHTMLAttributes } from "react";
import styled from "styled-components";

interface SizeProps {
  size?: number;
}

export function Button(
  props: ButtonHTMLAttributes<HTMLButtonElement> & SizeProps
) {
  return <ButtonBox size={props.size ?? 1}> {props.children} </ButtonBox>;
}

const ButtonBox = styled.button<SizeProps>`
  font-size: ${(props) => props.size}rem;
  margin: 0.5rem;
`;
