import { FiDownload } from "react-icons/fi";
import toast from "react-hot-toast";
import api from "../../services/api";

export default function ExportFlashcardsMenu({ setId }) {
  const download = async (format) => { try { const response = await api.get(`/flashcards/sets/${setId}/export/${format}`, { responseType: "blob" }); const disposition = response.headers["content-disposition"] || ""; const name = disposition.match(/filename="([^"]+)"/)?.[1] || `flashcards.${format}`; const url = URL.createObjectURL(response.data); const link = document.createElement("a"); link.href = url; link.download = name; link.click(); URL.revokeObjectURL(url); toast.success(`${format.toUpperCase()} exported`); } catch (error) { toast.error(error.response?.data?.detail || `Could not export ${format.toUpperCase()}`); } };
  return <div className="flex gap-2"><button className="btn-secondary" onClick={() => download("pdf")}><FiDownload /> PDF</button><button className="btn-secondary" onClick={() => download("csv")}><FiDownload /> CSV</button></div>;
}
