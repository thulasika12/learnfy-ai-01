import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";

import { getNote, updateNote } from "../../services/api";
import Button from "../../components/Button";
import Card from "../../components/Card";
import Loader from "../../components/Loader";

const subjects = ["Mathematics", "Physics", "Chemistry", "Biology", "Computer Science", "English", "Other"];

export default function EditNote() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [form, setForm] = useState({ title: "", description: "", subject: "Mathematics" });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getNote(id)
      .then((res) => {
        setForm({
          title: res.data.title,
          description: res.data.description || "",
          subject: res.data.subject,
        });
      })
      .catch(() => toast.error("Could not load note"))
      .finally(() => setLoading(false));
  }, [id]);

  const handleSubmit = async (ev) => {
    ev.preventDefault();
    if (!form.title.trim()) return toast.error("Title is required");
    setSaving(true);
    try {
      await updateNote(id, form);
      toast.success("Note updated successfully");
      navigate(`/notes/${id}`);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Could not update note");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <Loader />;

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="page-title">Edit Note</h1>
      <Card>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm font-medium text-slate-600 mb-1 block">Title</label>
            <input
              className="input-field"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-600 mb-1 block">Description</label>
            <textarea
              className="input-field min-h-[120px]"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-600 mb-1 block">Subject</label>
            <select
              className="input-field"
              value={form.subject}
              onChange={(e) => setForm({ ...form, subject: e.target.value })}
            >
              {subjects.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
          <Button type="submit" className="w-full" loading={saving}>
            Save Changes
          </Button>
        </form>
      </Card>
    </div>
  );
}
