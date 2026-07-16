import React from "react";
import styles from "./CenteredLayout.module.css";

interface CenteredLayoutProps {
  children: React.ReactNode;
}

export const CenteredLayout: React.FC<CenteredLayoutProps> = ({ children }) => {
  return (
    <div className={styles.wrapper}>
      <main className={styles.container}>{children}</main>
    </div>
  );
};
