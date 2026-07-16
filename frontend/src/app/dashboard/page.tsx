"use client";

import React, { useEffect, useState } from "react";
import { CenteredLayout } from "../../components/templates/CenteredLayout/CenteredLayout";
import { Typography } from "../../components/atoms/Typography/Typography";
import { Button } from "../../components/atoms/Button/Button";
import styles from "./dashboard.module.css";

interface UserProfile {
  id: string;
  email: string;
  name: string;
  picture: string;
}

export default function DashboardPage() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchSession = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const response = await fetch(`${apiUrl}/api/v1/auth/me`, {
          credentials: "include", // Requerido para transmitir la cookie HttpOnly
        });

        if (response.ok) {
          const data = await response.json();
          if (data.status === "success" && data.user) {
            setUser(data.user);
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

  const handleLogout = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      await fetch(`${apiUrl}/api/v1/auth/logout`, {
        method: "POST",
        credentials: "include", // Requerido para borrar la cookie HttpOnly
      });
    } catch (e) {
      console.error("Error al cerrar sesión en el servidor:", e);
    }
    window.location.href = "/";
  };

  if (isLoading) {
    return (
      <CenteredLayout>
        <div className={styles.card}>
          <div className={styles.spinner}></div>
          <Typography variant="h1" className={styles.title}>
            Cargando Panel...
          </Typography>
        </div>
      </CenteredLayout>
    );
  }

  if (!user) {
    return (
      <CenteredLayout>
        <div className={styles.card}>
          <div className={styles.errorIcon}>🔒</div>
          <Typography variant="h1" className={styles.titleError}>
            Acceso Denegado
          </Typography>
          <Typography variant="h2" className={styles.subtitle}>
            Inicia sesión para poder acceder al panel de control de MindGuard.
          </Typography>
          <Button onClick={() => window.location.href = "/"} className={styles.btn}>
            Iniciar Sesión
          </Button>
        </div>
      </CenteredLayout>
    );
  }

  return (
    <CenteredLayout>
      <div className={styles.card}>
        {user.picture && (
          <img
            src={user.picture}
            alt={user.name}
            className={styles.avatar}
            referrerPolicy="no-referrer"
          />
        )}
        <Typography variant="h1" className={styles.titleSuccess}>
          ¡Bienvenido de vuelta!
        </Typography>
        <div className={styles.profileBox}>
          <Typography variant="body" className={styles.name}>
            {user.name}
          </Typography>
          <Typography variant="caption" className={styles.email}>
            {user.email}
          </Typography>
        </div>
        <Typography variant="h2" className={styles.welcomeText}>
          Te has autenticado correctamente en **MindGuard**.
        </Typography>
        <Button onClick={handleLogout} className={styles.btnSecondary}>
          Cerrar Sesión
        </Button>
      </div>
    </CenteredLayout>
  );
}
