import { Link, NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";

export default function Layout() {
  const { account, isAuthenticated, logout } = useAuth();

  return (
    <div className="career-app">
      <header className="career-header">
        <div className="career-header-inner">
          <Link className="career-brand" to="/">
            <img
              src="/glen-moniques-logo.png"
              alt="Glen Moniques"
            />
            <div>
              <strong>Glen Moniques</strong>
              <span>Careers Portal</span>
            </div>
          </Link>

          <nav className="career-nav">
            <NavLink to="/">Vacancies</NavLink>

            {isAuthenticated ? (
              <>
                <NavLink to="/dashboard">My Applications</NavLink>
                <NavLink to="/account">Account</NavLink>
                <button
                  type="button"
                  className="career-nav-button"
                  onClick={logout}
                >
                  Sign Out
                </button>
              </>
            ) : (
              <>
                <NavLink to="/login">Sign In</NavLink>
                <NavLink
                  className="career-nav-create"
                  to="/create-account"
                >
                  Create Account
                </NavLink>
              </>
            )}
          </nav>
        </div>
      </header>

      {isAuthenticated && account ? (
        <div className="career-session-bar">
          <div className="career-container">
            Signed in as{" "}
            <strong>
              {account.first_name} {account.last_name}
            </strong>
            <span>{account.applicant_number}</span>
          </div>
        </div>
      ) : null}

      <main>
        <Outlet />
      </main>

      <footer className="career-footer">
        <div className="career-container career-footer-grid">
          <div>
            <strong>GLEN MONIQUES (PTY) LTD</strong>
            <p>Careers and recruitment portal</p>
          </div>
          <div>
            <p>Reg. 2020/089305/07</p>
            <p>admin@glenmoniques.co.za</p>
            <p>015 880 2413</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
