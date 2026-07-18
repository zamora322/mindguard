"use client";

import React, { useEffect, useState } from "react";
import { Typography } from "../../components/atoms/Typography/Typography";
import { Button } from "../../components/atoms/Button/Button";
import { 
  Home, 
  Plug, 
  CalendarCheck, 
  Settings, 
  HelpCircle, 
  LogOut, 
  Menu, 
  Mail, 
  Calendar, 
  Brain, 
  Loader2,
  CheckCircle2,
  RefreshCw
} from "lucide-react";
import styles from "./dashboard.module.css";

interface UserProfile {
  id: string;
  email: string;
  name: string;
  picture: string;
}

interface IntegrationsState {
  google: boolean;
  gmail: boolean;
  calendar: boolean;
}

interface SyncStatusState {
  status: string;
  syncedCount: number;
}

export default function DashboardPage() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [integrations, setIntegrations] = useState<IntegrationsState>({
    google: false,
    gmail: false,
    calendar: false
  });
  const [gmailSyncStatus, setGmailSyncStatus] = useState<SyncStatusState>({
    status: "idle",
    syncedCount: 0
  });
  const [calendarSyncStatus, setCalendarSyncStatus] = useState<SyncStatusState>({
    status: "idle",
    syncedCount: 0
  });

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    const fetchGmailSyncStatus = async () => {
      try {
        const response = await fetch(`${apiUrl}/api/v1/auth/sync-status?provider=gmail`, {
          credentials: "include",
        });
        if (response.ok) {
          const data = await response.json();
          setGmailSyncStatus({
            status: data.status,
            syncedCount: data.synced_count || 0
          });
        }
      } catch (e) {
        console.error("Error al obtener gmail sync-status:", e);
      }
    };

    const fetchCalendarSyncStatus = async () => {
      try {
        const response = await fetch(`${apiUrl}/api/v1/auth/sync-status?provider=calendar`, {
          credentials: "include",
        });
        if (response.ok) {
          const data = await response.json();
          setCalendarSyncStatus({
            status: data.status,
            syncedCount: data.synced_count || 0
          });
        }
      } catch (e) {
        console.error("Error al obtener calendar sync-status:", e);
      }
    };

    const fetchIntegrations = async () => {
      try {
        const response = await fetch(`${apiUrl}/api/v1/auth/integrations`, {
          credentials: "include",
        });
        if (response.ok) {
          const data = await response.json();
          setIntegrations(data);
          if (data.gmail) {
            fetchGmailSyncStatus();
          }
          if (data.calendar) {
            fetchCalendarSyncStatus();
          }
        }
      } catch (e) {
        console.error("Error al obtener integraciones:", e);
      }
    };

    const fetchSession = async () => {
      try {
        const response = await fetch(`${apiUrl}/api/v1/auth/me`, {
          credentials: "include",
        });

        if (response.ok) {
          const data = await response.json();
          if (data.status === "success" && data.user) {
            setUser(data.user);
            fetchIntegrations();
          }
        }
      } catch (e) {
        console.error("Error al recuperar sesión activa:", e);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSession();
  }, []);

  // Polling gmail sync status if currently syncing or idle
  useEffect(() => {
    if (integrations.gmail && (gmailSyncStatus.status === "syncing" || gmailSyncStatus.status === "idle")) {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const interval = setInterval(async () => {
        try {
          const res = await fetch(`${apiUrl}/api/v1/auth/sync-status?provider=gmail`, {
            credentials: "include"
          });
          if (res.ok) {
            const data = await res.json();
            setGmailSyncStatus({
              status: data.status,
              syncedCount: data.synced_count || 0
            });
            if (data.status === "completed" || data.status === "failed") {
              clearInterval(interval);
            }
          }
        } catch (e) {
          console.error("Error en polling de gmail sync-status:", e);
        }
      }, 2000);
      return () => clearInterval(interval);
    }
  }, [integrations.gmail, gmailSyncStatus.status]);

  // Polling calendar sync status if currently syncing or idle
  useEffect(() => {
    if (integrations.calendar && (calendarSyncStatus.status === "syncing" || calendarSyncStatus.status === "idle")) {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const interval = setInterval(async () => {
        try {
          const res = await fetch(`${apiUrl}/api/v1/auth/sync-status?provider=calendar`, {
            credentials: "include"
          });
          if (res.ok) {
            const data = await res.json();
            setCalendarSyncStatus({
              status: data.status,
              syncedCount: data.synced_count || 0
            });
            if (data.status === "completed" || data.status === "failed") {
              clearInterval(interval);
            }
          }
        } catch (e) {
          console.error("Error en polling de calendar sync-status:", e);
        }
      }, 2000);
      return () => clearInterval(interval);
    }
  }, [integrations.calendar, calendarSyncStatus.status]);

  const handleLogout = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      await fetch(`${apiUrl}/api/v1/auth/logout`, {
        method: "POST",
        credentials: "include",
      });
    } catch (e) {
      console.error("Error al cerrar sesión en el servidor:", e);
    }
    window.location.href = "/";
  };

  const handleConnectGmail = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/v1/auth/login?scope_type=gmail`);
      if (response.ok) {
        const data = await response.json();
        if (data.url) {
          window.location.href = data.url;
        }
      }
    } catch (e) {
      console.error("Error al obtener la URL de conexión a Gmail:", e);
    }
  };

  const handleConnectCalendar = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/v1/auth/login?scope_type=calendar`);
      if (response.ok) {
        const data = await response.json();
        if (data.url) {
          window.location.href = data.url;
        }
      }
    } catch (e) {
      console.error("Error al obtener la URL de conexión a Google Calendar:", e);
    }
  };

  const handleManualSync = async (provider: "gmail" | "calendar") => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      if (provider === "gmail") {
        setGmailSyncStatus({ status: "syncing", syncedCount: 0 });
      } else {
        setCalendarSyncStatus({ status: "syncing", syncedCount: 0 });
      }

      await fetch(`${apiUrl}/api/v1/auth/sync-trigger?provider=${provider}`, {
        method: "POST",
        credentials: "include",
      });
    } catch (e) {
      console.error(`Error al iniciar sincronización manual de ${provider}:`, e);
    }
  };

  if (isLoading) {
    return (
      <div className={styles.loadingContainer}>
        <div className={styles.spinner}></div>
      </div>
    );
  }

  return (
    <div className={styles.dashboardLayout}>
      {/* Sidebar */}
      <aside className={`${styles.sidebar} ${isSidebarOpen ? "" : styles.sidebarCollapsed}`}>
        <div className={styles.sidebarHeader}>
          <div className={styles.logoContainer}>
            <img src="/logo.png" alt="MindGuard" className={styles.logo} />
            <div className={styles.brandInfo}>
              <span className={styles.brandName}>MindGuard</span>
              <span className={styles.brandSubtitle}>Asistente IA</span>
            </div>
          </div>
        </div>

        <nav className={styles.sidebarNav}>
          <a href="#" className={`${styles.navItem} ${styles.navItemActive}`}>
            <Home className={styles.navIcon} size={20} />
            <span>Inicio</span>
          </a>
          <a href="#" className={styles.navItem}>
            <Plug className={styles.navIcon} size={20} />
            <span>Integraciones</span>
          </a>
          <a href="#" className={styles.navItem}>
            <CalendarCheck className={styles.navIcon} size={20} />
            <span>Mi Jornada</span>
          </a>
          <a href="#" className={styles.navItem}>
            <Settings className={styles.navIcon} size={20} />
            <span>Configuración</span>
          </a>
        </nav>

        <div className={styles.sidebarFooter}>
          <div className={styles.divider}></div>
          <a href="#" className={styles.navItem}>
            <HelpCircle className={styles.navIcon} size={20} />
            <span>Ayuda</span>
          </a>
          <button onClick={handleLogout} className={styles.logoutButton}>
            <LogOut className={styles.navIcon} size={18} />
            <span>Cerrar Sesión</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className={styles.mainContent}>
        <button 
          className={styles.mobileMenuToggle} 
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
        >
          <Menu size={24} />
        </button>

        <header className={styles.header}>
          <h1 className={styles.greeting}>¡Hola, {user?.name || "Usuario"}!</h1>
          <p className={styles.headerSubtitle}>
            Bienvenido a tu panel de control y asistencia cognitiva.
          </p>
        </header>

        {/* 2x2 Cards Grid */}
        <div className={styles.cardsGrid}>
          {/* Card A: Profile */}
          <div className={`${styles.card} ${styles.profileCard}`}>
            <div className={styles.profileCardContent}>
              <div className={styles.profileHeader}>
                {user?.picture ? (
                  <img
                    src={user.picture}
                    alt={user.name}
                    className={styles.profileAvatar}
                    referrerPolicy="no-referrer"
                  />
                ) : (
                  <div className={styles.profileAvatarPlaceholder}>
                    {user?.name ? user.name.charAt(0) : "U"}
                  </div>
                )}
                <div className={styles.profileDetails}>
                  <h3 className={styles.profileName}>{user?.name || "Usuario MindGuard"}</h3>
                  <span className={styles.profileEmail}>{user?.email || "usuario@mindguard.ai"}</span>
                </div>
              </div>
              
              <div className={styles.badgeContainer}>
                <span className={integrations.google ? styles.statusBadge : styles.statusBadgeDisconnected}>
                  <span className={integrations.google ? styles.statusDot : styles.statusDotDisconnected}></span>
                  {integrations.google ? "🟢 Conectado" : "⚪ No conectado"}
                </span>
                <div className={styles.accentWave}></div>
              </div>
            </div>
            
            <div className={styles.cardFooter}>
              <span className={styles.statusLabel}>
                {integrations.google ? "ESTADO: CONECTADA" : "ESTADO: DESCONECTADA"}
              </span>
            </div>
          </div>

          {/* Card B: Gmail Integration */}
          <div className={styles.card}>
            <div>
              <div className={styles.cardHeaderInline}>
                <div className={styles.cardHeaderLeft}>
                  <Mail className={styles.gmailIcon} size={24} />
                  <h3 className={styles.cardTitle}>Gmail</h3>
                </div>
                <span className={integrations.gmail ? styles.statusTextConnected : styles.statusTextDisconnected}>
                  {integrations.gmail 
                    ? (gmailSyncStatus.status === "syncing" ? "🟡 Sincronizando..." : "🟢 Conectado") 
                    : "⚪ No conectado"}
                </span>
              </div>
              <p className={styles.cardDescription}>
                Conecta Gmail para que MindGuard pueda analizar tu carga de correo y ayudarte a priorizar tu trabajo.
              </p>
              
              {/* Syncing State Progress Bar */}
              {integrations.gmail && gmailSyncStatus.status === "syncing" && (
                <div className={styles.syncProgressContainer}>
                  <div className={styles.syncProgressLabel}>
                    <Loader2 className={styles.syncSpinnerIcon} size={16} />
                    <span>Sincronizando correos de los últimos 8 días...</span>
                  </div>
                  <div className={styles.progressBarTrack}>
                    <div className={styles.progressBarFill}></div>
                  </div>
                </div>
              )}

              {/* Sync Completed State Badge & Manual Sync Button */}
              {integrations.gmail && gmailSyncStatus.status === "completed" && (
                <div className={styles.syncRow}>
                  <div className={styles.syncSuccessBadge}>
                    <CheckCircle2 size={14} />
                    <span>
                      {gmailSyncStatus.syncedCount > 0
                        ? `${gmailSyncStatus.syncedCount} correos nuevos agregados (8 días)`
                        : "0 correos nuevos (8 días)"}
                    </span>
                  </div>
                  <button 
                    className={styles.syncButton}
                    onClick={() => handleManualSync("gmail")}
                    title="Sincronizar Gmail manualmente"
                  >
                    <RefreshCw size={14} />
                    <span>Sincronizar ahora</span>
                  </button>
                </div>
              )}
            </div>
            {!integrations.gmail && (
              <button 
                className={styles.outlineButton}
                onClick={handleConnectGmail}
              >
                Conectar Gmail
              </button>
            )}
          </div>

          {/* Card C: Google Calendar Integration */}
          <div className={styles.card}>
            <div>
              <div className={styles.cardHeaderInline}>
                <div className={styles.cardHeaderLeft}>
                  <Calendar className={styles.calendarIcon} size={24} />
                  <h3 className={styles.cardTitle}>Google Calendar</h3>
                </div>
                <span className={integrations.calendar ? styles.statusTextConnected : styles.statusTextDisconnected}>
                  {integrations.calendar 
                    ? (calendarSyncStatus.status === "syncing" ? "🟡 Sincronizando..." : "🟢 Conectado") 
                    : "⚪ No conectado"}
                </span>
              </div>
              <p className={styles.cardDescription}>
                Conecta tu calendario para identificar reuniones, bloques de enfoque y posibles conflictos.
              </p>

              {/* Syncing State Progress Bar */}
              {integrations.calendar && calendarSyncStatus.status === "syncing" && (
                <div className={styles.syncProgressContainer}>
                  <div className={styles.syncProgressLabel}>
                    <Loader2 className={styles.syncSpinnerIcon} size={16} />
                    <span>Sincronizando eventos de los próximos 8 días...</span>
                  </div>
                  <div className={styles.progressBarTrack}>
                    <div className={styles.progressBarFill}></div>
                  </div>
                </div>
              )}

              {/* Sync Completed State Badge & Manual Sync Button */}
              {integrations.calendar && calendarSyncStatus.status === "completed" && (
                <div className={styles.syncRow}>
                  <div className={styles.syncSuccessBadge}>
                    <CheckCircle2 size={14} />
                    <span>
                      {calendarSyncStatus.syncedCount > 0
                        ? `${calendarSyncStatus.syncedCount} eventos nuevos agregados (8 días)`
                        : "0 eventos nuevos (8 días)"}
                    </span>
                  </div>
                  <button 
                    className={styles.syncButton}
                    onClick={() => handleManualSync("calendar")}
                    title="Sincronizar Google Calendar manualmente"
                  >
                    <RefreshCw size={14} />
                    <span>Sincronizar ahora</span>
                  </button>
                </div>
              )}
            </div>
            {!integrations.calendar && (
              <button 
                className={styles.outlineButton}
                onClick={handleConnectCalendar}
              >
                Conectar Calendario
              </button>
            )}
          </div>

          {/* Card D: Cognitive Load */}
          <div className={`${styles.card} ${styles.cognitiveCard}`}>
            <div className={styles.cognitiveIconContainer}>
              <Brain className={styles.cognitiveIcon} size={24} />
            </div>
            <h4 className={styles.cognitiveTitle}>Carga Cognitiva</h4>
            <p className={styles.cognitiveDescription}>
              Aún no hay suficiente información para generar un análisis.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
