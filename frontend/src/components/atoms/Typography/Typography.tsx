import React from "react";
import styles from "./Typography.module.css";

type Variant = "h1" | "h2" | "body" | "caption";

interface TypographyProps {
  variant?: Variant;
  children: React.ReactNode;
  className?: string;
  id?: string;
}

export const Typography: React.FC<TypographyProps> = ({
  variant = "body",
  children,
  className = "",
  id,
}) => {
  // Use semantic HTML elements based on variant
  const Component = variant === "h1" ? "h1" : variant === "h2" ? "h2" : variant === "caption" ? "span" : "p";
  const variantClass = styles[variant] || "";

  return (
    <Component id={id} className={`${variantClass} ${className}`}>
      {children}
    </Component>
  );
};
