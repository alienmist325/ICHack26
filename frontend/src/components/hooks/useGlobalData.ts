import { useContext } from "react";
import { GlobalDataContext } from "./useSetupGlobalData";
import { GlobalData } from "../../types";

export function useGlobalData() {
  return useContext(GlobalDataContext) as GlobalData;
}
