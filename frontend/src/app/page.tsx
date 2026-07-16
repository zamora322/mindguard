"use client";

import React, { useState } from "react";
import { CenteredLayout } from "../components/templates/CenteredLayout/CenteredLayout";
import { SignUpCard } from "../components/organisms/SignUpCard/SignUpCard";

export default function Home() {
  const [isLoading, setIsLoading] = useState(false);

  const handleGoogleSignIn = async () => {
    setIsLoading(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/v1/auth/login`);

      if (!response.ok) {
        throw new Error("No se pudo obtener la URL de autenticación");
      }

      const data = await response.json();

      if (data.url) {
        // Redirigir al flujo de consentimiento de Google OAuth
        window.location.href = data.url;
      } else {
        throw new Error("La respuesta del backend no contiene una URL válida");
      }
    } catch (error) {
      console.error("Error al iniciar sesión con Google:", error);
      alert("Error al intentar conectar con Google.");
      setIsLoading(false);
    }
  };

  return (
    <CenteredLayout>
      <SignUpCard onGoogleSignIn={handleGoogleSignIn} isLoading={isLoading} />
    </CenteredLayout>
  );
}
