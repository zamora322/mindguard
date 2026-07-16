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
  History 
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

export default function DashboardPage() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [integrations, setIntegrations] = useState<IntegrationsState>({
    google: false,
    gmail: false,
    calendar: false
  });

  useEffect(() => {
    const fetchSession = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const response = await fetch(`${apiUrl}/api/v1/auth/me`, {
          credentials: "include",
        });

        if (response.ok) {
          const data = await response.json();
          if (data.status === "success" && data.user) {
            setUser(data.user);
            // Si el usuario tiene sesión activa, recuperamos sus integraciones
            fetchIntegrations(apiUrl);
          }
        }
      } catch (e) {
        console.error("Error al recuperar sesión activa:", e);
      } finally {
        setIsLoading(false);
      }
    };

    const fetchIntegrations = async (apiUrl: string) => {
      try {
        const response = await fetch(`${apiUrl}/api/v1/auth/integrations`, {
          credentials: "include",
        });
        if (response.ok) {
          const data = await response.json();
          setIntegrations(data);
        }
      } catch (e) {
        console.error("Error al obtener integraciones:", e);
      }
    };

    fetchSession();
  }, []);

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

  if (isLoading) {
    return (
      <div className={styles.loadingContainer}>
        <div className={styles.spinner}></div>
        <Typography variant="h1" className={styles.loadingTitle}>
          Cargando Panel...
        </Typography>
      </div>
    );
  }

  if (!user) {
    return (
      <div className={styles.deniedContainer}>
        <div className={styles.deniedCard}>
          <div className={styles.errorIcon}>🔒</div>
          <Typography variant="h1" className={styles.titleError}>
            Acceso Denegado
          </Typography>
          <Typography variant="h2" className={styles.subtitle}>
            Inicia sesión para poder acceder al panel de control de MindGuard.
          </Typography>
          <Button onClick={() => window.location.href = "/"} className={styles.btnPrimary}>
            Iniciar Sesión
          </Button>
        </div>
      </div>
    );
  }

  // Helper to extract first name
  const firstName = user.name ? user.name.split(" ")[0] : "Usuario";

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
            <span className={styles.navText}>Inicio</span>
          </a>
          <a href="#" className={styles.navItem}>
            <Plug className={styles.navIcon} size={20} />
            <span className={styles.navText}>Integraciones</span>
          </a>
          <a href="#" className={styles.navItem}>
            <CalendarCheck className={styles.navIcon} size={20} />
            <span className={styles.navText}>Mi Jornada</span>
          </a>
          <a href="#" className={styles.navItem}>
            <Settings className={styles.navIcon} size={20} />
            <span className={styles.navText}>Configuración</span>
          </a>
        </nav>

        <div className={styles.sidebarFooter}>
          <div className={styles.divider}></div>
          <a href="#" className={styles.navItem}>
            <HelpCircle className={styles.navIcon} size={20} />
            <span className={styles.navText}>Ayuda</span>
          </a>
          <button onClick={handleLogout} className={styles.logoutButton}>
            <LogOut className={styles.navIcon} size={20} />
            <span className={styles.navText}>Cerrar Sesión</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className={styles.mainContent}>
        {/* Mobile menu toggle button */}
        <button 
          className={styles.mobileMenuToggle} 
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
        >
          <Menu size={24} />
        </button>

        <header className={styles.header}>
          <h1 className={styles.greeting}>¡Hola, {firstName}!</h1>
          <p className={styles.headerSubtitle}>
            Protege tu tiempo de enfoque y mantén un equilibrio saludable en tu jornada.
          </p>
        </header>

        {/* 2x2 Cards Grid */}
        <div className={styles.cardsGrid}>
          {/* Card A: Profile */}
          <div className={`${styles.card} ${styles.profileCard}`}>
            <div className={styles.profileCardContent}>
              <div className={styles.profileHeader}>
                {user.picture ? (
                  <img
                    src={user.picture}
                    alt={user.name}
                    className={styles.profileAvatar}
                    referrerPolicy="no-referrer"
                  />
                ) : (
                  <div className={styles.profileAvatarPlaceholder}>
                    {user.name ? user.name.charAt(0) : "U"}
                  </div>
                )}
                <div className={styles.profileDetails}>
                  <h3 className={styles.profileName}>{user.name}</h3>
                  <span className={styles.profileEmail}>{user.email}</span>
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
                  {integrations.gmail ? "🟢 Conectado" : "⚪ No conectado"}
                </span>
              </div>
              <p className={styles.cardDescription}>
                Conecta Gmail para que MindGuard pueda analizar tu carga de correo y ayudarte a priorizar tu trabajo.
              </p>
            </div>
            <button 
              className={integrations.gmail ? styles.outlineButtonConnected : styles.outlineButton}
              onClick={integrations.gmail ? undefined : handleConnectGmail}
            >
              {integrations.gmail ? "Desconectar Gmail" : "Conectar Gmail"}
            </button>
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
                  {integrations.calendar ? "🟢 Conectado" : "⚪ No conectado"}
                </span>
              </div>
              <p className={styles.cardDescription}>
                Conecta tu calendario para identificar reuniones, bloques de enfoque y posibles conflictos.
              </p>
            </div>
            <button 
              className={integrations.calendar ? styles.outlineButtonConnected : styles.outlineButton}
              onClick={integrations.calendar ? undefined : handleConnectCalendar}
            >
              {integrations.calendar ? "Desconectar Calendario" : "Conectar Calendario"}
            </button>
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
            <span className={styles.cognitiveFooter}>Conecta Gmail y Google Calendar para comenzar.</span>
          </div>
        </div>

        {/* Lower Section: Recent Activity */}
        <section className={styles.recentActivitySection}>
          <h2 className={styles.sectionTitle}>Actividad reciente</h2>
          <div className={styles.activityEmptyCard}>
            <History className={styles.historyIcon} size={36} />
            <p className={styles.activityEmptyText}>
              Cuando conectes tus herramientas aparecerán aquí los eventos más importantes de tu jornada.
            </p>
          </div>
        </section>
      </main>
    </div>
  );
}
