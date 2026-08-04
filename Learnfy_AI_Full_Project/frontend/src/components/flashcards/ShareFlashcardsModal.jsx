import { useState } from "react";
import toast from "react-hot-toast";
import { FiCopy, FiShare2, FiX } from "react-icons/fi";
import Modal from "../Modal";
import { shareFlashcardSet, unshareFlashcardSet } from "../../services/api";

export default function ShareFlashcardsModal({ flashcardSet, isOpen, onClose, onChanged }) {
  const [days, setDays] = useState(""); const [link, setLink] = useState(flashcardSet.share_token ? `${window.location.origin}/flashcards/shared/${flashcardSet.share_token}` : ""); const [loading, setLoading] = useState(false);
  const enable = async () => { setLoading(true); try { const response = await shareFlashcardSet(flashcardSet.id, { expires_in_days: days ? Number(days) : null }); setLink(response.data.share_url); onChanged?.({ ...flashcardSet, is_public: true, share_token: response.data.share_token }); toast.success("Read-only share link created"); } catch { toast.error("Could not create share link"); } finally { setLoading(false); } };
  const disable = async () => { setLoading(true); try { await unshareFlashcardSet(flashcardSet.id); setLink(""); onChanged?.({ ...flashcardSet, is_public: false, share_token: null }); toast.success("Sharing disabled"); } catch { toast.error("Could not disable sharing"); } finally { setLoading(false); } };
  const copy = async () => { await navigator.clipboard.writeText(link); toast.success("Link copied"); };
  const nativeShare = async () => { if (navigator.share) await navigator.share({ title: flashcardSet.title, url: link }); else copy(); };
  return <Modal isOpen={isOpen} onClose={onClose} title="Share flashcards"><div className="space-y-4"><p className="text-sm text-slate-500">Anyone with the link can view this set read-only. Your account details stay private.</p>{!link && <label className="block text-sm font-medium dark:text-slate-200">Link expiry<select className="input-field mt-1" value={days} onChange={(e) => setDays(e.target.value)}><option value="">Never</option><option value="7">7 days</option><option value="30">30 days</option><option value="90">90 days</option></select></label>}{link && <input readOnly className="input-field" value={link} /> }<div className="flex flex-wrap gap-2">{!link ? <button disabled={loading} onClick={enable} className="btn-primary"><FiShare2 /> Enable sharing</button> : <><button onClick={copy} className="btn-primary"><FiCopy /> Copy link</button><button onClick={nativeShare} className="btn-secondary"><FiShare2 /> Share</button><button disabled={loading} onClick={disable} className="btn-secondary text-red-600"><FiX /> Disable</button></>}</div></div></Modal>;
}
