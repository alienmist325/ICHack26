import { createContext, useState } from "react";
import { GlobalData, House } from "../../types";

export const GlobalDataContext = createContext<GlobalData | null>(null);

export function useSetupGlobalData(): GlobalData {
  const [randomConfig, setRandomConfig] = useState<string | undefined>(
    "this is a thing"
  );
  const [houses, setHouses] = useState<House[]>(getHouses());

  return {
    randomConfig,
    setRandomConfig,
    houses,
    setHouses,
  };
}

function getHouses() {
  const house1: House = {
    address: "123 Example St, Exampletown",
    listingTitle: "Beautiful 3 Bedroom House",
    listingUrl: "http://example.com/listing/123",
    price: 350000,
    rightmoveId: "12345678",
    id: "1",
    bedrooms: 3,
    bathrooms: 2,
    features: ["Garden", "Garage", "Close to schools"],
  };
  const house2: House = {
    address: "456 Sample Ave, Samplecity",
    listingTitle: "Modern 2 Bedroom Apartment",
    listingUrl: "http://example.com/listing/456",
    price: 250000,
    rightmoveId: "87654321",
    id: "2",
    bedrooms: 2,
    bathrooms: 1,
    features: ["Balcony", "City View", "Gym Access"],
  };
  const house3: House = {...house1, id: "3", rightmoveId: "11223344", listingTitle: "Cozy 4 Bedroom Cottage"};
  return [house1, house2, house3];
}
