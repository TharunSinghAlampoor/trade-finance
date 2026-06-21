import Navbar from "./Navbar";

export default function Layout({ me, children }) {
  return (
    <div className="relative z-10 min-h-screen">
      <Navbar me={me} />
      <main className="relative z-10">{children}</main>
    </div>
  );
}
