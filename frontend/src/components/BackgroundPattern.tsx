import styled from 'styled-components';
import { colors } from '../constants';

/**
 * Modern background pattern with subtle building outlines
 * Creates a professional, whimsical aesthetic with geometric buildings
 */
export const BackgroundPattern = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: ${colors.lightBg};
  z-index: -1;
  overflow: hidden;

  /* SVG background pattern with building outlines */
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 800"><defs><pattern id="buildings" x="0" y="0" width="200" height="400" patternUnits="userSpaceOnUse"><g fill="none" stroke="%23e2e8f0" stroke-width="0.5" opacity="0.4"><rect x="10" y="200" width="30" height="180"/><rect x="15" y="210" width="5" height="8"/><rect x="23" y="210" width="5" height="8"/><rect x="15" y="223" width="5" height="8"/><rect x="23" y="223" width="5" height="8"/><rect x="15" y="236" width="5" height="8"/><rect x="23" y="236" width="5" height="8"/><rect x="50" y="150" width="35" height="230"/><rect x="58" y="165" width="4" height="7"/><rect x="67" y="165" width="4" height="7"/><rect x="58" y="178" width="4" height="7"/><rect x="67" y="178" width="4" height="7"/><rect x="58" y="191" width="4" height="7"/><rect x="67" y="191" width="4" height="7"/><rect x="95" y="180" width="28" height="200"/><rect x="102" y="195" width="4" height="6"/><rect x="110" y="195" width="4" height="6"/><rect x="102" y="207" width="4" height="6"/><rect x="110" y="207" width="4" height="6"/><rect x="130" y="220" width="25" height="160"/><rect x="136" y="235" width="3" height="5"/><rect x="143" y="235" width="3" height="5"/><rect x="136" y="245" width="3" height="5"/><rect x="143" y="245" width="3" height="5"/></g></pattern></defs><rect width="1200" height="800" fill="url(%23buildings)"/></svg>');
  background-repeat: repeat;
  background-size: 300px 400px;
  background-position: 0 0;
`;

export default BackgroundPattern;
