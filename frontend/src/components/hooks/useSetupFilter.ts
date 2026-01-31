import { createContext, useState } from "react";
import { Filter } from "../../types";

export const FilterContext = createContext<Filter | null>(null);

export function useSetupFilter(): Filter {
  const [maxPrice, setMaxPrice] = useState<number | undefined>(100);

  return {
    maxPrice,
    setMaxPrice,
  };
}
