import React from "react";
import styles from "./Button.module.css";

interface ButtonProps {
  onClick?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  disabled?: boolean;
  children: React.ReactNode;
  className?: string;
  id?: string;
}

export const Button: React.FC<ButtonProps> = ({
  onClick,
  disabled = false,
  children,
  className = "",
  id,
}) => {
  return (
    <button
      id={id}
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`${styles.button} ${className}`}
    >
      {children}
    </button>
  );
};
