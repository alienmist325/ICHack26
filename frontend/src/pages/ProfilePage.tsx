import styled from "styled-components";
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { FiArrowLeft, FiSave, FiTrash2, FiPlus } from "react-icons/fi";
import { api } from "../api/client";
import { useToast } from "../components/hooks/useToast";
import BackgroundPattern from "../components/BackgroundPattern";
import Button from "../components/FormElements/Button";
import FormInput from "../components/FormElements/Input";
import CardComponent from "../components/FormElements/Card";
import PageHeader from "../components/PageHeader";
import { colors, spacing, animations } from "../constants";
import UnifiedHeader from "../components/layout/UnifiedHeader";
import { FooterContainer } from "../components/layout/FooterContainer";
import {
  InputLocation,
  LocationRowArea,
} from "../components/layout/LocationRowArea";
import { useGlobalData } from "../components/hooks/useGlobalData";

const PageContainer = styled.div`
  min-height: 100vh;
  width: 100vw;
  box-sizing: border-box;
  background: ${colors.lightBg};
  padding-top: 80px;
  padding-bottom: 60px;
  padding-left: 20px;
  padding-right: 20px;
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
`;

const Container = styled.div`
  max-width: 800px;
  margin: 0 auto;
`;

const CardWrapper = styled(CardComponent)`
  padding: 40px;
  animation: slideUp 0.6s ease-out;

  @keyframes slideUp {
    from {
      opacity: 0;
      transform: translateY(40px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  @media (max-width: 768px) {
    padding: 30px 20px;
  }
`;

const Section = styled.div`
  margin-bottom: 40px;
  padding-bottom: 40px;
  border-bottom: 2px solid ${colors.borderColor};

  &:last-child {
    border-bottom: none;
  }
`;

const SectionTitle = styled.h2`
  font-size: 18px;
  font-weight: 600;
  color: ${colors.medText};
  margin: 0 0 20px 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const FormGroup = styled.div`
  margin-bottom: 20px;
`;

const Label = styled.label`
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: ${colors.medText};
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

export const Input = styled.input`
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-size: 15px;
  transition: all 0.3s ease;
  background: #f7fafc;
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;

  &:focus {
    outline: none;
    border-color: #667eea;
    background: white;
    box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  &::placeholder {
    color: #cbd5e0;
  }
`;

const Textarea = styled.textarea`
  width: 100%;
  padding: 12px 16px;
  border: 2px solid ${colors.borderColor};
  border-radius: 8px;
  font-size: 15px;
  transition: all 0.3s ease;
  background: ${colors.lightBg};
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
  resize: vertical;
  min-height: 100px;

  &:focus {
    outline: none;
    border-color: ${colors.teal};
    background: ${colors.white};
    box-shadow: 0 0 0 4px ${colors.teal}20;
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  &::placeholder {
    color: ${colors.lightText};
  }
`;

const CheckboxLabel = styled.label`
  display: flex;
  align-items: center;
  gap: 12px;
  color: ${colors.medText};
  cursor: pointer;
  margin-bottom: 12px;

  input {
    width: 18px;
    height: 18px;
    cursor: pointer;
    accent-color: ${colors.teal};
  }
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 12px;
  margin-top: 30px;

  @media (max-width: 768px) {
    flex-direction: column;
  }
`;

const ButtonWrapper = styled.div`
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
`;

const ErrorMessage = styled.div`
  background: ${colors.error}15;
  color: ${colors.error};
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 20px;
  font-size: 13px;
  border: 1px solid ${colors.error}30;
`;

const SuccessMessage = styled.div`
  background: ${colors.success}15;
  color: ${colors.success};
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 20px;
  font-size: 13px;
  border: 1px solid ${colors.success}30;
`;

const LoadingContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
`;

const Spinner = styled.div`
  border: 3px solid ${colors.borderColor};
  border-top: 3px solid ${colors.teal};
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;

  @keyframes spin {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }
`;

interface UserProfile {
  id: number;
  email: string;
  is_active: boolean;
  bio?: string;
  dream_property_description?: string;
  preferred_price_min?: number;
  preferred_price_max?: number;
  preferred_bedrooms_min?: number;
  preferred_property_types?: string[];
  preferred_locations?: string[];
  notification_viewing_reminder_days?: number;
  notification_email_enabled?: boolean;
  notification_in_app_enabled?: boolean;
  notification_feed_changes_enabled?: boolean;
  created_at: string;
  updated_at: string;
}

export function ProfilePage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { addToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const [bio, setBio] = useState("");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [minBedrooms, setMinBedrooms] = useState("");
  const [maxBedrooms, setMaxBedrooms] = useState("");
  const [locationAddresses, setLocationAddresses] = useState<InputLocation[]>(
    []
  );
  const [emailUpdates, setEmailUpdates] = useState(true);
  const [pushNotifications, setPushNotifications] = useState(true);
  const [locations, setLocations] = useState("");
  const [notificationViewingReminder, setNotificationViewingReminder] =
    useState("3");
  const [notificationEmailEnabled, setNotificationEmailEnabled] =
    useState(true);
  const [notificationInAppEnabled, setNotificationInAppEnabled] =
    useState(true);
  const [notificationFeedChangesEnabled, setNotificationFeedChangesEnabled] =
    useState(true);

  // Load profile on mount
  useEffect(() => {
    loadProfile();
  }, [user]);

  const loadProfile = async () => {
    if (!user) return;

    try {
      setLoading(true);
      setError(null);

      const response = await api.get("/users/");
      const profile: UserProfile = response;

      // Extract flat fields from backend response
      setBio(profile.bio || "");
      setMinPrice(profile.preferred_price_min?.toString() || "");
      setMaxPrice(profile.preferred_price_max?.toString() || "");
      setMinBedrooms(profile.preferred_bedrooms_min?.toString() || "");
      setLocations((profile.preferred_locations || []).join(", "));

      // Notification settings
      setNotificationViewingReminder(
        profile.notification_viewing_reminder_days?.toString() || "3"
      );
      setNotificationEmailEnabled(profile.notification_email_enabled ?? true);
      setNotificationInAppEnabled(profile.notification_in_app_enabled ?? true);
      setNotificationFeedChangesEnabled(
        profile.notification_feed_changes_enabled ?? true
      );
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : "Failed to load profile";
      setError(errorMsg);
      addToast(errorMsg, "error");
    } finally {
      setLoading(false);
    }
  };

  const { keyLocations, setKeyLocations } = useGlobalData();

  const addLocation = () => {
    setLocationAddresses([...locationAddresses, { label: "", address: "" }]);
  };

  const removeLocation = (index: number) => {
    const newLocations = [...locationAddresses];
    const deletedLocation = newLocations.splice(index, 1);
    setLocationAddresses(newLocations);

    // Find the entry with the same label and remove that from the key locations
    const newKeyLocations = keyLocations.filter(
      (value) => value.label === deletedLocation[0].label
    );
    setKeyLocations(newKeyLocations);
  };

  const updateLocationAddress = (index: number, address: string) => {
    const newLocations = [...locationAddresses];
    const currentLocation = newLocations[index];
    newLocations[index] = { ...currentLocation, address };
    setLocationAddresses(newLocations);
  };

  const updateLocationLabel = (index: number, label: string) => {
    const newLocations = [...locationAddresses];
    const currentLocation = newLocations[index];
    newLocations[index] = { ...currentLocation, label };
    setLocationAddresses(newLocations);
  };

  const handleSaveProfile = async () => {
    if (!user) return;

    try {
      setSaving(true);
      setError(null);
      setSuccess(false);

      // Send flat fields that match backend schema
      const profileData = {
        bio: bio || undefined,
        preferred_price_min: minPrice ? parseInt(minPrice) : undefined,
        preferred_price_max: maxPrice ? parseInt(maxPrice) : undefined,
        preferred_bedrooms_min: minBedrooms ? parseInt(minBedrooms) : undefined,
        preferred_locations:
          locations
            .split(",")
            .map((l) => l.trim())
            .filter((l) => l) || undefined,
        notification_viewing_reminder_days: notificationViewingReminder
          ? parseInt(notificationViewingReminder)
          : 3,
        notification_email_enabled: notificationEmailEnabled,
        notification_in_app_enabled: notificationInAppEnabled,
        notification_feed_changes_enabled: notificationFeedChangesEnabled,
      };

      await api.put("/users/", profileData);
      setSuccess(true);
      addToast("Profile updated successfully!", "success");

      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : "Failed to update profile";
      setError(errorMsg);
      addToast(errorMsg, "error");
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (!user) return;

    const confirmed = window.confirm(
      "Are you sure you want to delete your account? This action cannot be undone."
    );

    if (!confirmed) return;

    try {
      setSaving(true);
      setError(null);

      await api.delete("/users");
      addToast("Account deleted successfully", "success");

      setTimeout(() => navigate("/login"), 1500);
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : "Failed to delete account";
      setError(errorMsg);
      addToast(errorMsg, "error");
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <>
        <UnifiedHeader />
        <PageContainer>
          <Container>
            <CardWrapper>
              <LoadingContainer>
                <Spinner />
              </LoadingContainer>
            </CardWrapper>
          </Container>
        </PageContainer>
        <FooterContainer />
      </>
    );
  }

  return (
    <>
      <UnifiedHeader />
      <PageContainer>
        <Container>
          <CardWrapper>
            <PageHeader
              title="Profile Settings"
              showBackButton={true}
              onBack={() => navigate("/")}
            />

            {error && <ErrorMessage>{error}</ErrorMessage>}
            {success && (
              <SuccessMessage>Profile updated successfully!</SuccessMessage>
            )}

            {/* Bio Section */}
            <Section>
              <SectionTitle>About You</SectionTitle>
              <FormGroup>
                <Label>Bio</Label>
                <Textarea
                  placeholder="Tell us about yourself and what you're looking for in a property..."
                  value={bio}
                  onChange={(e) => setBio(e.target.value)}
                  disabled={saving}
                />
              </FormGroup>
            </Section>

            {/* Preferences Section */}
            <Section>
              <SectionTitle>Property Preferences</SectionTitle>

              <FormGroup>
                <Label>Price Range</Label>
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: "12px",
                  }}
                >
                  <div>
                    <FormInput
                      type="number"
                      placeholder="Min price (£)"
                      value={minPrice}
                      onChange={(e) => setMinPrice(e.target.value)}
                      disabled={saving}
                    />
                  </div>
                  <div>
                    <FormInput
                      type="number"
                      placeholder="Max price (£)"
                      value={maxPrice}
                      onChange={(e) => setMaxPrice(e.target.value)}
                      disabled={saving}
                    />
                  </div>
                </div>
              </FormGroup>

              <FormGroup>
                <Label>Bedrooms</Label>
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: "12px",
                  }}
                >
                  <div>
                    <FormInput
                      type="number"
                      placeholder="Min bedrooms"
                      value={minBedrooms}
                      onChange={(e) => setMinBedrooms(e.target.value)}
                      disabled={saving}
                    />
                  </div>
                  <div>
                    <FormInput
                      type="number"
                      placeholder="Max bedrooms"
                      value={maxBedrooms}
                      onChange={(e) => setMaxBedrooms(e.target.value)}
                      disabled={saving}
                    />
                  </div>
                </div>
              </FormGroup>
              <FormGroup>
                <Label>Preferred Locations</Label>
                <FormInput
                  type="text"
                  placeholder="E.g., London, Manchester, Bristol (comma-separated)"
                  value={locations}
                  onChange={(e) => setLocations(e.target.value)}
                  disabled={saving}
                />
              </FormGroup>
  
            <FormGroup>
              <Label>Key Locations</Label>
              {locationAddresses.map((location, index) => (
                <LocationRowArea
                  inputLocation={location}
                  index={index}
                  key={index}
                  removeLocation={removeLocation}
                  updateLocationAddress={updateLocationAddress}
                  updateLocationLabel={updateLocationLabel}
                ></LocationRowArea>
              ))}
              <Button
                type="button"
                onClick={addLocation}
                disabled={saving}
                style={{ marginTop: "8px", width: "100%" }}
              >
                <FiPlus /> Add Location
              </Button>
            </FormGroup>
          </Section>

            {/* Notifications Section */}
            <Section>
              <SectionTitle>Notifications</SectionTitle>

              <FormGroup>
                <Label>Viewing Reminder (days before viewing)</Label>
                <FormInput
                  type="number"
                  min="1"
                  max="30"
                  value={notificationViewingReminder}
                  onChange={(e) => setNotificationViewingReminder(e.target.value)}
                  disabled={saving}
                />
              </FormGroup>

              <CheckboxLabel>
                <input
                  type="checkbox"
                  checked={notificationEmailEnabled}
                  onChange={(e) => setNotificationEmailEnabled(e.target.checked)}
                  disabled={saving}
                />
                Email notifications enabled
              </CheckboxLabel>

              <CheckboxLabel>
                <input
                  type="checkbox"
                  checked={notificationInAppEnabled}
                  onChange={(e) => setNotificationInAppEnabled(e.target.checked)}
                  disabled={saving}
                />
                In-app notifications enabled
              </CheckboxLabel>

              <CheckboxLabel>
                <input
                  type="checkbox"
                  checked={notificationFeedChangesEnabled}
                  onChange={(e) => setNotificationFeedChangesEnabled(e.target.checked)}
                  disabled={saving}
                />
                Notify me when shared feed changes
              </CheckboxLabel>
            </Section>

            {/* Actions */}
            <ButtonGroup>
              <ButtonWrapper>
                <Button
                  variant="primary"
                  onClick={handleSaveProfile}
                  disabled={saving}
                  style={{ width: "100%", display: "flex", gap: "8px" }}
                >
                  <FiSave />
                  {saving ? "Saving..." : "Save Changes"}
                </Button>
              </ButtonWrapper>
              <ButtonWrapper>
                <Button
                  variant="danger"
                  onClick={handleDeleteAccount}
                  disabled={saving}
                  style={{ width: "100%", display: "flex", gap: "8px" }}
                >
                  <FiTrash2 />
                  Delete Account
                </Button>
              </ButtonWrapper>
            </ButtonGroup>
          </CardWrapper>
        </Container>
      </PageContainer>
      <FooterContainer />
    </>
  );
}
