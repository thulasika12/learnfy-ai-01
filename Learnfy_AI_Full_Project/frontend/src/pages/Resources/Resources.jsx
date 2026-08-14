import { useState } from "react";
import toast from "react-hot-toast";
import { FiBookOpen, FiDownload, FiTrash2, FiUploadCloud } from "react-icons/fi";

import { useAuth } from "../../hooks/useAuth";
import useFetch from "../../hooks/useFetch";
import { BASE_URL, deleteResource, getResources, uploadResource } from "../../services/api";
import Button from "../../components/Button";
import Card from "../../components/Card";
import { SkeletonGrid } from "../../components/Motion";
import StreamSelect from "../../components/subjects/StreamSelect";
import SubjectSelect from "../../components/subjects/SubjectSelect";
import AcademicContextFields from "../../components/subjects/AcademicContextFields";
import { useAcademicDefaults } from "../../hooks/useAcademicDefaults";

export default function Resources() {
  const { user } = useAuth();
  const { data: resources, loading, refetch } = useFetch(() => getResources(), []);
  const [form, setForm] = useState({ title: "", description: "", stream: "Physical Science", subject: "Physics" });
  const [academic, setAcademic] = useAcademicDefaults();
  const [filters, setFilters] = useState({ stream: "", subject: "" });
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const canUpload = user?.role === "teacher" || user?.role === "admin";

  const handleUpload = async (event) => {
    event.preventDefault();
    if (!form.title.trim()) return toast.error("Resource title is required");
    setUploading(true);
    try {
      const data = new FormData();
      data.append("title", form.title);
      data.append("description", form.description);
      data.append("subject", academic.subject.trim());
      data.append("grade", academic.grade);
      data.append("stream", academic.stream);
      data.append("medium", academic.medium);
      if (file) data.append("file", file);
      await uploadResource(data);
      setForm({ title: "", description: "", stream: "Physical Science", subject: "Physics" });
      setFile(null);
      toast.success("Resource uploaded");
      refetch();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Could not upload resource");
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this resource?")) return;
    try {
      await deleteResource(id);
      toast.success("Resource deleted");
      refetch();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Could not delete resource");
    }
  };

  return (
    <div className="mx-auto max-w-6xl space-y-7 px-4 py-8 md:px-6">
      <div>
        <h1 className="page-title flex items-center gap-2">
          <FiBookOpen /> Study Resources
        </h1>
        <p className="mt-2 text-sm text-slate-500">
          Teacher-curated PDFs, presentations, documents, and learning materials.
        </p>
      </div>

      {canUpload && (
        <Card>
          <h2 className="mb-4 font-bold text-slate-800">Upload a resource</h2>
          <form onSubmit={handleUpload} className="grid gap-4 md:grid-cols-2">
            <input
              className="input-field"
              placeholder="Resource title"
              value={form.title}
              onChange={(event) => setForm({ ...form, title: event.target.value })}
            />
            <div className="md:col-span-2"><AcademicContextFields value={academic} onChange={setAcademic} /></div>
            <textarea
              className="input-field min-h-24 md:col-span-2"
              placeholder="Short description"
              value={form.description}
              onChange={(event) => setForm({ ...form, description: event.target.value })}
            />
            <label className="input-field flex cursor-pointer items-center gap-2 text-sm text-slate-500">
              <FiUploadCloud />
              {file?.name || "Choose PDF, DOCX, PPT, image, or text file"}
              <input
                type="file"
                className="hidden"
                accept=".pdf,.doc,.docx,.ppt,.pptx,.txt,.png,.jpg,.jpeg,.webp"
                onChange={(event) => setFile(event.target.files?.[0] || null)}
              />
            </label>
            <Button type="submit" loading={uploading}>Upload Resource</Button>
          </form>
        </Card>
      )}

      {loading ? (
        <SkeletonGrid />
      ) : resources?.length ? (
        <><div className="mb-4 grid gap-3 sm:grid-cols-2"><StreamSelect value={filters.stream} includeAll onChange={(stream) => setFilters({ stream, subject: "" })} /><SubjectSelect stream={filters.stream} value={filters.subject} includeAll onChange={(subject) => setFilters({ ...filters, subject })} /></div><div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {resources.filter((resource) => !filters.subject || resource.subject === filters.subject).map((resource) => (
            <Card key={resource.id} className="flex flex-col gap-3">
              <span className="w-fit rounded-full bg-primary-50 px-3 py-1 text-xs font-semibold text-primary-700">
                {[resource.grade, resource.subject, resource.medium?.toUpperCase()].filter(Boolean).join(" · ")}
              </span>
              <h2 className="font-bold text-slate-800">{resource.title}</h2>
              <p className="flex-1 text-sm text-slate-500">{resource.description || "No description provided."}</p>
              <div className="flex items-center justify-between border-t border-slate-100 pt-3">
                {resource.file_url ? (
                  <a
                    href={`${BASE_URL}${resource.file_url}`}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-1 text-sm font-semibold text-primary-600"
                  >
                    <FiDownload /> Download
                  </a>
                ) : (
                  <span className="text-xs text-slate-400">No attachment</span>
                )}
                {(user?.role === "admin" || user?.id === resource.teacher_id) && (
                  <button
                    onClick={() => handleDelete(resource.id)}
                    className="rounded-lg p-2 text-red-500 hover:bg-red-50"
                    title="Delete resource"
                  >
                    <FiTrash2 />
                  </button>
                )}
              </div>
            </Card>
          ))}
        </div></>
      ) : (
        <Card className="py-12 text-center text-slate-500">No resources have been uploaded yet.</Card>
      )}
    </div>
  );
}
