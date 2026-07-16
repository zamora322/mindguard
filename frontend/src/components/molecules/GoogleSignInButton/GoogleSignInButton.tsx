import React from "react";
import { Button } from "../../atoms/Button/Button";
import { GoogleIcon } from "../../atoms/GoogleIcon/GoogleIcon";
import styles from "./GoogleSignInButton.module.css";

interface GoogleSignInButtonProps {
  onClick?: () => void;
  disabled?: boolean;
}

export const GoogleSignInButton: React.FC<GoogleSignInButtonProps> = ({
  onClick,
  disabled = false,
}) => {
  return (
    <Button
      onClick={onClick}
      disabled={disabled}
      className={styles.googleBtn}
    >
      <GoogleIcon className={styles.icon} />
      <span className={styles.text}>Continuar con Google</span>
    </Button>
  );
};
