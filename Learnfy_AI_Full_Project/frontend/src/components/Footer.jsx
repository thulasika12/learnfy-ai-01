import { Link } from "react-router-dom";
import { FiGithub, FiTwitter, FiLinkedin } from "react-icons/fi";

export default function Footer() {
  return (
    <footer className="bg-slate-900 text-slate-300 mt-20">
      <div className="max-w-7xl mx-auto px-6 py-12 grid grid-cols-1 md:grid-cols-4 gap-8">
        <div>
          <div className="flex items-center gap-2 mb-3">
            <img src="/images/logo.png" alt="Learnfy AI" className="w-9 h-9 rounded-lg" />
            <span className="font-extrabold text-lg text-white">Learnfy AI</span>
          </div>
          <p className="text-sm text-slate-400">Learn • Connect • Grow — AI-powered learning for every student.</p>
        </div>

        <div>
          <h4 className="font-semibold text-white mb-3">Platform</h4>
          <ul className="space-y-2 text-sm">
            <li><Link to="/notes" className="hover:text-white">Explore Notes</Link></li>
            <li><Link to="/ai/chat" className="hover:text-white">AI Doubt Solver</Link></li>
            <li><Link to="/groups" className="hover:text-white">Study Groups</Link></li>
          </ul>
        </div>

        <div>
          <h4 className="font-semibold text-white mb-3">Company</h4>
          <ul className="space-y-2 text-sm">
            <li><a href="#" className="hover:text-white">About</a></li>
            <li><a href="#" className="hover:text-white">Privacy Policy</a></li>
            <li><a href="#" className="hover:text-white">Terms of Service</a></li>
          </ul>
        </div>

        <div>
          <h4 className="font-semibold text-white mb-3">Connect</h4>
          <div className="flex gap-3">
            <a href="#" className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700"><FiGithub /></a>
            <a href="#" className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700"><FiTwitter /></a>
            <a href="#" className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700"><FiLinkedin /></a>
          </div>
        </div>
      </div>
      <div className="border-t border-slate-800 py-4 text-center text-xs text-slate-500">
        © {new Date().getFullYear()} Learnfy AI. All rights reserved.
      </div>
    </footer>
  );
}
