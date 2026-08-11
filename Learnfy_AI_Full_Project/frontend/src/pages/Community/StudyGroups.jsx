import { useState } from "react";
import toast from "react-hot-toast";
import {
  FiCheck,
  FiClock,
  FiMessageSquare,
  FiPlus,
  FiSend,
  FiShield,
  FiTrash2,
  FiUsers,
  FiX,
} from "react-icons/fi";

import useFetch from "../../hooks/useFetch";
import { usePreferences } from "../../hooks/usePreferences";
import {
  getGroups,
  createGroup,
  deleteGroup,
  joinGroup,
  leaveGroup,
  getJoinRequests,
  approveJoinRequest,
  rejectJoinRequest,
  getDiscussions,
  postDiscussion,
} from "../../services/api";
import Card from "../../components/Card";
import Button from "../../components/Button";
import Modal from "../../components/Modal";
import Loader from "../../components/Loader";
import AcademicContextFields, { emptyAcademicContext } from "../../components/subjects/AcademicContextFields";
import { useAcademicDefaults } from "../../hooks/useAcademicDefaults";

export default function StudyGroups() {
  const { t } = usePreferences();
  const { data: groups, loading, refetch } = useFetch(() => getGroups(), []);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ name: "", description: "" });
  const [academic, setAcademic] = useAcademicDefaults();
  const [creating, setCreating] = useState(false);
  const [deletingGroup, setDeletingGroup] = useState(null);

  const [activeGroup, setActiveGroup] = useState(null);
  const [discussions, setDiscussions] = useState([]);
  const [message, setMessage] = useState("");
  const [loadingDiscussions, setLoadingDiscussions] = useState(false);
  const [posting, setPosting] = useState(false);

  const [adminGroup, setAdminGroup] = useState(null);
  const [joinRequests, setJoinRequests] = useState([]);
  const [loadingRequests, setLoadingRequests] = useState(false);
  const [reviewingRequest, setReviewingRequest] = useState(null);

  const handleCreate = async (ev) => {
    ev.preventDefault();
    if (!form.name.trim()) return toast.error("Group name is required");
    setCreating(true);
    try {
      await createGroup({ ...form, grade: academic.grade || null, subject: academic.subject.trim() || null, medium: academic.medium || null });
      toast.success("Study group created!");
      setShowCreate(false);
      setForm({ name: "", description: "" });
      setAcademic(emptyAcademicContext);
      refetch();
    } catch {
      toast.error("Please log in to create a group");
    } finally {
      setCreating(false);
    }
  };

  const handleMembership = async (group) => {
    try {
      if (group.is_member) {
        await leaveGroup(group.id);
        toast.success("Left group");
      } else {
        const res = await joinGroup(group.id);
        toast.success(res.data.message || "Join request sent to the group admin");
      }
      refetch();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Please log in to update group membership");
    }
  };

  const handleDeleteGroup = async (group) => {
    const confirmed = window.confirm(
      `Delete "${group.name}"? Members, requests, and discussions will also be deleted.`
    );
    if (!confirmed) return;

    setDeletingGroup(group.id);
    try {
      await deleteGroup(group.id);
      toast.success("Study group deleted");
      refetch();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Could not delete this group");
    } finally {
      setDeletingGroup(null);
    }
  };

  const openDiscussion = async (group) => {
    if (!group.is_member) {
      toast.error("Your join request must be approved before opening discussions");
      return;
    }
    setActiveGroup(group);
    setLoadingDiscussions(true);
    try {
      const res = await getDiscussions(group.id);
      setDiscussions(res.data);
    } catch {
      toast.error("Could not load discussions");
    } finally {
      setLoadingDiscussions(false);
    }
  };

  const openJoinRequests = async (group) => {
    setAdminGroup(group);
    setLoadingRequests(true);
    try {
      const res = await getJoinRequests(group.id);
      setJoinRequests(res.data);
    } catch (err) {
      setAdminGroup(null);
      toast.error(err.response?.data?.detail || "Could not load join requests");
    } finally {
      setLoadingRequests(false);
    }
  };

  const handleRequestDecision = async (request, action) => {
    setReviewingRequest(request.id);
    try {
      if (action === "approve") {
        await approveJoinRequest(adminGroup.id, request.id);
        toast.success(`${request.user?.name || "User"} joined the group`);
      } else {
        await rejectJoinRequest(adminGroup.id, request.id);
        toast.success("Join request rejected");
      }
      setJoinRequests((items) => items.filter((item) => item.id !== request.id));
      refetch();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Could not review this request");
    } finally {
      setReviewingRequest(null);
    }
  };

  const handlePostMessage = async (ev) => {
    ev.preventDefault();
    if (!message.trim()) return;
    setPosting(true);
    try {
      const res = await postDiscussion(activeGroup.id, { message });
      setDiscussions((d) => [...d, res.data]);
      setMessage("");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Join the group before posting");
    } finally {
      setPosting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="page-title flex items-center gap-2">
          <FiUsers className="text-primary-600" /> {t("groups.title")}
        </h1>
        <Button onClick={() => setShowCreate(true)}>
          <FiPlus /> {t("groups.create")}
        </Button>
      </div>

      {loading ? (
        <Loader />
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {groups?.map((g) => (
            <Card key={g.id} className="flex flex-col gap-3">
              <h3 className="font-bold text-slate-800">{g.name}</h3>
              {g.is_admin && (
                <span className="inline-flex w-fit items-center gap-1 rounded-full bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-700">
                  <FiShield /> {t("groups.admin")}
                </span>
              )}
              <p className="text-sm text-slate-500 line-clamp-3">{g.description}</p>
              {g.subject && <span className="w-fit rounded-full bg-primary-50 px-2.5 py-1 text-xs font-semibold text-primary-700 dark:bg-primary-950/40 dark:text-primary-300">{g.subject}</span>}
              <p className="text-xs text-slate-400">
                {g.member_count} {t("groups.members")}
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                {g.is_admin ? (
                  <>
                    <Button
                      variant="secondary"
                      className="min-w-[120px] flex-1"
                      onClick={() => openJoinRequests(g)}
                    >
                      <FiShield />
                      {t("groups.requests")}
                      {g.pending_request_count ? ` (${g.pending_request_count})` : ""}
                    </Button>
                    <Button
                      variant="secondary"
                      className="min-w-[100px] flex-1 border-red-200 text-red-600 hover:bg-red-50"
                      loading={deletingGroup === g.id}
                      disabled={deletingGroup !== null}
                      onClick={() => handleDeleteGroup(g)}
                    >
                      <FiTrash2 /> {t("groups.delete")}
                    </Button>
                  </>
                ) : (
                  <Button
                    variant="secondary"
                    className="flex-1"
                    disabled={g.join_request_status === "pending"}
                    onClick={() => handleMembership(g)}
                  >
                    {g.is_member ? (
                      t("groups.leave")
                    ) : g.join_request_status === "pending" ? (
                      <>
                        <FiClock /> {t("groups.pending")}
                      </>
                    ) : (
                      t("groups.requestJoin")
                    )}
                  </Button>
                )}
                <Button
                  className="min-w-[100px] flex-1"
                  disabled={!g.is_member}
                  onClick={() => openDiscussion(g)}
                >
                  <FiMessageSquare /> {t("groups.discuss")}
                </Button>
              </div>
            </Card>
          ))}
          {groups?.length === 0 && (
            <p className="text-slate-500 col-span-full text-center py-10">
              {t("groups.noGroups")}
            </p>
          )}
        </div>
      )}

      {/* Create Group Modal */}
      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title="Create a Study Group">
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="text-sm font-medium text-slate-600 mb-1 block">Group Name</label>
            <input
              className="input-field"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
          </div>
          <AcademicContextFields value={academic} onChange={setAcademic} />
          <div>
            <label className="text-sm font-medium text-slate-600 mb-1 block">Description</label>
            <textarea
              className="input-field min-h-[100px]"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </div>
          <Button type="submit" className="w-full" loading={creating}>
            Create Group
          </Button>
        </form>
      </Modal>

      {/* Group Admin Join Requests Modal */}
      <Modal
        isOpen={!!adminGroup}
        onClose={() => setAdminGroup(null)}
        title={`Join Requests — ${adminGroup?.name || ""}`}
        maxWidth="max-w-xl"
      >
        {loadingRequests ? (
          <Loader />
        ) : (
          <div className="space-y-3">
            {joinRequests.map((request) => (
              <div
                key={request.id}
                className="flex flex-col gap-3 rounded-xl border border-slate-200 p-4 sm:flex-row sm:items-center"
              >
                <img
                  src={
                    request.user?.profile_image ||
                    `https://api.dicebear.com/7.x/initials/svg?seed=${request.user?.name}`
                  }
                  className="h-10 w-10 rounded-full object-cover"
                  alt=""
                />
                <div className="min-w-0 flex-1">
                  <p className="font-semibold text-slate-800">{request.user?.name}</p>
                  <p className="truncate text-xs text-slate-500">{request.user?.email}</p>
                </div>
                <div className="flex gap-2">
                  <Button
                    className="flex-1 sm:flex-none"
                    loading={reviewingRequest === request.id}
                    disabled={reviewingRequest !== null}
                    onClick={() => handleRequestDecision(request, "approve")}
                  >
                    <FiCheck /> Approve
                  </Button>
                  <Button
                    variant="secondary"
                    className="flex-1 sm:flex-none"
                    disabled={reviewingRequest !== null}
                    onClick={() => handleRequestDecision(request, "reject")}
                  >
                    <FiX /> Reject
                  </Button>
                </div>
              </div>
            ))}
            {joinRequests.length === 0 && (
              <div className="py-8 text-center">
                <FiUsers className="mx-auto mb-2 text-3xl text-slate-300" />
                <p className="text-sm text-slate-500">No pending join requests.</p>
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* Discussion Modal */}
      <Modal isOpen={!!activeGroup} onClose={() => setActiveGroup(null)} title={activeGroup?.name} maxWidth="max-w-xl">
        {loadingDiscussions ? (
          <Loader />
        ) : (
          <div className="space-y-4">
            <div className="max-h-80 overflow-y-auto space-y-3">
              {discussions.map((d) => (
                <div key={d.id} className="flex gap-3">
                  <img
                    src={d.user?.profile_image || `https://api.dicebear.com/7.x/initials/svg?seed=${d.user?.name}`}
                    className="w-8 h-8 rounded-full object-cover"
                    alt="user"
                  />
                  <div className="bg-slate-50 rounded-xl px-4 py-2.5 flex-1">
                    <p className="text-sm font-semibold text-slate-700">{d.user?.name}</p>
                    <p className="text-sm text-slate-600">{d.message}</p>
                  </div>
                </div>
              ))}
              {discussions.length === 0 && (
                <p className="text-sm text-slate-400 text-center py-4">No messages yet. Start the discussion!</p>
              )}
            </div>
            <form onSubmit={handlePostMessage} className="flex gap-2">
              <input
                className="input-field flex-1"
                placeholder="Write a message..."
                value={message}
                onChange={(e) => setMessage(e.target.value)}
              />
              <Button type="submit" loading={posting}>
                <FiSend />
              </Button>
            </form>
          </div>
        )}
      </Modal>
    </div>
  );
}
