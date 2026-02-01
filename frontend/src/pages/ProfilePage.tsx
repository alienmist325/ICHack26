import styled from "styled-components";
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { FiArrowLeft, FiSave, FiTrash2 } from "react-icons/fi";
import { api } from "../api/client";
import { useToast } from "../components/hooks/useToast";

const PageContainer = styled.div`
  min-height: 100vh;
  width: 100vw;
  box-sizing: border-box;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 40px 20px;
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
`;

const Container = styled.div`
  max-width: 800px;
  margin: 0 auto;
`;

const Card = styled.div`
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
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

const Header = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 30px;
`;

const BackButton = styled.button`
  background: none;
  border: none;
  color: #667eea;
  font-size: 24px;
  cursor: pointer;
  transition: all 0.3s ease;
  padding: 8px;
  display: flex;
  align-items: center;

  &:hover {
    color: #764ba2;
    transform: translateX(-4px);
  }
`;

const Title = styled.h1`
  font-size: 32px;
  font-weight: 700;
  color: #1a202c;
  margin: 0;
`;

const Section = styled.div`
  margin-bottom: 40px;
  padding-bottom: 40px;
  border-bottom: 2px solid #e2e8f0;

  &:last-child {
    border-bottom: none;
  }
`;

const SectionTitle = styled.h2`
  font-size: 18px;
  font-weight: 600;
  color: #2d3748;
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
  color: #2d3748;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const Input = styled.input`
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
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-size: 15px;
  transition: all 0.3s ease;
  background: #f7fafc;
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
  resize: vertical;
  min-height: 100px;

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

const CheckboxLabel = styled.label`
  display: flex;
  align-items: center;
  gap: 12px;
  color: #4a5568;
  cursor: pointer;
  margin-bottom: 12px;

  input {
    width: 18px;
    height: 18px;
    cursor: pointer;
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

const Button = styled.button`
  padding: 12px 24px;
  border: none;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  flex: 1;
`;

const SaveButton = styled(Button)`
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`;

const DeleteButton = styled(Button)`
  background: #fed7d7;
  color: #c53030;
  border: 2px solid #fc8181;

  &:hover:not(:disabled) {
    background: #fc8181;
    color: white;
    transform: translateY(-2px);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`;

const ErrorMessage = styled.div`
  background: #fed7d7;
  color: #c53030;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 20px;
  font-size: 13px;
`;

const SuccessMessage = styled.div`
  background: #c6f6d5;
  color: #22543d;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 20px;
  font-size: 13px;
`;

const LoadingContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
`;

const Spinner = styled.div`
  border: 3px solid #e2e8f0;
  border-top: 3px solid #667eea;
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
  bio?: string;
  preferences?: {
    minPrice?: number;
    maxPrice?: number;
    propertyTypes?: string[];
    locations?: string[];
    minBedrooms?: number;
    maxBedrooms?: number;
  };
  notifications?: {
    emailUpdates?: boolean;
    pushNotifications?: boolean;
  };
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
  const [locations, setLocations] = useState("");
  const [emailUpdates, setEmailUpdates] = useState(true);
  const [pushNotifications, setPushNotifications] = useState(true);

  // Load profile on mount
  useEffect(() => {
    loadProfile();
  }, [user]);

  const loadProfile = async () => {
    if (!user) return;

    try {
      setLoading(true);
      setError(null);

      const response = await api.get("/users/profile");
      const profile: UserProfile = response;

      setBio(profile.bio || "");
      setMinPrice(profile.preferences?.minPrice?.toString() || "");
      setMaxPrice(profile.preferences?.maxPrice?.toString() || "");
      setMinBedrooms(profile.preferences?.minBedrooms?.toString() || "");
      setMaxBedrooms(profile.preferences?.maxBedrooms?.toString() || "");
      setLocations((profile.preferences?.locations || []).join(", "));
      setEmailUpdates(profile.notifications?.emailUpdates ?? true);
      setPushNotifications(profile.notifications?.pushNotifications ?? true);
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : "Failed to load profile";
      setError(errorMsg);
      addToast(errorMsg, "error");
    } finally {
      setLoading(false);
    }
  };

  const handleSaveProfile = async () => {
    if (!user) return;

    try {
      setSaving(true);
      setError(null);
      setSuccess(false);

      const profileData = {
        bio,
        preferences: {
          minPrice: minPrice ? parseInt(minPrice) : undefined,
          maxPrice: maxPrice ? parseInt(maxPrice) : undefined,
          minBedrooms: minBedrooms ? parseInt(minBedrooms) : undefined,
          maxBedrooms: maxBedrooms ? parseInt(maxBedrooms) : undefined,
          locations: locations
            .split(",")
            .map((l) => l.trim())
            .filter((l) => l),
        },
        notifications: {
          emailUpdates,
          pushNotifications,
        },
      };

      await api.put("/users/profile", profileData);
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

      await api.delete("/users/profile");
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
      <PageContainer>
        <Container>
          <Card>
            <LoadingContainer>
              <Spinner />
            </LoadingContainer>
          </Card>
        </Container>
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <Container>
        <Card>
          <Header>
            <BackButton onClick={() => navigate("/")}>
              <FiArrowLeft />
            </BackButton>
            <Title>Profile Settings</Title>
            <div style={{ width: 40 }} />
          </Header>

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
                  <Input
                    type="number"
                    placeholder="Min price (£)"
                    value={minPrice}
                    onChange={(e) => setMinPrice(e.target.value)}
                    disabled={saving}
                  />
                </div>
                <div>
                  <Input
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
                  <Input
                    type="number"
                    placeholder="Min bedrooms"
                    value={minBedrooms}
                    onChange={(e) => setMinBedrooms(e.target.value)}
                    disabled={saving}
                  />
                </div>
                <div>
                  <Input
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
              <Input
                type="text"
                placeholder="E.g., London, Manchester, Bristol (comma-separated)"
                value={locations}
                onChange={(e) => setLocations(e.target.value)}
                disabled={saving}
              />
            </FormGroup>
          </Section>

          {/* Notifications Section */}
          <Section>
            <SectionTitle>Notifications</SectionTitle>

            <CheckboxLabel>
              <input
                type="checkbox"
                checked={emailUpdates}
                onChange={(e) => setEmailUpdates(e.target.checked)}
                disabled={saving}
              />
              Email me updates about new properties matching my preferences
            </CheckboxLabel>

            <CheckboxLabel>
              <input
                type="checkbox"
                checked={pushNotifications}
                onChange={(e) => setPushNotifications(e.target.checked)}
                disabled={saving}
              />
              Send me push notifications on my device
            </CheckboxLabel>
          </Section>

          {/* Actions */}
          <ButtonGroup>
            <SaveButton onClick={handleSaveProfile} disabled={saving}>
              <FiSave />
              {saving ? "Saving..." : "Save Changes"}
            </SaveButton>
            <DeleteButton onClick={handleDeleteAccount} disabled={saving}>
              <FiTrash2 />
              Delete Account
            </DeleteButton>
          </ButtonGroup>
        </Card>
      </Container>
    </PageContainer>
  );
}
