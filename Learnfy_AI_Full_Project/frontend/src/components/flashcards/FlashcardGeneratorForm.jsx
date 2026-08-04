import { useEffect, useState } from "react";
import { FiFile, FiFileText, FiLayers, FiUploadCloud } from "react-icons/fi";
import toast from "react-hot-toast";

import Button from "../Button";
import { generateFlashcards, generateFlashcardsFromFile, generateFlashcardsFromNote, generateFlashcardsFromText, getNotes } from "../../services/api";
import AcademicContextFields, { emptyAcademicContext } from "../subjects/AcademicContextFields";

const sources = [{ id: "topic", label: "Topic", icon: FiLayers }, { id: "text", label: "Paste notes", icon: FiFileText }, { id: "note", label: "Saved note", icon: FiFile }, { id: "pdf", label: "PDF", icon: FiUploadCloud }, { id: "document", label: "Document", icon: FiUploadCloud }];

export default function FlashcardGeneratorForm({ initialNoteId, onGenerated }) {
  const [source, setSource] = useState(initialNoteId ? "note" : "topic");
  const [notes, setNotes] = useState([]);
  const [file, setFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({ topic: "", title: "", text: "", note_id: initialNoteId || "", count: 10, difficulty: "medium", language: "en" });
  const [academic, setAcademic] = useState(emptyAcademicContext);

  useEffect(() => { if (source === "note" && !notes.length) getNotes({}).then((res) => setNotes(res.data)).catch(() => toast.error("Could not load notes")); }, [notes.length, source]);

  const submit = async (event) => {
    event.preventDefault(); if (loading) return;
    if (form.count < 1 || form.count > 30) return toast.error("Choose between 1 and 30 cards");
    setLoading(true); setUploadProgress(0);
    try {
      const common = { subject: academic.subject.trim(), grade: academic.grade, medium: academic.medium, count: Number(form.count), difficulty: form.difficulty, language: form.language };
      let response;
      if (source === "topic") {
        if (!form.topic.trim()) throw new Error("Enter a topic");
        response = await generateFlashcards({ ...common, topic: form.topic.trim() });
      } else if (source === "text") {
        if (form.text.trim().length < 20) throw new Error("Paste at least 20 characters of notes");
        response = await generateFlashcardsFromText({ ...common, title: form.title.trim() || "My Notes", text: form.text.trim() });
      } else if (source === "note") {
        if (!form.note_id) throw new Error("Select a saved note");
        response = await generateFlashcardsFromNote({ note_id: Number(form.note_id), count: common.count, difficulty: common.difficulty, language: common.language });
      } else {
        if (!file) throw new Error(`Choose a ${source === "pdf" ? "PDF" : "document"}`);
        const data = new FormData(); data.append("file", file); data.append("title", form.title.trim() || file.name.replace(/\.[^.]+$/, ""));
        Object.entries(common).forEach(([key, value]) => data.append(key, value));
        response = await generateFlashcardsFromFile(`/flashcards/generate-from-${source}`, data, (progress) => setUploadProgress(progress.total ? Math.round(progress.loaded / progress.total * 100) : 0));
      }
      onGenerated(response.data); toast.success(`${response.data.cards.length} flashcards generated`);
    } catch (error) {
      toast.error(error.response?.data?.detail || error.message || "Could not generate flashcards");
    } finally { setLoading(false); }
  };

  return <form onSubmit={submit} className="space-y-5">
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-5" role="tablist" aria-label="Flashcard source">
      {sources.map((item) => <button key={item.id} type="button" role="tab" aria-selected={source === item.id} onClick={() => setSource(item.id)} className={`flex min-h-16 flex-col items-center justify-center gap-1 rounded-lg border px-2 text-xs font-semibold ${source === item.id ? "border-primary-500 bg-primary-50 text-primary-700 dark:bg-slate-800" : "border-slate-200 text-slate-500 dark:border-slate-700"}`}><item.icon size={18} />{item.label}</button>)}
    </div>
    {source === "topic" && <label className="block text-sm font-medium dark:text-slate-200">Topic<input className="input-field mt-1" value={form.topic} onChange={(e) => setForm({ ...form, topic: e.target.value })} placeholder="e.g. Photosynthesis" /></label>}
    {source === "text" && <><label className="block text-sm font-medium dark:text-slate-200">Set title<input className="input-field mt-1" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} /></label><label className="block text-sm font-medium dark:text-slate-200">Notes<textarea className="input-field mt-1 min-h-36" value={form.text} onChange={(e) => setForm({ ...form, text: e.target.value })} placeholder="Paste the source notes here..." /></label></>}
    {source === "note" && <label className="block text-sm font-medium dark:text-slate-200">Learnfy note<select className="input-field mt-1" value={form.note_id} onChange={(e) => setForm({ ...form, note_id: e.target.value })}><option value="">Select a note</option>{notes.map((note) => <option key={note.id} value={note.id}>{note.title} ({note.subject})</option>)}</select></label>}
    {["pdf", "document"].includes(source) && <><label className="block text-sm font-medium dark:text-slate-200">Set title<input className="input-field mt-1" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Defaults to filename" /></label><label className="flex min-h-28 cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-slate-300 p-4 text-center dark:border-slate-600"><FiUploadCloud size={25} /><span className="mt-2 text-sm">{file?.name || (source === "pdf" ? "Choose a text-based PDF" : "Choose TXT, Markdown, PDF, or DOCX")}</span><input type="file" className="sr-only" accept={source === "pdf" ? ".pdf,application/pdf" : ".txt,.md,.pdf,.docx"} onChange={(e) => setFile(e.target.files?.[0] || null)} /></label>{uploadProgress > 0 && <div className="h-2 overflow-hidden rounded bg-slate-100"><div className="h-full bg-primary-500" style={{ width: `${uploadProgress}%` }} /></div>}</>}
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <div className="sm:col-span-2 lg:col-span-4"><AcademicContextFields value={academic} onChange={setAcademic} /></div>
      <label className="text-sm font-medium dark:text-slate-200">Cards<input type="number" min="1" max="30" className="input-field mt-1" value={form.count} onChange={(e) => setForm({ ...form, count: e.target.value })} /></label>
      <label className="text-sm font-medium dark:text-slate-200">Difficulty<select className="input-field mt-1" value={form.difficulty} onChange={(e) => setForm({ ...form, difficulty: e.target.value })}><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></select></label>
      <label className="text-sm font-medium dark:text-slate-200">Language<select className="input-field mt-1" value={form.language} onChange={(e) => setForm({ ...form, language: e.target.value })}><option value="en">English</option><option value="ta">தமிழ்</option><option value="si">සිංහල</option></select></label>
    </div>
    <Button type="submit" loading={loading} className="w-full">Generate Flashcards</Button>
  </form>;
}
