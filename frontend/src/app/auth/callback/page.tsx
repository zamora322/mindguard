"use client";

import React, { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { CenteredLayout } from "../../../components/templates/CenteredLayout/CenteredLayout";
import { Typography } from "../../../components/atoms/Typography/Typography";
import { Button } from "../../../components/atoms/Button/Button";
import styles from "./callback.module.css";

interface UserProfile {
  id: string;
  email: string;
  name: string;
  given_name: string;
  family_name: string;
  picture: string;
}

function CallbackContent() {
  const searchParams = useSearchParams();
  const code = searchParams.get("code");
  const errorParam = searchParams.get("error");

  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [user, setUser] = useState<UserProfile | null>(null);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    if (errorParam) {
      setStatus("error");
      setErrorMessage(`Google retornó un error: ${errorParam}`);
      return;
    }

    if (!code) {
      setStatus("error");
      setErrorMessage("No se encontró ningún código de autenticación en la URL.");
      return;
    }

    const verifyAuth = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const response = await fetch(`${apiUrl}/api/v1/auth/callback`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ code }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || "Error al verificar con el servidor backend");
        }

        const data = await response.json();
        if (data.status === "success" && data.user) {
          setUser(data.user);
          setStatus("success");
        } else {
          throw new Error("Respuesta inválida del servidor");
        }
      } catch (err: any) {
        console.error("Error durante verificación:", err);
        setStatus("error");
        setErrorMessage(err.message || "Error al conectar con el servidor backend.");
      }
    };

    verifyAuth();
  }, [code, errorParam]);

  const handleGoHome = () => {
    window.location.href = "/";
  };

  if (status === "loading") {
    return (
      <div className={styles.card}>
        <div className={styles.spinner}></div>
        <Typography variant="h1" className={styles.title}>
          Validando autenticación
        </Typography>
        <Typography variant="h2" className={styles.subtitle}>
          Conectando de forma segura con los servidores de Google...
        </Typography>
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className={styles.card}>
        <div className={styles.errorIcon}>⚠️</div>
        <Typography variant="h1" className={styles.titleError}>
          Error de Autenticación
        </Typography>
        <Typography variant="h2" className={styles.subtitle}>
          {errorMessage}
        </Typography>
        <Button onClick={handleGoHome} className={styles.btn}>
          Volver a Intentar
        </Button>
      </div>
    );
  }

  return (
    <div className={styles.card}>
      {user?.picture && (
        <img
          src={user.picture}
          alt={user.name}
          className={styles.avatar}
          referrerPolicy="no-referrer"
        />
      )}
      <Typography variant="h1" className={styles.titleSuccess}>
        ¡Inicio de sesión exitoso!
      </Typography>
      <div className={styles.profileBox}>
        <Typography variant="body" className={styles.name}>
          {user?.name}
        </Typography>
        <Typography variant="caption" className={styles.email}>
          {user?.email}
        </Typography>
      </div>
      <Typography variant="h2" className={styles.welcomeText}>
        Te has autenticado correctamente en <br>MindGuard</br>.
      </Typography>
      <Button onClick={handleGoHome} className={styles.btnSecondary}>
        Cerrar Sesión
      </Button>
    </div>
  );
}

export default function CallbackPage() {
  return (
    <CenteredLayout>
      <Suspense fallback={
        <div className={styles.card}>
          <div className={styles.spinner}></div>
          <Typography variant="h1" className={styles.title}>
            Cargando...
          </Typography>
        </div>
      }>
        <CallbackContent />
      </Suspense>
    </CenteredLayout>
  );
}
