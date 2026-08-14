import { Component, useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";
import {
  FiAward,
  FiCheckCircle,
  FiHelpCircle,
  FiRefreshCw,
  FiXCircle,
} from "react-icons/fi";

import { aiGenerateQuiz, aiSubmitQuiz } from "../../services/api";
import { usePreferences } from "../../hooks/usePreferences";
import Card from "../../components/Card";
import Button from "../../components/Button";
import Loader from "../../components/Loader";
import AcademicContextFields from "../../components/subjects/AcademicContextFields";
import { useAcademicDefaults } from "../../hooks/useAcademicDefaults";
import { motion } from "framer-motion";

const apiErrorMessage = (error, fallback) => {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string" && detail.trim()) return detail;
  if (typeof detail?.message === "string" && detail.message.trim()) return detail.message;
  if (!error?.response) return "The server could not be reached. Check your connection and try again.";
  return `${fallback} (HTTP ${error.response.status}).`;
};

const isValidQuestion = (question) =>
  Number.isInteger(question?.id) &&
  typeof question?.question === "string" &&
  question.question.trim().length > 0 &&
  Array.isArray(question?.options) &&
  question.options.length === 4 &&
  question.options.every((option) => typeof option === "string" && option.trim().length > 0);

class QuizErrorBoundary extends Component {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    console.error("Quiz page render error", error, info);
  }

  render() {
    if (!this.state.hasError) return this.props.children;
    return (
      <Card>
        <div role="alert" className="space-y-3 text-center">
          <h2 className="text-lg font-bold text-slate-800 dark:text-white">The quiz could not be displayed</h2>
          <p className="text-sm text-slate-600 dark:text-slate-300">The quiz data was not in the expected format. Please generate it again.</p>
          <Button onClick={() => this.setState({ hasError: false })}>Try Again</Button>
        </div>
      </Card>
    );
  }
}

function QuizGeneratorContent() {
  const { language, t } = usePreferences();
  const [form, setForm] = useState({
    subject: "",
    topic: "",
    num_questions: 5,
    difficulty: "medium",
    language,
  });
  const [academic, setAcademic] = useAcademicDefaults();
  const [quiz, setQuiz] = useState(null);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [empty, setEmpty] = useState(false);

  useEffect(() => {
    setForm((current) => ({ ...current, language }));
  }, [language]);

  const reviewByQuestion = useMemo(
    () =>
      Object.fromEntries(
        (result?.review || []).map((item) => [item.question_id, item])
      ),
    [result]
  );

  const generateQuiz = async () => {
    if (!form.topic.trim()) return toast.error(t("quiz.enterTopic"));

    setLoading(true);
    setQuiz(null);
    setAnswers({});
    setResult(null);
    setErrorMessage("");
    setEmpty(false);
    try {
      const response = await aiGenerateQuiz({ ...form, grade: academic.grade, medium: academic.medium, subject: academic.subject.trim() });
      const data = response?.data;
      if (!Array.isArray(data?.questions) || data.questions.length === 0) {
        setEmpty(true);
        return;
      }
      if (!data.questions.every(isValidQuestion)) {
        throw new Error("The server returned quiz data in an unexpected format.");
      }
      setQuiz(data);
    } catch (error) {
      const message = error.message === "The server returned quiz data in an unexpected format."
        ? error.message
        : apiErrorMessage(error, t("quiz.generateError"));
      setErrorMessage(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = (event) => {
    event.preventDefault();
    generateQuiz();
  };

  const selectAnswer = (questionId, answer) => {
    if (result) return;
    setAnswers((current) => ({ ...current, [questionId]: answer }));
  };

  const handleSubmit = async () => {
    const questions = Array.isArray(quiz?.questions) ? quiz.questions.filter(isValidQuestion) : [];
    if (!questions.length) {
      setQuiz(null);
      setEmpty(true);
      return;
    }
    const answeredCount = questions.filter((question) => answers[question.id]).length;
    if (answeredCount !== questions.length) {
      return toast.error(t("quiz.answerAll"));
    }

    setSubmitting(true);
    try {
      const response = await aiSubmitQuiz({
        answers: questions.map((question) => ({
          question_id: question.id,
          selected_answer: answers[question.id],
        })),
      });
      setResult(response.data);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (error) {
      const message = apiErrorMessage(error, t("quiz.submitError"));
      setErrorMessage(message);
      toast.error(message);
    } finally {
      setSubmitting(false);
    }
  };

  const resetQuiz = () => {
    setQuiz(null);
    setAnswers({});
    setResult(null);
    setErrorMessage("");
    setEmpty(false);
  };

  const tryAgain = () => generateQuiz();

  const resultMessage =
    result?.percentage >= 80
      ? t("quiz.excellent")
      : result?.percentage >= 50
        ? t("quiz.good")
        : t("quiz.keepPractising");

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="page-title flex items-center gap-2">
          <FiHelpCircle className="text-primary-600" /> {t("quiz.title")}
        </h1>
        <p className="mt-1 text-sm text-slate-500">{t("quiz.subtitle")}</p>
      </div>

      {!quiz && (
        <Card>
          <form onSubmit={handleGenerate} className="space-y-4">
            <AcademicContextFields value={academic} onChange={setAcademic} />
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-600">
                  {t("quiz.questionCount")}
                </label>
                <input
                  type="number"
                  min={1}
                  max={20}
                  className="input-field"
                  value={form.num_questions}
                  onChange={(event) =>
                    setForm({ ...form, num_questions: Number(event.target.value) })
                  }
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-600 dark:text-slate-300">
                  {t("quiz.difficulty")}
                </label>
                <select className="input-field" value={form.difficulty} onChange={(event) => setForm({ ...form, difficulty: event.target.value })}>
                  <option value="easy">{t("quiz.easy")}</option>
                  <option value="medium">{t("quiz.medium")}</option>
                  <option value="hard">{t("quiz.hard")}</option>
                </select>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-600">
                  {t("quiz.topic")}
                </label>
                <input
                  className="input-field"
                  placeholder={t("quiz.topicPlaceholder")}
                  value={form.topic}
                  onChange={(event) => setForm({ ...form, topic: event.target.value })}
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-600">
                  {t("quiz.quizLanguage")}
                </label>
                <select
                  className="input-field"
                  value={form.language}
                  onChange={(event) => setForm({ ...form, language: event.target.value })}
                >
                  <option value="en">{t("language.english")}</option>
                  <option value="ta">{t("language.tamil")}</option>
                  <option value="si">{t("language.sinhala")}</option>
                </select>
              </div>
            </div>

            <Button type="submit" className="w-full" loading={loading}>
              {t("quiz.generate")}
            </Button>
          </form>
        </Card>
      )}

      {loading && <Loader label={t("quiz.generating")} />}

      {!loading && errorMessage && (
        <Card>
          <div role="alert" className="space-y-3 text-center">
            <p className="font-semibold text-red-700 dark:text-red-300">{errorMessage}</p>
            <Button variant="secondary" onClick={tryAgain}><FiRefreshCw /> {t("quiz.tryAgain")}</Button>
          </div>
        </Card>
      )}

      {!loading && empty && !errorMessage && (
        <Card>
          <div role="status" className="space-y-3 text-center">
            <p className="font-semibold text-slate-700 dark:text-slate-200">No quiz questions were generated. Try a different topic or try again.</p>
            <Button variant="secondary" onClick={tryAgain}><FiRefreshCw /> {t("quiz.tryAgain")}</Button>
          </div>
        </Card>
      )}

      {result && (
        <Card className="border border-primary-200 bg-brand-gradient-soft text-center dark:border-primary-800">
          <motion.div initial={{ scale: .75, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ type: "spring", stiffness: 220, damping: 18 }}><FiAward className="mx-auto mb-2 text-4xl text-primary-600" /></motion.div>
          <h2 className="text-xl font-bold text-slate-800">{t("quiz.result")}</h2>
          <div className="my-4 flex items-center justify-center gap-8">
            <div>
              <p className="text-sm text-slate-500">{t("quiz.score")}</p>
              <p className="text-3xl font-extrabold text-primary-600">
                {result.score}/{result.total}
              </p>
            </div>
            <div>
              <p className="text-sm text-slate-500">{t("quiz.percentage")}</p>
              <p className="text-3xl font-extrabold text-primary-600">
                {result.percentage}%
              </p>
            </div>
          </div>
          <p className="font-medium text-slate-700">{resultMessage}</p>
        </Card>
      )}

      {Array.isArray(quiz?.questions) && quiz.questions.length > 0 && (
        <div className="space-y-4">
          {quiz.questions.map((question, index) => {
            const review = reviewByQuestion[question.id];
            return (
              <motion.div key={question.id} initial={{opacity:0,x:16}} animate={{opacity:1,x:0}} transition={{delay:index*.035}}><Card>
                <div className="mb-3 flex items-start justify-between gap-3">
                  <p className="font-semibold text-slate-800">
                    {index + 1}. {question.question}
                  </p>
                  {review &&
                    (review.is_correct ? (
                      <span className="inline-flex shrink-0 items-center gap-1 text-sm font-semibold text-emerald-600">
                        <FiCheckCircle /> {t("quiz.correct")}
                      </span>
                    ) : (
                      <span className="inline-flex shrink-0 items-center gap-1 text-sm font-semibold text-red-600">
                        <FiXCircle /> {t("quiz.incorrect")}
                      </span>
                    ))}
                </div>

                <div className="space-y-2">
                  {question.options.map((option, optionIndex) => {
                    const selected = answers[question.id] === option;
                    const isCorrectOption = review?.correct_answer === option;
                    const isWrongSelection = Boolean(review && selected && !review.is_correct);
                    let optionClass =
                      "border-slate-200 text-slate-600 hover:border-primary-300 hover:bg-primary-50 dark:border-slate-600 dark:hover:bg-slate-800";

                    if (!review && selected) {
                      optionClass =
                        "border-primary-500 bg-primary-50 text-primary-700 ring-2 ring-primary-100 dark:bg-primary-950/50 dark:text-primary-200";
                    } else if (isCorrectOption) {
                      optionClass =
                        "border-emerald-500 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300";
                    } else if (isWrongSelection) {
                      optionClass =
                        "border-red-500 bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-300";
                    }

                    return (
                      <label
                        key={`${question.id}-${optionIndex}`}
                        className={`flex w-full items-center gap-3 rounded-xl border px-4 py-3 text-left text-sm transition focus-within:ring-2 focus-within:ring-primary-500 ${result ? "cursor-default" : "cursor-pointer"} ${optionClass}`}
                      >
                        <input type="radio" name={`question-${question.id}`} value={option} checked={selected} disabled={Boolean(result)} onChange={() => selectAnswer(question.id, option)} className="sr-only" />
                        <span
                          className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full border text-xs font-bold ${
                            selected ? "border-current" : "border-slate-300"
                          }`}
                        >
                          {String.fromCharCode(65 + optionIndex)}
                        </span>
                        {option}
                      </label>
                    );
                  })}
                </div>

                {review && (
                  <div className="mt-4 rounded-xl bg-slate-50 p-3 text-sm dark:bg-slate-800">
                    <p className="text-slate-600">
                      <span className="font-semibold">{t("quiz.yourAnswer")}:</span>{" "}
                      {review.selected_answer || t("quiz.notAnswered")}
                    </p>
                    {!review.is_correct && <p className="mt-1 font-semibold text-emerald-700 dark:text-emerald-300">
                      {t("quiz.correctAnswer")}: {review.correct_answer}
                    </p>}
                  </div>
                )}
              </Card></motion.div>
            );
          })}

          {!result ? (
            <Button className="w-full" loading={submitting} onClick={handleSubmit}>
              <FiCheckCircle />
              {submitting ? t("quiz.submitting") : t("quiz.submit")}
            </Button>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2">
              <Button variant="secondary" className="w-full" onClick={tryAgain} loading={loading}>
                <FiRefreshCw /> {t("quiz.tryAgain")}
              </Button>
              <Button className="w-full" onClick={resetQuiz}>
                <FiRefreshCw /> {t("quiz.newQuiz")}
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function QuizGenerator() {
  return <QuizErrorBoundary><QuizGeneratorContent /></QuizErrorBoundary>;
}
