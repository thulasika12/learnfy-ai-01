import AppRoutes from "./routes/AppRoutes";
import ErrorBoundary from "./components/ErrorBoundary";
import { MotionConfig } from "framer-motion";

function App() {
  return <ErrorBoundary><MotionConfig reducedMotion="user"><AppRoutes /></MotionConfig></ErrorBoundary>;
}

export default App;
