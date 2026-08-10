import Link from "next/link";

const NAV = [
  { href: "/", label: "Dashboard" },
  { href: "/runs", label: "Research Runs" },
  { href: "/candidates", label: "Candidates" },
  { href: "/audit", label: "Audit & QA" },
  { href: "/settings", label: "Settings" },
];

export function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">investing-insight</div>
        <nav>
          {NAV.map((item) => (
            <Link key={item.href} href={item.href} className="nav-link">
              {item.label}
            </Link>
          ))}
        </nav>
        <p className="sidebar-note">PC · 1280px+ audit console</p>
      </aside>
      <div className="main-wrap">{children}</div>
    </div>
  );
}
