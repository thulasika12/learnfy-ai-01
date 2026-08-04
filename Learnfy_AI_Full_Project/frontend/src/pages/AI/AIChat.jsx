import { useState, useRef, useEffect } from "react";
import { FiSend, FiZap } from "react-icons/fi";
import toast from "react-hot-toast";

import { aiChat } from "../../services/api";
import ChatMessage from "../../components/ChatMessage";
import Card from "../../components/Card";
import AcademicContextFields, { emptyAcademicContext } from "../../components/subjects/AcademicContextFields";
import { usePreferences } from "../../hooks/usePreferences";

export default function AIChat() {
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Hi! I'm your AI study tutor. Ask me anything about any subject 📚" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [academic, setAcademic] = useState(emptyAcademicContext);
  const { language } = usePreferences();
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async (ev) => {
    ev.preventDefault();
    if (!input.trim() || loading) return;

    const question = input.trim();
    setMessages((m) => [...m, { role: "user", content: question }]);
    setInput("");
    setLoading(true);

    try {
      const res = await aiChat({ question, grade: academic.grade || undefined, subject: academic.subject.trim() || undefined, medium: academic.medium || undefined, response_language: language });
      setMessages((m) => [...m, { role: "assistant", content: res.data.answer }]);
    } catch (err) {
      toast.error(err.response?.data?.detail || "AI service is unavailable right now");
      setMessages((m) => [
        ...m,
        { role: "assistant", content: "Sorry, I couldn't process that. Please try again." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto flex flex-col h-[calc(100vh-8rem)]">
      <div className="mb-4">
        <h1 className="page-title flex items-center gap-2">
          <FiZap className="text-primary-600" /> AI Doubt Solver
        </h1>
        <p className="text-slate-500 text-sm mt-1">Ask any academic question — get a clear explanation instantly.</p>
      </div>

      <Card className="flex-1 flex flex-col overflow-hidden p-0">
        <div className="border-b border-slate-100 p-3 dark:border-slate-700"><AcademicContextFields value={academic} onChange={setAcademic} requireSubject={false} /></div>
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {messages.map((m, i) => (
            <ChatMessage key={i} role={m.role} content={m.content} />
          ))}
          {loading && (
            <div className="flex items-center gap-2 text-slate-400 text-sm pl-11">
              <span className="w-2 h-2 rounded-full bg-primary-400 animate-bounce" />
              <span className="w-2 h-2 rounded-full bg-primary-400 animate-bounce [animation-delay:0.1s]" />
              <span className="w-2 h-2 rounded-full bg-primary-400 animate-bounce [animation-delay:0.2s]" />
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <form onSubmit={handleSend} className="border-t border-slate-100 p-4 flex gap-2">
          <input
            className="input-field flex-1"
            placeholder="Type your question here..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
          <button type="submit" disabled={loading} className="btn-primary px-4">
            <FiSend />
          </button>
        </form>
      </Card>
    </div>
  );
}
