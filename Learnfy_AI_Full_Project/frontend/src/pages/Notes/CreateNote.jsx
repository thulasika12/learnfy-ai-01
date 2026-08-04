import { useState } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { FiUploadCloud, FiFile } from "react-icons/fi";

import { uploadNote } from "../../services/api";
import Button from "../../components/Button";
import Card from "../../components/Card";
import AcademicContextFields, { emptyAcademicContext } from "../../components/subjects/AcademicContextFields";

export default function CreateNote() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ title: "", description: "" });
  const [academic, setAcademic] = useState(emptyAcademicContext);
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (ev) => {
    ev.preventDefault();
    if (!form.title.trim()) return toast.error("Please add a title");

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("title", form.title);
      formData.append("description", form.description);
      formData.append("subject", academic.subject.trim());
      formData.append("grade", academic.grade);
      formData.append("stream", academic.stream);
      formData.append("medium", academic.medium);
      if (file) formData.append("file", file);

      const res = await uploadNote(formData);
      toast.success("Note uploaded successfully!");
      navigate(`/notes/${res.data.id}`);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="page-title">Upload a Note</h1>

      <Card>
        <form onSubmit={handleSubmit} className="space-y-4">
          <AcademicContextFields value={academic} onChange={setAcademic} />
          <div>
            <label className="text-sm font-medium text-slate-600 mb-1 block">Title</label>
            <input
              className="input-field"
              placeholder="e.g. Newton's Laws of Motion — Summary"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
            />
          </div>

          <div>
            <label className="text-sm font-medium text-slate-600 mb-1 block">Description</label>
            <textarea
              className="input-field min-h-[120px]"
              placeholder="Briefly describe what these notes cover..."
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </div>

          <div>
            <label className="text-sm font-medium text-slate-600 mb-1 block">Attach File (optional)</label>
            <label className="flex flex-col items-center justify-center gap-2 border-2 border-dashed border-slate-200 rounded-xl p-8 cursor-pointer hover:border-primary-400 hover:bg-primary-50/40 transition-colors">
              {file ? (
                <>
                  <FiFile size={28} className="text-primary-600" />
                  <span className="text-sm text-slate-600">{file.name}</span>
                </>
              ) : (
                <>
                  <FiUploadCloud size={28} className="text-slate-400" />
                  <span className="text-sm text-slate-500">Click to select a PDF, DOC, or image</span>
                </>
              )}
              <input type="file" className="hidden" onChange={(e) => setFile(e.target.files?.[0] || null)} />
            </label>
          </div>

          <Button type="submit" className="w-full" loading={loading}>
            Upload Note
          </Button>
        </form>
      </Card>
    </div>
  );
}
