import { House } from "../../types";
import { Button } from "./Button";

import { IoBed } from "react-icons/io5";
import { GiHouse } from "react-icons/gi";
import { FaMoneyBillAlt } from "react-icons/fa";
import { FaToiletPaper } from "react-icons/fa6";

export interface HouseCardProps {
  house: House;
}

export function HouseCard(props: HouseCardProps) {
  const { house } = props;
  return (
    <Button size={2}>
      <div style={{ display: "flex", alignItems: "center", gap: "5rem" }}>
        <div style={{ fontSize: "8em" }}>
          <GiHouse />
        </div>
        <div style={{ textAlign: "left" }}>
          <h2>{house.listingTitle}</h2>
          <p style={{ fontSize: "0.8em" }}>
            {" "}
            <GiHouse /> <em>Address: </em> {house.address}
          </p>
          <p style={{ fontSize: "0.8em" }}>
            {" "}
            <FaMoneyBillAlt /> <em>Price: </em>£{house.price}
          </p>
          {house.bedrooms !== undefined && (
            <p style={{ fontSize: "0.8em" }}>
              <IoBed /> <em>Bedrooms: </em> {house.bedrooms}
            </p>
          )}
          {house.bathrooms !== undefined && (
            <p style={{ fontSize: "0.8em" }}>
              {" "}
              <FaToiletPaper /> <em>Bathrooms: </em> {house.bathrooms}
            </p>
          )}
          {house.features && house.features.length > 0 && (
            <ul
              style={{
                fontSize: "0.8em",
                margin: "0.5rem 0",
                paddingLeft: "1rem",
              }}
            >
              {house.features.map((feature, index) => (
                <li key={index}>{feature}</li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </Button>
  );
}
