/**
 * Auth layout - renders pages without the main navigation sidebar.
 * Used for login and register pages.
 */
export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
