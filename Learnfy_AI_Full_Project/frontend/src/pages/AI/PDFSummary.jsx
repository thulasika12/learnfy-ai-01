import { useState } from "react";
import toast from "react-hot-toast";
import { FiFileText, FiUploadCloud } from "react-icons/fi";

import { aiSummarize, aiSummarizeFile } from "../../services/api";
import Card from "../../components/Card";
import Button from "../../components/Button";
import Loader from "../../components/Loader";
import AcademicContextFields, { emptyAcademicContext } from "../../components/subjects/AcademicContextFields";
import { usePreferences } from "../../hooks/usePreferences";

const lengths = [
  { value: "short", label: "Short" },
  { value: "medium", label: "Medium" },
  { value: "long", label: "Detailed" },
];

export default function PDFSummary() {
  const [text, setText] = useState("");
  const [length, setLength] = useState("medium");
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);
  const [fileName, setFileName] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [academic, setAcademic] = useState(emptyAcademicContext); const { language } = usePreferences();

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setFileName(file.name);
    setSelectedFile(file);

    if (file.type === "text/plain" || file.name.toLowerCase().endsWith(".md")) {
      const content = await file.text();
      setText(content);
    } else {
      setText("");
      toast.success("Document selected. Learnfy will extract its text securely.");
    }
  };

  const handleSummarize = async () => {
    if (!selectedFile && text.trim().length < 10) {
      return toast.error("Please paste or upload some note text first");
    }
    setLoading(true);
    setSummary("");
    try {
      let res;
      if (selectedFile) {
        const formData = new FormData();
        formData.append("file", selectedFile);
        formData.append("length", length);
        if (academic.subject.trim()) formData.append("subject", academic.subject.trim());
        if (academic.grade) formData.append("grade", academic.grade);
        if (academic.medium) formData.append("medium", academic.medium);
        formData.append("response_language", language);
        res = await aiSummarizeFile(formData);
      } else {
        res = await aiSummarize({ text, length, subject: academic.subject.trim() || undefined, grade: academic.grade || undefined, medium: academic.medium || undefined, response_language: language });
      }
      setSummary(res.data.summary);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Could not generate summary");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="page-title flex items-center gap-2">
          <FiFileText className="text-primary-600" /> AI Note Summarizer
        </h1>
        <p className="text-slate-500 text-sm mt-1">
          Paste notes or upload a TXT, PDF, or DOCX document to get an instant summary.
        </p>
      </div>

      <Card>
        <div className="mb-4"><AcademicContextFields value={academic} onChange={setAcademic} requireSubject={false} /></div>
        <label className="flex flex-col items-center justify-center gap-2 border-2 border-dashed border-slate-200 rounded-xl p-6 cursor-pointer hover:border-primary-400 hover:bg-primary-50/40 transition-colors mb-4">
          <FiUploadCloud size={24} className="text-slate-400" />
          <span className="text-sm text-slate-500">
            {fileName || "Upload a TXT, PDF, or DOCX file (or paste text below)"}
          </span>
          <input type="file" accept=".txt,.md,.pdf,.docx" className="hidden" onChange={handleFileChange} />
        </label>

        <textarea
          className="input-field min-h-[180px]"
          placeholder="Paste your notes here..."
          value={text}
          onChange={(e) => setText(e.target.value)}
        />

        <div className="flex items-center gap-2 mt-4 mb-4">
          {lengths.map((l) => (
            <button
              key={l.value}
              onClick={() => setLength(l.value)}
              className={`px-4 py-1.5 rounded-xl text-sm font-semibold border transition-colors ${
                length === l.value
                  ? "bg-brand-gradient text-white border-transparent"
                  : "border-slate-200 text-slate-600 hover:bg-slate-50"
              }`}
            >
              {l.label}
            </button>
          ))}
        </div>

        <Button onClick={handleSummarize} loading={loading} className="w-full">
          Generate Summary
        </Button>
      </Card>

      {loading && <Loader label="Summarizing your notes..." />}

      {summary && (
        <Card>
          <h3 className="font-bold text-slate-800 mb-3">Summary</h3>
          <p className="text-sm text-slate-600 whitespace-pre-wrap leading-relaxed">{summary}</p>
        </Card>
      )}
    </div>
  );
}
