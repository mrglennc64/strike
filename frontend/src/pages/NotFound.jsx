import { Link } from "react-router-dom";

// Catch-all for unknown routes — a blank page reads as a crash, so say plainly
// that the URL doesn't exist and point back home.
export default function NotFound() {
  return (
    <div className="app">
      <header>
        <div className="nav">
          <Link to="/" className="home-link">← Home</Link>
        </div>
        <h1>Page not found</h1>
        <p className="sub">
          There's nothing at this address. It may have moved, or the URL has a
          typo.
        </p>
      </header>
      <p>
        <Link to="/" className="home-link">Go back to the dashboard</Link>
      </p>
      <footer>404 — no slate here.</footer>
    </div>
  );
}
