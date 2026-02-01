import { useEffect, useState } from "react";
import { api, LocationCoordinate, TravelTimeResult } from "../../api/client";

export function TravelTimeDisplay({ property_id }: { property_id: number }) {
  const [travelTimes, setTravelTimes] = useState<
    TravelTimeResult[] | undefined
  >(undefined);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const storedKeyLocations = localStorage.getItem("key_locations");
    if (storedKeyLocations) {
      const parsed = JSON.parse(storedKeyLocations) as LocationCoordinate[];

      setIsLoading(true);

      api
        .getTravelTimes({
          property_id,
          destinations: parsed,
        })
        .then((response) => {
          setTravelTimes(response.results);
          setIsLoading(false);
        })
        .catch((err) => {
          console.error("Failed to parse stored tokens:", err);
          localStorage.removeItem("auth_tokens");
        })
        .finally(() => {
          setIsLoading(false);
        });
    }
  }, []);

  return (
    <>
      {isLoading ? (
        <div>Loading...</div>
      ) : (
        travelTimes?.map((travelTime) => {
          <div>
            {travelTime.destination.label} is {travelTime.travel_time_minutes}{" "}
            minutes and {travelTime.travel_time_seconds} seconds away
          </div>;
        })
      )}
    </>
  );
}
