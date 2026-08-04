import { useState, useRef } from "react";
import toast from "react-hot-toast";
import { FiCamera, FiMail, FiAward, FiEdit2 } from "react-icons/fi";

import { useAuth } from "../../hooks/useAuth";
import { updateAcademicProfile, updateProfile, uploadAvatar } from "../../services/api";
import Card from "../../components/Card";
import Button from "../../components/Button";
import AcademicContextFields, { emptyAcademicContext } from "../../components/subjects/AcademicContextFields";

const badges = [
  { label: "Fast Learner", color: "bg-amber-100 text-amber-700" },
  { label: "Top Contributor", color: "bg-primary-100 text-primary-700" },
  { label: "7-Day Streak", color: "bg-emerald-100 text-emerald-700" },
];

export default function Profile() {
  const { user, updateUserCache } = useAuth();
  const [editing, setEditing] = useState(false);
  const [bio, setBio] = useState(user?.bio || "");
  const [academic, setAcademic] = useState(emptyAcademicContext);
  const [saving, setSaving] = useState(false);
  const fileRef = useRef(null);

  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await updateProfile({ bio });
      if (academic.educationLevelId) await updateAcademicProfile({ education_level_id:Number(academic.educationLevelId), grade_id:academic.gradeId?Number(academic.gradeId):null, medium:academic.medium||null, subject_ids:academic.subjectId?[academic.subjectId]:[], school_name:null, district:null, guardian_consent:true });
      updateUserCache(res.data);
      toast.success("Profile updated");
      setEditing(false);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Could not update profile");
    } finally {
      setSaving(false);
    }
  };

  const handleAvatarChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await uploadAvatar(formData);
      updateUserCache(res.data);
      toast.success("Profile picture updated");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Upload failed");
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <h1 className="page-title">My Profile</h1>

      <Card className="flex flex-col sm:flex-row items-center gap-6">
        <div className="relative">
          <img
            src={user?.profile_image || `https://api.dicebear.com/7.x/initials/svg?seed=${user?.name}`}
            className="w-24 h-24 rounded-full object-cover border-4 border-white shadow-md"
            alt="avatar"
          />
          <button
            onClick={() => fileRef.current?.click()}
            className="absolute bottom-0 right-0 w-8 h-8 bg-primary-600 text-white rounded-full flex items-center justify-center shadow-md hover:bg-primary-700"
          >
            <FiCamera size={14} />
          </button>
          <input type="file" accept="image/*" ref={fileRef} className="hidden" onChange={handleAvatarChange} />
        </div>

        <div className="text-center sm:text-left flex-1">
          <h2 className="text-xl font-bold text-slate-800">{user?.name}</h2>
          <p className="text-slate-500 flex items-center justify-center sm:justify-start gap-1 text-sm mt-1">
            <FiMail size={14} /> {user?.email}
          </p>
          <span className="inline-block mt-2 text-xs font-semibold px-3 py-1 rounded-full bg-primary-50 text-primary-700 capitalize">
            {user?.role}
          </span>
          <div className="mt-2 flex flex-wrap justify-center gap-2 sm:justify-start">{user?.student_verification_status==="verified"&&<span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">Verified Student</span>}{user?.student_verification_status==="pending"&&<span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-700">Student proof pending</span>}{user?.student_verification_status==="rejected"&&<span className="rounded-full bg-red-100 px-3 py-1 text-xs font-semibold text-red-700">Student proof needs attention</span>}</div>
        </div>
      </Card>

      <Card>
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-bold text-slate-800">About / Learning Interests</h3>
          <button onClick={() => setEditing(!editing)} className="text-primary-600 hover:text-primary-700">
            <FiEdit2 size={16} />
          </button>
        </div>
        {editing ? (
          <div className="space-y-3">
            <textarea
              className="input-field min-h-[100px]"
              placeholder="Tell others what you're studying and interested in..."
              value={bio}
              onChange={(e) => setBio(e.target.value)}
            />
            <AcademicContextFields value={academic} onChange={setAcademic} />
            <Button onClick={handleSave} loading={saving}>
              Save Changes
            </Button>
          </div>
        ) : (
          <div><p className="text-sm text-slate-500">{user?.bio || "No bio added yet. Click edit to add one."}</p>{user?.academic_subject && <p className="mt-3 text-sm font-semibold text-primary-600">A/L · {user.academic_stream} · {user.academic_subject}</p>}</div>
        )}
      </Card>

      <Card>
        <h3 className="font-bold text-slate-800 mb-4 flex items-center gap-2">
          <FiAward /> Achievement Badges
        </h3>
        <div className="flex flex-wrap gap-2">
          {badges.map((b) => (
            <span key={b.label} className={`text-xs font-semibold px-3 py-1.5 rounded-full ${b.color}`}>
              {b.label}
            </span>
          ))}
        </div>
      </Card>
    </div>
  );
}
