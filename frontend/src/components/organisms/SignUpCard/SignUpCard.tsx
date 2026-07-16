import React from "react";
import { Logo } from "../../atoms/Logo/Logo";
import { Typography } from "../../atoms/Typography/Typography";
import { GoogleSignInButton } from "../../molecules/GoogleSignInButton/GoogleSignInButton";
import { LegalDisclaimer } from "../../molecules/LegalDisclaimer/LegalDisclaimer";
import styles from "./SignUpCard.module.css";

interface SignUpCardProps {
  onGoogleSignIn?: () => void;
  isLoading?: boolean;
}

export const SignUpCard: React.FC<SignUpCardProps> = ({
  onGoogleSignIn,
  isLoading = false,
}) => {
  return (
    <div className={styles.card}>
      <header className={styles.header}>
        <Logo size={80} className={styles.logo} />
        <div className={styles.textGroup}>
          <Typography variant="h1" className={styles.title}>
            Tu asistente inteligente para el bienestar laboral
          </Typography>
          <Typography variant="h2" className={styles.subtitle}>
            Conecta tu cuenta de Google para analizar tu correo,
            calendario y ayudarte a proteger tu tiempo de enfoque.
          </Typography>
        </div>
      </header>

      <main className={styles.main}>
        <GoogleSignInButton onClick={onGoogleSignIn} disabled={isLoading} />
      </main>

      <footer className={styles.footer}>
        <LegalDisclaimer />
      </footer>
    </div>
  );
};
