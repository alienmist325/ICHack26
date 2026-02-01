import styled from "styled-components";
import { Input } from "../../pages/ProfilePage";
import { FiSave, FiTrash2 } from "react-icons/fi";
import { useState } from "react";
import { api } from "../../api/client";
import { useToast } from "../hooks/useToast";
import { useGlobalData } from "../hooks/useGlobalData";

const LocationRow = styled.div`
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
  align-items: center;
`;

const IconButton = styled.button`
  padding: 12px;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  background: white;
  color: #4a5568;
  min-width: 46px;

  &:hover:not(:disabled) {
    border-color: #667eea;
    color: #667eea;
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`;

const RemoveButton = styled(IconButton)`
  border-color: #fed7d7;
  color: #c53030;
  background: #fff5f5;

  &:hover:not(:disabled) {
    border-color: #fc8181;
    background: #fed7d7;
    color: #c53030;
  }
`;

export interface InputLocation {
  label: string;
  address: string;
}

export function LocationRowArea({
  inputLocation,
  index,
  updateLocationAddress,
  updateLocationLabel,
  removeLocation,
}: {
  inputLocation: InputLocation;
  index: number;
  updateLocationAddress: (index: number, value: string) => void;
  updateLocationLabel: (index: number, value: string) => void;
  removeLocation: (index: number) => void;
}) {
  const [saving, setSaving] = useState(false);

  const { addToast } = useToast();
  const { keyLocations, setKeyLocations } = useGlobalData();

  const handleSaveProfile = async () => {
    try {
      setSaving(true);
      //   setError(null);
      //   setSuccess(false);

      // Add the index if it doesn't exist
      const latLong = await api.getLatLong({ address: inputLocation.address });
      setKeyLocations([
        ...keyLocations,
        { label: inputLocation.label, ...latLong },
      ]);
      //   setSuccess(true);
      addToast("Key address added successfully!", "success");

      //   setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      console.log(err);
      const errorMsg =
        err instanceof Error ? err.message : "Key address was not valid";
      //   setError(errorMsg);
      addToast(errorMsg, "error");
    } finally {
      setSaving(false);
    }
  };

  return (
    <LocationRow key={index}>
      <Input
        value={inputLocation.label}
        onChange={(e) => updateLocationLabel(index, e.target.value)}
        placeholder="Enter name"
        disabled={saving}
      />
      <Input
        value={inputLocation.address}
        onChange={(e) => updateLocationAddress(index, e.target.value)}
        placeholder="Enter location"
        disabled={saving}
      />
      <IconButton onClick={handleSaveProfile} disabled={saving} title="Save">
        <FiSave />
      </IconButton>
      <RemoveButton
        onClick={() => removeLocation(index)}
        disabled={saving}
        title="Remove"
      >
        <FiTrash2 />
      </RemoveButton>
    </LocationRow>
  );
}
