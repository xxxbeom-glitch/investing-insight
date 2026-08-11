import Link from "next/link";

const NAV = [
  { href: "/", label: "대시보드" },
  { href: "/runs", label: "리서치 실행" },
  { href: "/candidates", label: "후보 종목" },
  { href: "/audit", label: "감사·QA" },
  { href: "/ops", label: "운영 상태" },
  { href: "/settings", label: "설정" },
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
        <p className="sidebar-note">PC · 가로 1280px 이상</p>
      </aside>
      <div className="main-wrap">{children}</div>
    </div>
  );
}
