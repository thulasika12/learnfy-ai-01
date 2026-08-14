import { useState } from "react";
import { Outlet } from "react-router-dom";
import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import { PageTransition } from "../components/Motion";

export default function DashboardLayout() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      <Navbar showSidebarToggle onToggleSidebar={() => setMobileOpen(true)} />
      <div className="flex max-w-7xl mx-auto">
        <Sidebar mobileOpen={mobileOpen} onClose={() => setMobileOpen(false)} />
        <main className="flex-1 p-4 md:p-8 min-w-0">
          <PageTransition><Outlet /></PageTransition>
        </main>
      </div>
    </div>
  );
}
