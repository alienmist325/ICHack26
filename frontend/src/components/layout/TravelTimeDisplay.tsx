import { useEffect, useState } from "react";
import { api, TravelTimeResult } from "../../api/client";
import { useGlobalData } from "../hooks/useGlobalData";
import { useToast } from "../hooks/useToast";
import { CardContainer } from "./HouseCard";

export function TravelTimeDisplay({ property_id }: { property_id: number }) {
  const [travelTimes, setTravelTimes] = useState<
    TravelTimeResult[] | undefined
  >(undefined);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const { keyLocations } = useGlobalData();

  const { addToast } = useToast();

  console.log(isLoading);

  useEffect(() => {
    const parsed = keyLocations;

    setIsLoading(true);

    api
      .getTravelTimes({
        property_id,
        destinations: parsed,
      })
      .then((response) => {
        console.log(response.results);
        setTravelTimes(response.results);
        addToast("Successfully computed routes to key locations", "success");
      })
      .catch((err) => {
        console.error("Failed to parse key locations:", err);
        addToast("Failed to parse key locations", "error");
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, []);

  return (
    <CardContainer>
      {isLoading ? (
        <div>Loading...</div>
      ) : travelTimes ? (
        travelTimes.map((travelTime) => (
          <div>
            {travelTime.destination.label} is{" "}
            {travelTime.travel_time_minutes.toPrecision(2) + " "}
            minutes away
          </div>
        ))
      ) : (
        <div> You haven't specified any key locations yet. </div>
      )}
    </CardContainer>
  );
}
