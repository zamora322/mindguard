import React from "react";
import Image from "next/image";
import styles from "./Logo.module.css";

interface LogoProps {
  size?: number;
  className?: string;
}

export const Logo: React.FC<LogoProps> = ({ size = 96, className = "" }) => {
  return (
    <div className={`${styles.logoContainer} ${className}`}>
      <Image
        src="/logo.png"
        alt="MindGuard Logo"
        width={size}
        height={size}
        className={styles.logoImage}
        priority
      />
    </div>
  );
};
