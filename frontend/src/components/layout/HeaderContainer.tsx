import styled from "styled-components";
import { colors } from "../../constants";

export const HeaderContainer = styled.header`
  flex: 0 0 auto;
  background-color: ${colors.rightMoveBlue};
  color: white;
  z-index: 10;
  display: flex;
  padding: 1rem;
  font-size: 2rem;
  justify-content: center;
  font-weight: 800;
`;
