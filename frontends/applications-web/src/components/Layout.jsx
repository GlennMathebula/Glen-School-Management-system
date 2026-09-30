import { NavLink } from "react-router-dom";
import { APP_CONFIG } from "../config/app";

function NavItem({ to, children }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `nav-link ${isActive ? "nav-link-active" : ""}`
      }
    >
      {children}
    </NavLink>
  );
}

export default function Layout({ children }) {
  return (
    <div className="app-shell">
      <header className="site-header">
        <div className="container header-inner">
          <NavLink className="brand" to="/">
            <img
              className="brand-logo"
              src="/glen-moniques-logo.png"
              alt="Glen Moniques"
            />
            <span className="brand-copy">
              <strong>{APP_CONFIG.organisation}</strong>
              <span>{APP_CONFIG.tagline}</span>
            </span>
          </NavLink>

          <nav className="main-nav" aria-label="Primary navigation">
            <NavItem to="/apply">Apply</NavItem>
            <NavItem to="/status">Application Status</NavItem>
            <NavItem to="/register">Register</NavItem>
          </nav>
        </div>
      </header>

      <main>{children}</main>

      <footer className="site-footer">
        <div className="container footer-grid">
          <div>
            <strong>{APP_CONFIG.legalName}</strong>
            <p>{APP_CONFIG.tagline}</p>
          </div>
          <div>
            <p>Reg. {APP_CONFIG.registrationNumber}</p>
            <p>{APP_CONFIG.email}</p>
            <p>{APP_CONFIG.phone}</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
