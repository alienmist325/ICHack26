import { createContext, useState } from "react";
import { GlobalData } from "../../types";

export const GlobalDataContext = createContext<GlobalData | null>(null);

export function useSetupGlobalData(): GlobalData {
  const [randomConfig, setRandomConfig] = useState<string | undefined>(
    "this is a thing"
  );

  return {
    randomConfig,
    setRandomConfig,
  };
}
