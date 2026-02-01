import "./App.css";
import styled from "styled-components";
import { Routes, Route, Navigate } from "react-router-dom";
import {
  FilterContext,
  useSetupFilter,
} from "./components/hooks/useSetupFilter";
import {
  GlobalDataContext,
  useSetupGlobalData,
} from "./components/hooks/useSetupGlobalData";
import { ToastContext, useSetupToast } from "./components/hooks/useToast";
import { ToastList } from "./components/ui/Toast";
import { AuthContext, useSetupAuth } from "./hooks/useAuth";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { HouseSearchLayout } from "./pages/HouseSearchLayout";
import { ProfilePage } from "./pages/ProfilePage";
import { FavoritesPage } from "./pages/FavoritesPage";
import { SettingsPage } from "./pages/SettingsPage";
import { HousePage } from "./pages/HousePage";

const AppContainer = styled.div`
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
`;

function App() {
  const filter = useSetupFilter();
  const globalData = useSetupGlobalData();
  const toast = useSetupToast();
  const auth = useSetupAuth();

  return (
    <AuthContext.Provider value={auth}>
      <GlobalDataContext.Provider value={globalData}>
        <FilterContext.Provider value={filter}>
          <ToastContext.Provider value={toast}>
            <Routes>
              {/* Public Routes */}
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />

              {/* Protected Routes */}
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <AppContainer>
                      <HouseSearchLayout />
                      <ToastList
                        toasts={toast.toasts}
                        onRemove={toast.removeToast}
                      />
                    </AppContainer>
                  </ProtectedRoute>
                }
              />

              <Route
                path="/profile"
                element={
                  <ProtectedRoute>
                    <>
                      <ProfilePage />
                      <ToastList
                        toasts={toast.toasts}
                        onRemove={toast.removeToast}
                      />
                    </>
                  </ProtectedRoute>
                }
              />

              <Route
                path="/favorites"
                element={
                  <ProtectedRoute>
                    <>
                      <FavoritesPage />
                      <ToastList
                        toasts={toast.toasts}
                        onRemove={toast.removeToast}
                      />
                    </>
                  </ProtectedRoute>
                }
              />

              <Route
                path="/settings"
                element={
                  <ProtectedRoute>
                    <>
                      <SettingsPage />
                      <ToastList
                        toasts={toast.toasts}
                        onRemove={toast.removeToast}
                      />
                    </>
                  </ProtectedRoute>
                }
              />

              <Route
                path="/house"
                element={
                  <ProtectedRoute>
                    <>
                      <HousePage />
                      <ToastList
                        toasts={toast.toasts}
                        onRemove={toast.removeToast}
                      />
                    </>
                  </ProtectedRoute>
                }
              />

              {/* Catch-all redirect */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </ToastContext.Provider>
        </FilterContext.Provider>
      </GlobalDataContext.Provider>
    </AuthContext.Provider>
  );
}

export default App;
