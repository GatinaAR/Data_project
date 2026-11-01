import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Медиа-Пульс",
  description: "Аналитика новостной повестки",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="ru">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
