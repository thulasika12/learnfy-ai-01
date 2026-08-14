import { Outlet } from "react-router-dom";
import Navbar from "../components/Navbar";
import Footer from "../components/Footer";
import { PageTransition } from "../components/Motion";

export default function MainLayout() {
  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-950">
      <Navbar />
      <main className="flex-1">
        <PageTransition><Outlet /></PageTransition>
      </main>
      <Footer />
    </div>
  );
}
