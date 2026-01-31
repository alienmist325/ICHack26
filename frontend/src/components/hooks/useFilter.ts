import { useContext } from "react";
import { Filter } from "../../types";
import { FilterContext } from "./useSetupFilter";

export function useFilter() {
  return useContext(FilterContext) as Filter;
}
