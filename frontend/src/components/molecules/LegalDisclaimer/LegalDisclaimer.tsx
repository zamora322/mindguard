import React from "react";
import { Typography } from "../../atoms/Typography/Typography";
import styles from "./LegalDisclaimer.module.css";

export const LegalDisclaimer: React.FC = () => {
  return (
    <div className={styles.container}>
      <Typography variant="caption" className={styles.disclaimerText}>
        Al continuar, aceptas nuestros{" "}
        <a href="#" className={styles.link}>
          Términos de Servicio
        </a>{" "}
        y{" "}
        <a href="#" className={styles.link}>
          Política de Privacidad
        </a>
      </Typography>
    </div>
  );
};
