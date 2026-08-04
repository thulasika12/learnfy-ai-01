import { Component } from "react";

export default class ErrorBoundary extends Component {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    console.error("Unexpected application error", error, info);
  }

  render() {
    if (!this.state.hasError) return this.props.children;
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50 p-5 text-slate-900 dark:bg-slate-950 dark:text-white">
        <section className="w-full max-w-lg rounded-lg border border-slate-200 bg-white p-7 text-center shadow-sm dark:border-slate-700 dark:bg-slate-900">
          <img src="/images/logo.png" alt="Learnfy AI" className="mx-auto h-12 w-12 rounded-lg object-cover" />
          <h1 className="mt-5 text-2xl font-bold">This page could not be displayed</h1>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">An unexpected error occurred. Reload the page or return to your dashboard.</p>
          <div className="mt-6 flex flex-wrap justify-center gap-3"><button type="button" className="btn-primary" onClick={() => window.location.reload()}>Reload page</button><a className="btn-secondary" href="/dashboard">Back to Dashboard</a></div>
        </section>
      </main>
    );
  }
}
