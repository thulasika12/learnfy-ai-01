import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  FiArrowRight,
  FiBookOpen,
  FiCheckCircle,
  FiFileText,
  FiHelpCircle,
  FiMessageCircle,
  FiPlay,
  FiTrendingUp,
  FiUsers,
  FiZap,
} from "react-icons/fi";

import { usePreferences } from "../hooks/usePreferences";

const features = [
  {
    icon: FiMessageCircle,
    titleKey: "home.featureDoubt",
    descKey: "home.featureDoubtDesc",
    tone: "from-violet-500 to-indigo-500",
  },
  {
    icon: FiFileText,
    titleKey: "home.featureNotes",
    descKey: "home.featureNotesDesc",
    tone: "from-cyan-500 to-sky-500",
  },
  {
    icon: FiUsers,
    titleKey: "home.featureGroups",
    descKey: "home.featureGroupsDesc",
    tone: "from-emerald-500 to-teal-500",
  },
  {
    icon: FiHelpCircle,
    titleKey: "home.featureQuiz",
    descKey: "home.featureQuizDesc",
    tone: "from-amber-500 to-orange-500",
  },
  {
    icon: FiTrendingUp,
    titleKey: "home.featureProgress",
    descKey: "home.featureProgressDesc",
    tone: "from-fuchsia-500 to-pink-500",
  },
  {
    icon: FiBookOpen,
    titleKey: "home.featureSpace",
    descKey: "home.featureSpaceDesc",
    tone: "from-blue-500 to-indigo-500",
  },
];

const stats = [
  ["AI-powered", "Study support"],
  ["24/7", "Doubt assistance"],
  ["One place", "For every learner"],
];
const learningFlow = ["Discover", "Understand", "Practise", "Connect", "Track"];

export default function Home() {
  const { t } = usePreferences();

  return (
    <div className="overflow-hidden bg-[#f8fbff] dark:bg-slate-950">
      <section className="relative isolate overflow-hidden bg-slate-950 text-white">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_15%_20%,rgba(45,212,191,0.28),transparent_30%),radial-gradient(circle_at_85%_30%,rgba(99,102,241,0.34),transparent_35%),linear-gradient(135deg,#071426_0%,#0f2040_50%,#172554_100%)]" />
        <div className="absolute inset-0 opacity-30 [background-image:linear-gradient(rgba(255,255,255,.05)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.05)_1px,transparent_1px)] [background-size:48px_48px]" />

        <motion.div
          className="absolute -top-24 right-8 h-72 w-72 rounded-full bg-cyan-400/20 blur-3xl"
          animate={{ scale: [1, 1.18, 1], x: [0, 18, 0] }}
          transition={{ repeat: Infinity, duration: 8 }}
        />
        <motion.div
          className="absolute -bottom-24 left-8 h-72 w-72 rounded-full bg-violet-500/25 blur-3xl"
          animate={{ scale: [1.1, 0.95, 1.1], x: [0, -16, 0] }}
          transition={{ repeat: Infinity, duration: 10 }}
        />

        <div className="relative z-10 mx-auto grid max-w-7xl items-center gap-14 px-6 py-20 lg:grid-cols-[1.1fr_.9fr] lg:py-28">
          <motion.div
            initial="hidden" animate="show" variants={{ hidden:{opacity:0}, show:{opacity:1,transition:{staggerChildren:.1}} }}
          >
            <motion.div variants={{hidden:{opacity:0,y:16},show:{opacity:1,y:0}}} className="mb-6 inline-flex items-center gap-2 rounded-full border border-cyan-300/20 bg-white/10 px-4 py-2 text-sm font-semibold text-cyan-100 backdrop-blur">
              <FiZap className="text-cyan-300" /> {t("home.badge")}
            </motion.div>

            <motion.h1 variants={{hidden:{opacity:0,y:18},show:{opacity:1,y:0}}} className="max-w-3xl text-4xl font-black leading-tight tracking-tight sm:text-5xl lg:text-7xl">
              {t("home.heroOne")}
              <span className="block bg-gradient-to-r from-cyan-300 via-sky-300 to-violet-300 bg-clip-text text-transparent">
                {t("home.heroTwo")}
              </span>
            </motion.h1>

            <motion.p variants={{hidden:{opacity:0,y:18},show:{opacity:1,y:0}}} className="mt-6 max-w-2xl break-words text-lg leading-8 text-slate-300 md:text-xl">
              {t("home.description")}
            </motion.p>

            <motion.div variants={{hidden:{opacity:0,y:18},show:{opacity:1,y:0}}} className="mt-9 flex flex-col gap-4 sm:flex-row">
              <Link
                to="/register"
                className="inline-flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-cyan-400 to-blue-500 px-7 py-3.5 font-bold text-slate-950 shadow-xl shadow-cyan-500/20 transition hover:-translate-y-0.5 hover:shadow-cyan-400/30"
              >
                {t("home.startFree")} <FiArrowRight />
              </Link>
              <Link
                to="/notes"
                className="inline-flex items-center justify-center gap-2 rounded-2xl border border-white/20 bg-white/10 px-7 py-3.5 font-bold text-white backdrop-blur transition hover:bg-white/15"
              >
                <FiPlay /> {t("home.exploreNotes")}
              </Link>
            </motion.div>

            <div className="mt-9 flex flex-wrap gap-x-6 gap-y-3 text-sm text-slate-300">
              {[t("home.easy"), t("home.studentFriendly"), t("home.aiSupport")].map((item) => (
                <span key={item} className="flex items-center gap-2">
                  <FiCheckCircle className="text-emerald-300" /> {item}
                </span>
              ))}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 35 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.7, delay: 0.15 }}
            className="relative"
          >
            <div className="absolute -inset-5 rounded-[2.5rem] bg-gradient-to-r from-cyan-400/20 to-violet-500/20 blur-2xl" />
            <div className="relative rounded-[2rem] border border-white/15 bg-white/10 p-5 shadow-2xl backdrop-blur-xl">
              <div className="rounded-[1.5rem] bg-white p-6 text-slate-800 shadow-xl">
                <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                  <div className="flex items-center gap-3">
                    <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 text-white">
                      <FiZap size={21} />
                    </div>
                    <div>
                      <p className="font-extrabold">AI Study Assistant</p>
                      <p className="text-xs text-emerald-600">● Online and ready</p>
                    </div>
                  </div>
                  <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-bold text-indigo-600">Gemini</span>
                </div>

                <div className="space-y-4 py-6">
                  <div className="max-w-[85%] rounded-2xl rounded-tl-sm bg-slate-100 px-4 py-3 text-sm leading-6">
                    Hi! What topic would you like to understand today?
                  </div>
                  <div className="ml-auto max-w-[82%] rounded-2xl rounded-tr-sm bg-gradient-to-r from-indigo-600 to-violet-600 px-4 py-3 text-sm leading-6 text-white">
                    Explain photosynthesis in a simple way.
                  </div>
                  <div className="max-w-[90%] rounded-2xl rounded-tl-sm border border-cyan-100 bg-cyan-50 px-4 py-3 text-sm leading-6">
                    Plants use sunlight, water, and carbon dioxide to make food and release oxygen. Think of leaves as tiny solar kitchens! 🌱
                  </div>
                </div>

                <div className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-400">
                  Ask your academic question...
                  <span className="ml-auto flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 text-white">
                    <FiArrowRight />
                  </span>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      <section className="relative z-20 mx-auto -mt-8 max-w-5xl px-6">
        <div className="grid overflow-hidden rounded-3xl border border-slate-100 bg-white shadow-xl shadow-slate-200/60 sm:grid-cols-3">
          {stats.map(([value, label], index) => (
            <div key={value} className={`px-7 py-6 text-center ${index ? "border-t sm:border-l sm:border-t-0" : ""} border-slate-100`}>
              <p className="text-xl font-black text-slate-900">{value}</p>
              <p className="mt-1 text-sm text-slate-500">{label}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-6 py-24">
        <div className="mx-auto max-w-2xl text-center">
          <span className="rounded-full bg-indigo-50 px-4 py-2 text-sm font-bold text-indigo-600">
            {t("home.allInOne")}
          </span>
          <h2 className="mt-5 text-3xl font-black tracking-tight text-slate-900 md:text-5xl">
            {t("home.studySmarter")}
          </h2>
          <p className="mt-4 text-lg leading-8 text-slate-500">
            {t("home.toolsDescription")}
          </p>
        </div>

        <div className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature, index) => (
            <motion.div
              key={feature.titleKey}
              initial={{ opacity: 0, y: 22 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: index * 0.06 }}
              className="group rounded-3xl border border-slate-100 bg-white p-7 shadow-sm transition duration-300 hover:-translate-y-2 hover:shadow-xl hover:shadow-slate-200/70"
            >
              <div className={`flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br ${feature.tone} text-white shadow-lg transition group-hover:scale-110`}>
                <feature.icon size={24} />
              </div>
              <h3 className="mt-6 text-xl font-extrabold text-slate-900">
                {t(feature.titleKey)}
              </h3>
              <p className="mt-3 leading-7 text-slate-500">{t(feature.descKey)}</p>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 pb-20" aria-label="Learning flow">
        <motion.div initial="hidden" whileInView="show" viewport={{once:true,amount:.35}} variants={{show:{transition:{staggerChildren:.1}}}} className="grid gap-3 sm:grid-cols-5">
          {learningFlow.map((step,index)=><motion.div key={step} variants={{hidden:{opacity:0,x:-12},show:{opacity:1,x:0}}} className="relative rounded-2xl border border-primary-100 bg-white px-4 py-5 text-center font-bold text-slate-800 shadow-sm dark:border-slate-700 dark:bg-slate-900 dark:text-white"><span className="mb-2 block text-xs text-primary-500">0{index+1}</span>{step}{index<learningFlow.length-1&&<FiArrowRight className="absolute -right-4 top-1/2 z-10 hidden -translate-y-1/2 text-primary-400 sm:block"/>}</motion.div>)}
        </motion.div>
      </section>

      <section className="mx-auto max-w-7xl px-6 pb-24">
        <div className="relative overflow-hidden rounded-[2rem] bg-gradient-to-r from-indigo-600 via-violet-600 to-cyan-500 px-7 py-14 text-center text-white shadow-2xl shadow-indigo-200 md:px-14 md:py-16">
          <div className="absolute -right-14 -top-14 h-48 w-48 rounded-full bg-white/10" />
          <div className="absolute -bottom-20 -left-8 h-56 w-56 rounded-full bg-slate-950/10" />
          <div className="relative">
            <p className="text-sm font-bold uppercase tracking-[0.2em] text-cyan-100">
              {t("home.journey")}
            </p>
            <h2 className="mt-4 text-3xl font-black md:text-5xl">{t("home.ready")}</h2>
            <p className="mx-auto mt-4 max-w-2xl text-lg text-white/85">
              {t("home.ctaDescription")}
            </p>
            <Link
              to="/register"
              className="mt-8 inline-flex items-center gap-2 rounded-2xl bg-white px-7 py-3.5 font-extrabold text-indigo-700 shadow-xl transition hover:-translate-y-0.5"
            >
              {t("home.createFree")} <FiArrowRight />
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
